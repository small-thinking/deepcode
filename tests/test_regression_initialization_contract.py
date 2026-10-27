"""Regression checks accept different RNGs, scales, and bias initializations."""
import contextlib
import io
import json
from pathlib import Path
import unittest

import torch


DIRECTORY = Path(__file__).resolve().parents[1] / "problems/402-linear-logistic-regression-training"
REFERENCE = (DIRECTORY / "solution.py").read_text()
CHECKS = json.loads((DIRECTORY / "tests.json").read_text())
INITIALIZATION = '''    w = torch.randn(X.shape[1], dtype=X.dtype, device=X.device)
    b = torch.randn((), dtype=X.dtype, device=X.device)'''


class RegressionInitializationContractTests(unittest.TestCase):
    def run_checks(self, source):
        scope = {}
        exec(source, scope)
        previous_dtype = torch.get_default_dtype()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                for check in CHECKS:
                    exec(check["test"], scope)
        finally:
            torch.set_default_dtype(previous_dtype)

    def test_default_rng_large_initialization_and_zero_bias_pass(self):
        # These exceed the old abs(weight) < 0.1 bound and consume global RNG.
        variants = (
            INITIALIZATION.replace("torch.randn(", "100 * torch.randn("),
            INITIALIZATION.replace("b = torch.randn((), dtype=X.dtype, device=X.device)",
                                   "b = X.new_zeros(())"),
            '''    g = torch.Generator().manual_seed(19)
    w = torch.randn(X.shape[1], generator=g, dtype=X.dtype).to(X.device)
    b = torch.randn((), generator=g, dtype=X.dtype).to(X.device)''',
            '''    import random
    w = X.new_tensor([random.gauss(0, 5) for _ in range(X.shape[1])])
    b = X.new_tensor(random.gauss(0, 5))''',
            '''    g = torch.Generator()
    g.seed()
    w = torch.randn(X.shape[1], generator=g, dtype=X.dtype).to(X.device)
    b = torch.randn((), generator=g, dtype=X.dtype).to(X.device)''',
        )
        self.assertIn(INITIALIZATION, REFERENCE)
        with torch.random.fork_rng():
            torch.manual_seed(31)
            for initialization in variants:
                with self.subTest(initialization=initialization):
                    self.run_checks(REFERENCE.replace(INITIALIZATION, initialization))

    def test_one_step_check_still_rejects_wrong_gradients(self):
        check = CHECKS[-1]["test"]
        mutations = (
            ("missing linear factor", "2 * (z-y)", "(z-y)"),
            ("wrong logistic factor", "z.sigmoid() - y", "2 * (z.sigmoid() - y)"),
            ("no weight update", "w = w - lr*dw", "w = w"),
            ("no bias update", "b = b - lr*db", "b = b"),
            ("regularize bias", "db = residual.mean()", "db = residual.mean() + l2*b"),
            ("missing weight L2", "+ l2*w", "+ 0*w"),
        )
        for name, old, new in mutations:
            with self.subTest(mutation=name), torch.random.fork_rng():
                torch.manual_seed(23)
                self.assertIn(old, REFERENCE)
                scope = {}
                exec(REFERENCE.replace(old, new), scope)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(AssertionError):
                    exec(check, scope)


if __name__ == "__main__":
    unittest.main()
