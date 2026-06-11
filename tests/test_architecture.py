import unittest

from deepcode import server


class ArchitectureTest(unittest.TestCase):
    def test_backend_serves_frontend_directory(self):
        self.assertEqual(server.FRONTEND_DIR.name, "frontend")
        self.assertTrue((server.FRONTEND_DIR / "index.html").exists())
        self.assertTrue((server.FRONTEND_DIR / "app.js").exists())
        self.assertTrue((server.FRONTEND_DIR / "styles.css").exists())


if __name__ == "__main__":
    unittest.main()
