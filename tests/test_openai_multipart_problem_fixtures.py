import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "openai_multipart.py"
).read_text(encoding="utf-8")


class OpenAIMultipartProblemFixtureTest(unittest.TestCase):
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

    def test_infection_spread_basic_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-simulation")

    def test_infection_spread_immunity_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-static-immunity")

    def test_infection_spread_recovery_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-recovery")

    def test_infection_spread_pending_death_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-pending-death")

    def test_infection_spread_transition_death_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-transition-death")

    def test_infection_spread_optimal_burn_reference_solution_passes(self):
        self._assert_reference_solution_passes("infection-spread-optimal-burn")

    def test_session_tracker_reference_solution_passes(self):
        self._assert_reference_solution_passes("session-tracker")

    def test_gpu_credit_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("gpu-credit-ledger-ii")

    def test_durable_kv_store_reference_solution_passes(self):
        self._assert_reference_solution_passes("durable-in-memory-kv-store")

    def test_sharded_matmul_reference_solution_passes(self):
        self._assert_reference_solution_passes("sharded-matrix-multiplication")

    def test_versioned_social_graph_reference_solution_passes(self):
        self._assert_reference_solution_passes("versioned-social-graph")


if __name__ == "__main__":
    unittest.main()
