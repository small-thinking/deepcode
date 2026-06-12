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
            self.assertNotIn("_runtime", payload["problem"])

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

    def test_returns_501_for_unregistered_evaluator(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "not_registered"}},
                tests=[],
            )
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "print('training placeholder')\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 501)
            self.assertIn("Unsupported evaluator", payload["error"])

    def test_runs_ml_modeling_submission_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "identity behavior", "test": "assert identity(4) == 4\nprint('ok')"}],
            )
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["results"][0]["actual_output"], "ok")

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

    def _write_problem(self, root, folder, problem_id, problem_overrides=None, tests=None):
        problem_dir = root / folder
        problem_dir.mkdir()
        problem = {
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
        if problem_overrides:
            problem.update(problem_overrides)
        (problem_dir / "problem.json").write_text(
            json.dumps(problem),
            encoding="utf-8",
        )
        (problem_dir / "tests.json").write_text(
            json.dumps(
                tests
                if tests is not None
                else [{"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"}]
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
