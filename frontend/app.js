const THEME_KEY = "deepcode-theme";
const PROBLEM_TIMERS_KEY = "deepcode-problem-timers";
const EDITOR_HISTORY_STORAGE_KEY = "deepcode-editor-history";
const EDITOR_HISTORY_LIMIT = 100;
const EDITOR_HISTORY_SESSION_LIMIT = 6;
const PLAYGROUND_CODE_KEY = "deepcode-playground-code";
const PLAYGROUND_SESSIONS_KEY = "deepcode-playground-sessions";
const LEGACY_PLAYGROUND_SNAPSHOTS_KEY = "deepcode-playground-snapshots";
const PLAYGROUND_STARTER_CODE = `import torch
from torch import nn

torch.manual_seed(7)

x = torch.randn(4, 3)
model = nn.Linear(3, 2)
y = model(x)

print(f"PyTorch {torch.__version__}")
print("input shape:", tuple(x.shape))
print("output shape:", tuple(y.shape))
print(y)
`;
const PROBLEM_SECTION_CLASSES = {
  prompt: "problem-section problem-prompt-section",
  data: "problem-section problem-data-section",
  metadata: "problem-section problem-metadata-section",
  example: "problem-section problem-example-section",
  references: "problem-section problem-references-section",
  tests: "problem-section problem-tests-section",
  environment: "problem-section problem-environment-section",
};
const initialPlaygroundSessionState = loadPlaygroundSessionState();

const state = {
  view: "problems",
  problems: [],
  categories: [],
  difficulties: [],
  companyNames: [],
  companyProfiles: [],
  filters: {
    search: "",
    category: "all",
    difficulty: "all",
    company: "all",
    sort: "id",
    order: "asc",
  },
  companies: [],
  selected: null,
  selectedCompany: null,
  customTests: [],
  dataLink: null,
  dataLinkTarget: "",
  activeTab: "description",
  activeResultIndex: 0,
  runResult: null,
  runLogs: [],
  activeRunCheck: null,
  runStartedAt: null,
  runElapsedSeconds: 0,
  runningTestIndex: null,
  runningCustomTestIndex: null,
  pendingCustomTestScrollIndex: null,
  error: null,
  loading: true,
  running: false,
  playgroundRunning: false,
  playgroundResult: null,
  playgroundRunSource: "",
  playgroundSessionName: "",
  playgroundSessions: initialPlaygroundSessionState.sessions,
  playgroundActiveSessionId: initialPlaygroundSessionState.activeSessionId,
  theme: initialTheme(),
  layout: {
    problemRatio: 0.46,
    resultsRatio: 0.32,
  },
};

const app = document.querySelector("#app");
let codeEditor = null;
let activePaneResize = null;
let runTimer = null;
let problemTimer = null;

function initialTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  return stored === "light" || stored === "dark" ? stored : "dark";
}

function applyTheme() {
  document.body.setAttribute("data-theme", state.theme);
  setEditorTheme();
}

function setEditorTheme() {
  if (!codeEditor || !window.ace) return;
  codeEditor.setTheme(state.theme === "dark" ? "ace/theme/tomorrow_night" : "ace/theme/chrome");
}

function toggleTheme() {
  state.theme = state.theme === "dark" ? "light" : "dark";
  localStorage.setItem(THEME_KEY, state.theme);
  applyTheme();
  updateThemeToggle();
}

function themeToggleLabel() {
  return `Dark mode: ${state.theme === "dark" ? "On" : "Off"}`;
}

function themeToggleButton() {
  return `<button class="ghost-button theme-toggle" id="theme-toggle" aria-pressed="${state.theme === "dark"}">${themeToggleLabel()}</button>`;
}

function loadProblemTimers() {
  try {
    const timers = JSON.parse(localStorage.getItem(PROBLEM_TIMERS_KEY) || "{}");
    return timers && typeof timers === "object" && !Array.isArray(timers) ? timers : {};
  } catch {
    return {};
  }
}

function problemTimerFor(slug) {
  const saved = loadProblemTimers()[slug];
  const elapsedMs = Number(saved?.elapsedMs);
  const startedAt = Number(saved?.startedAt);
  return {
    elapsedMs: Number.isFinite(elapsedMs) ? Math.max(0, elapsedMs) : 0,
    startedAt: Number.isFinite(startedAt) && startedAt > 0 ? startedAt : null,
  };
}

function problemTimerIsRunning(timer) {
  return timer.startedAt !== null;
}

function problemTimerElapsedMs(timer) {
  return timer.elapsedMs + (problemTimerIsRunning(timer) ? Math.max(0, Date.now() - timer.startedAt) : 0);
}

