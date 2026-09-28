import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore

ROOT = Path(__file__).resolve().parents[1]


class MaskedQKVAttentionFixtureTest(unittest.TestCase):
    def test_reference_solution_matches_native_attention_and_gradients(self):
        problem = ProblemStore(ROOT / "problems").get_problem("pytorch-masked-qkv-attention")
        code = (ROOT / "tests/reference_solutions/masked_qkv_attention.py").read_text()
        result = evaluate_submission(EvaluationRequest(
            code=code, problem=problem, tests=problem["tests"],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
