import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "practice_set_g.py"
).read_text(encoding="utf-8")


class PracticeSetGFixtureTest(unittest.TestCase):
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

    def test_minimum_capacity_subset_reference_solution_passes(self):
        self._assert_reference_solution_passes("minimum-capacity-subset")

    def test_digit_permutation_lower_bound_reference_solution_passes(self):
        self._assert_reference_solution_passes("digit-permutation-lower-bound")

    def test_multi_article_line_formatter_reference_solution_passes(self):
        self._assert_reference_solution_passes("multi-article-line-formatter")


if __name__ == "__main__":
    unittest.main()