function formatProblemTimer(timer) {
  const totalSeconds = Math.floor(problemTimerElapsedMs(timer) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}

function saveProblemTimer(slug, timer) {
  const timers = loadProblemTimers();
  if (!timer.elapsedMs && !problemTimerIsRunning(timer)) {
    delete timers[slug];
  } else {
    timers[slug] = { elapsedMs: timer.elapsedMs, startedAt: timer.startedAt };
  }
  localStorage.setItem(PROBLEM_TIMERS_KEY, JSON.stringify(timers));
}

function renderProblemTimer(problem) {
  const timer = problemTimerFor(problem.slug);
  const running = problemTimerIsRunning(timer);
  const action = running ? "Pause" : timer.elapsedMs ? "Resume" : "Start";
  return `
    <div class="problem-timer" role="group" aria-label="Problem timer">
      <time class="problem-timer-display" id="problem-timer-display" aria-label="Elapsed time">${formatProblemTimer(timer)}</time>
      <button class="ghost-button problem-timer-toggle" id="problem-timer-toggle" aria-pressed="${running}">${action}</button>
      <button class="icon-button" id="problem-timer-reset" aria-label="Reset problem timer" title="Reset timer">↻</button>
    </div>
  `;
}

function stopProblemTimer() {
  if (!problemTimer) return;
  clearInterval(problemTimer);
  problemTimer = null;
}

function updateProblemTimerDisplay() {
  if (!state.selected) return;
  const timer = problemTimerFor(state.selected.slug);
  const display = document.querySelector("#problem-timer-display");
  if (display) display.textContent = formatProblemTimer(timer);
}

function syncProblemTimer() {
  stopProblemTimer();
  if (!state.selected || !problemTimerIsRunning(problemTimerFor(state.selected.slug))) return;
  updateProblemTimerDisplay();
  problemTimer = setInterval(updateProblemTimerDisplay, 1000);
}

function toggleProblemTimer() {
  if (!state.selected) return;
  const slug = state.selected.slug;
  const timer = problemTimerFor(slug);
  if (problemTimerIsRunning(timer)) {
    timer.elapsedMs = problemTimerElapsedMs(timer);
    timer.startedAt = null;
  } else {
    timer.startedAt = Date.now();
  }
  saveProblemTimer(slug, timer);
  syncProblemTimer();
  updateProblemTimerDisplay();
  const button = document.querySelector("#problem-timer-toggle");
  if (button) {
    const running = problemTimerIsRunning(timer);
    button.textContent = running ? "Pause" : timer.elapsedMs ? "Resume" : "Start";
    button.setAttribute("aria-pressed", String(running));
  }
}

function resetProblemTimer() {
  if (!state.selected) return;
  saveProblemTimer(state.selected.slug, { elapsedMs: 0, startedAt: null });
  stopProblemTimer();
  updateProblemTimerDisplay();
  const button = document.querySelector("#problem-timer-toggle");
  if (button) {
    button.textContent = "Start";
    button.setAttribute("aria-pressed", "false");
  }
}

function mainNavigation() {
  return `
    <nav class="main-nav" aria-label="Main navigation">
      <button class="nav-tab ${state.view === "problems" ? "active" : ""}" data-app-view="problems">Problems</button>
      <button class="nav-tab ${state.view === "companies" ? "active" : ""}" data-app-view="companies">Companies</button>
      <button class="nav-tab ${state.view === "playground" ? "active" : ""}" data-app-view="playground">Playground</button>
    </nav>
  `;
}

function updateThemeToggle() {
  const toggle = document.querySelector("#theme-toggle");
  if (!toggle) return;
  toggle.textContent = themeToggleLabel();
  toggle.setAttribute("aria-pressed", String(state.theme === "dark"));
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function markdownInline(value) {
  return escapeHtml(value).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdownLines(lines) {
  const blocks = [];
  let paragraphLines = [];
  let listItems = [];

  const flushParagraph = () => {
    if (!paragraphLines.length) return;
    blocks.push(`<p>${paragraphLines.map((line) => markdownInline(line)).join("<br>")}</p>`);
    paragraphLines = [];
  };

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(`<ul>${listItems.map((item) => `<li>${markdownInline(item)}</li>`).join("")}</ul>`);
    listItems = [];
  };

  lines.forEach((line) => {
    if (line.startsWith("- ")) {
      flushParagraph();
      listItems.push(line.slice(2));
      return;
    }
    flushList();
    paragraphLines.push(line);
  });

  flushParagraph();
  flushList();
  return blocks.join("");
}

function markdownLite(value) {
  const normalized = String(value ?? "").trim();
  if (!normalized) return "";

  return normalized
    .split(/\n{2,}/)
    .map((block) => {
      const lines = block.split("\n");
      if (lines.length === 1 && block.startsWith("### ")) return `<h4>${markdownInline(block.slice(4))}</h4>`;
      if (lines.length === 1 && block.startsWith("## ")) return `<h3>${markdownInline(block.slice(3))}</h3>`;
      return renderMarkdownLines(lines);
    })
    .join("");
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function percent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function paneLayoutStyle() {
  return `style="--problem-pane-width: ${percent(state.layout.problemRatio)}; --results-pane-height: ${percent(
    state.layout.resultsRatio
  )};"`;
}

function applyPaneSizes() {
  const layout = document.querySelector(".detail-layout");
  if (!layout) return;
  layout.style.setProperty("--problem-pane-width", percent(state.layout.problemRatio));
  layout.style.setProperty("--results-pane-height", percent(state.layout.resultsRatio));
  codeEditor?.resize();
}

function startPaneResize(event) {
  const handle = event.currentTarget;
  activePaneResize = handle.dataset.resizeHandle;
  document.body.classList.add("is-resizing");
  handle.setPointerCapture?.(event.pointerId);
  window.addEventListener("pointermove", updatePaneResize);
  window.addEventListener("pointerup", stopPaneResize, { once: true });
  updatePaneResize(event);
  event.preventDefault();
}

function updatePaneResize(event) {
  if (!activePaneResize) return;

  if (activePaneResize === "problem-code") {
    const layout = document.querySelector(".detail-layout");
    if (!layout) return;
    const rect = layout.getBoundingClientRect();
    state.layout.problemRatio = clamp((event.clientX - rect.left) / rect.width, 0.28, 0.68);
  }

  if (activePaneResize === "code-results") {
    const panel = document.querySelector(".editor-panel");
    if (!panel) return;
    const rect = panel.getBoundingClientRect();
    const headerHeight = panel.querySelector(".panel-header")?.getBoundingClientRect().height ?? 0;
    const usableHeight = Math.max(1, rect.height - headerHeight);
    state.layout.resultsRatio = clamp((rect.bottom - event.clientY) / usableHeight, 0.18, 0.62);
  }

  applyPaneSizes();
}

function stopPaneResize() {
  activePaneResize = null;
  document.body.classList.remove("is-resizing");
  window.removeEventListener("pointermove", updatePaneResize);
}

function handlePaneResizeKeydown(event) {
  const handle = event.currentTarget;
  const step = event.shiftKey ? 0.05 : 0.025;
  let handled = false;

  if (handle.dataset.resizeHandle === "problem-code") {
    if (event.key === "ArrowLeft") {
      state.layout.problemRatio = clamp(state.layout.problemRatio - step, 0.28, 0.68);
      handled = true;
    }
    if (event.key === "ArrowRight") {
      state.layout.problemRatio = clamp(state.layout.problemRatio + step, 0.28, 0.68);
      handled = true;
    }
  }

  if (handle.dataset.resizeHandle === "code-results") {
    if (event.key === "ArrowUp") {
      state.layout.resultsRatio = clamp(state.layout.resultsRatio + step, 0.18, 0.62);
      handled = true;
    }
    if (event.key === "ArrowDown") {
      state.layout.resultsRatio = clamp(state.layout.resultsRatio - step, 0.18, 0.62);
      handled = true;
    }
  }

  if (!handled) return;
  event.preventDefault();
  applyPaneSizes();
}

function paramsFromFilters() {
  const params = new URLSearchParams();
  Object.entries(state.filters).forEach(([key, value]) => {
    if (value && value !== "all") params.set(key, value);
  });
  return params.toString();
}

function setProblemSort(sortKey) {
  const sameColumn = state.filters.sort === sortKey;
  state.filters.order = sameColumn
    ? state.filters.order === "asc"
      ? "desc"
      : "asc"
    : defaultProblemSortOrder(sortKey);
  state.filters.sort = sortKey;
  loadProblems();
}

function defaultProblemSortOrder(sortKey) {
  return sortKey === "frequency" ? "desc" : "asc";
}

async function loadProblems() {
  state.view = "problems";
  state.selectedCompany = null;
  state.loading = true;
  state.error = null;
  render();
  try {
    const query = paramsFromFilters();
    const payload = await api(`/api/problems${query ? `?${query}` : ""}`);
    state.problems = payload.problems;
    state.categories = payload.categories;
    state.difficulties = payload.difficulties;
    state.companyNames = payload.companies || [];
    state.companyProfiles = payload.company_profiles || [];
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

async function loadProblem(identifier) {
  state.view = "problems";
  state.selectedCompany = null;
  state.error = null;
  state.runResult = null;
  state.activeResultIndex = 0;
  state.customTests = [];
  state.dataLink = null;
  state.dataLinkTarget = "";
  state.loading = true;
  render();
  try {
    const payload = await api(`/api/problems/${encodeURIComponent(identifier)}`);
    state.selected = payload.problem;
    if (isMlCodingProblem(state.selected)) {
      await loadCustomTests();
    }
    if (supportsDataLinkSetup(state.selected)) {
      await loadDataLink();
    }
    state.activeTab = "description";
    syncStarterCode(state.selected);
    location.hash = `#/problems/${state.selected.slug}`;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

async function loadCompanies() {
  if (codeEditor) saveCode(editorCode());
  state.view = "companies";
  state.selected = null;
  state.selectedCompany = null;
  state.error = null;
  state.loading = true;
  render();
  try {
    const payload = await api("/api/companies");
    state.companies = payload.companies || [];
    location.hash = "#/companies";
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

async function loadCompany(identifier) {
  if (codeEditor) saveCode(editorCode());
  state.view = "companies";
  state.selected = null;
  state.selectedCompany = null;
  state.error = null;
  state.loading = true;
  render();
  try {
    const payload = await api(`/api/companies/${encodeURIComponent(identifier)}`);
    state.selectedCompany = payload.company;
    location.hash = `#/companies/${state.selectedCompany.slug}`;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

function isMlCodingProblem(problem) {
  const evaluation = problem?.evaluation || {};
  return (evaluation.type || "ml_coding") === "ml_coding";
}

function supportsDataLinkSetup(problem) {
  const evaluation = problem?.evaluation || {};
  const type = evaluation.type || "ml_coding";
  return ["ml_modeling", "ml_torch_modeling", "ml_torch_lab"].includes(type) && Boolean(problem?.data?.path);
}

function codeKey(slug) {
  return `deepcode-code:${slug}`;
}

function editorSessionKey() {
  if (state.view === "playground") return "playground";
  return state.selected ? `problem:${state.selected.slug}` : null;
}

function starterKey(slug) {
  return `deepcode-starter:${slug}`;
}

function normalizeSavedCode(value) {
  return String(value ?? "").replace(/\r\n/g, "\n").trim();
}

function isLegacyNGramStarterDraft(code) {
  const normalized = normalizeSavedCode(code);
  const hasClassAndTrainStub =
    normalized.includes("class NGramCharModel:") &&
    normalized.includes("def train(self, text):\n        pass") &&
    !normalized.includes("return self");
  const hasGenerateEvaluateStubs =
    hasClassAndTrainStub &&
    normalized.includes('def generate(self, prompt="", max_new_chars=100):\n        pass') &&
    normalized.includes("def evaluate(self, text):\n        pass");
  const hasTopKStubs =
    hasClassAndTrainStub &&
    normalized.includes("def prob(self, context, ch):\n        pass") &&
    normalized.includes("def perplexity(self, text):\n        pass") &&
    normalized.includes("def sample_top_k(self, context, k=5):\n        pass");

  const hasOldBlankInitStarter =
    hasGenerateEvaluateStubs &&
    !normalized.includes("DEEPCODE_DATA_PATH/tiny_shakespeare.txt") &&
    !normalized.includes("self.alpha");
  const hasPreviousBlankGenerateStarter =
    hasGenerateEvaluateStubs &&
    normalized.includes("DEEPCODE_DATA_PATH/tiny_shakespeare.txt") &&
    !normalized.includes("def prob(self, context, ch):") &&
    !normalized.includes("def perplexity(self, text):") &&
    !normalized.includes("def sample_top_k(self, context, k=5):") &&
    !normalized.includes("self.alpha");
  const hasPreviousAlphaTopKStarter =
    hasTopKStubs &&
    normalized.includes("DEEPCODE_DATA_PATH/tiny_shakespeare.txt") &&
    normalized.includes("def __init__(self, n=3, alpha=1.0):\n        pass") &&
    !normalized.includes("self.alpha");
  const hasPreviousInitializedStarter =
    hasGenerateEvaluateStubs &&
    normalized.includes("DEEPCODE_DATA_PATH/tiny_shakespeare.txt") &&
    normalized.includes("if n < 1 or alpha < 0:") &&
    normalized.includes("self.alpha = alpha") &&
    normalized.includes("self._trained = False") &&
    normalized.includes("self.counts = defaultdict(Counter)") &&
    normalized.includes("self.global_counts = Counter()") &&
    normalized.includes("self.vocab = set()");

  return (
    hasOldBlankInitStarter ||
    hasPreviousBlankGenerateStarter ||
    hasPreviousAlphaTopKStarter ||
    hasPreviousInitializedStarter
  );
}

function shouldRefreshStoredCode(savedCode, lastStarterCode) {
  if (!savedCode) return true;
  if (lastStarterCode && normalizeSavedCode(savedCode) === normalizeSavedCode(lastStarterCode)) return true;
  return isLegacyNGramStarterDraft(savedCode);
}

function syncStarterCode(problem) {
  const key = codeKey(problem.slug);
  const versionKey = starterKey(problem.slug);
  const starterCode = problem.starter_code || "";
  const savedCode = localStorage.getItem(key);
  const lastStarterCode = localStorage.getItem(versionKey);

  if (shouldRefreshStoredCode(savedCode, lastStarterCode)) {
    localStorage.setItem(key, starterCode);
  }
  localStorage.setItem(versionKey, starterCode);
}

function currentCode() {
  if (state.view === "playground") {
    return localStorage.getItem(PLAYGROUND_CODE_KEY) ?? PLAYGROUND_STARTER_CODE;
  }
  return state.selected ? localStorage.getItem(codeKey(state.selected.slug)) ?? state.selected.starter_code ?? "" : "";
}

function validEditorHistory(value) {
  if (!value || typeof value !== "object" || !Array.isArray(value.undo) || !Array.isArray(value.redo)) return null;
  const undo = value.undo.filter((snapshot) => typeof snapshot === "string").slice(-EDITOR_HISTORY_LIMIT);
  const redo = value.redo.filter((snapshot) => typeof snapshot === "string").slice(-EDITOR_HISTORY_LIMIT);
  if (!undo.length) return null;
  return {
    undo,
    redo,
    updatedAt: Number.isFinite(value.updatedAt) ? value.updatedAt : 0,
  };
}

function loadEditorHistories() {
  try {
    const saved = JSON.parse(localStorage.getItem(EDITOR_HISTORY_STORAGE_KEY) || "{}");
    if (!saved || typeof saved !== "object" || Array.isArray(saved)) return {};
    return Object.fromEntries(
      Object.entries(saved)
        .map(([key, value]) => [key, validEditorHistory(value)])
        .filter(([, history]) => history)
    );
  } catch {
    return {};
  }
}

function persistEditorHistories(histories) {
  const recentHistories = Object.fromEntries(
    Object.entries(histories)
      .sort(([, left], [, right]) => right.updatedAt - left.updatedAt)
      .slice(0, EDITOR_HISTORY_SESSION_LIMIT)
  );
  try {
    localStorage.setItem(EDITOR_HISTORY_STORAGE_KEY, JSON.stringify(recentHistories));
    return true;
  } catch {
    return false;
  }
}

function historyForEditorSession(sessionKey, code) {
  const histories = loadEditorHistories();
  const history = histories[sessionKey];
  if (history && history.undo[history.undo.length - 1] === code) return history;

  const initialHistory = { undo: [code], redo: [], updatedAt: Date.now() };
  histories[sessionKey] = initialHistory;
  persistEditorHistories(histories);
  return initialHistory;
}

function persistEditorHistory(sessionKey, history) {
  const histories = loadEditorHistories();
  histories[sessionKey] = history;
  persistEditorHistories(histories);
}

function recordEditorHistory(session) {
  if (session.$deepcodeApplyingHistory || !session.$deepcodeHistory || !session.$deepcodeSessionKey) return;
  const history = session.$deepcodeHistory;
  const code = session.getValue();
  if (history.undo[history.undo.length - 1] === code) return;
  history.undo.push(code);
  if (history.undo.length > EDITOR_HISTORY_LIMIT) history.undo.splice(0, history.undo.length - EDITOR_HISTORY_LIMIT);
  history.redo = [];
  history.updatedAt = Date.now();
  persistEditorHistory(session.$deepcodeSessionKey, history);
}

function applyEditorHistorySnapshot(session, code) {
  session.$deepcodeApplyingHistory = true;
  session.setValue(code);
  session.$deepcodeApplyingHistory = false;
  saveCode(code);
}

function undoEditorHistory() {
  const session = codeEditor?.session;
  const history = session?.$deepcodeHistory;
  if (!session || !history || history.undo.length < 2) return;
  history.redo.push(history.undo.pop());
  history.updatedAt = Date.now();
  persistEditorHistory(session.$deepcodeSessionKey, history);
  applyEditorHistorySnapshot(session, history.undo[history.undo.length - 1]);
}

function redoEditorHistory() {
  const session = codeEditor?.session;
  const history = session?.$deepcodeHistory;
  if (!session || !history || !history.redo.length) return;
  const code = history.redo.pop();
  history.undo.push(code);
  history.updatedAt = Date.now();
  persistEditorHistory(session.$deepcodeSessionKey, history);
  applyEditorHistorySnapshot(session, code);
}

function resetEditorHistory(code) {
  const sessionKey = editorSessionKey();
  if (!sessionKey) return;
  const history = { undo: [code], redo: [], updatedAt: Date.now() };
  persistEditorHistory(sessionKey, history);
  const session = codeEditor?.session;
  if (!session || session.$deepcodeSessionKey !== sessionKey) {
    return;
  }
  session.$deepcodeHistory = history;
  applyEditorHistorySnapshot(session, code);
}

function editorCode() {
  if (codeEditor) return codeEditor.getValue();
  return document.querySelector("#code-editor-fallback")?.value ?? currentCode();
}

function normalizePythonIndentation(code) {
  return String(code ?? "")
    .split("\n")
    .map((line) => {
      const match = line.match(/^[\t ]+/);
      if (!match) return line;
      return `${match[0].replaceAll("\t", "    ")}${line.slice(match[0].length)}`;
    })
    .join("\n");
}

function setEditorCode(value) {
  if (codeEditor) {
    if (codeEditor.getValue() !== value) codeEditor.setValue(value, -1);
    return;
  }
  const fallback = document.querySelector("#code-editor-fallback");
  if (fallback) fallback.value = value;
}

function saveCode(value) {
  if (state.view === "playground") {
    localStorage.setItem(PLAYGROUND_CODE_KEY, value);
    updatePlaygroundSessionStatus(value);
    return;
  }
  if (!state.selected) return;
  localStorage.setItem(codeKey(state.selected.slug), value);
}

function validPlaygroundSessions(value) {
  if (!Array.isArray(value)) return [];
  return value
    .filter(
      (session) =>
        session &&
        typeof session.id === "string" &&
        typeof session.name === "string" &&
        typeof session.code === "string" &&
        typeof session.createdAt === "string"
    )
    .map((session) => ({
      id: session.id,
      name: session.name,
      code: session.code,
      createdAt: session.createdAt,
      updatedAt: typeof session.updatedAt === "string" ? session.updatedAt : session.createdAt,
    }));
}

function loadPlaygroundSessionState() {
  try {
    const parsed = JSON.parse(localStorage.getItem(PLAYGROUND_SESSIONS_KEY) || "null");
    const sessions = validPlaygroundSessions(parsed?.sessions);
    const activeSessionId = sessions.some((session) => session.id === parsed?.activeSessionId)
      ? parsed.activeSessionId
      : null;
    if (parsed && Array.isArray(parsed.sessions)) return { sessions, activeSessionId };
  } catch {}

  try {
    const legacySnapshots = JSON.parse(localStorage.getItem(LEGACY_PLAYGROUND_SNAPSHOTS_KEY) || "[]");
    return { sessions: validPlaygroundSessions(legacySnapshots), activeSessionId: null };
  } catch {
    return { sessions: [], activeSessionId: null };
  }
}

function persistPlaygroundSessions(sessions, activeSessionId) {
  try {
    localStorage.setItem(PLAYGROUND_SESSIONS_KEY, JSON.stringify({ sessions, activeSessionId }));
    return true;
  } catch {
    state.error = "Could not save Playground sessions in browser storage. Delete an older session and try again.";
    return false;
  }
}

function playgroundSessionId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function activePlaygroundSession() {
  return state.playgroundSessions.find((session) => session.id === state.playgroundActiveSessionId) || null;
}

function playgroundSessionDirty(code = currentCode(), name = state.playgroundSessionName) {
  const activeSession = activePlaygroundSession();
  if (!activeSession) return true;
  const draftName = String(name ?? "").trim();
  return code !== activeSession.code || (draftName !== "" && draftName !== activeSession.name);
}

function playgroundSessionStatusText(code = currentCode()) {
  const activeSession = activePlaygroundSession();
  if (!activeSession) return "Current: unsaved draft";
  return playgroundSessionDirty(code)
    ? `Current: ${activeSession.name} · unsaved changes`
    : `Current: ${activeSession.name} · saved`;
}

function updatePlaygroundSessionStatus(code = currentCode()) {
  const status = document.querySelector("#playground-session-status");
  const saveButton = document.querySelector("#playground-session-save");
  const activeSession = activePlaygroundSession();
  const dirty = playgroundSessionDirty(code);
  if (status) {
    status.textContent = playgroundSessionStatusText(code);
    status.classList.toggle("dirty", dirty);
  }
  if (saveButton) {
    saveButton.disabled = state.playgroundRunning || !activeSession || !dirty;
    saveButton.title = !activeSession
      ? "Use Save as new first"
      : dirty
        ? "Save code or name changes to the current session"
        : "No unsaved changes";
  }
}

function savePlaygroundSession() {
  if (state.view !== "playground" || state.playgroundRunning) return;
  const activeSession = activePlaygroundSession();
  if (!activeSession) {
    state.error = "Use Save as new to create a session before using Save.";
    render();
    return;
  }
  if (!playgroundSessionDirty(editorCode())) return;
  const code = normalizePythonIndentation(editorCode());
  const name = state.playgroundSessionName.trim() || activeSession.name;
  setEditorCode(code);
  saveCode(code);
  const updatedSession = { ...activeSession, name, code, updatedAt: new Date().toISOString() };
  const sessions = [updatedSession, ...state.playgroundSessions.filter((session) => session.id !== activeSession.id)];
  state.error = null;
  if (!persistPlaygroundSessions(sessions, activeSession.id)) {
    render();
    return;
  }
  state.playgroundSessions = sessions;
  state.playgroundSessionName = "";
  render();
}

function savePlaygroundSessionAs() {
  if (state.view !== "playground" || state.playgroundRunning) return;
  const code = normalizePythonIndentation(editorCode());
  const name = state.playgroundSessionName.trim() || `Session ${state.playgroundSessions.length + 1}`;
  const createdAt = new Date().toISOString();
  const session = { id: playgroundSessionId(), name, code, createdAt, updatedAt: createdAt };
  const sessions = [session, ...state.playgroundSessions];
  state.error = null;
  if (!persistPlaygroundSessions(sessions, session.id)) {
    render();
    return;
  }
  setEditorCode(code);
  saveCode(code);
  state.playgroundSessions = sessions;
  state.playgroundActiveSessionId = session.id;
  state.playgroundSessionName = "";
  render();
}

function openPlaygroundSession(sessionId) {
  const session = state.playgroundSessions.find((item) => item.id === sessionId);
  if (!session || state.playgroundRunning || session.id === state.playgroundActiveSessionId) return;
  const activeSession = activePlaygroundSession();
  if (
    playgroundSessionDirty() &&
    !window.confirm(`Discard unsaved changes in "${activeSession?.name || "current draft"}" and open "${session.name}"?`)
  ) {
    return;
  }
  state.error = null;
  if (!persistPlaygroundSessions(state.playgroundSessions, session.id)) {
    render();
    return;
  }
  localStorage.setItem(PLAYGROUND_CODE_KEY, session.code);
  state.playgroundActiveSessionId = session.id;
  state.playgroundSessionName = "";
  state.playgroundResult = null;
  state.playgroundRunSource = "";
  render();
}

function deletePlaygroundSession(sessionId) {
  const session = state.playgroundSessions.find((item) => item.id === sessionId);
  if (!session || !window.confirm(`Delete session "${session.name}"?`)) return;
  const sessions = state.playgroundSessions.filter((item) => item.id !== sessionId);
  const activeSessionId = session.id === state.playgroundActiveSessionId ? null : state.playgroundActiveSessionId;
  state.error = null;
  if (!persistPlaygroundSessions(sessions, activeSessionId)) {
    render();
    return;
  }
  state.playgroundSessions = sessions;
  state.playgroundActiveSessionId = activeSessionId;
  if (!activeSessionId) state.playgroundSessionName = "";
  render();
}

function formatSessionTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function customTestSignature(problem) {
  const match = String(problem?.starter_code || "").match(/def\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*:/);
  if (!match) return null;

  const parameters = match[2]
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.split("=")[0].split(":")[0].replace(/^[*/\s]+/, "").trim())
    .filter((name) => name && name !== "self" && name !== "cls");

  return parameters.length ? { functionName: match[1], parameters } : null;
}

function defaultCustomTest() {
  const signature = customTestSignature(state.selected);
  if (!signature) {
    return { name: `Custom test ${state.customTests.length + 1}`, input: "", test: "", expected_output: "", mode: "raw" };
  }

  return {
    name: `Custom test ${state.customTests.length + 1}`,
    arguments: Object.fromEntries(signature.parameters.map((parameter) => [parameter, ""])),
    expected_output: "",
    mode: "arguments",
  };
}

function customTestMode(test, signature) {
  if (!signature) return "raw";
  if (test.mode === "raw") return "raw";
  return test.mode === "arguments" || test.arguments ? "arguments" : "raw";
}

function ensureCustomTestArguments(test, signature) {
  if (!signature) return test;
  return {
    ...test,
    mode: "arguments",
    arguments: {
      ...Object.fromEntries(signature.parameters.map((parameter) => [parameter, ""])),
      ...(test.arguments || {}),
    },
  };
}

async function loadCustomTests() {
  if (!state.selected || !isMlCodingProblem(state.selected)) {
    state.customTests = [];
    return;
  }
  const payload = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/custom-tests`);
  state.customTests = payload.custom_tests || [];
}

async function saveCustomTests() {
  if (!state.selected || !isMlCodingProblem(state.selected)) return;
  collectCustomTestInputs();
  try {
    const payload = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/custom-tests`, {
      method: "PUT",
      body: JSON.stringify({ custom_tests: state.customTests }),
    });
    state.customTests = payload.custom_tests || [];
    state.error = null;
  } catch (error) {
    state.error = error.message;
  }
  render();
}

function collectCustomTestInputs() {
  if (!state.selected || state.activeTab !== "tests") return;
  const signature = customTestSignature(state.selected);
  document.querySelectorAll("[data-custom-index][data-custom-field]").forEach((field) => {
    const index = Number(field.dataset.customIndex);
    const key = field.dataset.customField;
    if (!Number.isInteger(index) || !key || !state.customTests[index]) return;
    const next = { ...state.customTests[index], [key]: field.value };
    state.customTests[index] = key === "mode" && field.value === "arguments" ? ensureCustomTestArguments(next, signature) : next;
  });
  document.querySelectorAll("[data-custom-index][data-custom-argument]").forEach((field) => {
    const index = Number(field.dataset.customIndex);
    const parameter = field.dataset.customArgument;
    if (!Number.isInteger(index) || !parameter || !state.customTests[index]) return;
    const current = ensureCustomTestArguments(state.customTests[index], signature);
    state.customTests[index] = {
      ...current,
      arguments: { ...(current.arguments || {}), [parameter]: field.value },
    };
  });
}

function addCustomTest() {
  collectCustomTestInputs();
  state.pendingCustomTestScrollIndex = state.customTests.length;
  state.customTests = [...state.customTests, defaultCustomTest()];
  render();
}

function removeCustomTest(index) {
  collectCustomTestInputs();
  state.customTests = state.customTests.filter((_, currentIndex) => currentIndex !== index);
  render();
}

async function loadDataLink() {
  if (!state.selected || !supportsDataLinkSetup(state.selected)) {
    state.dataLink = null;
    state.dataLinkTarget = "";
    return;
  }
  const payload = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/data-link`);
  state.dataLink = payload;
  state.dataLinkTarget = payload.target_path || "";
}

async function saveDataLink() {
  if (!state.selected || !supportsDataLinkSetup(state.selected)) return;
  const field = document.querySelector("#data-link-target");
  const targetPath = field?.value?.trim() || state.dataLinkTarget;
  try {
    const payload = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/data-link`, {
      method: "PUT",
      body: JSON.stringify({ target_path: targetPath }),
    });
    state.dataLink = payload;
    state.dataLinkTarget = payload.target_path || targetPath;
    state.error = null;
  } catch (error) {
    state.error = error.message;
  }
  render();
}

async function removeDataLink() {
  if (!state.selected || !supportsDataLinkSetup(state.selected)) return;
  try {
    const payload = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/data-link`, {
      method: "DELETE",
    });
    state.dataLink = payload;
    state.dataLinkTarget = "";
    state.error = null;
  } catch (error) {
    state.error = error.message;
  }
  render();
}

function teardownEditor() {
  if (!codeEditor) return;
  codeEditor.destroy();
  codeEditor = null;
}

function mountEditor() {
  if (!state.selected && state.view !== "playground") {
    teardownEditor();
    return;
  }

  const aceContainer = document.querySelector("#code-editor");
  const fallback = document.querySelector("#code-editor-fallback");
  if (!aceContainer || !fallback) return;

  if (!window.ace) {
    fallback.hidden = false;
    aceContainer.hidden = true;
    return;
  }

  fallback.hidden = true;
  aceContainer.hidden = false;
  window.ace.config.set("basePath", "/vendor/ace");
  codeEditor = window.ace.edit(aceContainer);
  const sessionKey = editorSessionKey();
  codeEditor.setValue(currentCode(), -1);
  setEditorTheme();
  codeEditor.session.setMode("ace/mode/python");
  codeEditor.session.setUseWorker(false);
  codeEditor.setOptions({
    fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
    fontSize: "14px",
    tabSize: 4,
    useSoftTabs: true,
    showPrintMargin: false,
    wrap: true,
    highlightActiveLine: true,
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
  });
  if (sessionKey) {
    const session = codeEditor.session;
    session.$deepcodeSessionKey = sessionKey;
    session.$deepcodeHistory = historyForEditorSession(sessionKey, session.getValue());
    session.on("change", () => {
      saveCode(session.getValue());
      recordEditorHistory(session);
    });
  }
  codeEditor.commands.addCommand({
    name: "runCode",
    bindKey: { win: "Ctrl-Enter", mac: "Command-Enter" },
    exec: () => (state.view === "playground" ? runPlayground() : runTests()),
  });
  codeEditor.commands.addCommand({
    name: "deepcodeUndo",
    bindKey: { win: "Ctrl-Z", mac: "Command-Z" },
    exec: undoEditorHistory,
  });
  codeEditor.commands.addCommand({
    name: "deepcodeRedo",
    bindKey: { win: "Ctrl-Y|Ctrl-Shift-Z", mac: "Command-Shift-Z" },
    exec: redoEditorHistory,
  });
}

function startRunTimer() {
  stopRunTimer();
  state.runStartedAt = Date.now();
  state.runElapsedSeconds = 0;
  runTimer = setInterval(updateRunElapsed, 1000);
}

function stopRunTimer() {
  if (runTimer) {
    clearInterval(runTimer);
    runTimer = null;
  }
}

function updateRunElapsed() {
  if (!state.runStartedAt) return;
  state.runElapsedSeconds = Math.max(0, Math.floor((Date.now() - state.runStartedAt) / 1000));
  const elapsed = document.querySelector("#run-elapsed");
  if (elapsed) elapsed.textContent = `${state.runElapsedSeconds}s elapsed`;
}

async function runTests(testIndex = null) {
  if (!state.selected) return;
  const code = normalizePythonIndentation(editorCode());
  setEditorCode(code);
  saveCode(code);
  const payload = { code };
  if (Number.isInteger(testIndex)) payload.test_index = testIndex;
  await runPayload(payload, { testIndex });
}

async function runCustomTests(customIndex = null) {
  if (!state.selected || !isMlCodingProblem(state.selected)) return;
  collectCustomTestInputs();
  const customTests = Number.isInteger(customIndex) ? [state.customTests[customIndex]] : state.customTests;
  if (!customTests.length) {
    state.error = "Add at least one custom test before running custom checks";
    render();
    return;
  }
  const code = normalizePythonIndentation(editorCode());
  setEditorCode(code);
  saveCode(code);
  const payload = { code, custom_only: true, custom_tests: customTests };
  await runPayload(payload, { customIndex: Number.isInteger(customIndex) ? customIndex : "all" });
}

async function runPayload(payload, { testIndex = null, customIndex = null } = {}) {
  state.running = true;
  state.runResult = null;
  state.runLogs = [];
  state.activeRunCheck = null;
  state.activeResultIndex = 0;
  state.runningTestIndex = Number.isInteger(testIndex) ? testIndex : null;
  state.runningCustomTestIndex = Number.isInteger(customIndex) || customIndex === "all" ? customIndex : null;
  state.error = null;
  startRunTimer();
  render();
  updateRunElapsed();
  try {
    const didStream = await runTestsWithStream(payload);
    if (!didStream) {
      state.runResult = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/run`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    if (!state.runResult) {
      throw new Error("Runner stream ended before returning a result");
    }
    if (state.runResult.problem_status) {
      syncProblemStatus(state.selected.slug, state.runResult.problem_status);
    }
  } catch (error) {
    state.error = error.message;
  } finally {
    stopRunTimer();
    state.running = false;
    state.runStartedAt = null;
    state.runningTestIndex = null;
    state.runningCustomTestIndex = null;
    state.activeRunCheck = null;
    render();
  }
}

async function runTestsWithStream(payload) {
  if (typeof ReadableStream === "undefined") return false;

  const response = await fetch(`/api/problems/${encodeURIComponent(state.selected.slug)}/run/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) return false;

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    lines.filter(Boolean).forEach(processRunEvent);
    if (done) break;
  }
  if (buffer.trim()) processRunEvent(buffer);
  return true;
}

function processRunEvent(line) {
  const event = JSON.parse(line);
  if (event.type === "error") {
    throw new Error(event.error || "Runner stream failed");
  }
  if (event.type === "check_started") {
    state.activeRunCheck = event.name || `Check ${event.index + 1}`;
    updateRunStatus();
    return;
  }
  if (event.type === "log") {
    state.runLogs.push({ stream: event.stream || "stdout", text: event.text || "" });
    updateRunLogPanel();
    return;
  }
  if (event.type === "run_finished") {
    state.runResult = event.result;
  }
}

function updateRunStatus() {
  const target = document.querySelector("#run-target");
  if (target) target.textContent = activeRunTargetLabel();
}

function updateRunLogPanel() {
  const panel = document.querySelector("#run-log-lines");
  if (!panel) return;
  panel.innerHTML = renderRunLogLines();
  panel.scrollTop = panel.scrollHeight;
}

async function runPlayground(sessionId = null) {
  if (state.view !== "playground" || state.playgroundRunning) return;
  const session = sessionId ? state.playgroundSessions.find((item) => item.id === sessionId) : null;
  if (sessionId && !session) return;
  const code = normalizePythonIndentation(session ? session.code : editorCode());
  if (!session) {
    setEditorCode(code);
    saveCode(code);
  }
  state.playgroundRunning = true;
  state.playgroundResult = null;
  const activeSession = activePlaygroundSession();
  state.playgroundRunSource = session
    ? session.name
    : activeSession
      ? `${activeSession.name}${playgroundSessionDirty(code) ? " (unsaved changes)" : ""}`
      : "Unsaved draft";
  state.error = null;
  render();
  try {
    state.playgroundResult = await api("/api/playground/run", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  } catch (error) {
    state.error = error.message;
  } finally {
    state.playgroundRunning = false;
    render();
  }
}

function resetPlayground() {
  localStorage.setItem(PLAYGROUND_CODE_KEY, PLAYGROUND_STARTER_CODE);
  resetEditorHistory(PLAYGROUND_STARTER_CODE);
  state.playgroundResult = null;
  state.playgroundRunSource = "";
  state.error = null;
  render();
}

async function resetCode() {
  if (!state.selected) return;
  const starterCode = state.selected.starter_code || "";
  localStorage.setItem(codeKey(state.selected.slug), starterCode);
  resetEditorHistory(starterCode);
  state.runResult = null;
  state.activeResultIndex = 0;
  state.error = null;
  try {
    const payload = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/reset`, { method: "POST" });
    if (payload.problem_status) {
      syncProblemStatus(state.selected.slug, payload.problem_status);
    }
  } catch (error) {
    state.error = error.message;
  }
  render();
}

function problemCompleted(problem) {
  return problem?.personal_status?.completed === true;
}

function completedProblemCount() {
  return state.problems.filter(problemCompleted).length;
}

function syncProblemStatus(slug, status) {
  const personalStatus = { completed: status?.completed === true, completed_at: status?.completed_at || null };
  state.problems = state.problems.map((problem) =>
    problem.slug === slug ? { ...problem, personal_status: personalStatus } : problem
  );
  if (state.selected?.slug === slug) {
    state.selected = { ...state.selected, personal_status: personalStatus };
  }
}

function randomProblem() {
  if (!state.problems.length) return;
  const index = Math.floor(Math.random() * state.problems.length);
  loadProblem(state.problems[index].slug);
}

function backToList() {
  if (codeEditor) saveCode(editorCode());
  const needsProblemCatalog = state.problems.length === 0;
  state.view = "problems";
  state.selected = null;
  state.selectedCompany = null;
  state.runResult = null;
  state.activeResultIndex = 0;
  state.error = null;
  location.hash = "";
  if (needsProblemCatalog) {
    loadProblems();
    return;
  }
  render();
}

function backToCompanies() {
  const needsCompanyCatalog = state.companies.length === 0;
  state.view = "companies";
  state.selected = null;
  state.selectedCompany = null;
  state.error = null;
  location.hash = "#/companies";
  if (needsCompanyCatalog) {
    loadCompanies();
    return;
  }
  render();
}

function openPlayground() {
  if (codeEditor) saveCode(editorCode());
  state.view = "playground";
  state.selected = null;
  state.selectedCompany = null;
  state.error = null;
  if (location.hash !== "#/playground") {
    location.hash = "#/playground";
  }
  render();
}

function difficultyPill(difficulty) {
  return `<span class="pill ${escapeHtml(difficulty)}">${escapeHtml(difficulty)}</span>`;
}

function labelList(values, className = "label-list") {
  const labels = (values || []).map((value) => `<span class="label">${escapeHtml(value)}</span>`).join("");
  return labels ? `<div class="${className}">${labels}</div>` : "";
}

function companyProfileSlug(companyName) {
  const normalized = String(companyName ?? "").trim().toLocaleLowerCase();
  if (!normalized) return null;
  const profile = state.companyProfiles.find((item) =>
    [item.name, ...(item.aliases || [])].some((value) => String(value ?? "").trim().toLocaleLowerCase() === normalized)
  );
  return profile?.slug || null;
}

function companyFrequencyBadge(frequency) {
  const stars = frequency?.stars;
  if (!Number.isInteger(stars) || stars < 1 || stars > 5) return "";
  return `<span class="company-frequency" aria-label="Interview-signal frequency tier ${stars}">${"★".repeat(stars)}</span>`;
}

function problemFrequencyStars(problem) {
  return Math.max(
    0,
    ...Object.values(problem?.interview_frequency || {}).map((frequency) => {
      const stars = frequency?.stars;
      return Number.isInteger(stars) && stars >= 1 && stars <= 5 ? stars : 0;
    })
  );
}

function problemFrequencyBadge(problem) {
  const stars = problemFrequencyStars(problem);
  if (!stars) return `<span class="muted-cell" aria-label="No interview-signal frequency tier">-</span>`;
  return `<span class="problem-frequency" aria-label="Highest interview-signal frequency tier ${stars}" title="Highest company-specific interview-signal tier">${"★".repeat(stars)}</span>`;
}

function companyFrequencyFor(frequencies, companyName) {
  return Object.entries(frequencies || {}).find(
    ([company]) => String(company).trim().toLocaleLowerCase() === String(companyName).trim().toLocaleLowerCase()
  )?.[1];
}

function companyLabelList(values, className = "company-list", frequencies = {}) {
  const labels = (values || [])
    .map((value) => {
      const profileSlug = companyProfileSlug(value);
      const label = profileSlug
        ? `<button class="label company-label-link" type="button" data-company-profile="${escapeHtml(profileSlug)}">${escapeHtml(value)}</button>`
        : `<span class="label">${escapeHtml(value)}</span>`;
      return `<span class="company-label-with-frequency">${label}${companyFrequencyBadge(companyFrequencyFor(frequencies, value))}</span>`;
    })
    .join("");
  return labels ? `<div class="${className}">${labels}</div>` : "";
}

function problemDisplayId(problem) {
  return problem?.display_id ?? problem?.id ?? "";
}

function render() {
  teardownEditor();
  if (state.view === "playground") {
    renderPlayground();
  } else if (state.view === "companies") {
    if (state.selectedCompany) {
      renderCompanyDetail();
    } else {
      renderCompanies();
    }
  } else if (state.selected) {
    renderDetail();
  } else {
    renderList();
  }
  bindEvents();
  mountEditor();
  applyPaneSizes();
  syncProblemTimer();
  scrollPendingCustomTestIntoView();
}

function companyStageSummary(stage) {
  if (stageResearchPending(stage)) return "";
  return [stage?.company_state, stage?.funding_stage].filter(Boolean).join(" · ");
}

function stageResearchPending(stage) {
  const status = [stage?.company_state, stage?.funding_stage]
    .filter(Boolean)
    .join(" ")
    .toLocaleLowerCase();
  return status.includes("not independently verified") || status.includes("not recorded in opportunity 2026");
}

function companyFundingSummary(stage) {
  return [stage?.amount, stage?.valuation, stage?.last_announced ? `announced ${stage.last_announced}` : ""]
    .filter(Boolean)
    .join(" · ");
}

function externalLinks(links, className = "reference-list") {
  const items = (links || [])
    .filter((link) => link && link.label && link.url)
    .map(
      (link) => `
        <a href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer">
          ${escapeHtml(link.label)}
        </a>
      `
    )
    .join("");
  return items ? `<div class="${className}">${items}</div>` : "";
}

function renderCompanies() {
  const cards = state.companies
    .map((company) => {
      const stage = company.stage || {};
      const stageSummary = companyStageSummary(stage);
      const funding = companyFundingSummary(stage);
      return `
        <button class="company-card" data-company-slug="${escapeHtml(company.slug)}">
          <div class="company-card-heading">
            <div>
              <h2>${escapeHtml(company.name)}</h2>
              <p>${escapeHtml(company.summary)}</p>
            </div>
            ${stageSummary ? `<span class="company-stage-badge">${escapeHtml(stageSummary)}</span>` : ""}
          </div>
          ${funding ? `<p class="company-funding">${escapeHtml(funding)}</p>` : ""}
          <footer><strong>${escapeHtml(company.problem_count || 0)}</strong> related DeepCode problem${company.problem_count === 1 ? "" : "s"}</footer>
        </button>
      `;
    })
    .join("");

  app.innerHTML = `
    <main class="page company-page">
      <header class="topbar">
        <div class="brand">
          <div class="mark">DC</div>
          <div>
            <h1>Company Hub</h1>
            <p>Research context, interview signals, and linked practice.</p>
          </div>
        </div>
        <div class="topbar-actions">
          ${mainNavigation()}
          ${themeToggleButton()}
        </div>
      </header>
      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}
      <section class="company-intro">
        <div>
          <strong>${state.companies.length}</strong>
          <span>profile${state.companies.length === 1 ? "" : "s"}</span>
        </div>
        <p>Profiles capture hiring and interview context. Stage badges appear only when the profile cites a public source. Where a business snapshot is tracked, it uses the same fixed fields and marks unavailable figures as not publicly disclosed.</p>
      </section>
      <section class="company-card-grid" aria-label="Company profiles">
        ${state.loading ? `<div class="loading-screen">Loading company profiles...</div>` : cards || `<div class="empty-state">No company profiles yet.</div>`}
      </section>
    </main>
  `;
}

function companyMetaRow(label, value) {
  if (!value) return "";
  return `<div class="company-meta-row"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function renderBusinessSnapshot(snapshot) {
  if (!snapshot) return "";
  return `
    <section class="company-detail-section">
      <div class="company-section-heading">
        <div>
          <h2>Business snapshot</h2>
          <p>Publicly sourced figures only. Private-company valuation is not public-market capitalization.</p>
        </div>
      </div>
      <dl class="company-meta-grid">
        ${companyMetaRow("Founded", snapshot.founded)}
        ${companyMetaRow("Team size", snapshot.team_size)}
        ${companyMetaRow("ARR / annualized revenue", snapshot.arr_or_revenue)}
        ${companyMetaRow("Latest valuation", snapshot.valuation)}
        ${companyMetaRow("Latest financing", snapshot.latest_financing)}
      </dl>
      ${externalLinks(snapshot.sources, "company-source-list")}
    </section>
  `;
}

function renderCompanyDetail() {
  const company = state.selectedCompany;
  const stage = company.stage || {};
  const stageSummary = companyStageSummary(stage);
  const interview = company.interview_process || {};
  const interviewStages = (interview.stages || [])
    .map(
      (item) => `
        <article class="interview-stage-card">
          <div class="interview-stage-heading">
            <h3>${escapeHtml(item.name)}</h3>
            <span class="evidence-badge">${escapeHtml(item.evidence_tier)}</span>
          </div>
          <p>${escapeHtml(item.signal)}</p>
          ${externalLinks(item.sources, "company-source-list")}
        </article>
      `
    )
    .join("");
  const notes = (company.notes || [])
    .map((note) => `<article class="company-note"><strong>${escapeHtml(note.label)}</strong><p>${escapeHtml(note.detail)}</p></article>`)
    .join("");
  const relatedProblems = (company.related_problems || [])
    .map(
      (problem) => `
        <button class="company-problem-card" data-company-problem="${escapeHtml(problem.slug)}">
          <span>#${escapeHtml(problem.display_id ?? problem.id)}</span>
          <strong>${escapeHtml(problem.title)}</strong>
          <small>${escapeHtml(problem.category)} · ${escapeHtml(problem.difficulty)}</small>
        </button>
      `
    )
    .join("");

  app.innerHTML = `
    <main class="page company-page company-detail-page">
      <header class="topbar">
        <div class="company-detail-navigation">
          <button class="ghost-button" id="company-back-button">← Companies</button>
          ${mainNavigation()}
        </div>
        <div class="topbar-actions">${themeToggleButton()}</div>
      </header>
      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}
      <article class="company-detail-panel">
        <header class="company-hero">
          <div>
            <p class="eyebrow">Company profile</p>
            <h1>${escapeHtml(company.name)}</h1>
            <p>${escapeHtml(company.summary)}</p>
          </div>
          <div class="company-hero-stage">
            ${stageSummary ? `<span class="company-stage-badge">${escapeHtml(stageSummary)}</span>` : ""}
            <small>Last reviewed ${escapeHtml(company.updated_at || "not recorded")}</small>
          </div>
        </header>

        ${renderBusinessSnapshot(company.business_snapshot)}

        <section class="company-detail-section">
          <h2>Company links</h2>
          ${externalLinks(company.links)}
        </section>

        <section class="company-detail-section">
          <div class="company-section-heading">
            <div>
              <h2>Interview process</h2>
              <p>${escapeHtml(interview.summary || "No interview-process context recorded yet.")}</p>
            </div>
            ${interview.evidence_tier ? `<span class="evidence-badge">${escapeHtml(interview.evidence_tier)}</span>` : ""}
          </div>
          <div class="interview-stage-list">${interviewStages || `<div class="empty-state">No stage signals recorded yet.</div>`}</div>
        </section>

        <section class="company-detail-section">
          <h2>Related DeepCode problems</h2>
          <div class="company-problem-list">${relatedProblems || `<div class="empty-state">No linked problems yet.</div>`}</div>
        </section>

        ${notes ? `<section class="company-detail-section"><h2>Research notes</h2><div class="company-note-list">${notes}</div></section>` : ""}
        ${company.references?.length ? `<section class="company-detail-section"><h2>Sources</h2>${externalLinks(company.references)}</section>` : ""}
      </article>
    </main>
  `;
}

function scrollPendingCustomTestIntoView() {
  if (!Number.isInteger(state.pendingCustomTestScrollIndex)) return;
  const index = state.pendingCustomTestScrollIndex;
  state.pendingCustomTestScrollIndex = null;
  const target = document.querySelector(`[data-custom-test-index="${index}"]`);
  const scroller = target?.closest(".problem-body");
  if (!target || !scroller) return;

  const targetRect = target.getBoundingClientRect();
  const scrollerRect = scroller.getBoundingClientRect();
  const centeredOffset = targetRect.top - scrollerRect.top - (scrollerRect.height - targetRect.height) / 2;
  scroller.scrollTop += centeredOffset;
}

function renderList() {
  const categoryOptions = [
    `<option value="all">All Categories</option>`,
    ...state.categories.map((category) => {
      const selected = state.filters.category === category ? "selected" : "";
      return `<option value="${escapeHtml(category)}" ${selected}>${escapeHtml(category)}</option>`;
    }),
  ].join("");

  const difficultyOptions = [
    `<option value="all">All Difficulties</option>`,
    ...state.difficulties.map((difficulty) => {
      const selected = state.filters.difficulty === difficulty ? "selected" : "";
      return `<option value="${escapeHtml(difficulty)}" ${selected}>${escapeHtml(difficulty)}</option>`;
    }),
  ].join("");

  const companyOptions = [
    `<option value="all">All Companies</option>`,
    ...state.companyNames.map((company) => {
      const selected = state.filters.company === company ? "selected" : "";
      return `<option value="${escapeHtml(company)}" ${selected}>${escapeHtml(company)}</option>`;
    }),
  ].join("");

  app.innerHTML = `
    <main class="page">
      <header class="topbar">
        <div class="brand">
          <div class="mark">DC</div>
          <div>
            <h1>DeepCode</h1>
            <p>${state.problems.length} local problem${state.problems.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        <div class="topbar-actions">
          ${mainNavigation()}
          <button class="ghost-button" id="random-problem">Random</button>
          ${themeToggleButton()}
        </div>
      </header>

      <section class="stat-grid" aria-label="Collection status">
        <div class="stat-card"><strong>${state.problems.length}</strong><span>Visible problems</span></div>
        <div class="stat-card"><strong>${completedProblemCount()}</strong><span>Completed</span></div>
        <div class="stat-card"><strong>${state.categories.length}</strong><span>Categories</span></div>
        <div class="stat-card"><strong>Py</strong><span>Local runner</span></div>
      </section>

      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}

      <section class="filters">
        <div class="filter-row">
          <input class="field" id="search" value="${escapeHtml(state.filters.search)}" placeholder="Search problems..." />
          <select class="field" id="category">${categoryOptions}</select>
          <select class="field" id="difficulty">${difficultyOptions}</select>
          <select class="field" id="company">${companyOptions}</select>
          <select class="field" id="sort">
            <option value="id" ${state.filters.sort === "id" ? "selected" : ""}>Sort by ID</option>
            <option value="title" ${state.filters.sort === "title" ? "selected" : ""}>Sort by Title</option>
            <option value="difficulty" ${state.filters.sort === "difficulty" ? "selected" : ""}>Sort by Difficulty</option>
            <option value="category" ${state.filters.sort === "category" ? "selected" : ""}>Sort by Category</option>
            <option value="frequency" ${state.filters.sort === "frequency" ? "selected" : ""}>Sort by Stars</option>
            <option value="completed" ${state.filters.sort === "completed" ? "selected" : ""}>Sort by Complete</option>
          </select>
          <button class="primary-button" id="apply-filters">Apply</button>
        </div>
      </section>

      <section class="table-panel">
        ${state.loading ? `<div class="loading-screen">Loading problems...</div>` : problemTable()}
      </section>
    </main>
  `;
}

function renderPlayground() {
  const activeSession = activePlaygroundSession();
  const sessionDirty = playgroundSessionDirty();
  const runButtonContent = state.playgroundRunning
    ? `<span class="button-spinner" aria-hidden="true"></span><span>Running</span>`
    : "Run code";
  app.innerHTML = `
    <main class="page page-detail playground-page">
      <header class="topbar playground-topbar">
        <div class="brand">
          <div class="mark">DC</div>
          <div>
            <h1>PyTorch Playground</h1>
            <p>Free-form local experiments, separate from problem submissions.</p>
          </div>
        </div>
        <div class="topbar-actions">
          ${mainNavigation()}
          ${themeToggleButton()}
        </div>
      </header>

      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}

      <section class="playground-panel" aria-label="PyTorch Playground">
        <div class="panel-header playground-panel-header">
          <div class="panel-title">
            <h2>${escapeHtml(activeSession?.name || "scratch.py")}</h2>
            <p>Python + PyTorch · Cmd/Ctrl + Enter to run · 30 second limit</p>
          </div>
          <div class="editor-actions">
            <button class="ghost-button" id="playground-reset" ${state.playgroundRunning ? "disabled" : ""}>Reset example</button>
            <button
              class="primary-button"
              id="playground-run"
              ${state.playgroundRunning ? "disabled" : ""}
              aria-busy="${state.playgroundRunning}"
            >${runButtonContent}</button>
          </div>
        </div>
        <section class="playground-sessions" aria-label="Saved Playground sessions">
          <div class="playground-session-toolbar">
            <div>
              <strong>Sessions</strong>
              <span id="playground-session-status" class="${sessionDirty ? "dirty" : ""}">
                ${escapeHtml(playgroundSessionStatusText())}
              </span>
            </div>
            <div class="playground-session-save">
              <input
                class="field"
                id="playground-session-name"
                value="${escapeHtml(state.playgroundSessionName)}"
                placeholder="${activeSession ? "Rename current or name a new session" : "New session name (optional)"}"
                aria-label="Session name"
                maxlength="80"
                ${state.playgroundRunning ? "disabled" : ""}
              />
              <button
                class="ghost-button"
                id="playground-session-save"
                ${state.playgroundRunning || !activeSession || !sessionDirty ? "disabled" : ""}
                title="${
                  !activeSession
                    ? "Use Save as new first"
                    : sessionDirty
                      ? "Save code or name changes to the current session"
                      : "No unsaved changes"
                }"
              >
                Save
              </button>
              <button class="ghost-button" id="playground-session-save-as" ${state.playgroundRunning ? "disabled" : ""}>
                Save as new
              </button>
            </div>
          </div>
          ${renderPlaygroundSessions()}
        </section>
        <div class="playground-workspace">
          <section class="playground-editor" aria-label="Python editor">
            <div class="code-pane">
              <div id="code-editor" class="code-editor ace-editor"></div>
              <textarea id="code-editor-fallback" class="code-editor fallback-editor" spellcheck="false">${escapeHtml(
                currentCode()
              )}</textarea>
            </div>
          </section>
          <section class="playground-console" aria-label="Execution output">
            <div class="playground-console-header">
              <strong>Console</strong>
              <span>${
                state.playgroundRunSource
                  ? `Last run: ${escapeHtml(state.playgroundRunSource)}`
                  : "Runs in a temporary local process"
              }</span>
            </div>
            <div class="playground-console-body">${renderPlaygroundResult()}</div>
          </section>
        </div>
        <p class="playground-safety-note">
          Playground code runs on this machine with a timeout and output limits. It is intended for your own code, not as a hardened sandbox for untrusted snippets.
        </p>
      </section>
    </main>
  `;
}

function renderPlaygroundSessions() {
  if (!state.playgroundSessions.length) {
    return `
      <div class="playground-session-empty">
        This is an unsaved draft. Use Save as new to create your first Playground session.
      </div>
    `;
  }
  return `
    <div class="playground-session-list">
      ${state.playgroundSessions
        .map(
          (session) => {
            const active = session.id === state.playgroundActiveSessionId;
            return `
            <article class="playground-session-card ${active ? "active" : ""}">
              <div class="playground-session-heading">
                <div>
                  <div class="playground-session-title">
                    <strong>${escapeHtml(session.name)}</strong>
                    ${active ? `<span class="playground-session-current">Current</span>` : ""}
                  </div>
                  <span>Updated ${escapeHtml(formatSessionTime(session.updatedAt))}</span>
                </div>
                <button
                  class="text-button danger"
                  data-delete-playground-session="${escapeHtml(session.id)}"
                  ${state.playgroundRunning ? "disabled" : ""}
                  aria-label="Delete ${escapeHtml(session.name)}"
                >Delete</button>
              </div>
              <div class="playground-session-actions">
                ${
                  active
                    ? ""
                    : `<button
                        class="ghost-button"
                        data-open-playground-session="${escapeHtml(session.id)}"
                        ${state.playgroundRunning ? "disabled" : ""}
                      >Open session</button>`
                }
                <button
                  class="primary-button"
                  data-run-playground-session="${escapeHtml(session.id)}"
                  ${state.playgroundRunning ? "disabled" : ""}
                >Run saved</button>
              </div>
            </article>
          `;
          }
        )
        .join("")}
    </div>
  `;
}

function renderPlaygroundResult() {
  if (state.playgroundRunning) {
    return `
      <div class="playground-running" aria-live="polite" aria-busy="true">
        <span class="run-spinner" aria-hidden="true"></span>
        <div><strong>Running locally...</strong><p>The process will stop automatically after 30 seconds.</p></div>
      </div>
    `;
  }

  const result = state.playgroundResult;
  if (!result) {
    return `<div class="playground-console-empty">Run the starter example or replace it with any PyTorch experiment.</div>`;
  }

  const completed = result.status === "completed";
  const statusLabel = completed ? "Completed" : result.status === "timed_out" ? "Timed out" : "Error";
  const exitLabel = result.exit_code === null ? "no exit code" : `exit ${result.exit_code}`;
  const duration = result.duration_ms < 1000 ? `${result.duration_ms} ms` : `${(result.duration_ms / 1000).toFixed(2)} s`;
  const stdout = result.stdout || "";
  const stderr = result.stderr || "";
  const noOutput = !stdout && !stderr;

  return `
    <div class="playground-result-summary ${completed ? "pass" : "fail"}">
      <span class="status-dot"></span>
      <strong>${statusLabel}</strong>
      <span>${escapeHtml(exitLabel)} · ${escapeHtml(duration)}</span>
    </div>
    ${
      stdout
        ? `<section class="console-stream"><span>stdout</span><pre>${escapeHtml(stdout)}</pre></section>`
        : ""
    }
    ${
      stderr
        ? `<section class="console-stream stderr"><span>stderr</span><pre>${escapeHtml(stderr)}</pre></section>`
        : ""
    }
    ${noOutput ? `<div class="playground-console-empty compact">Process completed without output.</div>` : ""}
  `;
}

function problemTable() {
  if (!state.problems.length) {
    return `<div class="empty-state">No problems match the current filters.</div>`;
  }

  const rows = state.problems
    .map(
      (problem) => `
      <tr data-slug="${escapeHtml(problem.slug)}">
        <td class="num-cell">${escapeHtml(problemDisplayId(problem))}</td>
        <td class="status-cell">${problemStatusBadge(problem)}</td>
        <td class="title-cell">${escapeHtml(problem.title)}</td>
        <td>${difficultyPill(problem.difficulty)}</td>
        <td class="category-cell">${escapeHtml(problem.category)}</td>
        <td>${companyLabelList(problem.companies) || `<span class="muted-cell">-</span>`}</td>
        <td class="frequency-cell">${problemFrequencyBadge(problem)}</td>
        <td>${labelList(problem.tags)}</td>
      </tr>
    `
    )
    .join("");

  return `
    <table>
      <thead>
        <tr>
          ${problemSortHeader("id", "#", "number")}
          ${problemSortHeader("completed", "Complete")}
          ${problemSortHeader("title", "Title")}
          ${problemSortHeader("difficulty", "Difficulty")}
          <th scope="col">Category</th>
          <th scope="col">Companies</th>
          ${problemSortHeader("frequency", "Stars")}
          <th scope="col">Tags</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function problemSortHeader(sortKey, label, accessibleLabel = label) {
  const active = state.filters.sort === sortKey;
  const order = active && state.filters.order === "desc" ? "desc" : "asc";
  const ariaSort = active ? (order === "desc" ? "descending" : "ascending") : "none";
  const nextOrder = active && order === "asc" ? "descending" : "ascending";
  const indicator = active ? (order === "asc" ? "↑" : "↓") : "↕";
  return `
    <th scope="col" aria-sort="${ariaSort}">
      <button
        class="problem-sort-button ${active ? "active" : ""}"
        type="button"
        data-problem-sort="${escapeHtml(sortKey)}"
        aria-label="Sort by ${escapeHtml(accessibleLabel)} ${nextOrder}"
      >
        <span>${escapeHtml(label)}</span>
        <span class="sort-indicator" aria-hidden="true">${indicator}</span>
      </button>
    </th>
  `;
}

function problemStatusBadge(problem) {
  const completed = problemCompleted(problem);
  return `
    <span
      class="completion-badge ${completed ? "completed" : "incomplete"}"
      aria-label="${completed ? "Completed" : "Not completed"}"
      title="${completed ? "Completed" : "Not completed"}"
    >${completed ? "✓" : ""}</span>
  `;
}

function renderDetail() {
  const problem = state.selected;
  const displayId = problemDisplayId(state.selected);
  const env = problem.environment || {};
  const runButtonState = state.running ? "disabled" : "";
  const runButtonContent = state.running
    ? `<span class="button-spinner" aria-hidden="true"></span><span>Running checks</span>`
    : "Run all tests";
  app.innerHTML = `
    <main class="page page-detail">
      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}
      <header class="problem-topbar">
        <div class="problem-navigation">
          <button class="ghost-button" id="problem-back-button">← Problems</button>
          ${mainNavigation()}
        </div>
        <div class="topbar-actions">
          ${renderProblemTimer(problem)}
          ${themeToggleButton()}
        </div>
      </header>
      <section class="detail-layout" ${paneLayoutStyle()}>
        <article class="detail-panel">
          <div class="panel-header">
            <div class="panel-title">
              <h2>${escapeHtml(problem.title)}</h2>
              <p>#${escapeHtml(displayId)} / ${escapeHtml(problem.category)} / ${escapeHtml(problem.difficulty)}</p>
            </div>
            <div class="tabs">
              ${tabButton("description", "Problem")}
              ${tabButton("tests", "Tests")}
              ${tabButton("environment", "Env")}
            </div>
          </div>
          <div class="problem-body">${renderProblemTab(problem, env)}</div>
        </article>

        <div
          class="pane-resizer problem-code-resizer"
          data-resize-handle="problem-code"
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize problem and editor panes"
          tabindex="0"
        ></div>

        <section class="editor-panel">
          <div class="panel-header">
            <div class="editor-actions">
              <button class="ghost-button" id="reset-code">Reset</button>
            </div>
            <button class="primary-button" id="run-tests" ${runButtonState} aria-busy="${state.running}">
              ${runButtonContent}
            </button>
          </div>
          <div class="code-pane">
            <div id="code-editor" class="code-editor ace-editor"></div>
            <textarea id="code-editor-fallback" class="code-editor fallback-editor" spellcheck="false">${escapeHtml(
              currentCode()
            )}</textarea>
          </div>
          <div
            class="pane-resizer code-results-resizer"
            data-resize-handle="code-results"
            role="separator"
            aria-orientation="horizontal"
            aria-label="Resize editor and results panes"
            tabindex="0"
          ></div>
          <div class="results">${renderResults()}</div>
        </section>
      </section>
    </main>
  `;
}

function tabButton(tab, label) {
  const active = state.activeTab === tab ? "active" : "";
  return `<button class="tab ${active}" data-tab="${tab}">${label}</button>`;
}

function renderProblemTab(problem, env) {
  if (state.activeTab === "tests") {
    return [renderProblemTests(problem.tests || []), renderCustomTests(problem)].join("");
  }

  if (state.activeTab === "environment") {
    return [renderProblemEnvironment(env), renderDataLinkSetup(problem)].join("");
  }

  return renderProblemDescription(problem);
}

function renderProblemBlock(sectionClass, title, body) {
  const content = String(body ?? "").trim();
  if (!content) return "";

  return `
    <section class="${sectionClass}">
      <h3 class="problem-section-title">${escapeHtml(title)}</h3>
      <div class="problem-section-body">${content}</div>
    </section>
  `;
}

function renderProblemDescription(problem) {
  return [
    renderProblemBlock(
      PROBLEM_SECTION_CLASSES.prompt,
      "Prompt",
      `<div class="problem-prompt">${markdownLite(problem.prompt)}</div>`
    ),
    renderProblemDataInfo(problem.data),
    renderProblemMetadata(problem),
    renderProblemExample(problem.example),
    renderReferences(problem.references),
  ].join("");
}

function renderProblemDataInfo(data) {
  if (!data?.path) return "";

  const rows = [
    ["Path", `<code>${escapeHtml(data.path)}</code>`],
    ["Contents", escapeHtml(data.format || "")],
    ["Note", markdownLite(data.note || "")],
    ["Setup", markdownLite(data.setup || "")],
    ["Runtime", markdownLite(data.runtime || "")],
  ]
    .filter(([, value]) => String(value ?? "").trim())
    .map((row) => `<div class="problem-meta-row"><div class="label">${row[0]}</div><div>${row[1]}</div></div>`)
    .join("");

  return renderProblemBlock(PROBLEM_SECTION_CLASSES.data, "Dataset", `<div class="problem-meta-grid">${rows}</div>`);
}

function renderProblemMetadata(problem) {
  const companies = companyLabelList(problem.companies, "company-list", problem.interview_frequency) || "None";
  const tags = labelList(problem.tags) || "None";
  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.metadata,
    "Metadata",
    `
      <div class="problem-meta-grid">
        <div class="problem-meta-row"><div class="label">Companies</div><div>${companies}</div></div>
        <div class="problem-meta-row"><div class="label">Tags</div><div>${tags}</div></div>
      </div>
    `
  );
}

function renderProblemExample(example) {
  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.example,
    "Example",
    `
      <div class="problem-example">
        <div class="problem-meta-row"><div class="label">Input</div><pre>${escapeHtml(example?.input || "")}</pre></div>
        <div class="problem-meta-row"><div class="label">Output</div><pre>${escapeHtml(example?.output || "")}</pre></div>
        <div class="problem-meta-row"><div class="label">Reasoning</div><div>${escapeHtml(example?.reasoning || "")}</div></div>
      </div>
    `
  );
}

function renderProblemTests(tests) {
  const cases = tests
    .map(
      (test, index) => `
        <div class="mini-block problem-test-case">
          <div class="test-case-heading">
            <strong>${escapeHtml(test.name || `Test ${index + 1}`)}</strong>
            <button
              class="ghost-button run-case-button"
              type="button"
              data-run-test-index="${index}"
              ${state.running ? "disabled" : ""}
            >
              Run
            </button>
          </div>
          <div class="test-detail-grid">
            <div>
              <span>Input</span>
              <pre>${escapeHtml(test.input || test.test)}</pre>
            </div>
            <div>
              <span>Call</span>
              <pre>${escapeHtml(test.test)}</pre>
            </div>
          </div>
          <hr />
          <span>Expected</span>
          <pre>${escapeHtml(test.expected_output)}</pre>
        </div>
      `
    )
    .join("");

  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.tests,
    "Visible Tests",
    `<div class="problem-test-list">${cases}</div>`
  );
}

