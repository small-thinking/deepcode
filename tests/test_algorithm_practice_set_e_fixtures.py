import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_e.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetEFixtureTest(unittest.TestCase):
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

    def test_multi_target_shortest_distances_reference_solution_passes(self):
        self._assert_reference_solution_passes("multi-target-shortest-distances")

    def test_directed_forest_validator_reference_solution_passes(self):
        self._assert_reference_solution_passes("directed-forest-validator")

    def test_prefix_sum_subarray_toolkit_reference_solution_passes(self):
        self._assert_reference_solution_passes("prefix-sum-subarray-toolkit")

    def test_minimum_command_racecar_reference_solution_passes(self):
        self._assert_reference_solution_passes("minimum-command-racecar")

    def test_quadratic_transform_sorted_array_reference_solution_passes(self):
        self._assert_reference_solution_passes("quadratic-transform-sorted-array")


if __name__ == "__main__":
    unittest.main()
