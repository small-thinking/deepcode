import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "systems_coding_practice_set_e.py"
).read_text(encoding="utf-8")


class SystemsCodingPracticeSetEFixtureTest(unittest.TestCase):
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

    def test_spreadsheet_formula_engines_reference_solution_passes(self):
        self._assert_reference_solution_passes("spreadsheet-formula-engines")

    def test_blocking_db_connection_pool_reference_solution_passes(self):
        self._assert_reference_solution_passes("blocking-db-connection-pool")


if __name__ == "__main__":
    unittest.main()