function renderCustomTestMode(test, index, signature, mode) {
  if (!signature) return "";

  return `
    <label class="custom-test-mode-field">
      <span>Mode</span>
      <select class="field custom-test-field" data-custom-index="${index}" data-custom-field="mode">
        <option value="arguments" ${mode === "arguments" ? "selected" : ""}>Argument inputs</option>
        <option value="raw" ${mode === "raw" ? "selected" : ""}>Custom call</option>
      </select>
    </label>
  `;
}

function renderCustomTestArguments(test, index, signature) {
  if (!signature) return "";
  const values = test.arguments || {};
  const fields = signature.parameters
    .map(
      (parameter) => `
        <label>
          <span>${escapeHtml(parameter)}</span>
          <textarea
            class="field custom-test-field"
            rows="2"
            data-custom-index="${index}"
            data-custom-argument="${escapeHtml(parameter)}"
          >${escapeHtml(values[parameter] || "")}</textarea>
        </label>
      `
    )
    .join("");

  return `<div class="custom-test-arguments">${fields}</div>`;
}

function renderRawCustomTestFields(test, index) {
  return `
    <label>
      <span>Input</span>
      <textarea
        class="field custom-test-field"
        rows="2"
        data-custom-index="${index}"
        data-custom-field="input"
      >${escapeHtml(test.input || "")}</textarea>
    </label>
    <label>
      <span>Call</span>
      <textarea
        class="field custom-test-field"
        rows="4"
        data-custom-index="${index}"
        data-custom-field="test"
      >${escapeHtml(test.test || "")}</textarea>
    </label>
  `;
}

