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

    def test_connect_k_accepts_assertion_based_input_validation(self):
        assertion_based = REFERENCE_SOLUTION.replace(
            "raise ValueError(", "raise AssertionError("
        )
        self._assert_reference_solution_passes("connect-k-game-engine", assertion_based)

    def test_connect_k_checks_reject_common_game_logic_errors(self):
        mutations = {
            "missing opposite diagonal": (
                "((1, 0), (0, 1), (1, 1), (1, -1))",
                "((1, 0), (0, 1), (1, 1))",
            ),
            "only counts one side of the last piece": (
                "for direction in (-1, 1):", "for direction in (1,):",
            ),
            "requires exactly K rather than at least K": (
                "if total >= self._k:", "if total == self._k:",
            ),
            "reports O wins as X wins": (
                "else GameStatus.PLAYER_O_WINS", "else GameStatus.PLAYER_X_WINS",
            ),
            "checks a full-board draw before a win": (
                "if self._wins_from(row, column, player):",
                "if sum(self._heights) < self._rows * self._columns and self._wins_from(row, column, player):",
            ),
            "consumes a turn on a full-column rejection": (
                'if row == self._rows:\n            raise ValueError("column is full")',
                'if row == self._rows:\n'
                '            self.current_player = Player.O if player is Player.X else Player.X\n'
                '            raise ValueError("column is full")',
            ),
        }
        for name, (before, after) in mutations.items():
            with self.subTest(name=name):
                self.assertIn(before, REFERENCE_SOLUTION)
                mutant = REFERENCE_SOLUTION.replace(before, after, 1)
                result = self._evaluate("connect-k-game-engine", mutant)
                self.assertEqual(result["status"], "failed", result)
                self.assertLess(result["passed"], result["total"], result)

    def test_keyed_box_collector_reference_solution_passes(self):
        self._assert_reference_solution_passes(
            "keyed-box-collector", KEYED_BOX_REFERENCE_SOLUTION
        )

    def test_box_checks_distinguish_possession_unlocking_and_collection(self):
        mutations = {
            "initial possession implies unlocked": (
                "possessed[box] = True", "possessed[box] = True; can_open[box] = True",
            ),
            "keys grant possession": (
                "can_open[target] = True", "can_open[target] = True; possessed[target] = True",
            ),
            "unlocked children still need a key": (
                "can_open = list(status)", "can_open = [False] * n",
            ),
            "processes an eligible box more than once": (
                " and not scheduled[box]", "",
            ),
        }
        for name, (before, after) in mutations.items():
            with self.subTest(name=name):
                self.assertIn(before, KEYED_BOX_REFERENCE_SOLUTION)
                mutant = KEYED_BOX_REFERENCE_SOLUTION.replace(before, after, 1)
                result = self._evaluate("keyed-box-collector", mutant)
                self.assertEqual(result["status"], "failed", result)

    def test_box_checks_allow_status_mutation(self):
        in_place = KEYED_BOX_REFERENCE_SOLUTION.replace(
            "can_open = list(status)", "can_open = status"
        )
        self._assert_reference_solution_passes("keyed-box-collector", in_place)

    def test_reactive_sum_key_store_reference_solution_passes(self):
        self._assert_reference_solution_passes("reactive-sum-key-store")

    def test_timestamped_account_ledger_reference_solution_passes(self):
        self._assert_reference_solution_passes("timestamped-account-ledger")

    def test_in_memory_relational_query_engine_reference_solution_passes(self):
        self._assert_reference_solution_passes("in-memory-relational-query-engine")


if __name__ == "__main__":
    unittest.main()
