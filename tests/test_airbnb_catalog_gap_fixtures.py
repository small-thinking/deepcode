import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "airbnb_catalog_gaps.py"
).read_text(encoding="utf-8")


class AirbnbCatalogGapFixtureTest(unittest.TestCase):
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

    def test_nested_array_list_iterator_reference_solution_passes(self):
        self._assert_reference_solution_passes("nested-array-list-iterator")

    def test_account_contact_components_reference_solution_passes(self):
        self._assert_reference_solution_passes("account-contact-components")

    def test_exact_target_purchase_plan_reference_solution_passes(self):
        self._assert_reference_solution_passes("exact-target-purchase-plan")


if __name__ == "__main__":
    unittest.main()