function renderCustomTests(problem) {
  if (!isMlCodingProblem(problem)) return "";

  const signature = customTestSignature(problem);
  const cases = state.customTests.length
    ? state.customTests
        .map((test, index) => {
          const mode = customTestMode(test, signature);
          const bodyFields =
            mode === "arguments" ? renderCustomTestArguments(test, index, signature) : renderRawCustomTestFields(test, index);
          return `
            <div class="mini-block problem-test-case custom-test-case" data-custom-test-index="${index}">
              <div class="test-case-heading">
                <strong>${escapeHtml(test.name || `Custom test ${index + 1}`)}</strong>
                <div class="custom-test-actions">
                  <button
                    class="ghost-button run-case-button"
                    type="button"
                    data-run-custom-test-index="${index}"
                    ${state.running ? "disabled" : ""}
                  >
                    Run
                  </button>
                  <button class="ghost-button remove-custom-test" type="button" data-remove-custom-test-index="${index}">
                    Remove
                  </button>
                </div>
              </div>
              <label>
                <span>Name</span>
                <input
                  class="field custom-test-field"
                  value="${escapeHtml(test.name || "")}"
                  data-custom-index="${index}"
                  data-custom-field="name"
                />
              </label>
              ${renderCustomTestMode(test, index, signature, mode)}
              ${bodyFields}
              <label>
                <span>Expected</span>
                <textarea
                  class="field custom-test-field"
                  rows="3"
                  data-custom-index="${index}"
                  data-custom-field="expected_output"
                >${escapeHtml(test.expected_output || "")}</textarea>
              </label>
            </div>
          `;
        })
        .join("")
    : `<div class="empty-state">No custom tests yet.</div>`;

  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.tests,
    "Custom Tests",
    `
      <div class="custom-test-editor">
        <div class="custom-test-toolbar">
          <button class="ghost-button" type="button" id="add-custom-test">Add case</button>
          <button class="ghost-button" type="button" id="save-custom-tests">Save</button>
          <button class="primary-button" type="button" id="run-custom-tests" ${state.running ? "disabled" : ""}>
            Run custom tests
          </button>
        </div>
        <div class="problem-test-list">${cases}</div>
      </div>
    `
  );
}

