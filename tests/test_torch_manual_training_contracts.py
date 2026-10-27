"""Preserve hand-derived gradients while migrating the array backend to Torch."""
import contextlib
import io
import json
from pathlib import Path
import unittest

import torch

from deepcode.evaluators import EvaluationRequest, evaluate_submission
from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]
FOLDERS = (
    "016-linear-regression-gradient-step", "402-linear-logistic-regression-training",
    "110-two-layer-numpy-network", "490-numpy-classifier-workout",
)


class TorchManualTrainingContracts(unittest.TestCase):
    def test_native_tensor_references_pass_real_evaluator(self):
        for folder in FOLDERS:
            path = ROOT / "problems" / folder
            metadata = json.loads((path / "problem.json").read_text())
            problem = ProblemStore(ROOT / "problems").get_problem(metadata["slug"])
            with self.subTest(problem=metadata["slug"]):
                self.assertEqual(problem["evaluation"]["type"], "ml_torch_modeling")
                self.assertEqual(problem["environment"]["packages"], ["torch"])
                result = evaluate_submission(EvaluationRequest(
                    code=(path / "solution.py").read_text(), problem=problem,
                    tests=problem["tests"], environment=problem["environment"],
                    runtime=problem.get("_runtime", {}),
                ))
                self.assertEqual(result["status"], "passed", result)
                self.assertEqual(result["passed"], len(problem["tests"]), result)

    def assert_manual_mlp_update(self, source):
        # Autograd is only an independent test oracle; the learner's code uses no autograd.
        scope = {}
        exec(source, scope)
        model = scope["TwoLayerNet"](2, 5, 3)
        x = torch.tensor([[.2, -.3], [.4, .1], [-.1, .5]], dtype=torch.float64)
        labels = torch.tensor([0, 2, 1])
        old = [getattr(model, name).clone() for name in ("W1", "b1", "W2", "b2")]
        w1, b1, w2, b2 = [value.clone().requires_grad_() for value in old]
        logits = (x @ w1 + b1).relu() @ w2 + b2
        expected_loss = torch.nn.functional.cross_entropy(logits, labels)
        gradients = torch.autograd.grad(expected_loss, (w1, b1, w2, b2))
        loss = model.train_step(x, labels, .17)
        for name, before, gradient in zip(("W1", "b1", "W2", "b2"), old, gradients):
            torch.testing.assert_close(getattr(model, name), before - .17*gradient)
        torch.testing.assert_close(loss, model.loss(model.forward(x), labels))

    def test_manual_mlp_update_matches_independent_autograd_oracle(self):
        source = (ROOT / "problems/110-two-layer-numpy-network/solution.py").read_text()
        self.assert_manual_mlp_update(source)
        for name, old, new in (
            ("updated W2 leaks into earlier gradient", "grad_logits @ self.W2.T",
             "grad_logits @ (self.W2 - learning_rate * grad_W2).T"),
            ("missing ReLU derivative", "grad_hidden * (hidden_linear > 0)", "grad_hidden"),
        ):
            with self.subTest(mutation=name):
                self.assertIn(old, source)
                with self.assertRaises(AssertionError):
                    self.assert_manual_mlp_update(source.replace(old, new))

    def test_student_checks_reject_autograd_shortcut(self):
        for folder in FOLDERS:
            path = ROOT / "problems" / folder
            source = (path / "solution.py").read_text()
            cases = json.loads((path / "tests.json").read_text())
            check = next(case for case in cases if "autograd" in case["test"])
            target = ("linear_regression_step" if folder.startswith("016") else
                      "train_regression" if folder.startswith("402") else
                      "train_epoch" if folder.startswith("490") else None)
            if target:
                mutation = f"\ndef {target}(*args, **kwargs):\n    torch.autograd.grad(torch.tensor(1., requires_grad=True), torch.tensor(1.))\n"
            else:
                mutation = "\nTwoLayerNet.train_step = lambda *args, **kwargs: torch.autograd.grad(torch.tensor(1., requires_grad=True), torch.tensor(1.))\n"
            with self.subTest(problem=folder):
                scope = {}
                exec(source + mutation, scope)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(AssertionError):
                    exec(check["test"], scope)


if __name__ == "__main__":
    unittest.main()
