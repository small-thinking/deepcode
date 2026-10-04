import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests" / "reference_solutions" / "luma_oa_ml.py").read_text(encoding="utf-8")
SLUGS = (
    "stable-softmax-list",
    "zero-impute-standardize-columns",
)


class LumaOaMlFixturesTest(unittest.TestCase):
    def setUp(self):
        self.store = ProblemStore(ROOT / "problems")

    def evaluate(self, slug, code):
        problem = self.store.get_problem(slug)
        return evaluate_submission(EvaluationRequest(
            code=code,
            problem=problem,
            tests=problem["tests"],
            environment=problem["environment"],
            runtime=problem.get("_runtime", {}),
        ))

    def test_reference_solutions_pass(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                result = self.evaluate(slug, REFERENCE)
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(self.store.get_problem(slug)["tests"]))


    def test_raw_exponentials_fail_on_large_logits(self):
        wrong = "import math\ndef softmax(logits):\n    weights = [math.exp(x) for x in logits]\n    return [x / sum(weights) for x in weights]\n"
        self.assertNotEqual(self.evaluate("stable-softmax-list", wrong)["status"], "passed")


    def test_sample_variance_fails(self):
        wrong = REFERENCE.replace(
            "variance = sum((value - mean) ** 2 for value in values) / rows",
            "variance = sum((value - mean) ** 2 for value in values) / (rows - 1)",
        )
        self.assertNotEqual(self.evaluate("zero-impute-standardize-columns", wrong)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
