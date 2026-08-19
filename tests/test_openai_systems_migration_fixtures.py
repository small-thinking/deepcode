import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "openai_systems_migration.py"
).read_text(encoding="utf-8")


class OpenAISystemsMigrationFixtureTest(unittest.TestCase):
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

    def test_event_time_gpu_credit_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("event-time-gpu-credit-ledger")

    def test_ipv4_cidr_iterator_reference_solution_passes(self):
        self._assert_reference_solution_passes("ipv4-cidr-iterator")

    def test_sticky_failure_credit_accounts_reference_solution_passes(self):
        self._assert_reference_solution_passes("sticky-failure-credit-accounts")

    def test_dependency_topology_analyzer_reference_solution_passes(self):
        self._assert_reference_solution_passes("dependency-topology-analyzer")


if __name__ == "__main__":
    unittest.main()
