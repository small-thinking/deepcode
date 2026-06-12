import unittest
from pathlib import Path

from deepcode import server


class ArchitectureTest(unittest.TestCase):
    def test_backend_serves_frontend_directory(self):
        self.assertEqual(server.FRONTEND_DIR.name, "frontend")
        self.assertTrue((server.FRONTEND_DIR / "index.html").exists())
        self.assertTrue((server.FRONTEND_DIR / "app.js").exists())
        self.assertTrue((server.FRONTEND_DIR / "styles.css").exists())

    def test_static_assets_are_served_without_browser_caching(self):
        server_source = Path(server.__file__).read_text(encoding="utf-8")
        static_handler = server_source.split("def _handle_static", maxsplit=1)[1].split(
            "\n\ndef run", maxsplit=1
        )[0]

        self.assertIn('self.send_header("Cache-Control", "no-store")', static_handler)


if __name__ == "__main__":
    unittest.main()
