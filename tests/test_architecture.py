import unittest
from pathlib import Path

from deepcode import server


ROOT = Path(__file__).resolve().parents[1]


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

    def test_default_port_avoids_common_8000_conflicts(self):
        server_source = Path(server.__file__).read_text(encoding="utf-8")

        self.assertEqual(server.DEFAULT_PORT, 8848)
        self.assertIn("def run(host: str = \"127.0.0.1\", port: int = DEFAULT_PORT)", server_source)
        self.assertIn('parser.add_argument("--port", default=DEFAULT_PORT, type=int)', server_source)

    def test_problem_assets_are_scoped_to_the_owning_problem_assets_directory(self):
        asset = ROOT / "problems" / "141-real-time-milestone-counter" / "assets" / "milestone-counter-architecture.svg"

        self.assertEqual(
            server.resolve_problem_asset(
                "/problem-assets/real-time-milestone-counter/assets/milestone-counter-architecture.svg",
                ROOT / "problems",
            ),
            asset.resolve(),
        )
        self.assertIsNone(server.resolve_problem_asset("/problem-assets/real-time-milestone-counter/../secret.png", ROOT / "problems"))
        self.assertIsNone(server.resolve_problem_asset("/problem-assets/real-time-milestone-counter/problem.json", ROOT / "problems"))


if __name__ == "__main__":
    unittest.main()