function renderProblemEnvironment(env) {
  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.environment,
    "Environment",
    `
      <div class="problem-meta-grid">
        <div class="problem-meta-row"><div class="label">Language</div><div>${escapeHtml(env.language || "python")}</div></div>
        <div class="problem-meta-row"><div class="label">Timeout</div><div>${escapeHtml(env.timeout_seconds || 2)} seconds per test</div></div>
        <div class="problem-meta-row"><div class="label">Comparator</div><div>${escapeHtml(env.comparator || "exact")}</div></div>
        <div class="problem-meta-row"><div class="label">Packages</div><div>${escapeHtml((env.packages || []).join(", ") || "standard library")}</div></div>
      </div>
    `
  );
}

function renderDataLinkSetup(problem) {
  if (!supportsDataLinkSetup(problem)) return "";

  const link = state.dataLink || {};
  const statusClass = link.exists && link.is_symlink ? "linked" : link.exists ? "blocked" : "missing";
  const statusText =
    link.exists && link.is_symlink ? "Linked" : link.exists ? "Path exists; not a symlink" : "Not linked";
  const target = state.dataLinkTarget || "";
  const removeDisabled = link.is_symlink ? "" : "disabled";

  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.environment,
    "Local Data",
    `
      <div class="data-link-panel">
        <div class="data-link-status ${statusClass}">
          <span>${escapeHtml(statusText)}</span>
          <code>${escapeHtml(link.link_path || problem.data?.path || "")}</code>
        </div>
        <label class="data-link-target">
          <span>Dataset folder</span>
          <input
            class="field"
            id="data-link-target"
            value="${escapeHtml(target)}"
            placeholder="/absolute/path/to/dataset"
          />
        </label>
        <div class="data-link-actions">
          <button class="primary-button" type="button" id="save-data-link">Link data</button>
          <button class="ghost-button" type="button" id="remove-data-link" ${removeDisabled}>Remove link</button>
        </div>
      </div>
    `
  );
}

