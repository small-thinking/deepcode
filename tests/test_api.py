import json
import tempfile
import unittest
from pathlib import Path

from deepcode.api import ApiContext, handle_api_request, stream_api_events
from deepcode.problem_store import ProblemStore
from deepcode.user_state import UserStateStore


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

    def test_lists_problems_with_local_personal_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")
            user_state.mark_completed("toy")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "GET",
                "/api/problems",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["problems"][0]["personal_status"]["completed"], True)

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

    def test_runs_selected_visible_test_for_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                tests=[
                    {"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"},
                    {"name": "harder", "input": "x = 5", "test": "print(identity(5))", "expected_output": "5"},
                ],
            )
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 4\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(payload["total"], 1)
            self.assertEqual([result["name"] for result in payload["results"]], ["basic"])

    def test_rejects_out_of_range_selected_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(Path(tmp), "toy", "1")
            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n", "test_index": 3}).encode("utf-8"),
            )

            self.assertEqual(status, 400)
            self.assertIn("test_index", payload["error"])

    def test_passing_submission_marks_problem_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return x\n"}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["problem_status"]["completed"], True)
            self.assertEqual(user_state.status_for("toy")["completed"], True)

    def test_passing_selected_test_does_not_mark_problem_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(
                Path(tmp) / "problems",
                "toy",
                "1",
                tests=[
                    {"name": "basic", "input": "x = 4", "test": "print(identity(4))", "expected_output": "4"},
                    {"name": "harder", "input": "x = 5", "test": "print(identity(5))", "expected_output": "5"},
                ],
            )

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/run",
                {},
                json.dumps({"code": "def identity(x):\n    return 4\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertNotIn("problem_status", payload)
            self.assertEqual(user_state.status_for("toy")["completed"], False)

    def test_reset_submission_status_marks_problem_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp) / "problems")
            user_state = UserStateStore(Path(tmp) / ".deepcode" / "user-state.json")
            self._write_problem(Path(tmp) / "problems", "toy", "1")
            user_state.mark_completed("toy")

            status, payload = handle_api_request(
                ApiContext(store=store, user_state=user_state),
                "POST",
                "/api/problems/toy/reset",
                {},
                None,
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["problem_status"], {"completed": False, "completed_at": None})
            self.assertEqual(user_state.status_for("toy")["completed"], False)

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

    def test_selected_visible_check_for_lab_problem_skips_hidden_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = ProblemStore(root)
            self._write_problem(
                root,
                "lab",
                "200",
                problem_overrides={
                    "evaluation": {"type": "ml_torch_lab", "harness": "harness.py"},
                    "environment": {"language": "python", "timeout_seconds": 10, "packages": ["torch"]},
                },
                tests=[{"name": "visible contract", "test": "assert callable(train)\nprint('visible ok')"}],
            )
            (root / "lab" / "harness.py").write_text(
                "raise AssertionError('hidden lab harness should not run')",
                encoding="utf-8",
            )

            status, payload = handle_api_request(
                ApiContext(store=store),
                "POST",
                "/api/problems/lab/run",
                {},
                json.dumps({"code": "def train():\n    return None\n", "test_index": 0}).encode("utf-8"),
            )

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["total"], 1)
            self.assertEqual(payload["results"][0]["name"], "visible contract")

    def test_streams_submission_logs_for_modeling_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProblemStore(Path(tmp))
            self._write_problem(
                Path(tmp),
                "toy",
                "1",
                problem_overrides={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "training", "test": "train()\nprint('done')\n"}],
            )
            events = list(
                stream_api_events(
                    ApiContext(store=store),
                    "POST",
                    "/api/problems/toy/run/stream",
                    {},
                    json.dumps({"code": "def train():\n    print('epoch 1 loss=0.25')\n"}).encode("utf-8"),
                )
            )

            log_events = [event for event in events if event["type"] == "log"]
            self.assertEqual(events[0], {"type": "run_started", "total": 1})
            self.assertEqual(log_events[0]["text"], "epoch 1 loss=0.25\n")
            self.assertEqual(events[-1]["type"], "run_finished")
            self.assertEqual(events[-1]["result"]["status"], "passed")

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
        problem_dir.mkdir(parents=True)
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
