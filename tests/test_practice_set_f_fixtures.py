import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "practice_set_f.py"
).read_text(encoding="utf-8")


class PracticeSetFFixtureTest(unittest.TestCase):
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

    def test_decimal_exact_fill_min_items_reference_solution_passes(self):
        self._assert_reference_solution_passes("decimal-exact-fill-min-items")

    def test_cyclic_linked_list_intersection_reference_solution_passes(self):
        self._assert_reference_solution_passes("cyclic-linked-list-intersection")

    def test_query_parameter_decoder_reference_solution_passes(self):
        self._assert_reference_solution_passes("query-parameter-decoder")

    def test_minimum_cost_bundle_cover_reference_solution_passes(self):
        self._assert_reference_solution_passes("minimum-cost-bundle-cover")


if __name__ == "__main__":
    unittest.main()