function renderReferences(references) {
  if (!Array.isArray(references) || references.length === 0) return "";

  const links = references
    .filter((reference) => reference && reference.label && reference.url)
    .map(
      (reference) => `
        <a href="${escapeHtml(reference.url)}" target="_blank" rel="noopener noreferrer">
          ${escapeHtml(reference.label)}
        </a>
      `
    )
    .join("");

  if (!links) return "";
  return renderProblemBlock(
    PROBLEM_SECTION_CLASSES.references,
    "Background",
    `<div class="reference-list" aria-label="Background references">${links}</div>`
  );
}

function renderResults() {
  if (state.running) {
    return renderRunningResults();
  }

  if (!state.runResult) {
    return `<div class="empty-state">No run yet.</div>`;
  }

  const result = state.runResult;
  const results = result.results || [];
  const activeIndex = results.length ? clamp(Number(state.activeResultIndex) || 0, 0, results.length - 1) : 0;
  const tabs = results
    .map(
      (item, index) => `
        <button
          class="result-tab ${index === activeIndex ? "active" : ""} ${item.passed ? "pass" : "fail"}"
          type="button"
          role="tab"
          id="result-tab-${index}"
          aria-selected="${index === activeIndex}"
          aria-controls="result-case-${index}"
          data-result-index="${index}"
        >
          <span class="status-dot"></span>
          <span>${escapeHtml(item.name || `Case ${index + 1}`)}</span>
        </button>
      `
    )
    .join("");

  return `
    <div class="result-summary">
      <strong>${escapeHtml(result.status)}</strong>
      <span>${result.passed} / ${result.total} passed</span>
    </div>
    <div class="result-tabs" role="tablist" aria-label="Test cases">${tabs}</div>
    ${renderResultCase(results[activeIndex], activeIndex)}
  `;
}

