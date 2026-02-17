/* WebApp/static/js/dashboard.js
   LibreRecorder UI
   - Domain tabs: Health / Ecology / Veterinary / More
   - Level tabs: Not Analyzed / Not for Analysis (Analyzed removed)
   - Two-panel row: Datasets + Models
   - Select dataset + select model + Run
   - Models are auto-discovered via GET /models (processing/*.py)
*/

(() => {
  // --------- Constants ----------
  const DOMAINS = [
    { id: "health",     label: "Health" },
    { id: "ecology",    label: "Ecology" },
    { id: "veterinary", label: "Veterinary" },
    { id: "more",       label: "More" },
  ];

  // Removed "Analyzed" per request
  const LEVELS = [
    "Not Analyzed",
    "Not for Analysis"
  ];

  // --------- DOM ----------
  const domainTabsEl = document.getElementById("domainTabs");
  const levelTabsEl  = document.getElementById("levelTabs");

  // Dataset + model panels (your new layout)
  const datasetsListEl  = document.getElementById("datasetsList");
  const modelsListEl    = document.getElementById("modelsList");
  const datasetsCountEl = document.getElementById("datasetsCount");
  const modelsCountEl   = document.getElementById("modelsCount");

  // Empty state
  const emptyEl = document.getElementById("emptyState");

  // Controls
  const searchEl   = document.getElementById("search");
  const btnRefresh = document.getElementById("btnRefresh");
  const btnQuick   = document.getElementById("btnQuickIntake");

  // Modal controls
  const modalBackdrop  = document.getElementById("modalBackdrop");
  const btnCloseModal  = document.getElementById("btnCloseModal");
  const btnCancelModal = document.getElementById("btnCancelModal");
  const btnSaveModal   = document.getElementById("btnSaveModal");

  const m_case   = document.getElementById("m_case");
  const m_domain = document.getElementById("m_domain");
  const m_level  = document.getElementById("m_level");
  const m_state  = document.getElementById("m_state");
  const m_desc   = document.getElementById("m_desc");
  const m_tags   = document.getElementById("m_tags");
  const m_notes  = document.getElementById("m_notes");

  // Run bar
  const selectedDatasetLabelEl = document.getElementById("selectedDatasetLabel");
  const selectedModelLabelEl   = document.getElementById("selectedModelLabel");
  const runStatusEl            = document.getElementById("runStatus");
  const btnRunModel            = document.getElementById("btnRunModel");

  // Resources panel tabs (unchanged)
  document.querySelectorAll(".resource-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".resource-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const panel = btn.getAttribute("data-panel");
      document.querySelectorAll(".resource-view").forEach(v => v.classList.remove("active"));
      const view = document.getElementById(`panel-${panel}`);
      if (view) view.classList.add("active");
    });
  });

  // --------- State ----------
  const STORE_KEY = "lr_ui_v3";

  const defaultUI = {
    activeDomain: "health",
    activeLevel: "Not Analyzed",
    search: ""
  };

  let ui = loadUI();

  let allCases  = []; // from /cases
  let allModels = []; // from /models

  let selectedCaseId  = null;
  let selectedModelId = null;

  // --------- Persistence ----------
  function loadUI() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return { ...defaultUI };
      const parsed = JSON.parse(raw);
      const merged = { ...defaultUI, ...parsed };

      if (!LEVELS.includes(merged.activeLevel)) merged.activeLevel = defaultUI.activeLevel;
      if (!DOMAINS.some(d => d.id === merged.activeDomain)) merged.activeDomain = defaultUI.activeDomain;

      return merged;
    } catch {
      return { ...defaultUI };
    }
  }

  function saveUI() {
    localStorage.setItem(STORE_KEY, JSON.stringify(ui));
  }

  // Metadata per case (still localStorage for now)
  function metaKey(caseId) {
    return `lr_meta_${caseId}`;
  }

  function loadMeta(caseId) {
    try {
      const raw = localStorage.getItem(metaKey(caseId));
      if (!raw) return null;
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function saveMeta(caseId, meta) {
    localStorage.setItem(metaKey(caseId), JSON.stringify(meta));
  }

  function ensureDefaultMeta(caseObj) {
    const existing = loadMeta(caseObj.case_id);
    if (existing) return existing;

    const meta = {
      domain: ui.activeDomain,
      level: ui.activeLevel,
      state: "Intake",
      description: caseObj.description || "",
      tags: "",
      notes: ""
    };
    saveMeta(caseObj.case_id, meta);
    return meta;
  }

  // --------- UI Helpers ----------
  function setBodyDomain(domainId) {
    // CSS uses: body[data-domain="health|ecology|veterinary|more"]
    document.body.setAttribute("data-domain", domainId);
  }

  function setRunEnabled() {
    const ok = !!selectedCaseId && !!selectedModelId;
    if (btnRunModel) btnRunModel.disabled = !ok;
  }

  function setRunStatus(msg) {
    if (!runStatusEl) return;
    runStatusEl.textContent = msg || "";
  }

  function clearSelectionsIfMissing() {
    if (selectedCaseId) {
      const exists = allCases.some(c => c.case_id === selectedCaseId);
      if (!exists) selectedCaseId = null;
    }
    if (selectedModelId) {
      const exists = allModels.some(m => m.id === selectedModelId);
      if (!exists) selectedModelId = null;
    }

    if (selectedDatasetLabelEl) selectedDatasetLabelEl.textContent = selectedCaseId || "None";
    if (selectedModelLabelEl) selectedModelLabelEl.textContent = selectedModelId || "None";
    setRunEnabled();
  }

  // --------- Rendering ----------
  function renderDomainTabs() {
    if (!domainTabsEl) return;
    domainTabsEl.innerHTML = "";

    DOMAINS.forEach(d => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = `tab ${ui.activeDomain === d.id ? "active" : ""}`;
      b.textContent = d.label;

      b.addEventListener("click", () => {
        ui.activeDomain = d.id;
        saveUI();
        setBodyDomain(ui.activeDomain);
        setRunStatus("");
        renderAll();
      });

      domainTabsEl.appendChild(b);
    });
  }

  function renderLevelTabs() {
    if (!levelTabsEl) return;
    levelTabsEl.innerHTML = "";

    LEVELS.forEach(level => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = `tab ${ui.activeLevel === level ? "active" : ""}`;
      b.textContent = level;

      b.addEventListener("click", () => {
        ui.activeLevel = level;
        saveUI();
        setRunStatus("");
        renderAll();
      });

      levelTabsEl.appendChild(b);
    });
  }

  function matchesSearch(caseObj, meta, q) {
    if (!q) return true;
    const hay = [
      caseObj.case_id || "",
      meta?.description || "",
      caseObj.description || "",
      meta?.tags || ""
    ].join(" ").toLowerCase();
    return hay.includes(q.toLowerCase());
  }

  async function getResultCount(caseId) {
    try {
      const r = await fetch(`/results/${encodeURIComponent(caseId)}`);
      if (!r.ok) return 0;
      const arr = await r.json();
      return Array.isArray(arr) ? arr.length : 0;
    } catch {
      return 0;
    }
  }

  function renderModels() {
    if (!modelsListEl) return;
    modelsListEl.innerHTML = "";

    const sorted = [...allModels].sort((a, b) => String(a.name).localeCompare(String(b.name)));

    for (const m of sorted) {
      const card = document.createElement("div");
      card.className = "item-card model";
      card.dataset.modelId = m.id;

      if (selectedModelId === m.id) card.classList.add("selected");

      // Keep the schematic card style you already had
      card.innerHTML = `
        <div class="item-left">
          <div class="badge">ML</div>
        </div>
        <div class="item-main">
          <div class="item-title">${escapeHtml(m.name || m.id)}</div>
          <div class="item-lines">
            <div><span class="k">id:</span> ${escapeHtml(m.id)}</div>
            ${m.file ? `<div><span class="k">file:</span> ${escapeHtml(m.file)}</div>` : ``}
          </div>
        </div>
      `;

      card.addEventListener("click", () => {
        selectedModelId = m.id;
        if (selectedModelLabelEl) selectedModelLabelEl.textContent = selectedModelId;
        setRunStatus("");
        setRunEnabled();
        renderModels(); // refresh highlight
      });

      modelsListEl.appendChild(card);
    }

    if (modelsCountEl) modelsCountEl.textContent = String(sorted.length);
    if (selectedModelLabelEl) selectedModelLabelEl.textContent = selectedModelId || "None";
    setRunEnabled();
  }

  async function renderDatasets() {
    if (!datasetsListEl) return;
    datasetsListEl.innerHTML = "";

    const q = (ui.search || "").trim();
    const visible = [];

    for (const c of allCases) {
      const meta = ensureDefaultMeta(c);

      if (meta.domain !== ui.activeDomain) continue;
      if (meta.level !== ui.activeLevel) continue;
      if (!matchesSearch(c, meta, q)) continue;

      visible.push({ c, meta });
    }

    if (datasetsCountEl) datasetsCountEl.textContent = String(visible.length);

    if (visible.length === 0) {
      if (emptyEl) {
        emptyEl.style.display = "block";
        emptyEl.textContent = "No datasets match this view. Upload or change filters.";
      }
      return;
    } else {
      if (emptyEl) emptyEl.style.display = "none";
    }

    for (const { c, meta } of visible) {
      const card = document.createElement("div");
      card.className = "item-card dataset";
      card.setAttribute("data-case", c.case_id);

      if (selectedCaseId === c.case_id) card.classList.add("selected");

      card.innerHTML = `
        <div class="item-left">
          <div class="badge">DS</div>
        </div>
        <div class="item-main">
          <div class="item-title">${escapeHtml(c.case_id)}</div>
          <div class="item-lines">
            <div class="muted">${escapeHtml((meta.description || c.description || "—").trim())}</div>
            <div><span class="k">Created:</span> ${new Date(c.created_at).toLocaleString()}</div>
            <div class="meta-row">
              <span class="muted">${escapeHtml(meta.tags || "")}</span>
              <span class="muted resCount">Results: …</span>
            </div>
          </div>

          <div class="item-actions">
            <a href="/render/${encodeURIComponent(c.case_id)}" target="_blank">View</a>
            <a href="/results/${encodeURIComponent(c.case_id)}" target="_blank">Raw</a>
            <a href="/rich_results/${encodeURIComponent(c.case_id)}" target="_blank">Rich</a>
            <a href="#" class="editLink">Edit</a>
          </div>
        </div>
      `;

      // Select dataset by clicking card (but not links)
      card.addEventListener("click", (e) => {
        const t = e.target;
        if (t && (t.tagName === "A" || t.closest("a"))) return;

        selectedCaseId = c.case_id;
        if (selectedDatasetLabelEl) selectedDatasetLabelEl.textContent = selectedCaseId;
        setRunStatus("");
        setRunEnabled();
        renderDatasets(); // refresh highlight
      });

      // Edit metadata
      const edit = card.querySelector(".editLink");
      if (edit) {
        edit.addEventListener("click", (e) => {
          e.preventDefault();
          openModal(c.case_id);
        });
      }

      datasetsListEl.appendChild(card);

      // fill result count async
      getResultCount(c.case_id).then(n => {
        const el = card.querySelector(".resCount");
        if (el) el.textContent = `Results: ${n}`;
      });
    }

    if (selectedDatasetLabelEl) selectedDatasetLabelEl.textContent = selectedCaseId || "None";
    setRunEnabled();
  }

  function renderAll() {
    setBodyDomain(ui.activeDomain);
    renderDomainTabs();
    renderLevelTabs();
    renderModels();
    renderDatasets();
    clearSelectionsIfMissing();
  }

  // --------- Modal ----------
  function openModal(caseId) {
    const c = allCases.find(x => x.case_id === caseId);
    if (!c) return;

    const meta = ensureDefaultMeta(c);

    m_case.value = c.case_id;
    m_case.disabled = true;

    m_domain.value = meta.domain || ui.activeDomain;
    m_level.value  = meta.level  || ui.activeLevel;
    m_state.value  = meta.state  || "Intake";
    m_desc.value   = meta.description || c.description || "";
    m_tags.value   = meta.tags || "";
    m_notes.value  = meta.notes || "";

    modalBackdrop.style.display = "flex";
  }

  function openQuickIntake() {
    m_case.value = "";
    m_case.disabled = false;

    m_domain.value = ui.activeDomain;
    m_level.value  = ui.activeLevel;
    m_state.value  = "Intake";
    m_desc.value   = "";
    m_tags.value   = "";
    m_notes.value  = "";

    modalBackdrop.style.display = "flex";
    m_case.focus();
  }

  function closeModal() {
    modalBackdrop.style.display = "none";
  }

  if (btnCloseModal) btnCloseModal.addEventListener("click", closeModal);
  if (btnCancelModal) btnCancelModal.addEventListener("click", closeModal);
  if (modalBackdrop) {
    modalBackdrop.addEventListener("click", (e) => {
      if (e.target === modalBackdrop) closeModal();
    });
  }

  if (btnSaveModal) {
    btnSaveModal.addEventListener("click", () => {
      const caseId = (m_case.value || "").trim();
      if (!caseId) {
        alert("Case ID is required. Upload a dataset first, or type an existing case id.");
        return;
      }

      const meta = {
        domain: m_domain.value,
        level: m_level.value,
        state: m_state.value,
        description: (m_desc.value || "").trim(),
        tags: (m_tags.value || "").trim(),
        notes: (m_notes.value || "").trim()
      };

      saveMeta(caseId, meta);
      closeModal();
      setRunStatus("");
      renderAll();
    });
  }

  if (btnQuick) btnQuick.addEventListener("click", openQuickIntake);

  // --------- Run model ----------
  if (btnRunModel) {
    btnRunModel.addEventListener("click", async () => {
      if (!selectedCaseId || !selectedModelId) return;

      try {
        btnRunModel.disabled = true;
        setRunStatus("Running…");

        const r = await fetch("/run_model", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            case_id: selectedCaseId,
            model_id: selectedModelId
          })
        });

        const data = await r.json().catch(() => ({}));
        if (!r.ok) {
          setRunStatus(data.error || `Run failed (${r.status})`);
          setRunEnabled();
          return;
        }

        // Prefer aggregate display if present
        if (data && data.aggregate && Object.keys(data.aggregate).length) {
          setRunStatus(`Done: ${prettyAggregate(data.aggregate)}`);
        } else if (data && typeof data.result !== "undefined") {
          const units = data.units ? ` ${data.units}` : "";
          setRunStatus(`Done: ${data.result}${units}`);
        } else {
          setRunStatus("Done.");
        }

        // refresh dataset list so "Results: N" updates
        renderDatasets();
        setRunEnabled();
      } catch (e) {
        console.error(e);
        setRunStatus("Run failed (network/server).");
        setRunEnabled();
      }
    });
  }

  // --------- Data ----------
  async function fetchCases() {
    const r = await fetch("/cases");
    if (!r.ok) throw new Error("Failed to fetch /cases");
    const arr = await r.json();
    return Array.isArray(arr) ? arr : [];
  }

  async function fetchModels() {
    const r = await fetch("/models");
    if (!r.ok) return [];
    const arr = await r.json();
    return Array.isArray(arr) ? arr : [];
  }

  // --------- Events ----------
  if (btnRefresh) {
    btnRefresh.addEventListener("click", async () => {
      await init();
    });
  }

  if (searchEl) {
    searchEl.value = ui.search || "";
    searchEl.addEventListener("input", () => {
      ui.search = searchEl.value;
      saveUI();
      setRunStatus("");
      renderAll();
    });
  }

  // --------- Helpers ----------
  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function prettyAggregate(agg) {
    // common patterns:
    // { mean_pixel_avg: 123.4 }
    // { class_counts: { Dark: 10, Light: 5 } }
    try {
      if (typeof agg.mean_pixel_avg !== "undefined") {
        return `mean_pixel_avg=${agg.mean_pixel_avg}`;
      }
      if (agg.class_counts && typeof agg.class_counts === "object") {
        const parts = Object.entries(agg.class_counts).map(([k, v]) => `${k}:${v}`);
        return `class_counts={${parts.join(", ")}}`;
      }
      // fallback
      return JSON.stringify(agg);
    } catch {
      return "ok";
    }
  }

  // --------- Init ----------
  async function init() {
    try {
      // Fetch both in parallel
      const [cases, models] = await Promise.all([fetchCases(), fetchModels()]);
      allCases = cases;
      allModels = models;

      // If nothing selected, keep as None. If selection exists but disappeared, clear.
      clearSelectionsIfMissing();

      renderAll();
    } catch (e) {
      console.error(e);
      if (emptyEl) {
        emptyEl.style.display = "block";
        emptyEl.textContent = "Dashboard failed to load. Check server logs.";
      }
    }
  }

  init();
})();

// Scroll hint (kept from your prior version)
document.addEventListener("DOMContentLoaded", () => {
  const hint = document.getElementById("scrollHint");
  const resources = document.querySelector(".resource-panel");

  if (!hint || !resources) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        hint.classList.remove("visible");
      } else {
        hint.classList.add("visible");
      }
    },
    { root: null, threshold: 0.05 }
  );

  observer.observe(resources);
});
