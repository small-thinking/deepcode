import unittest

from deepcode.evaluators import EvaluationRequest, UnsupportedEvaluatorError, evaluate_submission, get_evaluator


class EvaluatorRegistryTest(unittest.TestCase):
    def test_dispatches_ml_coding_evaluator(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def add_one(x):\n    return x + 1\n",
                problem={"evaluation": {"type": "ml_coding"}},
                tests=[{"name": "basic", "test": "print(add_one(4))", "expected_output": "5"}],
                environment={"timeout_seconds": 2, "comparator": "exact"},
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 1)

    def test_rejects_unknown_evaluator(self):
        with self.assertRaises(UnsupportedEvaluatorError):
            get_evaluator("not_registered")

    def test_dispatches_ml_modeling_assertion_checks(self):
        self.assertEqual(get_evaluator("ml_modeling").name, "ml_modeling")

        result = evaluate_submission(
            EvaluationRequest(
                code="def square(x):\n    return x * x\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[
                    {
                        "name": "square behavior",
                        "input": "x = 4",
                        "test": "assert square(4) == 16\nprint('ok')",
                    }
                ],
                environment={"timeout_seconds": 2},
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["results"][0]["expected_output"], "All assertions pass")
        self.assertEqual(result["results"][0]["actual_output"], "ok")

    def test_ml_modeling_reports_assertion_failures_without_stopping(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def square(x):\n    return x + 1\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[
                    {"name": "fails", "test": "assert square(4) == 16"},
                    {"name": "passes", "test": "assert square(0) == 1"},
                ],
                environment={"timeout_seconds": 2},
            )
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["passed"], 1)
        self.assertFalse(result["results"][0]["passed"])
        self.assertIn("AssertionError", result["results"][0]["actual_output"])
        self.assertTrue(result["results"][1]["passed"])

    def test_ml_modeling_times_out_cleanly(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def wait_forever():\n    while True:\n        pass\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[{"name": "timeout", "test": "wait_forever()"}],
                environment={"timeout_seconds": 1},
            )
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("Timed out", result["results"][0]["actual_output"])

    def test_ml_modeling_exposes_runtime_paths_to_checks(self):
        result = evaluate_submission(
            EvaluationRequest(
                code="def noop():\n    return None\n",
                problem={"evaluation": {"type": "ml_modeling"}},
                tests=[
                    {
                        "name": "runtime paths",
                        "test": (
                            "import os\n"
                            "assert os.environ['DEEPCODE_PROBLEM_DIR'].endswith('/problem')\n"
                            "assert os.environ['DEEPCODE_DATA_PATH'].endswith('/problem/data')\n"
                            "assert os.environ['DEEPCODE_RESULTS_PATH'].endswith('/problem/eval-results')\n"
                            "noop()\n"
                        ),
                    }
                ],
                environment={"timeout_seconds": 2},
                runtime={
                    "problem_dir": "/tmp/problem",
                    "data_path": "/tmp/problem/data",
                    "results_path": "/tmp/problem/eval-results",
                },
            )
        )

        self.assertEqual(result["status"], "passed")


if __name__ == "__main__":
    unittest.main()
