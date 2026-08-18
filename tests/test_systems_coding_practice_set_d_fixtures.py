import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "systems_coding_practice_set_d.py"
).read_text(encoding="utf-8")


class SystemsCodingPracticeSetDFixtureTest(unittest.TestCase):
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

    def test_connect_k_game_engine_reference_solution_passes(self):
        self._assert_reference_solution_passes("connect-k-game-engine")

    def test_keyed_box_collector_reference_solution_passes(self):
        self._assert_reference_solution_passes("keyed-box-collector")

    def test_reactive_sum_key_store_reference_solution_passes(self):
        self._assert_reference_solution_passes("reactive-sum-key-store")

    def test_timestamped_account_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("timestamped-account-ledger")

    def test_in_memory_relational_query_engine_reference_solution_passes(self):
        self._assert_reference_solution_passes("in-memory-relational-query-engine")


if __name__ == "__main__":
    unittest.main()
