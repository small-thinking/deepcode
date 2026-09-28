import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "systems_coding_practice_set_d.py"
).read_text(encoding="utf-8")
KEYED_BOX_REFERENCE_SOLUTION = (
    ROOT / "problems" / "218-keyed-box-collector" / "solution.py"
).read_text(encoding="utf-8")


class SystemsCodingPracticeSetDFixtureTest(unittest.TestCase):
    def _evaluate(self, slug, code):
        problem = ProblemStore(ROOT / "problems").get_problem(slug)
        return evaluate_submission(
            EvaluationRequest(
                code=code,
                problem=problem,
                tests=problem["tests"],
                environment=problem["environment"],
                runtime=problem.get("_runtime", {}),
            )
        )

    def _assert_reference_solution_passes(self, slug, code=REFERENCE_SOLUTION):
        result = self._evaluate(slug, code)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], result["total"])

    def test_connect_k_game_engine_reference_solution_passes(self):
        self._assert_reference_solution_passes("connect-k-game-engine")

    def test_keyed_box_collector_reference_solution_passes(self):
        self._assert_reference_solution_passes(
            "keyed-box-collector", KEYED_BOX_REFERENCE_SOLUTION
        )

    def test_keyed_box_collector_rejects_mutant_that_ignores_open_status(self):
        mutant = KEYED_BOX_REFERENCE_SOLUTION.replace(
            "unlocked.update(box.id for box in boxes if box.is_open)",
            "pass  # mutant ignores intrinsic open status",
        )
        self.assertNotEqual(mutant, KEYED_BOX_REFERENCE_SOLUTION)

        result = self._evaluate("keyed-box-collector", mutant)
        self.assertEqual(result["status"], "failed", result)
        failed_names = [case["name"] for case in result["results"] if not case["passed"]]
        self.assertEqual(
            failed_names,
            ["opens an intrinsically open child after discovery without a key"],
            result,
        )

    def test_reactive_sum_key_store_reference_solution_passes(self):
        self._assert_reference_solution_passes("reactive-sum-key-store")

    def test_timestamped_account_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("timestamped-account-ledger")

    def test_in_memory_relational_query_engine_reference_solution_passes(self):
        self._assert_reference_solution_passes("in-memory-relational-query-engine")


if __name__ == "__main__":
    unittest.main()
