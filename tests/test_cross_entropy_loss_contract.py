"""Validate the loss exercise through the real runner and common wrong answers."""
import contextlib
import io
import json
from pathlib import Path
import unittest

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "problems/526-cross-entropy-loss"
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
REFERENCE = (ROOT / "tests/reference_solutions/cross_entropy_loss.py").read_text()


class CrossEntropyLossContractTest(unittest.TestCase):
    def test_reference_passes_real_evaluator(self):
        problem = ProblemStore(ROOT / "problems").get_problem("cross-entropy-loss")
        result = evaluate_submission(EvaluationRequest(
            code=REFERENCE, problem=problem, tests=problem["tests"],
            environment=problem["environment"],
        ))
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(CHECKS), result)

    def test_logsumexp_alternative_passes(self):
        code = REFERENCE.replace(
            "torch.log_softmax(logits, dim=-1)",
            "logits - torch.logsumexp(logits, dim=-1, keepdim=True)",
        )
        namespace = {}
        exec(code, namespace)
        with contextlib.redirect_stdout(io.StringIO()):
            for check in CHECKS:
                with self.subTest(check=check["name"]):
                    exec(check["test"], namespace)

    def test_checks_reject_common_loss_mistakes(self):
        mutations = (
            ("wrong sign", "return -selected.mean()", "return selected.mean()", 0),
            ("sum instead of mean", "return -selected.mean()", "return -selected.sum()", 0),
            ("normalize batch axis", "logits, dim=-1", "logits, dim=0", 1),
            ("detach logits", "torch.log_softmax(logits,", "torch.log_softmax(logits.detach(),", 1),
            ("softmax then log", "torch.log_softmax(logits, dim=-1)", "torch.softmax(logits, dim=-1).log()", 2),
            ("double normalization", "torch.log_softmax(logits, dim=-1)", "torch.log_softmax(logits.softmax(-1), dim=-1)", 0),
            ("ignore mask", "if mask is not None:", "if False:", 3),
            ("force float32", "torch.log_softmax(logits,", "torch.log_softmax(logits.float(),", 5),
        )
        for name, old, new, index in mutations:
            with self.subTest(name=name):
                self.assertIn(old, REFERENCE)
                namespace = {}
                exec(REFERENCE.replace(old, new), namespace)
                with self.assertRaises((AssertionError, RuntimeError, IndexError)):
                    exec(CHECKS[index]["test"], namespace)

    def test_catalog_marks_authored_general_practice(self):
        problem = ProblemStore(ROOT / "problems").get_problem("cross-entropy-loss")
        self.assertEqual(problem["id"], "526")
        self.assertEqual(problem["companies"], ["General"])
        self.assertNotIn("interview_frequency", problem)
        self.assertIn("NotImplementedError", problem["starter_code"])


if __name__ == "__main__":
    unittest.main()
