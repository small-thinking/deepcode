import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
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

    def test_ngram_next_character_model_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("ngram-next-character-model")
        solution = r"""from collections import Counter, defaultdict
import math
import random


class NGramCharModel:
    def __init__(self, n=3, alpha=1.0):
        if n < 1:
            raise ValueError("n must be at least 1")
        if alpha <= 0:
            raise ValueError("alpha must be positive")
        self.n = n
        self.alpha = alpha
        self.counts = defaultdict(Counter)
        self.vocab = set()

    def _context_size(self):
        return self.n - 1

    def _normalize_context(self, context):
        size = self._context_size()
        return "" if size == 0 else str(context)[-size:]

    def _events(self, text):
        padding = "^" * self._context_size()
        padded = padding + text
        for index in range(self._context_size(), len(padded)):
            yield padded[index - self._context_size():index], padded[index]

    def train(self, text):
        if not isinstance(text, str) or not text:
            raise ValueError("text must be a non-empty string")
        self.counts = defaultdict(Counter)
        self.vocab = set(text)
        for context, char in self._events(text):
            self.counts[context][char] += 1
        return self

    def prob(self, context, ch):
        if not self.vocab or ch not in self.vocab:
            return 0.0
        context = self._normalize_context(context)
        context_counts = self.counts[context]
        total = sum(context_counts.values())
        vocab_size = len(self.vocab)
        return (context_counts[ch] + self.alpha) / (total + self.alpha * vocab_size)

    def perplexity(self, text):
        if text == "":
            return float("inf")
        log_prob = 0.0
        for context, char in self._events(text):
            probability = self.prob(context, char)
            if probability <= 0:
                return float("inf")
            log_prob += math.log(probability)
        return math.exp(-log_prob / len(text))

    def sample_top_k(self, context, k=5):
        if k < 1:
            raise ValueError("k must be at least 1")
        if not self.vocab:
            raise ValueError("model must be trained before sampling")
        ranked = sorted(
            ((char, self.prob(context, char)) for char in self.vocab),
            key=lambda item: (-item[1], item[0]),
        )[: min(k, len(self.vocab))]
        chars, weights = zip(*ranked)
        return random.choices(chars, weights=weights, k=1)[0]
"""

        result = evaluate_submission(
            EvaluationRequest(
                code=solution,
                problem=problem,
                tests=problem["tests"],
                environment=problem["environment"],
                runtime=problem.get("_runtime", {}),
            )
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], 6)


if __name__ == "__main__":
    unittest.main()
