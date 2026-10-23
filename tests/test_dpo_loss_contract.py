"""Exercise the DPO loss through the real runner and reject common math errors."""
import json
from pathlib import Path
import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/525-dpo-loss"
PROBLEM = json.loads((DIRECTORY / "problem.json").read_text())
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
REFERENCE = (ROOT / "tests/reference_solutions/dpo_loss.py").read_text()


class DpoLossContractTest(unittest.TestCase):
    def test_reference_passes_real_evaluator(self):
        problem = ProblemStore(ROOT / "problems").get_problem(PROBLEM["slug"])
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE, problem=problem, tests=problem["tests"],
            environment=problem["environment"],
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_equivalent_stable_implementations_pass(self):
        for expression in (
            "F.softplus(-logits).mean()",
            "torch.logaddexp(torch.zeros_like(logits), -logits).mean()",
        ):
            code = REFERENCE.replace("-F.logsigmoid(logits).mean()", expression)
            for check in CHECKS:
                with self.subTest(expression=expression, check=check["name"]):
                    namespace = {}
                    exec(compile(code, "stable alternative", "exec"), namespace)
                    exec(check["test"], namespace)

    def test_checks_reject_common_dpo_mistakes(self):
        mutations = (
            ("reverse preference", "policy_gap - reference_gap", "reference_gap - policy_gap", 0),
            ("omit reference", "policy_gap - reference_gap", "policy_gap", 3),
            ("add reference", "policy_gap - reference_gap", "policy_gap + reference_gap", 3),
            ("ignore beta", "beta * (policy_gap - reference_gap)", "policy_gap - reference_gap", 4),
            ("scale loss instead", "beta * (policy_gap - reference_gap)", "policy_gap - reference_gap", 0),
            ("sum batch", ".mean()", ".sum()", 2),
            ("detach policy chosen", "policy_chosen_logps -", "policy_chosen_logps.detach() -", 2),
            ("detach policy rejected", "- policy_rejected_logps", "- policy_rejected_logps.detach()", 2),
            ("reference gradients", ".detach()", "", 3),
            ("unstable sigmoid log", "F.logsigmoid(logits)", "torch.sigmoid(logits).log()", 5),
        )
        for name, old, new, index in mutations:
            with self.subTest(name=name):
                self.assertIn(old, REFERENCE)
                code = REFERENCE.replace(old, new)
                if name == "scale loss instead":
                    code = code.replace("return -F", "return -beta * F")
                namespace = {}
                exec(compile(code, name, "exec"), namespace)
                with self.assertRaises((AssertionError, RuntimeError)):
                    exec(CHECKS[index]["test"], namespace)

    def test_catalog_exposes_general_practice_without_company_claims(self):
        problem = ProblemStore(ROOT / "problems").get_problem("dpo-loss")
        self.assertEqual(problem["category"], "ML Coding")
        self.assertEqual(problem["companies"], ["General"])
        self.assertNotIn("interview_frequency", problem)
        self.assertIn("NotImplementedError", problem["starter_code"])


if __name__ == "__main__":
    unittest.main()
