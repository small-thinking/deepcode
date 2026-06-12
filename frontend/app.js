const THEME_KEY = "deepcode-theme";

const state = {
  problems: [],
  categories: [],
  difficulties: [],
  filters: {
    search: "",
    category: "all",
    difficulty: "all",
    sort: "id",
  },
  selected: null,
  activeTab: "description",
  activeResultIndex: 0,
  runResult: null,
  error: null,
  loading: true,
  running: false,
  theme: initialTheme(),
  layout: {
    problemRatio: 0.46,
    resultsRatio: 0.32,
  },
};

const app = document.querySelector("#app");
let codeEditor = null;
let activePaneResize = null;

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

function markdownLite(value) {
  const escaped = escapeHtml(value);
  return escaped
    .replace(/^### (.*)$/gm, "<h4>$1</h4>")
    .replace(/^## (.*)$/gm, "<h3>$1</h3>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");
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

async function loadProblems() {
  state.loading = true;
  state.error = null;
  render();
  try {
    const query = paramsFromFilters();
    const payload = await api(`/api/problems${query ? `?${query}` : ""}`);
    state.problems = payload.problems;
    state.categories = payload.categories;
    state.difficulties = payload.difficulties;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

async function loadProblem(identifier) {
  state.error = null;
  state.runResult = null;
  state.activeResultIndex = 0;
  state.loading = true;
  render();
  try {
    const payload = await api(`/api/problems/${encodeURIComponent(identifier)}`);
    state.selected = payload.problem;
    state.activeTab = "description";
    const key = codeKey(state.selected.slug);
    if (!localStorage.getItem(key)) {
      localStorage.setItem(key, state.selected.starter_code || "");
    }
    location.hash = `#/problems/${state.selected.slug}`;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loading = false;
    render();
  }
}

function codeKey(slug) {
  return `deepcode-code:${slug}`;
}

function currentCode() {
  return state.selected ? localStorage.getItem(codeKey(state.selected.slug)) ?? state.selected.starter_code ?? "" : "";
}

function editorCode() {
  if (codeEditor) return codeEditor.getValue();
  return document.querySelector("#code-editor-fallback")?.value ?? currentCode();
}

function saveCode(value) {
  if (!state.selected) return;
  localStorage.setItem(codeKey(state.selected.slug), value);
}

function teardownEditor() {
  if (!codeEditor) return;
  codeEditor.destroy();
  codeEditor = null;
}

function mountEditor() {
  if (!state.selected) {
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
  codeEditor.setValue(currentCode(), -1);
  codeEditor.session.on("change", () => saveCode(codeEditor.getValue()));
  codeEditor.commands.addCommand({
    name: "runTests",
    bindKey: { win: "Ctrl-Enter", mac: "Command-Enter" },
    exec: runTests,
  });
}

async function runTests() {
  if (!state.selected) return;
  const code = editorCode();
  saveCode(code);
  state.running = true;
  state.runResult = null;
  state.activeResultIndex = 0;
  state.error = null;
  render();
  try {
    state.runResult = await api(`/api/problems/${encodeURIComponent(state.selected.slug)}/run`, {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  } catch (error) {
    state.error = error.message;
  } finally {
    state.running = false;
    render();
  }
}

function resetCode() {
  if (!state.selected) return;
  localStorage.setItem(codeKey(state.selected.slug), state.selected.starter_code || "");
  state.runResult = null;
  state.activeResultIndex = 0;
  render();
}

function randomProblem() {
  if (!state.problems.length) return;
  const index = Math.floor(Math.random() * state.problems.length);
  loadProblem(state.problems[index].slug);
}

function backToList() {
  state.selected = null;
  state.runResult = null;
  state.activeResultIndex = 0;
  state.error = null;
  location.hash = "";
  render();
}

function difficultyPill(difficulty) {
  return `<span class="pill ${escapeHtml(difficulty)}">${escapeHtml(difficulty)}</span>`;
}

function render() {
  teardownEditor();
  if (state.selected) {
    renderDetail();
  } else {
    renderList();
  }
  bindEvents();
  mountEditor();
  applyPaneSizes();
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
          <button class="ghost-button" id="random-problem">Random</button>
          ${themeToggleButton()}
        </div>
      </header>

      <section class="stat-grid" aria-label="Collection status">
        <div class="stat-card"><strong>${state.problems.length}</strong><span>Visible problems</span></div>
        <div class="stat-card"><strong>${state.categories.length}</strong><span>Categories</span></div>
        <div class="stat-card"><strong>Py</strong><span>Local runner</span></div>
      </section>

      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}

      <section class="filters">
        <div class="filter-row">
          <input class="field" id="search" value="${escapeHtml(state.filters.search)}" placeholder="Search problems..." />
          <select class="field" id="category">${categoryOptions}</select>
          <select class="field" id="difficulty">${difficultyOptions}</select>
          <select class="field" id="sort">
            <option value="id" ${state.filters.sort === "id" ? "selected" : ""}>Sort by ID</option>
            <option value="title" ${state.filters.sort === "title" ? "selected" : ""}>Sort by Title</option>
            <option value="difficulty" ${state.filters.sort === "difficulty" ? "selected" : ""}>Sort by Difficulty</option>
            <option value="category" ${state.filters.sort === "category" ? "selected" : ""}>Sort by Category</option>
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

function problemTable() {
  if (!state.problems.length) {
    return `<div class="empty-state">No problems match the current filters.</div>`;
  }

  const rows = state.problems
    .map(
      (problem) => `
      <tr data-slug="${escapeHtml(problem.slug)}">
        <td class="num-cell">${escapeHtml(problem.id)}</td>
        <td class="title-cell">${escapeHtml(problem.title)}</td>
        <td>${difficultyPill(problem.difficulty)}</td>
        <td class="category-cell">${escapeHtml(problem.category)}</td>
        <td>${(problem.tags || []).map((tag) => `<span class="label">${escapeHtml(tag)}</span>`).join(", ")}</td>
      </tr>
    `
    )
    .join("");

  return `
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Title</th>
          <th>Difficulty</th>
          <th>Category</th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderDetail() {
  const problem = state.selected;
  const env = problem.environment || {};
  app.innerHTML = `
    <main class="page">
      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}
      <header class="problem-topbar">
        <button class="ghost-button" id="problem-back-button">← Problems</button>
        ${themeToggleButton()}
      </header>
      <section class="detail-layout" ${paneLayoutStyle()}>
        <article class="detail-panel">
          <div class="panel-header">
            <div class="panel-title">
              <h2>${escapeHtml(problem.title)}</h2>
              <p>#${escapeHtml(problem.id)} / ${escapeHtml(problem.category)} / ${escapeHtml(problem.difficulty)}</p>
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
            <button class="primary-button" id="run-tests" ${state.running ? "disabled" : ""}>
              ${state.running ? "Running..." : "Run tests"}
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
    return `
      <div class="test-list">
        ${(problem.tests || [])
          .map(
            (test, index) => `
          <div class="mini-block">
            <span>${escapeHtml(test.name || `Test ${index + 1}`)}</span>
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
          .join("")}
      </div>
    `;
  }

  if (state.activeTab === "environment") {
    return `
      <div class="env-grid">
        <div class="env-row"><div class="label">Language</div><div>${escapeHtml(env.language || "python")}</div></div>
        <div class="env-row"><div class="label">Timeout</div><div>${escapeHtml(env.timeout_seconds || 2)} seconds per test</div></div>
        <div class="env-row"><div class="label">Comparator</div><div>${escapeHtml(env.comparator || "exact")}</div></div>
        <div class="env-row"><div class="label">Packages</div><div>${escapeHtml((env.packages || []).join(", ") || "standard library")}</div></div>
      </div>
    `;
  }

  return `
    <p>${markdownLite(problem.prompt)}</p>
    <div class="example-box">
      <div class="example-row"><div class="label">Input</div><pre>${escapeHtml(problem.example?.input || "")}</pre></div>
      <div class="example-row"><div class="label">Output</div><pre>${escapeHtml(problem.example?.output || "")}</pre></div>
      <div class="example-row"><div class="label">Reasoning</div><div>${escapeHtml(problem.example?.reasoning || "")}</div></div>
    </div>
  `;
}

function renderResults() {
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

function renderResultCase(item, index) {
  if (!item) return "";

  return `
    <div
      class="result-case ${item.passed ? "pass" : "fail"}"
      role="tabpanel"
      id="result-case-${index}"
      aria-labelledby="result-tab-${index}"
    >
      <h4><span class="status-dot"></span>${escapeHtml(item.name || "test")}</h4>
      <div class="mini-block result-input"><span>Input</span><pre>${escapeHtml(item.input || item.test || "")}</pre></div>
      <div class="result-columns">
        <div class="mini-block"><span>Expected</span><pre>${escapeHtml(item.expected_output)}</pre></div>
        <div class="mini-block"><span>Actual</span><pre>${escapeHtml(item.actual_output)}</pre></div>
      </div>
    </div>
  `;
}

function bindEvents() {
  document.querySelector("#random-problem")?.addEventListener("click", randomProblem);
  document.querySelector("#theme-toggle")?.addEventListener("click", toggleTheme);
  document.querySelector("#apply-filters")?.addEventListener("click", () => {
    state.filters.search = document.querySelector("#search").value.trim();
    state.filters.category = document.querySelector("#category").value;
    state.filters.difficulty = document.querySelector("#difficulty").value;
    state.filters.sort = document.querySelector("#sort").value;
    loadProblems();
  });
  document.querySelector("#search")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") document.querySelector("#apply-filters").click();
  });
  document.querySelectorAll("tbody tr[data-slug]").forEach((row) => {
    row.addEventListener("click", () => loadProblem(row.dataset.slug));
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
  document.querySelector("#run-tests")?.addEventListener("click", runTests);
  document.querySelector("#reset-code")?.addEventListener("click", resetCode);
  document.querySelector("#code-editor-fallback")?.addEventListener("input", (event) => saveCode(event.target.value));
}

function bootFromHash() {
  const match = location.hash.match(/^#\/problems\/(.+)$/);
  if (match) {
    loadProblem(decodeURIComponent(match[1]));
  } else {
    loadProblems();
  }
}

window.addEventListener("hashchange", () => {
  const match = location.hash.match(/^#\/problems\/(.+)$/);
  if (match) {
    const slug = decodeURIComponent(match[1]);
    if (!state.selected || state.selected.slug !== slug) {
      loadProblem(slug);
    }
  } else if (!location.hash && state.selected) {
    backToList();
  }
});

applyTheme();
bootFromHash();
