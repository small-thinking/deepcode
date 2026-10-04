import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUGS = (
    "longest-common-substring-length",
    "largest-plus-sign",
    "sort-concentric-matrix-rings",
)
SOURCE = "https://www.1point3acres.com/interview/thread/1129671"


class XaiHumanDataOAFixtureTest(unittest.TestCase):
    def test_reference_solutions_pass_visible_cases(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                solution = (ROOT / "problems" / f"{problem['id']}-{slug}" / "solution.py").read_text(encoding="utf-8")
                result = evaluate_submission(
                    EvaluationRequest(
                        code=solution,
                        problem=problem,
                        tests=problem["tests"],
                        environment=problem["environment"],
                        runtime=problem.get("_runtime", {}),
                    )
                )
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))

    def test_distinct_questions_share_one_source_event(self):
        store = ProblemStore(ROOT / "problems")
        notion_ids = set()
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                self.assertIn("SpaceX AI", problem["companies"])
                self.assertIn(SOURCE, {ref["url"] for ref in problem["references"]})
                frequency = problem["interview_frequency"]["SpaceX AI"]
                self.assertEqual(frequency["stars"], 1)
                self.assertEqual(len(frequency["source_record_ids"]), 1)
                notion_ids.update(frequency["source_record_ids"])
        self.assertEqual(len(notion_ids), 3)


if __name__ == "__main__":
    unittest.main()
