import unittest
from pathlib import Path


class StaticUiTest(unittest.TestCase):
    def test_problem_detail_topbar_only_contains_navigation(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn('id="problem-back-button"', app_js)
        self.assertNotIn("problem-topbar-title", app_js)
        self.assertNotIn("problem-topbar-title", styles_css)

    def test_theme_toggle_is_available_on_list_and_detail_pages(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn('id="theme-toggle"', app_js)
        self.assertIn("data-theme", app_js)
        self.assertIn("body[data-theme=\"light\"]", styles_css)

    def test_theme_palette_uses_soft_neutral_surfaces(self):
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("--bg: #17191f;", styles_css)
        self.assertIn("--panel: #20232b;", styles_css)
        self.assertIn("--code-bg: #1e2128;", styles_css)
        self.assertIn("--bg: #eef1f5;", styles_css)
        self.assertIn("--panel: #f7f8fb;", styles_css)
        self.assertIn("--code-bg: #f1f3f7;", styles_css)
        self.assertNotIn("--bg: #050505;", styles_css)
        self.assertNotIn("--panel: #ffffff;", styles_css)

    def test_problem_references_render_as_background_links(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("renderReferences", app_js)
        self.assertIn('class="reference-list"', app_js)
        self.assertIn('target="_blank"', app_js)
        self.assertIn('rel="noopener noreferrer"', app_js)
        self.assertIn(".reference-list", styles_css)

    def test_problem_company_metadata_renders_in_list_and_detail(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("<th>Companies</th>", app_js)
        self.assertIn("problem.companies", app_js)
        self.assertIn("function renderProblemMetadata", app_js)
        self.assertIn('metadata: "problem-section problem-metadata-section"', app_js)
        self.assertIn(".company-list", styles_css)

    def test_problem_workspace_has_resizable_pane_hooks(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn('data-resize-handle="problem-code"', app_js)
        self.assertIn('data-resize-handle="code-results"', app_js)
        self.assertIn('role="separator"', app_js)
        self.assertIn('aria-orientation="vertical"', app_js)
        self.assertIn('aria-orientation="horizontal"', app_js)
        self.assertIn("startPaneResize", app_js)
        self.assertIn(".pane-resizer", styles_css)
        self.assertIn("--problem-pane-width", styles_css)
        self.assertIn("--results-pane-height", styles_css)

    def test_run_results_render_cases_as_tabs(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("activeResultIndex", app_js)
        self.assertIn("renderResultCase", app_js)
        self.assertIn('class="result-tabs"', app_js)
        self.assertIn('role="tablist"', app_js)
        self.assertIn("data-result-index", app_js)
        self.assertIn("aria-selected", app_js)
        self.assertIn(".result-tab", styles_css)
        self.assertIn(".result-case", styles_css)

    def test_running_checks_show_progress_feedback(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("runStartedAt", app_js)
        self.assertIn("runElapsedSeconds", app_js)
        self.assertIn("startRunTimer", app_js)
        self.assertIn("stopRunTimer", app_js)
        self.assertIn("renderRunningResults", app_js)
        self.assertIn('aria-live="polite"', app_js)
        self.assertIn("Running checks", app_js)
        self.assertIn(".running-results", styles_css)
        self.assertIn(".run-spinner", styles_css)
        self.assertIn("@keyframes spin", styles_css)

    def test_running_checks_can_show_live_runner_logs(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("runLogs", app_js)
        self.assertIn("/run/stream", app_js)
        self.assertIn("ReadableStream", app_js)
        self.assertIn("renderRunLogLines", app_js)
        self.assertIn("Runner log", app_js)
        self.assertIn(".run-log-panel", styles_css)
        self.assertIn(".run-log-line", styles_css)

    def test_run_tests_normalizes_indentation_before_submit(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("function normalizePythonIndentation", app_js)
        self.assertIn("const code = normalizePythonIndentation(editorCode())", app_js)
        self.assertIn("setEditorCode(code)", app_js)

    def test_visible_tests_can_run_individually(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("async function runTests(testIndex = null)", app_js)
        self.assertIn("Number.isInteger(testIndex)", app_js)
        self.assertIn("payload.test_index = testIndex", app_js)
        self.assertIn('data-run-test-index="${index}"', app_js)
        self.assertIn("runTests(Number(button.dataset.runTestIndex))", app_js)
        self.assertIn("Run all tests", app_js)
        self.assertIn(".test-case-heading", styles_css)
        self.assertIn(".run-case-button", styles_css)

    def test_ml_coding_custom_tests_can_be_edited_and_run(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("customTests", app_js)
        self.assertIn("function customTestSignature", app_js)
        self.assertIn("function defaultCustomTest", app_js)
        self.assertIn("function loadCustomTests", app_js)
        self.assertIn("function saveCustomTests", app_js)
        self.assertIn("function renderCustomTests", app_js)
        self.assertIn("function runCustomTests", app_js)
        self.assertIn("/custom-tests", app_js)
        self.assertIn("Argument inputs", app_js)
        self.assertIn("Custom call", app_js)
        self.assertIn("data-custom-argument", app_js)
        self.assertIn("pendingCustomTestScrollIndex", app_js)
        self.assertIn("function scrollPendingCustomTestIntoView", app_js)
        self.assertIn("data-custom-test-index", app_js)
        self.assertIn('closest(".problem-body")', app_js)
        self.assertIn("scroller.scrollTop", app_js)
        self.assertIn('data-custom-field="test"', app_js)
        self.assertIn('data-run-custom-test-index="${index}"', app_js)
        self.assertIn("custom_only", app_js)
        self.assertIn(".custom-test-editor", styles_css)
        self.assertIn(".custom-test-actions", styles_css)
        self.assertIn(".custom-test-arguments", styles_css)

    def test_modeling_data_link_setup_can_be_rendered_and_saved(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("dataLink", app_js)
        self.assertIn("function supportsDataLinkSetup", app_js)
        self.assertIn("function loadDataLink", app_js)
        self.assertIn("function saveDataLink", app_js)
        self.assertIn("function removeDataLink", app_js)
        self.assertIn("function renderDataLinkSetup", app_js)
        self.assertIn("/data-link", app_js)
        self.assertIn('id="data-link-target"', app_js)
        self.assertIn('id="save-data-link"', app_js)
        self.assertIn('id="remove-data-link"', app_js)
        self.assertIn(".data-link-panel", styles_css)
        self.assertIn(".data-link-status", styles_css)

    def test_dataset_instructions_render_separately_from_prompt(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("function renderProblemDataInfo", app_js)
        self.assertIn("renderProblemDataInfo(problem.data)", app_js)
        self.assertIn('"Dataset"', app_js)
        self.assertIn("data.note", app_js)
        self.assertNotIn("resolved local data directory", app_js)

    def test_starter_code_cache_refreshes_for_unedited_templates(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("function syncStarterCode", app_js)
        self.assertIn("function shouldRefreshStoredCode", app_js)
        self.assertIn("function isLegacyNGramStarterDraft", app_js)
        self.assertIn("deepcode-starter:", app_js)
        self.assertIn('!normalized.includes("DEEPCODE_DATA_PATH/tiny_shakespeare.txt")', app_js)
        self.assertIn("hasPreviousBlankGenerateStarter", app_js)
        self.assertIn("hasPreviousInitializedStarter", app_js)

    def test_problem_numbers_use_dynamic_display_ids(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("function problemDisplayId", app_js)
        self.assertIn("${escapeHtml(problemDisplayId(problem))}", app_js)
        self.assertIn("const displayId = problemDisplayId(state.selected)", app_js)

    def test_returning_from_direct_detail_load_refreshes_problem_catalog(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        back_to_list = app_js.split("function backToList() {", maxsplit=1)[1].split(
            "\n}\n\nfunction difficultyPill", maxsplit=1
        )[0]

        self.assertIn("const needsProblemCatalog = state.problems.length === 0;", back_to_list)
        self.assertIn("if (needsProblemCatalog)", back_to_list)
        self.assertIn("loadProblems();", back_to_list)
        self.assertIn("return;", back_to_list)

    def test_problem_prompt_renders_structured_copy(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn('class="problem-prompt"', app_js)
        self.assertNotIn("<p>${markdownLite(problem.prompt)}</p>", app_js)
        self.assertIn('line.startsWith("- ")', app_js)
        self.assertIn(".problem-prompt ul", styles_css)

    def test_problem_detail_uses_shared_display_blocks(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("function renderProblemBlock", app_js)
        self.assertIn("function renderProblemDescription", app_js)
        self.assertIn('prompt: "problem-section problem-prompt-section"', app_js)
        self.assertIn('example: "problem-section problem-example-section"', app_js)
        self.assertIn('references: "problem-section problem-references-section"', app_js)
        self.assertIn('tests: "problem-section problem-tests-section"', app_js)
        self.assertIn('environment: "problem-section problem-environment-section"', app_js)
        self.assertIn('class="${sectionClass}"', app_js)
        self.assertIn(".problem-section", styles_css)
        self.assertIn(".problem-section-title", styles_css)
        self.assertIn(".problem-example", styles_css)
        self.assertIn(".problem-test-case", styles_css)
        self.assertIn(".problem-meta-grid", styles_css)

    def test_detail_workspace_uses_responsive_full_width_layout(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn('<main class="page page-detail">', app_js)
        self.assertIn("--page-gutter", styles_css)
        self.assertIn("--page-max-width", styles_css)
        self.assertIn("width: calc(100% - var(--page-gutter) - var(--page-gutter))", styles_css)
        self.assertIn("max-width: var(--page-max-width)", styles_css)
        self.assertIn(".page-detail", styles_css)
        self.assertIn("max-width: none", styles_css)

    def test_problem_list_renders_local_completion_status(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("function problemCompleted", app_js)
        self.assertIn("function problemStatusBadge", app_js)
        self.assertIn("personal_status", app_js)
        self.assertIn("<th>Status</th>", app_js)
        self.assertIn('class="status-cell"', app_js)
        self.assertIn("✓", app_js)
        self.assertIn(".completion-badge", styles_css)
        self.assertIn(".completion-badge.completed", styles_css)
        self.assertIn(".status-cell", styles_css)

    def test_reset_code_clears_local_completion_status(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")

        reset_code = app_js.split("async function resetCode() {", maxsplit=1)[1].split(
            "\n}\n\nfunction problemCompleted", maxsplit=1
        )[0]

        self.assertIn("/reset", reset_code)
        self.assertIn('method: "POST"', reset_code)
        self.assertIn("syncProblemStatus", reset_code)

    def test_ui_uses_codex_like_system_fonts(self):
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("font-family: ui-sans-serif", styles_css)
        self.assertIn("font-family: ui-monospace", styles_css)
        self.assertNotIn("font-family: Inter,", styles_css)


if __name__ == "__main__":
    unittest.main()