function activeRunTargetLabel() {
  if (Number.isInteger(state.runningCustomTestIndex)) {
    const customTest = state.customTests[state.runningCustomTestIndex];
    const baseLabel = `Custom ${state.runningCustomTestIndex + 1}: ${customTest?.name || "local check"}`;
    return state.activeRunCheck ? `${state.activeRunCheck} · ${baseLabel}` : `${baseLabel} running locally`;
  }

  if (state.runningCustomTestIndex === "all") {
    const count = state.customTests.length;
    const baseLabel = count === 1 ? "1 custom check" : `${count} custom checks`;
    return state.activeRunCheck ? `${state.activeRunCheck} · ${baseLabel}` : `${baseLabel} running locally`;
  }

  const selectedTest = Number.isInteger(state.runningTestIndex)
    ? state.selected?.tests?.[state.runningTestIndex]
    : null;
  const testCount = selectedTest ? 1 : state.selected?.tests?.length || 0;
  const countLabel = testCount === 1 ? "1 visible check" : `${testCount} visible checks`;
  const baseLabel = selectedTest
    ? `Test ${state.runningTestIndex + 1}: ${selectedTest.name || "visible check"}`
    : countLabel;
  return state.activeRunCheck ? `${state.activeRunCheck} · ${baseLabel}` : `${baseLabel} running locally`;
}

