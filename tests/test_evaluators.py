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
            get_evaluator("ml_modeling")


if __name__ == "__main__":
    unittest.main()
