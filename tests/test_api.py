import json
import tempfile
import unittest
from pathlib import Path

from deepcode.api import ApiContext, handle_api_request
from deepcode.problem_store import ProblemStore


class ApiTest(unittest.TestCase):
    def test_lists_problems_with_facets(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(
                ApiContext(store=store),
                "GET",
                "/api/problems",
                {"category": ["Machine Learning"]},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["problems"][0]["slug"], "toy")
            self.assertEqual(payload["categories"], ["Machine Learning"])
            self.assertEqual(payload["difficulties"], ["easy"])

    def test_fetches_problem_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(ApiContext(store=store), "GET", "/api/problems/toy", {}, None)

            self.assertEqual(status, 200)
            self.assertEqual(payload["problem"]["starter_code"], "def identity(x):\n    pass\n")
            self.assertEqual(payload["problem"]["tests"][0]["input"], "x = 4")
            self.assertEqual(payload["problem"]["tests"][0]["expected_output"], "4")

    def test_runs_submission_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["passed"], 1)

    def test_returns_404_for_unknown_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            status, payload = handle_api_request(
                ApiContext(store=ProblemStore(Path(tmp))),
                "GET",
                "/api/problems/missing",
                {},
                None,
            )

            self.assertEqual(status, 404)
            self.assertEqual(payload["error"], "Problem not found")

    def _write_problem(self, root, folder, problem_id):
        problem_dir = root / folder
        problem_dir.mkdir()
        (problem_dir / "problem.json").write_text(
            json.dumps(
                {
                    "id": problem_id,
                    "slug": folder,
                    "title": "Toy Identity",
                    "category": "Machine Learning",
                    "difficulty": "easy",
                    "tags": ["toy"],
                    "prompt": "Return the input.",
                    "starter_code": "def identity(x):\n    pass\n",
                    "example": {"input": "x = 4", "output": "4", "reasoning": "Identity returns the same value."},
                    "environment": {
                        "language": "python",
                        "timeout_seconds": 2,
                        "packages": [],
                        "comparator": "exact",
                    },
                }
            ),
            encoding="utf-8",
        )
        (problem_dir / "tests.json").write_text(
            json.dumps([{"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"}]),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
