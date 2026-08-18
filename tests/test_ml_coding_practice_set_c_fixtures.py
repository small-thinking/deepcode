import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "ml_coding_practice_set_c.py"
).read_text(encoding="utf-8")


class MLCodingPracticeSetCFixtureTest(unittest.TestCase):
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

    def test_numpy_kmeans_clustering_reference_solution_passes(self):
        self._assert_reference_solution_passes("numpy-kmeans-clustering")

    def test_matrix_framework_debugging_reference_solution_passes(self):
        self._assert_reference_solution_passes("matrix-framework-debugging")

    def test_clipped_max_pooling_locations_reference_solution_passes(self):
        self._assert_reference_solution_passes("clipped-max-pooling-locations")


if __name__ == "__main__":
    unittest.main()
