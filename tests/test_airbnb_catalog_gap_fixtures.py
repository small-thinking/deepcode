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

    def test_nested_array_list_iterator_keeps_the_executable_contract_visible(self):
        problem = ProblemStore(ROOT / "problems").get_problem("nested-array-list-iterator")

        self.assertTrue(problem["prompt"].startswith("Implement `class NestedArrayListIterator`"))
        self.assertIn("One successful `next()` makes exactly one `remove()` available", problem["prompt"])
        self.assertIn("class NestedArrayListIterator", problem["starter_code"])
        self.assertEqual(len(problem["tests"]), 5)
        self.assertEqual(
            [test["input"] for test in problem["tests"]],
            [
                "rows = [[], [1, 2, 3], [4, 5], [], [], [6], [7, 8], [], [9], [10], []]",
                "rows = [[1, 2], [3], [4, 5, 6], []]",
                "rows = [[7], [], [], [8, 9], [10, 11], [], [12]]",
                "rows = [[], [], [], [1]]",
                "rows = [[15, 16], [17], [18], [19, 20]]",
            ],
        )

    def test_account_contact_components_reference_solution_passes(self):
        self._assert_reference_solution_passes("account-contact-components")

    def test_exact_target_purchase_plan_reference_solution_passes(self):
        self._assert_reference_solution_passes("exact-target-purchase-plan")


if __name__ == "__main__":
    unittest.main()
