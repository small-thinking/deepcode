import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
CODING_SLUGS = (
    "reddit-load-balancer-routing",
    "reddit-word-sequence-validation",
    "reddit-straight-line-word-search",
    "reader-mode-comment-filter",
)


class RedditSyncFixtureTest(unittest.TestCase):
    def test_reference_solutions_pass_and_broken_starters_fail(self):
        store = ProblemStore(ROOT / "problems")
        for slug in CODING_SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                solution = (
                    ROOT / "problems" / f"{int(problem['id']):03d}-{slug}" / "solution.py"
                ).read_text(encoding="utf-8")

                def evaluate(code):
                    return evaluate_submission(
                        EvaluationRequest(
                            code=code,
                            problem=problem,
                            tests=problem["tests"],
                            environment=problem["environment"],
                            runtime=problem.get("_runtime", {}),
                        )
                    )

                self.assertGreaterEqual(len(problem["tests"]), 6)
                result = evaluate(solution)
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]))
                self.assertNotEqual(evaluate(problem["starter_code"])["status"], "passed")


if __name__ == "__main__":
    unittest.main()
