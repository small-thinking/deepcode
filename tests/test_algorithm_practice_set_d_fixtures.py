import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_d.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetDFixtureTest(unittest.TestCase):
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

    def test_minimal_infix_expression_serializer_reference_solution_passes(self):
        self._assert_reference_solution_passes("minimal-infix-expression-serializer")

    def test_blocked_board_knight_distance_reference_solution_passes(self):
        self._assert_reference_solution_passes("blocked-board-knight-distance")

    def test_persistent_axis_coverage_reference_solution_passes(self):
        self._assert_reference_solution_passes("persistent-axis-coverage")

    def test_minimax_two_column_layout_reference_solution_passes(self):
        self._assert_reference_solution_passes("minimax-two-column-layout")

    def test_sparse_monochrome_square_components_reference_solution_passes(self):
        self._assert_reference_solution_passes("sparse-monochrome-square-components")


if __name__ == "__main__":
    unittest.main()
