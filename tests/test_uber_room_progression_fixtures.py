import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUG = "uber-room-progression-topk-leaderboard"


class UberRoomProgressionFixtureTest(unittest.TestCase):
    def test_reference_solution_passes_every_visible_case(self):
        store = ProblemStore(ROOT / "problems")
        problem = store.get_problem(SLUG)
        problem_dir = next((ROOT / "problems").glob(f"*-{SLUG}"))
        result = evaluate_submission(
            EvaluationRequest(
                code=(problem_dir / "solution.py").read_text(encoding="utf-8"),
                problem=problem,
                tests=problem["tests"],
                environment=problem["environment"],
                runtime=problem.get("_runtime", {}),
            )
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
