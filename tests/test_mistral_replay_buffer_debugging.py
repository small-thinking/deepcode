import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (
    ROOT / "tests" / "reference_solutions" / "mistral_replay_buffer_debugging.py"
).read_text(encoding="utf-8")


class MistralReplayBufferDebuggingFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem = ProblemStore(ROOT / "problems").get_problem(
            "replay-buffer-debugging"
        )

    def evaluate(self, code):
        return evaluate_submission(
            EvaluationRequest(
                code=code,
                problem=self.problem,
                tests=self.problem["tests"],
                environment=self.problem["environment"],
                runtime=self.problem.get("_runtime", {}),
            )
        )

    def test_reference_solution_passes_all_contract_cases(self):
        result = self.evaluate(REFERENCE)

        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(self.problem["tests"]))

    def test_buggy_starter_does_not_already_pass(self):
        result = self.evaluate(self.problem["starter_code"])

        self.assertNotEqual(result["status"], "passed", result)
        self.assertLess(result["passed"], len(self.problem["tests"]))

    def test_source_metadata_and_local_scope_are_explicit(self):
        self.assertEqual(self.problem["companies"], ["Mistral AI"])
        self.assertEqual(
            self.problem["interview_frequency"]["Mistral AI"],
            {
                "source_record_ids": ["35c6ce51456d8141b414e6ed51f79326"],
                "stars": 1,
                "synced_at": "2026-09-15",
            },
        )
        self.assertIn("equal batch lengths", self.problem["prompt"].lower())
        self.assertIn("nonempty buffer for sampling", self.problem["prompt"])
        urls = {reference["url"] for reference in self.problem["references"]}
        self.assertIn(
            "https://app.notion.com/p/35c6ce51456d8141b414e6ed51f79326", urls
        )
        self.assertIn(
            "https://www.1point3acres.com/bbs/thread-1144453-1-1.html", urls
        )


if __name__ == "__main__":
    unittest.main()
