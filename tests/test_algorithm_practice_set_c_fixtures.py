import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_c.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetCFixtureTest(unittest.TestCase):
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

    def test_physical_maze_route_discovery_reference_solution_passes(self):
        self._assert_reference_solution_passes("physical-maze-route-discovery")

    def test_connected_quota_grid_generator_reference_solution_passes(self):
        self._assert_reference_solution_passes("connected-quota-grid-generator")

    def test_target_expression_builder_reference_solution_passes(self):
        self._assert_reference_solution_passes("target-expression-builder")

    def test_nearby_almost_duplicate_reference_solution_passes(self):
        self._assert_reference_solution_passes("nearby-almost-duplicate")

    def test_nested_suffix_repeat_decoder_reference_solution_passes(self):
        self._assert_reference_solution_passes("nested-suffix-repeat-decoder")


if __name__ == "__main__":
    unittest.main()
