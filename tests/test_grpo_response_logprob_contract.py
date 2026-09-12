import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/247-grpo-response-logprob-training"
PROBLEM = json.loads((DIRECTORY / "problem.json").read_text())
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
REFERENCE = (ROOT / "tests/reference_solutions/openai_ml_posttraining_autograd.py").read_text()


def evaluate(code, checks):
    return evaluate_submission(EvaluationRequest(
        code=code, problem=PROBLEM, tests=checks,
        environment=PROBLEM["environment"],
    ))


class GrpoResponseLogprobContractTest(unittest.TestCase):
    def test_reference_passes(self):
        result = evaluate(REFERENCE, CHECKS)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_wrong_math_is_rejected(self):
        mutants = {
            "zero advantages": (REFERENCE + "\ndef group_relative_advantages(rewards, group_size, eps=1e-6):\n    return torch.zeros_like(rewards.detach())\n", [CHECKS[0]]),
            "zero loss": (REFERENCE + "\ndef grpo_loss(logits, reference_logits, sequences, response_mask, rewards, group_size, beta=0.01):\n    return logits.sum() * 0\n", [CHECKS[4]]),
            "unshifted KL": (REFERENCE.replace(
                "masked_kl(logits[:, :-1], reference_logits[:, :-1], response_mask[:, 1:])",
                "masked_kl(logits, reference_logits, response_mask)"), [CHECKS[4]]),
        }
        for name, (code, checks) in mutants.items():
            with self.subTest(name=name):
                self.assertNotEqual(code, REFERENCE)
                result = evaluate(code, checks)
                self.assertEqual(result["passed"], 0, result)


if __name__ == "__main__":
    unittest.main()
