import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_f.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetFFixtureTest(unittest.TestCase):
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

    def test_split_stay_listing_pairs_reference_solution_passes(self):
        self._assert_reference_solution_passes("split-stay-listing-pairs")

    def test_terrain_water_drop_rendering_reference_solution_passes(self):
        self._assert_reference_solution_passes("terrain-water-drop-rendering")

    def test_first_seen_record_deduper_reference_solution_passes(self):
        self._assert_reference_solution_passes("first-seen-record-deduper")

    def test_crown_region_board_score_reference_solution_passes(self):
        self._assert_reference_solution_passes("crown-region-board-score")


if __name__ == "__main__":
    unittest.main()
