import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
SLUGS = ["clip-symmetric-contrastive-loss", "alien-dictionary-order"]


class UberSeptemberFixtures(unittest.TestCase):
    def test_new_reference_solutions_pass_every_visible_case(self):
        store = ProblemStore(ROOT / "problems")
        for slug in SLUGS:
            with self.subTest(slug=slug):
                problem = store.get_problem(slug)
                problem_dir = next((ROOT / "problems").glob(f"*-{slug}"))
                result = evaluate_submission(
                    EvaluationRequest(
                        code=(problem_dir / "solution.py").read_text(encoding="utf-8"),
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
