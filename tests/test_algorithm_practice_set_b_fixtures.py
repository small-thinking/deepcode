import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_b.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetBFixtureTest(unittest.TestCase):
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

    def test_tennis_game_score_reference_solution_passes(self):
        self._assert_reference_solution_passes("tennis-game-score")

    def test_odd_even_linked_list_reference_solution_passes(self):
        self._assert_reference_solution_passes("odd-even-linked-list")

    def test_shortest_palindrome_prefix_reference_solution_passes(self):
        self._assert_reference_solution_passes("shortest-palindrome-prefix")


if __name__ == "__main__":
    unittest.main()
