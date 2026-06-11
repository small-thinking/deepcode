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


if __name__ == "__main__":
    unittest.main()
