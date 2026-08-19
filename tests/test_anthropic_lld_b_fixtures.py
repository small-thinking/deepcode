import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "anthropic_lld_b.py"
).read_text(encoding="utf-8")


class AnthropicLldBFixtureTest(unittest.TestCase):
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

    def test_basic_bank_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("basic-bank-ledger")

    def test_versioned_record_database_reference_solution_passes(self):
        self._assert_reference_solution_passes("versioned-record-database")

    def test_manual_lru_cache_reference_solution_passes(self):
        self._assert_reference_solution_passes("manual-lru-cache")

    def test_database_backup_catalog_reference_solution_passes(self):
        self._assert_reference_solution_passes("database-backup-catalog")


if __name__ == "__main__":
    unittest.main()
