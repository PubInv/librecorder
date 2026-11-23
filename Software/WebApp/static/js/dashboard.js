/* WebApp/static/js/dashboard.js
   LibreRecorder — v4
   Works with both structured and unstructured modes.
   Drives specimen + experiment lists for whichever mode is active.
*/

(() => {
  const DOMAINS = [
    { id: "health",     label: "Health" },
    { id: "ecology",    label: "Ecology" },
    { id: "veterinary", label: "Veterinary" },
    { id: "more",       label: "More" },
  ];
  const LEVELS = ["Not Analyzed", "Not for Analysis"];

  const STORE_KEY = "lr_ui_v5";
  const defaultUI = { activeDomain: "health", activeLevel: "Not Analyzed", search: "" };

  let ui        = loadUI();
  let allCases  = [];
  let allModels = [];

  let selectedCaseId    = null;
  let selectedCaseLabel = "";
  let selectedModelIds  = [];

  window.selectedCaseId    = null;
  window.selectedCaseLabel = "";
  window.selectedModelIds  = [];
  window.selectedModelId   = null;

  /* ══ PERSISTENCE ══ */
  function loadUI() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return { ...defaultUI };
      const p = JSON.parse(raw);
      const m = { ...defaultUI, ...p };
      if (!LEVELS.includes(m.activeLevel))               m.activeLevel  = defaultUI.activeLevel;
      if (!DOMAINS.some(d => d.id === m.activeDomain))   m.activeDomain = defaultUI.activeDomain;
      return m;
    } catch { return { ...defaultUI }; }
  }
  function saveUI() { localStorage.setItem(STORE_KEY, JSON.stringify(ui)); }

  function metaKey(id)  { return `lr_meta_${id}`; }
  function loadMeta(id) { try { const r = localStorage.getItem(metaKey(id)); return r ? JSON.parse(r) : null; } catch { return null; } }
  function saveMeta(id, m) { localStorage.setItem(metaKey(id), JSON.stringify(m)); }

  function ensureDefaultMeta(c) {
    const ex = loadMeta(c.case_id);
    if (ex) return ex;
    const m = { domain: ui.activeDomain, level: ui.activeLevel, description: c.description || "", tags: "", notes: "" };
    saveMeta(c.case_id, m);
    return m;
  }

  /* ══ UTILITIES ══ */
  function setBodyDomain(d) { document.body.setAttribute("data-domain", d); }
  function esc(s) { return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'); }
  function safe(x) { return String(x??'').trim(); }

  function matchesSearch(c, meta, q) {
    if (!q) return true;
    const hay = [c.case_id||"", meta?.description||"", c.description||"", meta?.tags||""].join(" ").toLowerCase();
    return hay.includes(q.toLowerCase());
  }

  /* ══ SELECTION SYNC ══ */
  function syncGlobals() {
    window.selectedCaseId    = selectedCaseId;
    window.selectedCaseLabel = selectedCaseLabel;
    window.selectedModelIds  = [...selectedModelIds];
    window.selectedModelId   = selectedModelIds[0] || null;
    if (typeof window.syncLibreRecorderProjectSelection === "function") {
      window.syncLibreRecorderProjectSelection();
    }
  }

  function updateHeaderLabels() {
    /* structured */
    const ss = document.getElementById("statSpecimen");
    const se = document.getElementById("statExperiments");
    if (ss) ss.textContent = selectedCaseLabel || selectedCaseId || "None";
    if (se) se.textContent = String(selectedModelIds.length);
    /* unstructured */
    [["selectedDatasetLabel",   selectedCaseLabel || "None"],
     ["selectedDatasetLabel-u", selectedCaseLabel || "None"],
     ["selectedModelLabel",     String(selectedModelIds.length)],
     ["selectedModelLabel-u",   String(selectedModelIds.length)],
    ].forEach(([id, val]) => { const el = document.getElementById(id); if (el) el.textContent = val; });

    /* advance buttons */
    const a1 = document.getElementById("btn-adv-1"); if (a1) a1.disabled = !selectedCaseId;
    const a2 = document.getElementById("btn-adv-2"); if (a2) a2.disabled = !selectedModelIds.length;
    /* run buttons */
    const canRun = !!(selectedCaseId && selectedModelIds.length);
    ["btnRunSelected","btnRunSelected-u"].forEach(id => { const b=document.getElementById(id); if(b) b.disabled=!canRun; });
    /* specimen card */
    const ssc = document.getElementById("selectedSpecimenCard");
    if (ssc) ssc.classList.toggle("has-value", !!selectedCaseId);
    const sscv = document.getElementById("selectedDatasetLabel");
    if (sscv) sscv.textContent = selectedCaseLabel || "None selected";
  }

  function refreshUI() { syncGlobals(); updateHeaderLabels(); }

  function clearSelectionsIfMissing() {
    if (selectedCaseId && !allCases.some(c => c.case_id === selectedCaseId)) {
      selectedCaseId = null; selectedCaseLabel = "";
    }
    const valid = new Set(allModels.map(m => m.id));
    selectedModelIds = selectedModelIds.filter(id => valid.has(id));
    refreshUI();
  }

  /* ══ RESULT COUNT ══ */
  async function getResultCount(caseId) {
    try { const r = await fetch(`/results/${encodeURIComponent(caseId)}`); if (!r.ok) return 0; const a = await r.json(); return Array.isArray(a) ? a.length : 0; }
    catch { return 0; }
  }

  /* ══ EMPTY STATE ══ */
  function setEmptyState(elId, show, msg) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.style.display = show ? "block" : "none";
    if (msg) el.textContent = msg;
  }

  /* ══ RENDER DOMAIN TABS ══ */
  function renderDomainTabs(tabsId) {
    const el = document.getElementById(tabsId);
    if (!el) return;
    const btns = el.querySelectorAll("[data-domain]");
    btns.forEach(btn => {
      btn.classList.toggle("active", ui.activeDomain === btn.getAttribute("data-domain"));
      btn.onclick = () => { ui.activeDomain = btn.getAttribute("data-domain"); saveUI(); setBodyDomain(ui.activeDomain); renderAll(); };
    });
  }

  /* ══ RENDER LEVEL TABS ══ */
  function renderLevelTabs(tabsId) {
    const el = document.getElementById(tabsId);
    if (!el) return;
    const btns = el.querySelectorAll("[data-level]");
    btns.forEach(btn => {
      btn.classList.toggle("active", ui.activeLevel === btn.getAttribute("data-level"));
      btn.onclick = () => { ui.activeLevel = btn.getAttribute("data-level"); saveUI(); renderAll(); };
    });
  }

  /* ══ INFER EXPERIMENT TRADEOFF ══ */
  function inferTradeoff(model) {
    const hay = [model.name||"", model.id||"", model.file||""].join(" ").toLowerCase();
    if (hay.includes("fast")||hay.includes("quick")||hay.includes("light")||hay.includes("mean")||hay.includes("darklight"))
      return { tradeoff:"Fast", tagClass:"warn", note:"Faster pass with lighter detail" };
    if (hay.includes("deep")||hay.includes("hq")||hay.includes("hires")||hay.includes("resolution")||hay.includes("accur"))
      return { tradeoff:"High detail", tagClass:"good", note:"More detailed but potentially slower" };
    return { tradeoff:"Balanced", tagClass:"", note:"General-purpose analytical experiment" };
  }

  /* ══ RENDER MODELS (experiments) ══ */
  function renderModels(listId, countId) {
    const listEl  = document.getElementById(listId);
    const countEl = document.getElementById(countId);
    if (!listEl) return;
    listEl.innerHTML = "";
    const sorted = [...allModels].sort((a,b) => String(a.name||a.id).localeCompare(String(b.name||b.id)));
    for (const m of sorted) {
      const { tradeoff, tagClass, note } = inferTradeoff(m);
      const isSelected = selectedModelIds.includes(m.id);
      const card = document.createElement("div");
      card.className = `model-chip${isSelected ? " active" : ""}`;
      card.dataset.modelId = m.id;
      card.innerHTML = `
        <div class="model-chip-top">
          <div class="model-chip-title">${esc(m.name || m.id)}</div>
          <span class="tag${tagClass ? " "+tagClass : ""}">${esc(tradeoff)}</span>
        </div>
        <div class="section-sub">${esc(note)}</div>
        <div class="chip-row">
          <span class="tag">id: ${esc(m.id)}</span>
          ${m.file ? `<span class="tag">file: ${esc(m.file)}</span>` : ""}
        </div>`;
      card.addEventListener("click", () => {
        if (selectedModelIds.includes(m.id)) selectedModelIds = selectedModelIds.filter(x => x !== m.id);
        else selectedModelIds = [...selectedModelIds, m.id];
        refreshUI();
        /* re-render all model lists */
        renderModels("modelsList",   "modelsCount");
        renderModels("modelsList-u", "modelsCount-u");
      });
      listEl.appendChild(card);
    }
    if (countEl) countEl.textContent = String(sorted.length);
    refreshUI();
  }

  /* ══ RENDER DATASETS (specimens) ══ */
  async function renderDatasets(listId, countId, emptyId, searchId) {
    const listEl  = document.getElementById(listId);
    const countEl = document.getElementById(countId);
    if (!listEl) return;
    listEl.innerHTML = "";
    const q       = safe(ui.search);
    const visible = [];
    for (const c of allCases) {
      const meta = ensureDefaultMeta(c);
      if (meta.domain !== ui.activeDomain) continue;
      if (meta.level  !== ui.activeLevel)  continue;
      if (!matchesSearch(c, meta, q))       continue;
      visible.push({ c, meta });
    }
    if (countEl) countEl.textContent = String(visible.length);
    if (!visible.length) {
      setEmptyState(emptyId, true, "No specimens match this view. Upload or change filters.");
      refreshUI(); return;
    }
    setEmptyState(emptyId, false);
    for (const { c, meta } of visible) {
      const isSelected = selectedCaseId === c.case_id;
      const card = document.createElement("div");
      card.className = `list-card${isSelected ? " active" : ""}`;
      card.dataset.caseId = c.case_id;
      card.innerHTML = `
        <h4>${esc(c.case_id)}</h4>
        <p>${esc((meta.description || c.description || "No description").trim())}</p>
        <div class="chip-row">
          <span class="tag">${esc(meta.domain || ui.activeDomain)}</span>
          <span class="tag">${esc(meta.level  || ui.activeLevel)}</span>
          ${meta.tags ? `<span class="tag">${esc(meta.tags)}</span>` : ""}
          <span class="tag resCount">Results: …</span>
        </div>
        <div class="inline-actions" style="margin-top:7px;">
          <a href="/render/${encodeURIComponent(c.case_id)}"       target="_blank" rel="noopener noreferrer">View</a>
          <a href="/results/${encodeURIComponent(c.case_id)}"      target="_blank" rel="noopener noreferrer">Raw</a>
          <a href="/rich_results/${encodeURIComponent(c.case_id)}" target="_blank" rel="noopener noreferrer">Rich</a>
          <a href="#" class="editLink">Edit</a>
        </div>`;
      card.addEventListener("click", e => {
        if (e.target && (e.target.tagName === "A" || e.target.closest("a"))) return;
        selectedCaseId    = c.case_id;
        selectedCaseLabel = c.case_id;
        refreshUI();
        /* re-render both lists */
        renderDatasets("datasetsList",   "datasetsCount",   "emptyState",   "search");
        renderDatasets("datasetsList-u", "datasetsCount-u", "emptyState-u", "search-u");
      });
      const edit = card.querySelector(".editLink");
      if (edit) edit.addEventListener("click", e => { e.preventDefault(); openModal(c.case_id); });
      listEl.appendChild(card);
      getResultCount(c.case_id).then(n => { const el = card.querySelector(".resCount"); if (el) el.textContent = `Results: ${n}`; });
    }
    refreshUI();
  }

  /* ══ RENDER ALL ══ */
  function renderAll() {
    setBodyDomain(ui.activeDomain);
    renderDomainTabs("domainTabs");
    renderDomainTabs("domainTabs-u");
    renderLevelTabs("levelTabs");
    renderLevelTabs("levelTabs-u");
    renderModels("modelsList",   "modelsCount");
    renderModels("modelsList-u", "modelsCount-u");
    renderDatasets("datasetsList",   "datasetsCount",   "emptyState",   "search");
    renderDatasets("datasetsList-u", "datasetsCount-u", "emptyState-u", "search-u");
    clearSelectionsIfMissing();
  }

  /* ══ PANE ACCORDION (unstructured) ══ */
  function setExpandedPane(name) {
    document.querySelectorAll("[data-pane-section]").forEach(s => {
      const active = s.getAttribute("data-pane-section") === name;
      s.classList.toggle("is-expanded", active);
      s.classList.toggle("is-collapsed", !active);
    });
    document.querySelectorAll("[data-pane-toggle]").forEach(t => {
      const active = t.getAttribute("data-pane-toggle") === name;
      t.setAttribute("aria-expanded", active ? "true" : "false");
      t.textContent = active ? "Collapse" : "Expand";
    });
  }
  function bindPaneAccordion() {
    document.querySelectorAll("[data-pane-toggle]").forEach(t => {
      t.addEventListener("click", function () { setExpandedPane(this.getAttribute("data-pane-toggle")); });
    });
  }

  /* ══ MODAL ══ */
  const modalBackdrop  = document.getElementById("modalBackdrop");
  const btnCloseModal  = document.getElementById("btnCloseModal");
  const btnCancelModal = document.getElementById("btnCancelModal");
  const btnSaveModal   = document.getElementById("btnSaveModal");
  const m_case         = document.getElementById("m_case");
  const m_domain       = document.getElementById("m_domain");
  const m_level        = document.getElementById("m_level");
  const m_desc         = document.getElementById("m_desc");
  const m_tags         = document.getElementById("m_tags");
  const m_notes        = document.getElementById("m_notes");

  function openModal(caseId) {
    const c = allCases.find(x => x.case_id === caseId);
    if (!c) return;
    const meta = ensureDefaultMeta(c);
    if (m_case)   { m_case.value = c.case_id; m_case.disabled = true; }
    if (m_domain) m_domain.value = meta.domain || ui.activeDomain;
    if (m_level)  m_level.value  = meta.level  || ui.activeLevel;
    if (m_desc)   m_desc.value   = meta.description || c.description || "";
    if (m_tags)   m_tags.value   = meta.tags   || "";
    if (m_notes)  m_notes.value  = meta.notes  || "";
    if (modalBackdrop) modalBackdrop.style.display = "flex";
  }

  function openQuickIntake() {
    if (m_case)   { m_case.value = ""; m_case.disabled = false; }
    if (m_domain) m_domain.value = ui.activeDomain;
    if (m_level)  m_level.value  = ui.activeLevel;
    if (m_desc)   m_desc.value   = "";
    if (m_tags)   m_tags.value   = "";
    if (m_notes)  m_notes.value  = "";
    if (modalBackdrop) modalBackdrop.style.display = "flex";
    if (m_case)   m_case.focus();
  }

  function closeModal() { if (modalBackdrop) modalBackdrop.style.display = "none"; }

  if (btnCloseModal)  btnCloseModal.addEventListener("click",  closeModal);
  if (btnCancelModal) btnCancelModal.addEventListener("click", closeModal);
  if (modalBackdrop)  modalBackdrop.addEventListener("click", e => { if (e.target === modalBackdrop) closeModal(); });

  if (btnSaveModal) {
    btnSaveModal.addEventListener("click", () => {
      const caseId = safe(m_case && m_case.value);
      if (!caseId) { alert("Case ID required. Upload a specimen first."); return; }
      saveMeta(caseId, {
        domain:      m_domain ? m_domain.value : ui.activeDomain,
        level:       m_level  ? m_level.value  : ui.activeLevel,
        description: safe(m_desc  && m_desc.value),
        tags:        safe(m_tags  && m_tags.value),
        notes:       safe(m_notes && m_notes.value)
      });
      closeModal();
      renderAll();
    });
  }

  /* ══ SEARCH ══ */
  function bindSearch(searchId) {
    const el = document.getElementById(searchId);
    if (!el) return;
    el.value = ui.search || "";
    el.addEventListener("input", () => { ui.search = el.value; saveUI(); renderAll(); });
  }

  /* ══ BUTTONS ══ */
  const btnQuick  = document.getElementById("btnQuickIntake");
  const btnRef    = document.getElementById("btnRefresh");
  if (btnQuick) btnQuick.addEventListener("click", openQuickIntake);
  if (btnRef)   btnRef.addEventListener("click",   async () => { await init(); });

  /* ══ FETCH ══ */
  async function fetchCases() {
    const r = await fetch("/cases");
    if (!r.ok) throw new Error("Failed /cases");
    const a = await r.json();
    return Array.isArray(a) ? a : [];
  }

  async function fetchModels() {
    const r = await fetch("/models");
    if (!r.ok) return [];
    const a = await r.json();
    return Array.isArray(a) ? a : [];
  }

  async function init() {
    try {
      const [cases, models] = await Promise.all([fetchCases(), fetchModels()]);
      allCases  = cases;
      allModels = models;
      clearSelectionsIfMissing();
      renderAll();
      refreshUI();
    } catch(e) {
      console.error(e);
      ["emptyState","emptyState-u"].forEach(id => setEmptyState(id, true, "Dashboard failed to load. Check server logs."));
    }
  }

  /* ══ INIT ══ */
  bindSearch("search");
  bindSearch("search-u");
  bindPaneAccordion();
  setExpandedPane("filters");
  init();

  /* scroll hint observer (legacy resource panel) */
  document.addEventListener("DOMContentLoaded", () => {
    const hint      = document.getElementById("scrollHint");
    const resources = document.querySelector(".resource-panel");
    if (!hint || !resources) return;
    new IntersectionObserver(([e]) => hint.classList.toggle("visible", !e.isIntersecting), { threshold: .05 }).observe(resources);
  });

})();
