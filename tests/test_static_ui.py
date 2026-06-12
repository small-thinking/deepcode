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

    def test_problem_references_render_as_background_links(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("renderReferences", app_js)
        self.assertIn('class="reference-list"', app_js)
        self.assertIn('target="_blank"', app_js)
        self.assertIn('rel="noopener noreferrer"', app_js)
        self.assertIn(".reference-list", styles_css)

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

    def test_run_tests_normalizes_indentation_before_submit(self):
        app_js = Path("frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("function normalizePythonIndentation", app_js)
        self.assertIn("const code = normalizePythonIndentation(editorCode())", app_js)
        self.assertIn("setEditorCode(code)", app_js)

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

    def test_ui_uses_codex_like_system_fonts(self):
        styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")

        self.assertIn("font-family: ui-sans-serif", styles_css)
        self.assertIn("font-family: ui-monospace", styles_css)
        self.assertNotIn("font-family: Inter,", styles_css)


if __name__ == "__main__":
    unittest.main()
