import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "anthropic_lld_a.py"
).read_text(encoding="utf-8")


class AnthropicLldAFixtureTest(unittest.TestCase):
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

    def test_transfer_accept_account_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("transfer-accept-account-ledger")

    def test_snapshot_task_manager_reference_solution_passes(self):
        self._assert_reference_solution_passes("snapshot-task-manager")

    def test_employee_grant_manager_reference_solution_passes(self):
        self._assert_reference_solution_passes("employee-grant-manager")

    def test_ml_configuration_registry_reference_solution_passes(self):
        self._assert_reference_solution_passes("ml-configuration-registry")


if __name__ == "__main__":
    unittest.main()
