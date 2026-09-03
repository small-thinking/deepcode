import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "spacex_spotify_catalog_gaps.py"
).read_text(encoding="utf-8")


class SpaceXSpotifyCatalogGapFixtureTest(unittest.TestCase):
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

    def test_image_patch_tensor_axis_reordering_reference_solution_passes(self):
        self._assert_reference_solution_passes("image-patch-tensor-axis-reordering")

    def test_sql_top_n_played_tracks_reference_solution_passes(self):
        self._assert_reference_solution_passes("sql-top-n-played-tracks")


if __name__ == "__main__":
    unittest.main()
