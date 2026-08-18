import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "stateful_practice_set_b.py"
).read_text(encoding="utf-8")


class StatefulPracticeSetBFixtureTest(unittest.TestCase):
    def _assert_reference_solution_passes(self, slug):
        problem = ProblemStore(ROOT / "problems").get_problem(slug)
        result = evaluate_submission(
            EvaluationRequest(
                code=REFERENCE_SOLUTION,
                problem=problem,
                tests=problem["tests"],
                environment=problem["environment"],
                runtime=problem.get("_runtime", {}),
            )
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_billing_status_replay_reference_solution_passes(self):
        self._assert_reference_solution_passes("billing-status-replay")

    def test_tennis_match_scoring_reference_solution_passes(self):
        self._assert_reference_solution_passes("tennis-match-scoring")

    def test_concurrent_bill_status_tracker_reference_solution_passes(self):
        self._assert_reference_solution_passes("concurrent-bill-status-tracker")


if __name__ == "__main__":
    unittest.main()
