import html
import re
import textwrap
import json
import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/247-grpo-response-logprob-training"
PROBLEM = json.loads((DIRECTORY / "problem.json").read_text())
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
CHECKS_BY_NAME = {check["name"]: check for check in CHECKS}
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

    def test_displayed_demo_code_passes_contract(self):
        demo = (DIRECTORY / "assets/response-alignment-lab.html").read_text()
        snippets = {name: html.unescape(code) for name, code in re.findall(
            r'<code data-contract="([a-z]+)">(.*?)</code>', demo, re.S)}
        self.assertEqual(set(snippets), {"advantages", "gather", "kl", "policy", "combined"})
        functions = [
            ("group_relative_advantages(rewards, group_size, eps=1e-6)",
             snippets["advantages"] + "\nreturn advantages"),
            ("gather_response_logprobs(logits, sequences, response_mask)",
             snippets["gather"] + "\nreturn selected"),
            ("masked_kl(policy_logits, reference_logits, response_mask)",
             snippets["kl"] + "\nreturn kl"),
            ("grpo_loss(logits, reference_logits, sequences, response_mask, rewards, group_size, beta=0.01)",
             "advantages = group_relative_advantages(rewards, group_size)\n" +
             snippets["policy"] + "\n" + snippets["combined"]),
        ]
        code = "import torch\nimport torch.nn.functional as F\n"
        for signature, body in functions:
            code += f"\ndef {signature}:\n" + textwrap.indent(body, "    ") + "\n"
        result = evaluate(code, CHECKS)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_wrong_math_is_rejected(self):
        mutants = {
            "zero advantages": (
                REFERENCE + "\ndef group_relative_advantages(rewards, group_size, eps=1e-6):\n    return torch.zeros_like(rewards.detach())\n",
                [CHECKS_BY_NAME["advantages are grouped, finite, and detached"]],
            ),
            "legacy zero-prefixed output": (REFERENCE.replace(
                "return gathered.masked_fill(~response_mask[:, 1:], 0.0)",
                "return F.pad(gathered.masked_fill(~response_mask[:, 1:], 0.0), (1, 0))"),
                [CHECKS_BY_NAME["response log probabilities use causal alignment and masks"]]),
            "unshifted token targets": (REFERENCE.replace(
                "sequences[:, 1:].unsqueeze(-1)", "sequences[:, :-1].unsqueeze(-1)"),
                [CHECKS_BY_NAME["compact log probabilities preserve batch shape and empty-mask gradients"]]),
            "zero loss": (
                REFERENCE + "\ndef grpo_loss(logits, reference_logits, sequences, response_mask, rewards, group_size, beta=0.01):\n    return logits.sum() * 0\n",
                [CHECKS_BY_NAME["combined loss exact causal KL and unequal response lengths"]],
            ),
            "unshifted KL": (REFERENCE.replace(
                "masked_kl(logits[:, :-1], reference_logits[:, :-1], response_mask[:, 1:])",
                "masked_kl(logits, reference_logits, response_mask)"),
                [CHECKS_BY_NAME["combined loss exact causal KL and unequal response lengths"]]),
            "masked log-probability gradient leak": (REFERENCE.replace(
                "return gathered.masked_fill(~response_mask[:, 1:], 0.0)",
                "return gathered.masked_fill(~response_mask[:, 1:], 0.0) + (logits[:, :-1].sum(dim=-1) - logits[:, :-1].sum(dim=-1).detach()) * (~response_mask[:, 1:]).to(logits.dtype)"),
                [CHECKS_BY_NAME["only selected predictable tokens contribute log-probability gradients"]]),
        }
        for name, (code, checks) in mutants.items():
            with self.subTest(name=name):
                self.assertNotEqual(code, REFERENCE)
                result = evaluate(code, checks)
                self.assertEqual(result["passed"], 0, result)


if __name__ == "__main__":
    unittest.main()
