import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "tests" / "reference_solutions" / "luma_oa_ml.py").read_text(encoding="utf-8")
SLUGS = (
    "centered-grayscale-crop",
    "stable-softmax-list",
    "gaussian-blur-kernel",
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

    def test_wrong_crop_offset_fails(self):
        wrong = "def center_crop(image, crop_h, crop_w):\n    return [row[:crop_w] for row in image[:crop_h]]\n"
        self.assertNotEqual(self.evaluate(SLUGS[0], wrong)["status"], "passed")

    def test_raw_exponentials_fail_on_large_logits(self):
        wrong = "import math\ndef softmax(logits):\n    weights = [math.exp(x) for x in logits]\n    return [x / sum(weights) for x in weights]\n"
        self.assertNotEqual(self.evaluate(SLUGS[1], wrong)["status"], "passed")

    def test_unweighted_gaussian_fails(self):
        wrong = "def gaussian_kernel(k, sigma):\n    return [[1 / (k*k) for _ in range(k)] for _ in range(k)]\n"
        self.assertNotEqual(self.evaluate(SLUGS[2], wrong)["status"], "passed")

    def test_sample_variance_fails(self):
        wrong = REFERENCE.replace(
            "variance = sum((value - mean) ** 2 for value in values) / rows",
            "variance = sum((value - mean) ** 2 for value in values) / (rows - 1)",
        )
        self.assertNotEqual(self.evaluate(SLUGS[3], wrong)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
