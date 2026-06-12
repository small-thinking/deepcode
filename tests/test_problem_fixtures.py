import unittest
from pathlib import Path

from deepcode.problem_store import ProblemStore
from deepcode.runner import run_submission


ROOT = Path(__file__).resolve().parents[1]


class ProblemFixtureTest(unittest.TestCase):
    def test_linear_regression_gradient_step_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("linear-regression-gradient-step")
        solution = """import numpy as np


def linear_regression_step(X, y, weights, bias, learning_rate):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    weights = np.asarray(weights, dtype=float)
    errors = X @ weights + bias - y
    n_rows = X.shape[0]
    weight_gradient = 2 / n_rows * (X.T @ errors)
    bias_gradient = 2 / n_rows * errors.sum()
    new_weights = weights - learning_rate * weight_gradient
    new_bias = bias - learning_rate * bias_gradient
    return new_weights, new_bias
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 3)


if __name__ == "__main__":
    unittest.main()
