/* WebApp/static/js/dashboard.js
   LibreRecorder Pipeline UI (no SQL changes)
   - Domain tabs: Health / Ecology / Veterinary / More
   - Level tabs: Not Analyzed / Analyzed / Not for Analysis
   - Columns: Intake, Microscopy QC, Preprocessing, Labeling, Modeling, Review, Published
   - Metadata stored in localStorage per case_id (for now)
*/

(() => {
  const DOMAINS = [
    { id: "health",     label: "Health",     accent: "#6a1e55" },
    { id: "ecology",    label: "Ecology",    accent: "#2f7d5a" },
    { id: "veterinary", label: "Veterinary", accent: "#355a9a" },
    { id: "more",       label: "More",       accent: "#555555" },
  ];

  const LEVELS = [
    "Not Analyzed",
    "Analyzed",
    "Not for Analysis"
  ];

  const STATES = [
    "Intake",
    "Microscopy QC",
    "Preprocessing",
    "Labeling",
    "Modeling",
    "Review",
    "Published"
  ];

  // --------- DOM ----------
  const domainTabsEl = document.getElementById("domainTabs");
  const levelTabsEl  = document.getElementById("levelTabs");
  const boardEl      = document.getElementById("board");
  const boardWrapEl  = document.getElementById("boardWrap");
  const emptyEl      = document.getElementById("emptyState");

  const searchEl     = document.getElementById("search");
  const btnRefresh   = document.getElementById("btnRefresh");
  const btnQuick     = document.getElementById("btnQuickIntake");

  const modalBackdrop = document.getElementById("modalBackdrop");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnCancelModal = document.getElementById("btnCancelModal");
  const btnSaveModal  = document.getElementById("btnSaveModal");

  const m_case   = document.getElementById("m_case");
  const m_domain = document.getElementById("m_domain");
  const m_level  = document.getElementById("m_level");
  const m_state  = document.getElementById("m_state");
  const m_desc   = document.getElementById("m_desc");
  const m_tags   = document.getElementById("m_tags");
  const m_notes  = document.getElementById("m_notes");

  // Resources panel tabs
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
  const STORE_KEY = "lr_pipeline_ui_v1";

  const defaultUI = {
    activeDomain: "health",
    activeLevel: "Not Analyzed",
    search: ""
  };

  let ui = loadUI();
  let allCases = []; // from /cases

  function loadUI() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return { ...defaultUI };
      const parsed = JSON.parse(raw);
      return { ...defaultUI, ...parsed };
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

    // Default behavior: put everything into current ui domain/level, Intake
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

  // --------- Rendering ----------
  function setBodyDomain(domainId) {
    document.body.classList.remove("domain-health", "domain-ecology", "domain-veterinary", "domain-more");
    document.body.classList.add(`domain-${domainId}`);
  }

  function renderDomainTabs() {
    domainTabsEl.innerHTML = "";
    DOMAINS.forEach(d => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = `tab ${d.id} ${ui.activeDomain === d.id ? "active" : ""}`;
      b.textContent = d.label;
      b.addEventListener("click", () => {
        ui.activeDomain = d.id;
        saveUI();
        setBodyDomain(ui.activeDomain);
        renderAll();
      });
      domainTabsEl.appendChild(b);
    });
  }

  function renderLevelTabs() {
    levelTabsEl.innerHTML = "";
    LEVELS.forEach(level => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = `tab ${ui.activeDomain} ${ui.activeLevel === level ? "active" : ""}`;
      b.textContent = level;
      b.addEventListener("click", () => {
        ui.activeLevel = level;
        saveUI();
        renderAll();
      });
      levelTabsEl.appendChild(b);
    });
  }

  function buildEmptyColumns() {
    boardEl.innerHTML = "";
    STATES.forEach(state => {
      const col = document.createElement("div");
      col.className = "column";

      const head = document.createElement("div");
      head.className = "column-header";
      const h = document.createElement("h3");
      h.textContent = state;

      const count = document.createElement("span");
      count.className = "column-count";
      count.textContent = "0";

      head.appendChild(h);
      head.appendChild(count);

      const body = document.createElement("div");
      body.className = "column-body";
      body.setAttribute("data-state", state);

      col.appendChild(head);
      col.appendChild(body);
      boardEl.appendChild(col);
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

  async function renderCards() {
    // clear all column bodies
    document.querySelectorAll(".column-body").forEach(b => (b.innerHTML = ""));

    const q = (ui.search || "").trim();
    const visible = [];

    for (const c of allCases) {
      const meta = ensureDefaultMeta(c);

      if (meta.domain !== ui.activeDomain) continue;
      if (meta.level !== ui.activeLevel) continue;
      if (!matchesSearch(c, meta, q)) continue;

      visible.push({ c, meta });
    }

    // show/hide empty state
    if (visible.length === 0) {
      emptyEl.style.display = "block";
      boardWrapEl.style.display = "none";
      return;
    } else {
      emptyEl.style.display = "none";
      boardWrapEl.style.display = "block";
    }

    // build cards and append
    for (const { c, meta } of visible) {
      const state = meta.state || "Intake";
      const colBody = document.querySelector(`.column-body[data-state="${cssEscape(state)}"]`)
        || document.querySelector(`.column-body[data-state="Intake"]`);

      const card = document.createElement("div");
      card.className = "card";
      card.setAttribute("data-case", c.case_id);

      const title = document.createElement("h4");
      title.textContent = c.case_id;

      const desc = document.createElement("p");
      desc.textContent = (meta.description || c.description || "").trim() || "—";

      const created = document.createElement("p");
      created.innerHTML = `<b>Created:</b> ${new Date(c.created_at).toLocaleString()}`;

      const metaRow = document.createElement("div");
      metaRow.className = "card-meta";
      metaRow.innerHTML = `<span>${meta.tags ? meta.tags : ""}</span><span class="resCount">Results: …</span>`;

      const actions = document.createElement("div");
      actions.className = "card-actions";
      actions.innerHTML = `
        <a href="/render/${encodeURIComponent(c.case_id)}" target="_blank">View</a>
        <a href="/results/${encodeURIComponent(c.case_id)}" target="_blank">Raw</a>
        <a href="/rich_results/${encodeURIComponent(c.case_id)}" target="_blank">Rich</a>
        <a href="#" class="editLink">Edit</a>
      `;

      card.appendChild(title);
      card.appendChild(desc);
      card.appendChild(created);
      card.appendChild(metaRow);
      card.appendChild(actions);

      // Edit metadata
      actions.querySelector(".editLink").addEventListener("click", (e) => {
        e.preventDefault();
        openModal(c.case_id);
      });

      colBody.appendChild(card);

      // fill result count async
      getResultCount(c.case_id).then(n => {
        const el = card.querySelector(".resCount");
        if (el) el.textContent = `Results: ${n}`;
      });
    }

    // update column counts
    document.querySelectorAll(".column").forEach(col => {
      const body = col.querySelector(".column-body");
      const countEl = col.querySelector(".column-count");
      const n = body ? body.querySelectorAll(".card").length : 0;
      if (countEl) countEl.textContent = String(n);
    });
  }

  function renderAll() {
    setBodyDomain(ui.activeDomain);
    renderDomainTabs();
    renderLevelTabs();
    buildEmptyColumns();
    renderCards();
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

  btnCloseModal.addEventListener("click", closeModal);
  btnCancelModal.addEventListener("click", closeModal);
  modalBackdrop.addEventListener("click", (e) => {
    if (e.target === modalBackdrop) closeModal();
  });

  btnSaveModal.addEventListener("click", () => {
    const caseId = (m_case.value || "").trim();
    if (!caseId) {
      alert("Case ID is required. Upload a dataset first, or type an existing case id.");
      return;
    }

    // If case doesn't exist in DB list, we still allow local metadata,
    // but it won't show until /cases returns it.
    const meta = {
      domain: m_domain.value,
      level: m_level.value,
      state: m_state.value,
      description: (m_desc.value || "").trim(),
      tags: (m_tags.value || "").trim(),
      notes: (m_notes.value || "").trim()
    };

    saveMeta(caseId, meta);

    // If user changed domain/level, keep them in sync with current view
    // only if they edited the active case in the current domain context.
    // (We do NOT auto-jump views; user can click tabs.)
    closeModal();
    renderAll();
  });

  btnQuick.addEventListener("click", openQuickIntake);

  // --------- Data ----------
  async function fetchCases() {
    const r = await fetch("/cases");
    if (!r.ok) throw new Error("Failed to fetch /cases");
    const arr = await r.json();
    if (!Array.isArray(arr)) return [];
    return arr;
  }

  // --------- Events ----------
  btnRefresh.addEventListener("click", async () => {
    await init();
  });

  searchEl.value = ui.search || "";
  searchEl.addEventListener("input", () => {
    ui.search = searchEl.value;
    saveUI();
    renderAll();
  });

  // --------- Helpers ----------
  function cssEscape(s) {
    // minimal escape for attribute selector use
    return String(s).replace(/"/g, '\\"');
  }

  // --------- Init ----------
  async function init() {
    try {
      allCases = await fetchCases();
      renderAll();
    } catch (e) {
      console.error(e);
      emptyEl.style.display = "block";
      emptyEl.textContent = "Dashboard failed to load cases. Check server logs.";
      boardWrapEl.style.display = "none";
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
    {
      root: null,
      threshold: 0.05  // triggers when even a sliver is visible
    }
  );

  observer.observe(resources);
});
