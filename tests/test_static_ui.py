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


if __name__ == "__main__":
    unittest.main()
