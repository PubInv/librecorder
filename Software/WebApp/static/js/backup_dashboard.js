/* WebApp/static/js/dashboard.js
   LibreRecorder UI
*/

(() => {
  const DOMAINS = [
    { id: "health", label: "Health" },
    { id: "ecology", label: "Ecology" },
    { id: "veterinary", label: "Veterinary" },
    { id: "more", label: "More" },
  ];

  const LEVELS = [
    "Not Analyzed",
    "Not for Analysis"
  ];

  const domainTabsEl = document.getElementById("domainTabs");
  const levelTabsEl  = document.getElementById("levelTabs");

  const datasetsListEl  = document.getElementById("datasetsList");
  const modelsListEl    = document.getElementById("modelsList");
  const datasetsCountEl = document.getElementById("datasetsCount");
  const modelsCountEl   = document.getElementById("modelsCount");

  const emptyEl = document.getElementById("emptyState");

  const searchEl   = document.getElementById("search");
  const btnRefresh = document.getElementById("btnRefresh");
  const btnQuick   = document.getElementById("btnQuickIntake");

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

  const selectedDatasetLabelEl = document.getElementById("selectedDatasetLabel");
  const selectedModelLabelEl   = document.getElementById("selectedModelLabel");
  const runStatusEl            = document.getElementById("runStatus");

  const STORE_KEY = "lr_ui_v3";

  const defaultUI = {
    activeDomain: "health",
    activeLevel: "Not Analyzed",
    search: ""
  };

  let ui = loadUI();
  let allCases = [];
  let allModels = [];

  let selectedCaseId = null;
  let selectedModelId = null;

  window.selectedCaseId = null;
  window.selectedModelId = null;

  function getRunBtn() {
    return document.getElementById("btnRunModel");
  }

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

  function setBodyDomain(domainId) {
    document.body.setAttribute("data-domain", domainId);
  }

  function syncGlobalSelection() {
    window.selectedCaseId = selectedCaseId;
    window.selectedModelId = selectedModelId;
  }

  function updateRunLabels() {
    if (selectedDatasetLabelEl) selectedDatasetLabelEl.textContent = selectedCaseId || "None";
    if (selectedModelLabelEl) selectedModelLabelEl.textContent = selectedModelId || "None";
  }

  function setRunEnabled() {
    const btn = getRunBtn();
    if (!btn) return;

    const ok = !!selectedCaseId && !!selectedModelId;

    btn.disabled = !ok;

    if (ok) {
      btn.removeAttribute("disabled");
      btn.classList.remove("is-disabled");
      btn.style.pointerEvents = "auto";
      btn.style.opacity = "1";
      btn.style.filter = "none";
    } else {
      btn.setAttribute("disabled", "disabled");
      btn.classList.add("is-disabled");
      btn.style.pointerEvents = "none";
      btn.style.opacity = "0.6";
    }

    console.log("setRunEnabled", {
      selectedCaseId,
      selectedModelId,
      ok,
      html: btn.outerHTML
    });
  }

  function setRunStatus(msg) {
    if (runStatusEl) runStatusEl.textContent = msg || "";
  }

  function refreshRunUI() {
    syncGlobalSelection();
    updateRunLabels();
    setRunEnabled();
  }

  function clearSelectionsIfMissing() {
    if (selectedCaseId && !allCases.some(c => c.case_id === selectedCaseId)) {
      selectedCaseId = null;
    }
    if (selectedModelId && !allModels.some(m => m.id === selectedModelId)) {
      selectedModelId = null;
    }
    refreshRunUI();
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
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

  function renderModels() {
    if (!modelsListEl) return;
    modelsListEl.innerHTML = "";

    const sorted = [...allModels].sort((a, b) => String(a.name).localeCompare(String(b.name)));

    for (const m of sorted) {
      const card = document.createElement("div");
      card.className = "item-card model";
      card.dataset.modelId = m.id;

      if (selectedModelId === m.id) card.classList.add("selected");

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
        refreshRunUI();
        setRunStatus("");
        renderModels();
      });

      modelsListEl.appendChild(card);
    }

    if (modelsCountEl) modelsCountEl.textContent = String(sorted.length);
    refreshRunUI();
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
      refreshRunUI();
      return;
    } else {
      if (emptyEl) emptyEl.style.display = "none";
    }

    for (const { c, meta } of visible) {
      const card = document.createElement("div");
      card.className = "item-card dataset";
      card.dataset.caseId = c.case_id;

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

      card.addEventListener("click", (e) => {
        const t = e.target;
        if (t && (t.tagName === "A" || t.closest("a"))) return;

        selectedCaseId = c.case_id;
        refreshRunUI();
        setRunStatus("");
        renderDatasets();
      });

      const edit = card.querySelector(".editLink");
      if (edit) {
        edit.addEventListener("click", (e) => {
          e.preventDefault();
          openModal(c.case_id);
        });
      }

      datasetsListEl.appendChild(card);

      getResultCount(c.case_id).then(n => {
        const el = card.querySelector(".resCount");
        if (el) el.textContent = `Results: ${n}`;
      });
    }

    refreshRunUI();
  }

  function renderAll() {
    setBodyDomain(ui.activeDomain);
    renderDomainTabs();
    renderLevelTabs();
    renderModels();
    renderDatasets();
    clearSelectionsIfMissing();
  }

  function openModal(caseId) {
    const c = allCases.find(x => x.case_id === caseId);
    if (!c) return;

    const meta = ensureDefaultMeta(c);

    if (m_case) {
      m_case.value = c.case_id;
      m_case.disabled = true;
    }
    if (m_domain) m_domain.value = meta.domain || ui.activeDomain;
    if (m_level) m_level.value = meta.level || ui.activeLevel;
    if (m_state) m_state.value = meta.state || "Intake";
    if (m_desc) m_desc.value = meta.description || c.description || "";
    if (m_tags) m_tags.value = meta.tags || "";
    if (m_notes) m_notes.value = meta.notes || "";

    if (modalBackdrop) modalBackdrop.style.display = "flex";
  }

  function openQuickIntake() {
    if (m_case) {
      m_case.value = "";
      m_case.disabled = false;
    }
    if (m_domain) m_domain.value = ui.activeDomain;
    if (m_level) m_level.value = ui.activeLevel;
    if (m_state) m_state.value = "Intake";
    if (m_desc) m_desc.value = "";
    if (m_tags) m_tags.value = "";
    if (m_notes) m_notes.value = "";

    if (modalBackdrop) modalBackdrop.style.display = "flex";
    if (m_case) m_case.focus();
  }

  function closeModal() {
    if (modalBackdrop) modalBackdrop.style.display = "none";
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
      const caseId = ((m_case && m_case.value) || "").trim();
      if (!caseId) {
        alert("Case ID is required. Upload a dataset first, or type an existing case id.");
        return;
      }

      const meta = {
        domain: m_domain ? m_domain.value : ui.activeDomain,
        level: m_level ? m_level.value : ui.activeLevel,
        state: m_state ? m_state.value : "Intake",
        description: ((m_desc && m_desc.value) || "").trim(),
        tags: ((m_tags && m_tags.value) || "").trim(),
        notes: ((m_notes && m_notes.value) || "").trim()
      };

      saveMeta(caseId, meta);
      closeModal();
      setRunStatus("");
      renderAll();
    });
  }

  if (btnQuick) btnQuick.addEventListener("click", openQuickIntake);

  function bindRunHandler() {
    const btn = getRunBtn();
    if (!btn) return;

    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (!selectedCaseId || !selectedModelId) {
        alert("Select a dataset and a model first.");
        refreshRunUI();
        return;
      }

      try {
        btn.disabled = true;
        btn.setAttribute("disabled", "disabled");
        setRunStatus("Starting...");

        const r = await fetch("/start_model_run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            case_id: selectedCaseId,
            model_id: selectedModelId
          })
        });

        const data = await r.json().catch(() => ({}));

        if (!r.ok || !data.ok) {
          setRunStatus(data.error || `Run failed (${r.status})`);
          refreshRunUI();
          return;
        }

        setRunStatus("Opening visualizer...");
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
          return;
        }

        setRunStatus("Job started.");
        refreshRunUI();
      } catch (err) {
        console.error(err);
        setRunStatus("Run failed (network/server).");
        refreshRunUI();
      }
    };

    refreshRunUI();
  }

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

  async function init() {
    try {
      const [cases, models] = await Promise.all([fetchCases(), fetchModels()]);
      allCases = cases;
      allModels = models;

      clearSelectionsIfMissing();
      renderAll();
      bindRunHandler();
      refreshRunUI();
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
