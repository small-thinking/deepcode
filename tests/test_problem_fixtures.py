import unittest
from pathlib import Path

from deepcode.problem_store import ProblemStore
from deepcode.runner import run_submission


ROOT = Path(__file__).resolve().parents[1]


class ProblemFixtureTest(unittest.TestCase):
    def test_matrix_vector_dot_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("matrix-vector-dot-product")
        solution = """def matrix_vector_dot(matrix, vector):
    if not matrix or not vector:
        return -1
    expected_width = len(vector)
    result = []
    for row in matrix:
        if not row or len(row) != expected_width:
            return -1
        result.append(sum(row[i] * vector[i] for i in range(expected_width)))
    return result
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_mean_baseline_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("mean-baseline-regressor")
        solution = """def mean_baseline(train_y, n_predictions):
    if n_predictions == 0:
        return []
    if n_predictions < 0 or not train_y:
        return -1
    value = round(sum(train_y) / len(train_y), 4)
    return [value] * n_predictions
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_classification_accuracy_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("classification-accuracy")
        solution = """def classification_accuracy(y_true, y_pred):
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return -1
    matches = sum(1 for expected, actual in zip(y_true, y_pred) if expected == actual)
    return round(matches / len(y_true), 4)
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

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
        self.assertEqual(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
