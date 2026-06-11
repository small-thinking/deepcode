import unittest
from pathlib import Path


class StaticUiTest(unittest.TestCase):
    def test_problem_detail_topbar_only_contains_navigation(self):
        app_js = Path("static/app.js").read_text(encoding="utf-8")
        styles_css = Path("static/styles.css").read_text(encoding="utf-8")

        self.assertIn('id="problem-back-button"', app_js)
        self.assertNotIn("problem-topbar-title", app_js)
        self.assertNotIn("problem-topbar-title", styles_css)


if __name__ == "__main__":
    unittest.main()
