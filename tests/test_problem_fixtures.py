import unittest
from pathlib import Path

from deepcode.evaluators import EvaluationRequest, evaluate_submission
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

    def test_source_attribution_highlighter_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("source-attribution-highlighter")
        solution = r"""def highlight_sources(document, sources):
    def is_word_char(char):
        return char.isalnum() or char == "_"

    def is_whole_token_match(start, end):
        left_ok = start == 0 or not is_word_char(document[start - 1])
        right_ok = end == len(document) or not is_word_char(document[end])
        return left_ok and right_ok

    matches = []
    counts = {source: 0 for source in sources}
    for source in sources:
        if not source:
            continue
        start = document.find(source)
        while start != -1:
            end = start + len(source)
            if is_whole_token_match(start, end):
                matches.append((start, end, source))
                counts[source] += 1
            start = document.find(source, start + 1)

    intervals = []
    for start, end, source in sorted(matches, key=lambda item: (item[0], item[1], item[2])):
        if not intervals or start > intervals[-1][1]:
            intervals.append([start, end, {source}])
            continue
        intervals[-1][1] = max(intervals[-1][1], end)
        intervals[-1][2].add(source)

    pieces = []
    cursor = 0
    citations = []
    for start, end, interval_sources in intervals:
        pieces.append(document[cursor:start])
        pieces.append("<yellow>")
        pieces.append(document[start:end])
        pieces.append("</yellow>")
        citations.append(sorted(interval_sources))
        cursor = end
    pieces.append(document[cursor:])
    return "".join(pieces), counts, citations
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_debug_transformer_attention_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("debug-transformer-attention")
        solution = r"""import math
import torch
from torch import nn
import torch.nn.functional as F


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout_p=0.0):
        super().__init__()
        if embed_dim % num_heads != 0:
            raise ValueError("embed_dim must be divisible by num_heads")
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.dropout_p = dropout_p
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, x, padding_mask=None):
        B, T, C = x.shape
        qkv = self.qkv(x).view(B, T, 3, self.num_heads, self.head_dim)
        q, k, v = qkv.unbind(dim=2)
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        scores = q @ k.transpose(-2, -1)
        scores = scores / math.sqrt(self.head_dim)

        future_mask = torch.triu(torch.ones(T, T, device=x.device, dtype=torch.bool), diagonal=1)
        scores = scores.masked_fill(future_mask, float("-inf"))

        if padding_mask is not None:
            scores = scores.masked_fill(~padding_mask[:, None, None, :], float("-inf"))

        weights = torch.softmax(scores, dim=-1)
        weights = F.dropout(weights, p=self.dropout_p, training=self.training)
        out = weights @ v
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(out)
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
        self.assertEqual(result["passed"], len(problem["tests"]))


if __name__ == "__main__":
    unittest.main()
