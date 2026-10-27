"""Exercise the Tensor contract through the evaluator and independent gradient checks."""
import json
from pathlib import Path
import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/366-binary-focal-loss"
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
REFERENCE = (ROOT / "tests/reference_solutions/binary_focal_loss.py").read_text()


class BinaryFocalLossContractTest(unittest.TestCase):
    def test_reference_passes_real_evaluator(self):
        problem = ProblemStore(ROOT / "problems").get_problem("binary-focal-loss")
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE, problem=problem, tests=problem["tests"],
            environment=problem["environment"], runtime=problem.get("_runtime", {}),
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_equivalent_branchwise_formula_passes(self):
        code = REFERENCE.replace(
            "losses = -alpha_t * one_minus_p_t.pow(gamma) * log_p_t",
            "losses = -torch.where(positive, "
            "alpha * (1-probabilities).pow(gamma) * probabilities.log(), "
            "(1-alpha) * probabilities.pow(gamma) * torch.log1p(-probabilities))",
        )
        for check in CHECKS:
            with self.subTest(check=check["name"]):
                namespace = {}
                exec(code, namespace)
                exec(check["test"], namespace)

    def test_checks_reject_common_formula_and_tensor_mistakes(self):
        mutations = (
            ("reversed labels", "positive = labels == 1", "positive = labels == 0", 0),
            ("ignore alpha", "positive = labels == 1", "alpha = .25\n    positive = labels == 1", 1),
            ("ignore gamma", ".pow(gamma)", ".pow(0)", 0),
            ("detach probabilities", "positive = labels == 1",
             "probabilities = probabilities.detach()\n    positive = labels == 1", 3),
            ("Python scalar return", "return losses.mean()", "return losses.mean().item()", 0),
            ("sum instead of mean", "return losses.mean()", "return losses.sum()", 0),
            ("wrong mean axis", "return losses.mean()", "return losses.mean(dim=-1)", 1),
            ("force float32", "positive = labels == 1",
             "probabilities = probabilities.float()\n    positive = labels == 1", 0),
            ("clip valid probabilities", "positive = labels == 1",
             "probabilities = probabilities.clamp(1e-7, 1-1e-7)\n    positive = labels == 1", 5),
        )
        for name, old, new, index in mutations:
            with self.subTest(mutation=name):
                self.assertIn(old, REFERENCE)
                namespace = {}
                exec(REFERENCE.replace(old, new), namespace)
                with self.assertRaises((AssertionError, RuntimeError, AttributeError, TypeError)):
                    exec(CHECKS[index]["test"], namespace)

    def test_catalog_preserves_identity_and_selects_torch_assertion_runtime(self):
        problem = ProblemStore(ROOT / "problems").get_problem("binary-focal-loss")
        self.assertEqual(problem["id"], "366")
        self.assertEqual(problem["evaluation"]["type"], "ml_torch_modeling")
        self.assertEqual(problem["environment"]["packages"], ["torch"])
        self.assertEqual(problem["companies"], ["Datadog", "General"])
        self.assertIn("NotImplementedError", problem["starter_code"])
        self.assertIn("probabilities, not logits", problem["prompt"])


if __name__ == "__main__":
    unittest.main()
