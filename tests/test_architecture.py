import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

from deepcode import server
from deepcode.problem_store import ProblemStore


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
        problem = ProblemStore(ROOT / "problems").get_problem("batched-llm-inference-service")
        asset = (
            ROOT
            / "problems"
            / "141-batched-llm-inference-service"
            / "assets"
            / "batched-llm-inference-architecture.png"
        )
        prefix_cache_asset = (
            ROOT
            / "problems"
            / "141-batched-llm-inference-service"
            / "assets"
            / "batched-llm-inference-prefix-cache-architecture.png"
        )

        self.assertEqual(
            server.resolve_problem_asset(
                "/problem-assets/batched-llm-inference-service/assets/batched-llm-inference-architecture.png",
                ROOT / "problems",
            ),
            asset.resolve(),
        )
        self.assertEqual(
            server.resolve_problem_asset(
                "/problem-assets/batched-llm-inference-service/assets/batched-llm-inference-prefix-cache-architecture.png",
                ROOT / "problems",
            ),
            prefix_cache_asset.resolve(),
        )
        self.assertEqual(problem["category"], "ML System Design")
        self.assertEqual(problem["evaluation"]["type"], "system_design")
        self.assertEqual(len(problem["assets"]), 2)
        self.assertIn("TTFT", problem["response"]["reference_answer"])
        self.assertIn("cross-request prefix", problem["response"]["reference_answer"].lower())
        self.assertIsNone(server.resolve_problem_asset("/problem-assets/batched-llm-inference-service/../secret.png", ROOT / "problems"))
        self.assertIsNone(server.resolve_problem_asset("/problem-assets/batched-llm-inference-service/problem.json", ROOT / "problems"))

    def test_problem_demos_are_declared_and_scoped_to_the_owning_problem(self):
        demo = (
            ROOT
            / "problems"
            / "348-cover-photo-conversion-evaluation"
            / "assets"
            / "cover-photo-decision-loop.html"
        )

        self.assertEqual(
            server.resolve_problem_demo(
                "/problem-demos/cover-photo-conversion-evaluation/assets/cover-photo-decision-loop.html",
                ROOT / "problems",
            ),
            demo.resolve(),
        )
        self.assertIsNone(
            server.resolve_problem_demo(
                "/problem-demos/cover-photo-conversion-evaluation/assets/../problem.json",
                ROOT / "problems",
            )
        )
        self.assertIsNone(
            server.resolve_problem_demo(
                "/problem-demos/cover-photo-conversion-evaluation/assets/not-declared.html",
                ROOT / "problems",
            )
        )
        self.assertIsNone(
            server.resolve_problem_demo(
                "/problem-demos/batched-llm-inference-service/assets/cover-photo-decision-loop.html",
                ROOT / "problems",
            )
        )

    def test_problem_demo_response_uses_html_content_type_and_restrictive_headers(self):
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.DeepCodeHandler)
        thread = Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            url = (
                f"http://127.0.0.1:{httpd.server_port}"
                "/problem-demos/cover-photo-conversion-evaluation/assets/cover-photo-decision-loop.html"
            )
            with urlopen(url, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "text/html")
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertEqual(response.headers["Content-Security-Policy"], server.PROBLEM_DEMO_CSP)
                self.assertEqual(response.headers["Cross-Origin-Resource-Policy"], "same-origin")
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                demo_path = ROOT / "problems/348-cover-photo-conversion-evaluation/assets/cover-photo-decision-loop.html"
                self.assertEqual(response.read(), demo_path.read_bytes())
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
