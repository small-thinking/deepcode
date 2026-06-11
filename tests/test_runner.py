import unittest

from deepcode.runner import run_submission


class RunnerTest(unittest.TestCase):
    def test_runs_each_test_case_and_reports_passes(self):
        result = run_submission(
            code="def dot_product(a, b):\n    return sum(x * y for x, y in zip(a, b))\n",
            tests=[
                {
                    "name": "small vectors",
                    "input": "a = [1, 2], b = [3, 4]",
                    "test": "print(dot_product([1, 2], [3, 4]))",
                    "expected_output": "11",
                },
                {"name": "zeros", "test": "print(dot_product([0, 2], [99, 5]))", "expected_output": "10"},
            ],
            timeout_seconds=2,
            comparator="exact",
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 2)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["results"][0]["input"], "a = [1, 2], b = [3, 4]")
        self.assertTrue(all(test["passed"] for test in result["results"]))

    def test_normalizes_numeric_outputs_with_small_float_differences(self):
        result = run_submission(
            code="def predict_mean(values):\n    return sum(values) / len(values)\n",
            tests=[
                {
                    "name": "float display",
                    "test": "print(predict_mean([1, 2, 4]))",
                    "expected_output": "2.3333333334",
                }
            ],
            timeout_seconds=2,
            comparator="numeric",
        )

        self.assertEqual(result["status"], "passed")

    def test_reports_wrong_answer_without_stopping_later_tests(self):
        result = run_submission(
            code="def always_zero(x):\n    return 0\n",
            tests=[
                {"name": "wrong", "test": "print(always_zero(2))", "expected_output": "2"},
                {"name": "right", "test": "print(always_zero(0))", "expected_output": "0"},
            ],
            timeout_seconds=2,
            comparator="exact",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["results"][0]["actual_output"], "0")
        self.assertFalse(result["results"][0]["passed"])
        self.assertTrue(result["results"][1]["passed"])

    def test_times_out_cleanly(self):
        result = run_submission(
            code="def wait_forever():\n    while True:\n        pass\n",
            tests=[{"name": "timeout", "test": "print(wait_forever())", "expected_output": "None"}],
            timeout_seconds=1,
            comparator="exact",
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("Timed out", result["results"][0]["actual_output"])


if __name__ == "__main__":
    unittest.main()
