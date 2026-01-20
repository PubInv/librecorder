// LibreRecorder Pipeline dashboard
// Requires backend route: GET/POST /meta/<case_id>
// Uses existing routes: /cases, /results/<case_id>

const DOMAINS = [
  { key: "health", label: "Health", theme: "#6a1e55" },
  { key: "ecology", label: "Ecology", theme: "#1f6a3f" },
  { key: "veterinary", label: "Veterinary", theme: "#1e4f6a" },
  { key: "more", label: "More", theme: "#5a5a5a" },
];

const LEVELS = [
  "Not Analyzed",
  "Analyzed",
  "Not for Analysis",
];

const ANALYSIS_COLUMNS = [
  "Intake",
  "Microscopy QC",
  "Preprocessing",
  "Labeling",
  "Modeling",
  "Review",
];

const state = {
  activeDomain: "health",
  activeLevel: "Not Analyzed",
  cases: [],
  metaByCase: {},
  resultsCountByCase: {},
};

function el(id){ return document.getElementById(id); }

function escapeHTML(s){
  return String(s || "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

async function apiJSON(url, opts){
  const r = await fetch(url, opts || {});
  const t = await r.text();
  try { return JSON.parse(t); } catch { return { error: "Non-JSON response", raw: t }; }
}

function normalizeMeta(m){
  const meta = m || {};
  if (!meta.domain) meta.domain = "health";
  if (!meta.level) meta.level = "Not Analyzed";
  if (!meta.columns) meta.columns = {};
  if (!meta.tags) meta.tags = [];
  if (!meta.notes) meta.notes = "";
  if (!meta.description) meta.description = "";
  return meta;
}

function getPrimaryColumn(meta){
  const cols = meta.columns || {};
  for (const k of ANALYSIS_COLUMNS){
    if (cols[k]) return k;
  }
  return "Intake";
}

function setPrimaryColumn(meta, col){
  if (!meta.columns) meta.columns = {};
  for (const k of ANALYSIS_COLUMNS) delete meta.columns[k];
  meta.columns[col] = "Active";
}

function applyTheme(){
  const d = DOMAINS.find(x => x.key === state.activeDomain) || DOMAINS[0];
  const root = document.documentElement;
  root.style.setProperty("--brand", d.theme);
  root.style.setProperty("--brand-weak", `${d.theme}1A`); // hex + alpha-ish (works in modern browsers)
  root.style.setProperty("--brand-border", `${d.theme}59`);
}

async function loadCases(){
  const cases = await apiJSON("/cases");
  state.cases = Array.isArray(cases) ? cases : [];
}

async function loadMetaFor(case_id){
  const m = await apiJSON(`/meta/${encodeURIComponent(case_id)}`);
  state.metaByCase[case_id] = normalizeMeta(m);
}

async function loadResultsCountFor(case_id){
  const r = await apiJSON(`/results/${encodeURIComponent(case_id)}`);
  state.resultsCountByCase[case_id] = Array.isArray(r) ? r.length : 0;
}

async function refresh(){
  await loadCases();

  await Promise.all(state.cases.map(async (c) => {
    await Promise.all([
      loadMetaFor(c.case_id),
      loadResultsCountFor(c.case_id),
    ]);
  }));

  render();
}

function renderDomainTabs(){
  const wrap = el("domainTabs");
  wrap.innerHTML = "";
  DOMAINS.forEach(d => {
    const b = document.createElement("button");
    b.className = "lr-tab" + (state.activeDomain === d.key ? " active" : "");
    b.textContent = d.label;
    b.onclick = () => {
      state.activeDomain = d.key;
      applyTheme();
      render();
    };
    wrap.appendChild(b);
  });
}

function renderLevelTabs(){
  const wrap = el("levelTabs");
  wrap.innerHTML = "";
  LEVELS.forEach(lv => {
    const b = document.createElement("button");
    b.className = "lr-subtab" + (state.activeLevel === lv ? " active" : "");
    b.textContent = lv;
    b.onclick = () => {
      state.activeLevel = lv;
      render();
    };
    wrap.appendChild(b);
  });
}

function caseMatchesSearch(c, meta, q){
  if (!q) return true;
  const s = q.toLowerCase();
  const tags = (meta.tags || []).join(",").toLowerCase();
  const desc = (meta.description || c.description || "").toLowerCase();
  return (c.case_id || "").toLowerCase().includes(s) || desc.includes(s) || tags.includes(s);
}

function buildCard(c){
  const meta = state.metaByCase[c.case_id] || normalizeMeta({});
  const resultsN = state.resultsCountByCase[c.case_id] || 0;

  const created = c.created_at ? new Date(c.created_at).toLocaleString() : "";
  const desc = meta.description || c.description || "No description";
  const tags = Array.isArray(meta.tags) ? meta.tags : [];

  const card = document.createElement("div");
  card.className = "lr-card";
  card.draggable = true;
  card.dataset.caseId = c.case_id;

  card.innerHTML = `
    <h4>${escapeHTML(c.case_id)}</h4>
    <p class="lr-desc">${escapeHTML(desc)}</p>

    <div class="lr-mini">
      <span>${escapeHTML(created)}</span>
      <span>Results: ${resultsN}</span>
    </div>

    <div class="lr-links">
      <a href="/render/${encodeURIComponent(c.case_id)}" target="_blank">View</a>
      <a href="/results/${encodeURIComponent(c.case_id)}" target="_blank">Raw</a>
      <a href="/rich_results/${encodeURIComponent(c.case_id)}" target="_blank">Rich</a>
    </div>

    <div class="lr-pillrow">
      ${tags.slice(0,6).map(t => `<span class="lr-pill">${escapeHTML(t)}</span>`).join("")}
    </div>
  `;

  card.addEventListener("dragstart", (e) => {
    e.dataTransfer.setData("text/plain", c.case_id);
  });

  card.addEventListener("dblclick", () => {
    openModalWithCase(c.case_id);
  });

  return card;
}

function buildColumn(colName, cards){
  const col = document.createElement("div");
  col.className = "lr-col";
  col.dataset.col = colName;

  const head = document.createElement("div");
  head.className = "lr-col-head";
  head.innerHTML = `
    <div class="lr-col-title">${escapeHTML(colName)}</div>
    <div class="lr-col-count">${cards.length}</div>
  `;

  const dropzone = document.createElement("div");
  dropzone.className = "lr-dropzone";

  dropzone.addEventListener("dragover", (e) => e.preventDefault());
  dropzone.addEventListener("drop", async (e) => {
    e.preventDefault();
    const case_id = e.dataTransfer.getData("text/plain");
    if (!case_id) return;

    const meta = normalizeMeta(state.metaByCase[case_id] || {});
    meta.domain = state.activeDomain;
    meta.level = state.activeLevel;
    setPrimaryColumn(meta, colName);

    await saveMeta(case_id, meta);
    state.metaByCase[case_id] = meta;
    render();
  });

  cards.forEach(cd => dropzone.appendChild(cd));

  col.appendChild(head);
  col.appendChild(dropzone);
  return col;
}

function renderBoard(){
  const board = el("board");
  const empty = el("emptyState");
  board.innerHTML = "";

  const q = (el("search").value || "").trim();

  const filtered = state.cases.filter(c => {
    const meta = state.metaByCase[c.case_id] || normalizeMeta({});
    const domainOk = (meta.domain || "health") === state.activeDomain;
    const levelOk = (meta.level || "Not Analyzed") === state.activeLevel;
    const searchOk = caseMatchesSearch(c, meta, q);
    return domainOk && levelOk && searchOk;
  });

  empty.style.display = filtered.length ? "none" : "block";

  ANALYSIS_COLUMNS.forEach(colName => {
    const cards = filtered
      .filter(c => {
        const meta = state.metaByCase[c.case_id] || normalizeMeta({});
        return getPrimaryColumn(meta) === colName;
      })
      .map(c => buildCard(c));

    board.appendChild(buildColumn(colName, cards));
  });
}

function render(){
  applyTheme();
  renderDomainTabs();
  renderLevelTabs();
  renderBoard();
}

async function saveMeta(case_id, meta){
  if (!meta.description){
    const c = state.cases.find(x => x.case_id === case_id);
    if (c && c.description) meta.description = c.description;
  }
  const r = await apiJSON(`/meta/${encodeURIComponent(case_id)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(meta)
  });
  if (r && r.error) alert("Meta save error: " + r.error);
}

/* Modal wiring */
function showModal(show){
  el("modalBackdrop").style.display = show ? "flex" : "none";
}

function openModalWithCase(case_id){
  const meta = normalizeMeta(state.metaByCase[case_id] || {});
  const c = state.cases.find(x => x.case_id === case_id);

  el("m_case").value = case_id || "";
  el("m_domain").value = meta.domain || "health";
  el("m_level").value = meta.level || "Not Analyzed";
  el("m_desc").value = meta.description || (c ? (c.description || "") : "");
  el("m_tags").value = (meta.tags || []).join(", ");
  el("m_notes").value = meta.notes || "";

  showModal(true);
}

async function saveModal(){
  const case_id = (el("m_case").value || "").trim();
  if (!case_id){
    alert("Enter an existing Case ID. Upload first.");
    return;
  }

  const meta = normalizeMeta(state.metaByCase[case_id] || {});
  meta.domain = el("m_domain").value;
  meta.level = el("m_level").value;
  meta.description = (el("m_desc").value || "").trim();
  meta.tags = (el("m_tags").value || "").split(",").map(s => s.trim()).filter(Boolean);
  meta.notes = (el("m_notes").value || "").trim();

  await saveMeta(case_id, meta);
  state.metaByCase[case_id] = meta;

  showModal(false);
  render();
}

function bindUI(){
  el("btnRefresh").addEventListener("click", refresh);
  el("btnQuickIntake").addEventListener("click", () => showModal(true));
  el("btnCloseModal").addEventListener("click", () => showModal(false));
  el("btnCancelModal").addEventListener("click", () => showModal(false));
  el("btnSaveModal").addEventListener("click", saveModal);

  el("modalBackdrop").addEventListener("click", (e) => {
    if (e.target && e.target.id === "modalBackdrop") showModal(false);
  });

  el("search").addEventListener("input", () => render());
}

/* Boot */
document.addEventListener("DOMContentLoaded", () => {
  bindUI();
  applyTheme();
  refresh();
});
