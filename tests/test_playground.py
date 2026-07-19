import unittest

from deepcode.playground import MAX_CODE_CHARS, run_playground


class PlaygroundRunnerTest(unittest.TestCase):
    def test_runs_python_and_captures_stdout(self):
        result = run_playground("values = [2, 3, 4]\nprint(sum(values))\n", timeout_seconds=2)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"], "9\n")
        self.assertEqual(result["stderr"], "")
        self.assertGreaterEqual(result["duration_ms"], 0)

    def test_reports_tracebacks_without_turning_them_into_api_errors(self):
        result = run_playground("raise RuntimeError('boom')\n", timeout_seconds=2)

        self.assertEqual(result["status"], "error")
        self.assertNotEqual(result["exit_code"], 0)
        self.assertIn("RuntimeError: boom", result["stderr"])

    def test_runs_with_the_project_pytorch_installation(self):
        result = run_playground(
            "import torch\nvalues = torch.tensor([2.0, 3.0, 4.0])\nprint(float(values.prod()))\n",
            timeout_seconds=10,
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stdout"], "24.0\n")
        self.assertEqual(result["stderr"], "")

    def test_times_out_and_stops_the_process(self):
        result = run_playground("while True:\n    pass\n", timeout_seconds=0.1)

        self.assertEqual(result["status"], "timed_out")
        self.assertIsNone(result["exit_code"])
        self.assertIn("timed out", result["stderr"])

    def test_rejects_empty_or_oversized_code(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            run_playground("  ")
        with self.assertRaisesRegex(ValueError, "at most"):
            run_playground("x" * (MAX_CODE_CHARS + 1))


if __name__ == "__main__":
    unittest.main()
