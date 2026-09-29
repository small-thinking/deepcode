import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "algorithm_practice_set_f.py"
).read_text(encoding="utf-8")


class AlgorithmPracticeSetFFixtureTest(unittest.TestCase):
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

    def _assert_reference_solution_passes(self, slug):
        problem = ProblemStore(ROOT / "problems").get_problem(slug)
        result = self._evaluate(slug, REFERENCE_SOLUTION)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_split_stay_listing_pairs_reference_solution_passes(self):
        self._assert_reference_solution_passes("split-stay-listing-pairs")

    def test_split_pair_checks_reject_common_coverage_errors(self):
        mutations = {
            "only checks alphabetical travel order": (
                "if first_then_second or second_then_first:",
                "if first_then_second:",
            ),
            "skips the earliest split boundary": (
                "max(start_day, suffix_start[", "max(start_day + 1, suffix_start[",
            ),
            "skips the latest split boundary": (
                "end_day - 1, prefix_end[", "end_day - 2, prefix_end[",
            ),
            "returns pairs in dictionary order": (
                "names = sorted(listings)", "names = list(listings)",
            ),
            "allows the same listing twice": (
                "names[first_index + 1 :]", "names[first_index :]",
            ),
            "sorts input lists in place": (
                "names = sorted(listings)",
                "for days in listings.values():\n"
                "        if isinstance(days, list):\n"
                "            days.sort()\n"
                "    names = sorted(listings)",
            ),
        }
        for name, (before, after) in mutations.items():
            with self.subTest(name=name):
                self.assertIn(before, REFERENCE_SOLUTION)
                mutant = REFERENCE_SOLUTION.replace(before, after)
                result = self._evaluate("split-stay-listing-pairs", mutant)
                self.assertEqual(result["status"], "failed", result)
                self.assertLess(result["passed"], result["total"], result)

    def test_terrain_water_drop_rendering_reference_solution_passes(self):
        self._assert_reference_solution_passes("terrain-water-drop-rendering")

    def test_first_seen_record_deduper_reference_solution_passes(self):
        self._assert_reference_solution_passes("first-seen-record-deduper")

    def test_crown_region_board_score_reference_solution_passes(self):
        self._assert_reference_solution_passes("crown-region-board-score")


if __name__ == "__main__":
    unittest.main()
