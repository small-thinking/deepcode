import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests" / "reference_solutions" / "luma_oa_general.py").read_text(
    encoding="utf-8"
)
SLUGS = (
    "adjacent-triangle-feasibility",
    "closest-pair-distance-2d",
)


def evaluate(problem, code):
    return evaluate_submission(
        EvaluationRequest(
            code=code,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
            runtime=problem.get("_runtime", {}),
        )
    )


class LumaOAGeneralFixturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = ProblemStore(ROOT / "problems")

    def test_reference_implementation_passes_all_cases(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = self.store.get_problem(slug)
                result = evaluate(problem, REFERENCE)
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))

    def test_fixtures_reject_plausible_wrong_interpretations(self):
        wrong = {
            "adjacent-triangle-feasibility": (
                "def triangle_flags(sides):\n"
                "    ordered = sorted(sides)\n"
                "    return [int(a + b > c) for a, b, c in zip(ordered, ordered[1:], ordered[2:])]\n"
            ),
            "closest-pair-distance-2d": (
                "import math\n"
                "def closest_pair_distance(points):\n"
                "    points = sorted(points)\n"
                "    return min(math.dist(a, b) for a, b in zip(points, points[1:]))\n"
            ),
        }
        for slug, code in wrong.items():
            with self.subTest(slug=slug):
                result = evaluate(self.store.get_problem(slug), code)
                self.assertNotEqual(result["status"], "passed", result)


if __name__ == "__main__":
    unittest.main()
