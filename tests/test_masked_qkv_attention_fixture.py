import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]


class MaskedQKVAttentionFixtureTest(unittest.TestCase):
    def evaluate(self, code, test_index=None):
        problem = ProblemStore(ROOT / "problems").get_problem("pytorch-masked-qkv-attention")
        return evaluate_submission(EvaluationRequest(
            code=code, problem=problem,
            tests=problem["tests"] if test_index is None else [problem["tests"][test_index]],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))

    def test_reference_solution_matches_native_attention_and_gradients(self):
        code = (ROOT / "tests/reference_solutions/masked_qkv_attention.py").read_text()
        result = self.evaluate(code)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], 5)

    def test_float32_intermediates_allow_normal_rounding(self):
        code = (ROOT / "tests/reference_solutions/masked_qkv_attention.py").read_text()
        code = code.replace(
            "    if output_dtype in (torch.float16, torch.bfloat16):\n"
            "        q, k, v = q.float(), k.float(), v.float()",
            "    q, k, v = q.float(), k.float(), v.float()",
        )
        result = self.evaluate(code)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], 5)

    def test_relaxed_tolerances_still_reject_incorrect_attention(self):
        code = (ROOT / "tests/reference_solutions/masked_qkv_attention.py").read_text()
        variants = (
            ("wrong scaling", code.replace("math.sqrt(q.shape[-1])", "q.shape[-1]"), 2),
            ("missing key gradient", code.replace("k.transpose", "k.detach().transpose"), 2),
            ("ignored mask", code.replace("if mask is not None:", "if False:"), 0),
        )
        for name, candidate, test_index in variants:
            with self.subTest(name=name):
                result = self.evaluate(candidate, test_index)
                self.assertNotEqual(result["status"], "passed", result)


if __name__ == "__main__":
    unittest.main()
