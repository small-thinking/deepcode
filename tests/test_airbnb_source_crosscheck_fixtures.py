import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOLUTION = (
    ROOT / "tests" / "reference_solutions" / "airbnb_source_crosscheck.py"
).read_text(encoding="utf-8")


class AirbnbSourceCrosscheckFixtureTest(unittest.TestCase):
    def test_source_backed_airbnb_questions_expose_reports(self):
        expected_urls = {
            "minimum-cost-bundle-cover": {
                "https://www.1point3acres.com/interview/thread/1137550",
                "https://www.1point3acres.com/bbs/thread-1146074-1-1.html",
                "https://www.1point3acres.com/interview/thread/1150336",
                "https://www.1point3acres.com/interview/thread/1151255",
                "https://www.1point3acres.com/interview/thread/1150756",
            },
            "query-parameter-decoder": {
                "https://www.1point3acres.com/interview/thread/1170012",
            },
            "reactive-sum-key-store": {
                "https://www.1point3acres.com/interview/thread/1173125",
                "https://www.1point3acres.com/bbs/thread-1131849-1-1.html",
            },
            "crown-region-board-score": {
                "https://www.1point3acres.com/interview/thread/1163600",
            },
            "digit-permutation-lower-bound": {
                "https://www.1point3acres.com/home/thread/1054795",
                "https://www.1point3acres.com/interview/thread/1173125",
                "https://www.1point3acres.com/interview/thread/1179104",
            },
            "reservation-hold-booking-platform": {
                "https://www.1point3acres.com/interview/thread/1163600",
            },
            "weighted-dag-ski-score": {
                "https://www.1point3acres.com/bbs/thread-1139472-1-1.html",
            },
            "nested-array-list-iterator": {
                "https://www.1point3acres.com/interview/thread/1123318",
            },
            "account-contact-components": {
                "https://www.1point3acres.com/interview/thread/1169233",
            },
            "exact-target-purchase-plan": {
                "https://www.1point3acres.com/interview/thread/1171020",
                "https://www.1point3acres.com/interview/thread/1162688",
            },
            "cover-photo-conversion-evaluation": {
                "https://www.1point3acres.com/interview/thread/1162688",
                "https://www.1point3acres.com/interview/thread/1171020",
            },
            "listing-quality-evaluation-design": {
                "https://www.1point3acres.com/interview/thread/1162688",
                "https://www.1point3acres.com/interview/thread/1171020",
            },
            "airbnb-motivation-reflection": {
                "https://www.1point3acres.com/interview/thread/1162688",
                "https://www.1point3acres.com/interview/thread/1171020",
            },
            "airbnb-cross-functional-project-story": {
                "https://www.1point3acres.com/interview/thread/1163600",
                "https://www.1point3acres.com/home/thread/716016",
            },
            "minimum-number-all-digits": {
                "https://www.1point3acres.com/home/thread/604924",
            },
        }

        store = ProblemStore(ROOT / "problems")
        for slug, urls in expected_urls.items():
            with self.subTest(slug=slug):
                references = store.get_problem(slug)["references"]
                self.assertEqual({reference["url"] for reference in references}, urls)

    def test_minimum_number_all_digits_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("minimum-number-all-digits")
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


if __name__ == "__main__":
    unittest.main()
