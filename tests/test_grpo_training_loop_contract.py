import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/489-grpo-training-loop-debugging"
PROBLEM = json.loads((DIRECTORY / "problem.json").read_text())
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
BY_NAME = {check["name"]: check for check in CHECKS}
REFERENCE = (ROOT / "tests/reference_solutions/grpo_training_loop.py").read_text()


def evaluate(code, checks):
    return evaluate_submission(EvaluationRequest(
        code=code, problem=PROBLEM, tests=checks,
        environment=PROBLEM["environment"],
    ))


class GrpoTrainingLoopContractTest(unittest.TestCase):
    def test_reference_passes(self):
        result = evaluate(REFERENCE, CHECKS)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_starter_has_exactly_six_independently_detectable_bugs(self):
        cases = (
            (
                "raw logits used as sampling weights",
                "    probabilities = torch.softmax(logits, dim=-1)\n",
                "    probabilities = logits\n",
                "sampling handles negative logits, stable extremes, replacement and generator",
            ),
            (
                "missing normalization epsilon",
                "(rewards.std(dim=1, keepdim=True, correction=0) + eps)",
                "rewards.std(dim=1, keepdim=True, correction=0)",
                "advantages normalize rows and detach including constant and singleton groups",
            ),
            (
                "reference shares current policy storage",
                "self.reference_logits = policy_logits.detach().clone()",
                "self.reference_logits = self.policy_logits.detach()",
                "exact forward KL uses prompt rows and keeps reference fixed",
            ),
            (
                "log difference used as ratio",
                "ratio = torch.exp(chosen_logp - old_logprobs)",
                "ratio = chosen_logp - old_logprobs",
                "stale importance ratio uses exponent and sign-sensitive clipping",
            ),
            (
                "optimistic clipping branch",
                "torch.minimum(ratio * advantages, clipped * advantages)",
                "torch.maximum(ratio * advantages, clipped * advantages)",
                "stale importance ratio uses exponent and sign-sensitive clipping",
            ),
            (
                "gradients accumulate between steps",
                "        self.optimizer.zero_grad()\n",
                "",
                "step returns pre-update loss and follows fresh SGD gradient each call",
            ),
        )
        broken = REFERENCE
        for name, correct, incorrect, check_name in cases:
            with self.subTest(name=name):
                self.assertEqual(REFERENCE.count(correct), 1)
                mutant = REFERENCE.replace(correct, incorrect)
                result = evaluate(mutant, [BY_NAME[check_name]])
                self.assertEqual(result["passed"], 0, result)
                broken = broken.replace(correct, incorrect)

        # The starter inlines the raw sampling weights instead of naming them.
        broken = broken.replace(
            "    probabilities = logits\n    return torch.multinomial(probabilities,",
            "    return torch.multinomial(logits,",
        )
        self.assertEqual(PROBLEM["starter_code"], broken)

    def test_wrong_loss_variants_are_rejected(self):
        mutants = {
            "detached ratio": (
                REFERENCE.replace(
                    "ratio = torch.exp(chosen_logp - old_logprobs)",
                    "ratio = torch.exp(chosen_logp - old_logprobs).detach()"),
                "stale importance ratio uses exponent and sign-sensitive clipping",
            ),
            "unclipped ratio": (
                REFERENCE.replace(
                    "torch.minimum(ratio * advantages, clipped * advantages)",
                    "ratio * advantages"),
                "stale importance ratio uses exponent and sign-sensitive clipping",
            ),
            "recompute old policy": (
                REFERENCE.replace(
                    'old_logprobs = batch["old_logprobs"].detach()',
                    'old_logprobs = F.log_softmax(self.policy_logits[ids], dim=-1).gather(1, responses).detach()'),
                "stale importance ratio uses exponent and sign-sensitive clipping",
            ),
            "reverse KL": (
                REFERENCE.replace(
                    "current_logp.exp() * (current_logp - reference_logp)",
                    "reference_logp.exp() * (reference_logp - current_logp)"),
                "exact forward KL uses prompt rows and keeps reference fixed",
            ),
        }
        for name, (code, check_name) in mutants.items():
            with self.subTest(name=name):
                self.assertNotEqual(code, REFERENCE)
                result = evaluate(code, [BY_NAME[check_name]])
                self.assertEqual(result["passed"], 0, result)


if __name__ == "__main__":
    unittest.main()
