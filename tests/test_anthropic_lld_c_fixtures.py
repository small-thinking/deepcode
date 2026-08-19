import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "anthropic_lld_c.py"
).read_text(encoding="utf-8")


class AnthropicLldCFixtureTest(unittest.TestCase):
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

    def test_object_storage_namespace_reference_solution_passes(self):
        self._assert_reference_solution_passes("object-storage-namespace")

    def test_typed_resource_registry_reference_solution_passes(self):
        self._assert_reference_solution_passes("typed-resource-registry")

    def test_matrix_kernel_tiling_cost_reference_solution_passes(self):
        self._assert_reference_solution_passes("matrix-kernel-tiling-cost")

    def test_versioned_get_when_database_reference_solution_passes(self):
        self._assert_reference_solution_passes("versioned-get-when-database")


if __name__ == "__main__":
    unittest.main()