function renderRunningResults() {
  const targetLabel = activeRunTargetLabel();
  return `
    <div class="running-results" aria-live="polite" aria-busy="true">
      <div class="running-status">
        <span class="run-spinner" aria-hidden="true"></span>
        <div>
          <strong>Running checks...</strong>
          <p><span id="run-elapsed">${state.runElapsedSeconds}s elapsed</span> · <span id="run-target">${escapeHtml(
            targetLabel
          )}</span></p>
        </div>
      </div>
      <section class="run-log-panel" aria-label="Runner log">
        <div class="run-log-header">
          <strong>Runner log</strong>
          <span>${state.runLogs.length} line${state.runLogs.length === 1 ? "" : "s"}</span>
        </div>
        <pre id="run-log-lines" class="run-log-lines">${renderRunLogLines()}</pre>
      </section>
    </div>
  `;
}

function renderRunLogLines() {
  if (!state.runLogs.length) return `<span class="run-log-empty">Waiting for runner output...</span>`;
  return state.runLogs
    .map(
      (entry) =>
        `<span class="run-log-line ${escapeHtml(entry.stream)}"><span class="run-log-stream">${escapeHtml(
          entry.stream
        )}</span>${escapeHtml(entry.text)}</span>`
    )
    .join("");
}

function renderResultCase(item, index) {
  if (!item) return "";
  const mismatch = item.assertion_mismatch;
  const hasSimpleMismatch =
    mismatch && typeof mismatch.actual === "string" && typeof mismatch.expected === "string";
  const expectedLabel = hasSimpleMismatch ? "Expected result" : "Expected";
  const actualLabel = hasSimpleMismatch ? "Actual result" : "Actual";
  const mismatchMessage = hasSimpleMismatch && mismatch.message ? `<p>${escapeHtml(mismatch.message)}</p>` : "";
  const traceback = hasSimpleMismatch
    ? `
      <details class="result-traceback">
        <summary>View assertion traceback</summary>
        <pre>${escapeHtml(item.actual_output)}</pre>
      </details>
    `
    : "";
  const expected = hasSimpleMismatch ? mismatch.expected : item.expected_output;
  const actual = hasSimpleMismatch ? mismatch.actual : item.actual_output;

  return `
    <div
      class="result-case ${item.passed ? "pass" : "fail"}"
      role="tabpanel"
      id="result-case-${index}"
      aria-labelledby="result-tab-${index}"
    >
      <h4><span class="status-dot"></span>${escapeHtml(item.name || "test")}</h4>
      <div class="mini-block result-input"><span>Input</span><pre>${escapeHtml(item.input || item.test || "")}</pre></div>
      ${hasSimpleMismatch ? `<div class="assertion-mismatch"><strong>Result mismatch</strong>${mismatchMessage}</div>` : ""}
      <div class="result-columns">
        <div class="mini-block"><span>${expectedLabel}</span><pre>${escapeHtml(expected)}</pre></div>
        <div class="mini-block"><span>${actualLabel}</span><pre>${escapeHtml(actual)}</pre></div>
      </div>
      ${traceback}
    </div>
  `;
}

function bindEvents() {
  document.querySelector("#random-problem")?.addEventListener("click", randomProblem);
  document.querySelector("#theme-toggle")?.addEventListener("click", toggleTheme);
  document.querySelectorAll("[data-app-view]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.appView === "playground") {
        openPlayground();
      } else if (button.dataset.appView === "companies") {
        loadCompanies();
      } else {
        backToList();
      }
    });
  });
  document.querySelector("#playground-run")?.addEventListener("click", () => runPlayground());
  document.querySelector("#playground-reset")?.addEventListener("click", resetPlayground);
  document.querySelector("#playground-session-name")?.addEventListener("input", (event) => {
    state.playgroundSessionName = event.target.value;
    updatePlaygroundSessionStatus(editorCode());
  });
  document.querySelector("#playground-session-name")?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    if (activePlaygroundSession()) {
      savePlaygroundSession();
    } else {
      savePlaygroundSessionAs();
    }
  });
  document.querySelector("#playground-session-save")?.addEventListener("click", savePlaygroundSession);
  document.querySelector("#playground-session-save-as")?.addEventListener("click", savePlaygroundSessionAs);
  document.querySelectorAll("[data-open-playground-session]").forEach((button) => {
    button.addEventListener("click", () => openPlaygroundSession(button.dataset.openPlaygroundSession));
  });
  document.querySelectorAll("[data-run-playground-session]").forEach((button) => {
    button.addEventListener("click", () => runPlayground(button.dataset.runPlaygroundSession));
  });
  document.querySelectorAll("[data-delete-playground-session]").forEach((button) => {
    button.addEventListener("click", () => deletePlaygroundSession(button.dataset.deletePlaygroundSession));
  });
  document.querySelector("#apply-filters")?.addEventListener("click", () => {
    state.filters.search = document.querySelector("#search").value.trim();
    state.filters.category = document.querySelector("#category").value;
    state.filters.difficulty = document.querySelector("#difficulty").value;
    state.filters.company = document.querySelector("#company").value;
    const selectedSort = document.querySelector("#sort").value;
    if (state.filters.sort !== selectedSort) state.filters.order = defaultProblemSortOrder(selectedSort);
    state.filters.sort = selectedSort;
    loadProblems();
  });
  document.querySelectorAll("[data-problem-sort]").forEach((button) => {
    button.addEventListener("click", () => setProblemSort(button.dataset.problemSort));
  });
  document.querySelector("#search")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") document.querySelector("#apply-filters").click();
  });
  document.querySelectorAll("tbody tr[data-slug]").forEach((row) => {
    row.addEventListener("click", () => loadProblem(row.dataset.slug));
  });
  document.querySelectorAll("[data-company-profile]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      loadCompany(button.dataset.companyProfile);
    });
  });
  document.querySelectorAll("[data-company-slug]").forEach((button) => {
    button.addEventListener("click", () => loadCompany(button.dataset.companySlug));
  });
  document.querySelectorAll("[data-company-problem]").forEach((button) => {
    button.addEventListener("click", () => loadProblem(button.dataset.companyProblem));
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      saveCode(editorCode());
      state.activeTab = tab.dataset.tab;
      render();
    });
  });
  document.querySelectorAll("[data-resize-handle]").forEach((handle) => {
    handle.addEventListener("pointerdown", startPaneResize);
    handle.addEventListener("keydown", handlePaneResizeKeydown);
  });
  document.querySelectorAll(".result-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      saveCode(editorCode());
      state.activeResultIndex = Number(tab.dataset.resultIndex) || 0;
      render();
    });
  });
  document.querySelector("#problem-back-button")?.addEventListener("click", backToList);
  document.querySelector("#company-back-button")?.addEventListener("click", backToCompanies);
  document.querySelector("#problem-timer-toggle")?.addEventListener("click", toggleProblemTimer);
  document.querySelector("#problem-timer-reset")?.addEventListener("click", resetProblemTimer);
  document.querySelector("#run-tests")?.addEventListener("click", () => runTests());
  document.querySelectorAll("[data-run-test-index]").forEach((button) => {
    button.addEventListener("click", () => runTests(Number(button.dataset.runTestIndex)));
  });
  document.querySelector("#add-custom-test")?.addEventListener("click", addCustomTest);
  document.querySelector("#save-custom-tests")?.addEventListener("click", saveCustomTests);
  document.querySelector("#run-custom-tests")?.addEventListener("click", () => runCustomTests());
  document.querySelectorAll("[data-run-custom-test-index]").forEach((button) => {
    button.addEventListener("click", () => runCustomTests(Number(button.dataset.runCustomTestIndex)));
  });
  document.querySelectorAll("[data-remove-custom-test-index]").forEach((button) => {
    button.addEventListener("click", () => removeCustomTest(Number(button.dataset.removeCustomTestIndex)));
  });
  document.querySelectorAll("[data-custom-index][data-custom-field], [data-custom-index][data-custom-argument]").forEach((field) => {
    field.addEventListener("input", collectCustomTestInputs);
    field.addEventListener("change", collectCustomTestInputs);
  });
  document.querySelector("#save-data-link")?.addEventListener("click", saveDataLink);
  document.querySelector("#remove-data-link")?.addEventListener("click", removeDataLink);
  document.querySelector("#data-link-target")?.addEventListener("input", (event) => {
    state.dataLinkTarget = event.target.value;
  });
  document.querySelector("#reset-code")?.addEventListener("click", resetCode);
  document.querySelector("#code-editor-fallback")?.addEventListener("input", (event) => saveCode(event.target.value));
}

function bootFromHash() {
  if (location.hash === "#/playground") {
    state.view = "playground";
    render();
    return;
  }
  const match = location.hash.match(/^#\/problems\/(.+)$/);
  if (match) {
    loadProblem(decodeURIComponent(match[1]));
    return;
  }
  if (location.hash === "#/companies") {
    loadCompanies();
    return;
  }
  const companyMatch = location.hash.match(/^#\/companies\/(.+)$/);
  if (companyMatch) {
    loadCompany(decodeURIComponent(companyMatch[1]));
  } else {
    loadProblems();
  }
}

window.addEventListener("hashchange", () => {
  if (codeEditor) saveCode(editorCode());
  if (location.hash === "#/playground") {
    if (state.view !== "playground" || state.selected) openPlayground();
    return;
  }
  const match = location.hash.match(/^#\/problems\/(.+)$/);
  if (match) {
    const slug = decodeURIComponent(match[1]);
    if (!state.selected || state.selected.slug !== slug) {
      loadProblem(slug);
    }
    return;
  }
  if (location.hash === "#/companies") {
    if (state.view !== "companies" || state.selectedCompany) {
      loadCompanies();
    }
    return;
  }
  const companyMatch = location.hash.match(/^#\/companies\/(.+)$/);
  if (companyMatch) {
    const slug = decodeURIComponent(companyMatch[1]);
    if (!state.selectedCompany || state.selectedCompany.slug !== slug) {
      loadCompany(slug);
    }
  } else if (!location.hash && (state.selected || state.selectedCompany || state.view === "playground")) {
    backToList();
  }
});

applyTheme();
bootFromHash();
