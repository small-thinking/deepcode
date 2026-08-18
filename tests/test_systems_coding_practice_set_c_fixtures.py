import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "systems_coding_practice_set_c.py"
).read_text(encoding="utf-8")


class SystemsCodingPracticeSetCFixtureTest(unittest.TestCase):
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

    def test_trie_prefix_search_reference_solution_passes(self):
        self._assert_reference_solution_passes("trie-prefix-search")

    def test_battleship_state_machine_reference_solution_passes(self):
        self._assert_reference_solution_passes("battleship-state-machine")

    def test_two_signal_interval_sweeper_reference_solution_passes(self):
        self._assert_reference_solution_passes("two-signal-interval-sweeper")

    def test_schema_aware_csv_ingestion_reference_solution_passes(self):
        self._assert_reference_solution_passes("schema-aware-csv-ingestion")


if __name__ == "__main__":
    unittest.main()
