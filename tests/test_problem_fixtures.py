import tempfile
import unittest
from pathlib import Path

import torch

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


class NGramCharModel:
    def __init__(self, n=3):
        if n < 1:
            raise ValueError("n must be at least 1")
        self.n = n
        self.counts = defaultdict(Counter)
        self.global_counts = Counter()
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
        self.global_counts = Counter(text)
        self.vocab = set(text)
        for context, char in self._events(text):
            self.counts[context][char] += 1
        return self

    def _prob(self, context, ch):
        if not self.vocab or ch not in self.vocab:
            return 0.0
        context = self._normalize_context(context)
        context_counts = self.counts[context]
        total = sum(context_counts.values())
        if total == 0 or context_counts[ch] == 0:
            return 0.0
        return context_counts[ch] / total

    def _top_char(self, counts):
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def generate(self, prompt="", max_new_chars=100):
        if max_new_chars < 0:
            raise ValueError("max_new_chars must be non-negative")
        if not self.vocab:
            raise ValueError("model must be trained before generation")
        output = str(prompt)
        for _ in range(max_new_chars):
            context = self._normalize_context(output)
            context_counts = self.counts.get(context)
            output += self._top_char(context_counts or self.global_counts)
        return output

    def evaluate(self, text):
        if text == "" or not self.vocab:
            return float("inf")
        log_prob = 0.0
        for context, char in self._events(text):
            probability = self._prob(context, char)
            if probability <= 0:
                return float("inf")
            log_prob += math.log(probability)
        return math.exp(-log_prob / len(text))
"""

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            tiny_shakespeare = (
                "First Citizen:\n"
                "Before we proceed any further, hear me speak.\n\n"
                "All:\n"
                "Speak, speak.\n\n"
                "First Citizen:\n"
                "You are all resolved rather to die than to famish?\n\n"
                "All:\n"
                "Resolved. resolved.\n\n"
            )
            (data_dir / "tiny_shakespeare.txt").write_text(tiny_shakespeare * 20, encoding="utf-8")
            runtime = dict(problem.get("_runtime", {}))
            runtime["data_path"] = str(data_dir)

            result = evaluate_submission(
                EvaluationRequest(
                    code=solution,
                    problem=problem,
                    tests=problem["tests"],
                    environment=problem["environment"],
                    runtime=runtime,
                )
            )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

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

    def test_streaming_logit_entropy_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("streaming-logit-entropy")
        solution = r"""import numpy as np


def entropy_from_logits(logits):
    values = np.asarray(logits, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("logits must be a non-empty 1D sequence")
    max_logit = values.max()
    weights = np.exp(values - max_logit)
    total = weights.sum()
    logsumexp = max_logit + np.log(total)
    return float(logsumexp - (weights @ values) / total)


def streaming_entropy(blocks):
    running_max = -np.inf
    scaled_sum = 0.0
    scaled_weighted_sum = 0.0
    seen = False

    for block in blocks:
        values = np.asarray(block, dtype=np.float64)
        if values.ndim != 1 or values.size == 0:
            raise ValueError("each block must be a non-empty 1D sequence")
        block_max = values.max()
        new_max = max(running_max, block_max)
        previous_scale = 0.0 if not seen else np.exp(running_max - new_max)
        block_weights = np.exp(values - new_max)
        scaled_sum = scaled_sum * previous_scale + block_weights.sum()
        scaled_weighted_sum = scaled_weighted_sum * previous_scale + block_weights @ values
        running_max = new_max
        seen = True

    if not seen:
        raise ValueError("blocks must contain at least one block")
    return float(running_max + np.log(scaled_sum) - scaled_weighted_sum / scaled_sum)
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_top_p_nucleus_sampling_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("top-p-nucleus-sampling")
        solution = r"""import numpy as np


def top_p_sample(logits, p, u, temperature=1.0):
    if not 0 < p <= 1:
        raise ValueError("p must be in (0, 1]")
    if not 0 <= u < 1:
        raise ValueError("u must be in [0, 1)")
    if temperature <= 0:
        raise ValueError("temperature must be positive")

    values = np.asarray(logits, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("logits must be a non-empty 1D sequence")

    scaled = values / temperature
    shifted = scaled - scaled.max()
    probs = np.exp(shifted)
    probs = probs / probs.sum()
    ordered = sorted(range(len(probs)), key=lambda index: (-probs[index], index))

    kept = []
    mass = 0.0
    for index in ordered:
        kept.append(index)
        mass += float(probs[index])
        if mass >= p:
            break

    threshold = u * mass
    cumulative = 0.0
    for index in kept:
        cumulative += float(probs[index])
        if threshold <= cumulative:
            return int(index)
    return int(kept[-1])
"""

        result = run_submission(
            code=solution,
            tests=problem["tests"],
            timeout_seconds=problem["environment"]["timeout_seconds"],
            comparator=problem["environment"]["comparator"],
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["passed"], len(problem["tests"]))

    def test_weighted_dataset_batcher_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("weighted-dataset-batcher")
        solution = r"""class WeightedDatasetBatcher:
    def __init__(self, datasets, weights, batch_size, offset=0):
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if not datasets or not weights:
            raise ValueError("datasets and weights must be non-empty")

        self.datasets = {name: list(values) for name, values in datasets.items()}
        self.weights = dict(weights)
        self.batch_size = batch_size
        self.order = []
        for name, weight in self.weights.items():
            if name not in self.datasets:
                raise ValueError("every weighted dataset must exist")
            if not isinstance(weight, int) or weight <= 0:
                raise ValueError("weights must be positive integers")
            if not self.datasets[name]:
                raise ValueError("datasets must be non-empty")
            self.order.extend([name] * weight)

        self.pos = 0
        self.offsets = {name: 0 for name in self.weights}
        self._skip(offset)

    def _skip(self, n_items):
        for _ in range(n_items):
            self._next_item()

    def _next_item(self):
        name = self.order[self.pos % len(self.order)]
        values = self.datasets[name]
        item = values[self.offsets[name] % len(values)]
        self.offsets[name] += 1
        self.pos += 1
        return (name, item)

    def next_batch(self):
        return [self._next_item() for _ in range(self.batch_size)]

    def state_dict(self):
        return {"pos": self.pos, "offsets": dict(self.offsets)}

    def load_state_dict(self, state):
        self.pos = int(state["pos"])
        self.offsets = {name: int(value) for name, value in state["offsets"].items()}
        return self
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

    def test_prefix_matrix_products_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("prefix-matrix-products")
        solution = r"""import torch


def prefix_matrix_products(W):
    if W.ndim != 3 or W.shape[1] != W.shape[2]:
        raise ValueError("W must have shape (N, D, D)")
    current = torch.eye(W.shape[-1], dtype=W.dtype, device=W.device)
    outputs = []
    for matrix in W:
        current = current @ matrix
        outputs.append(current)
    return torch.stack(outputs)


def prefix_matrix_products_backward(W, grad_P):
    if W.shape != grad_P.shape:
        raise ValueError("W and grad_P must have the same shape")
    if W.ndim != 3 or W.shape[1] != W.shape[2]:
        raise ValueError("W must have shape (N, D, D)")

    n_matrices, dim, _ = W.shape
    identity = torch.eye(dim, dtype=W.dtype, device=W.device)
    prefix_before = [identity]
    current = identity
    for matrix in W:
        current = current @ matrix
        prefix_before.append(current)

    grad_W = torch.zeros_like(W)
    for output_index in range(n_matrices):
        right = identity
        for matrix_index in range(output_index, -1, -1):
            left = prefix_before[matrix_index]
            grad_W[matrix_index] += left.T @ grad_P[output_index] @ right.T
            right = W[matrix_index] @ right
    return grad_W
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

    def test_mnist_torch_classifier_reference_solution_passes_hidden_harness_with_local_data(self):
        problem = ProblemStore(ROOT / "problems").get_problem("mnist-torch-classifier")
        solution = r"""import torch
from torch import nn


def build_model():
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(28 * 28, 128),
        nn.ReLU(),
        nn.Linear(128, 10),
    )


def train_model(model, train_loader, val_loader, epochs=2, device="cpu"):
    device = torch.device(device)
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        total_seen = 0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(images), labels)
            loss.backward()
            optimizer.step()
            batch_size = labels.numel()
            total_loss += float(loss.item()) * batch_size
            total_seen += batch_size
        print(f"epoch {epoch + 1}: loss={total_loss / max(total_seen, 1):.4f}")
    return model
"""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            results_dir = root / "eval-results"
            data_dir.mkdir()
            results_dir.mkdir()
            torch.save(
                {
                    "images": torch.zeros(64, 1, 28, 28, dtype=torch.float32),
                    "labels": torch.zeros(64, dtype=torch.long),
                },
                data_dir / "train.pt",
            )
            torch.save(
                {
                    "images": torch.zeros(16, 1, 28, 28, dtype=torch.float32),
                    "labels": torch.zeros(16, dtype=torch.long),
                },
                data_dir / "val.pt",
            )
            runtime = dict(problem.get("_runtime", {}))
            runtime["data_path"] = str(data_dir)
            runtime["results_path"] = str(results_dir)

            result = evaluate_submission(
                EvaluationRequest(
                    code=solution,
                    problem=problem,
                    tests=problem["tests"],
                    environment=problem["environment"],
                    runtime=runtime,
                )
            )

            metrics_path = results_dir / "metrics.json"
            metrics_written = metrics_path.exists()

        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["passed"], len(problem["tests"]) + 1)
        self.assertTrue(metrics_written)

    def test_vectorized_1nn_distance_network_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("vectorized-1nn-distance-network")
        solution = r"""import numpy as np


def predict_1nn_l2(queries, train_points, train_labels):
    queries = np.asarray(queries, dtype=float)
    train_points = np.asarray(train_points, dtype=float)
    train_labels = np.asarray(train_labels)
    distances = (
        np.sum(queries * queries, axis=1, keepdims=True)
        + np.sum(train_points * train_points, axis=1)[None, :]
        - 2.0 * queries @ train_points.T
    )
    nearest = np.argmin(distances, axis=1)
    return train_labels[nearest]


def l2_distance_logits(queries, train_points):
    queries = np.asarray(queries, dtype=float)
    train_points = np.asarray(train_points, dtype=float)
    weights = 2.0 * train_points.T
    bias = -np.sum(train_points * train_points, axis=1)
    return queries @ weights + bias


def predict_1nn_l1(queries, train_points, train_labels):
    queries = np.asarray(queries, dtype=float)
    train_points = np.asarray(train_points, dtype=float)
    train_labels = np.asarray(train_labels)
    distances = np.abs(queries[:, None, :] - train_points[None, :, :]).sum(axis=2)
    nearest = np.argmin(distances, axis=1)
    return train_labels[nearest]
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

    def test_file_duplicate_groups_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("file-duplicate-groups")
        solution = r"""from collections import defaultdict
import hashlib


def find_duplicate_files(files, read_file):
    by_size = defaultdict(list)
    for path, size in files:
        by_size[size].append(path)

    groups = []
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        by_hash = defaultdict(list)
        for path in paths:
            content = read_file(path)
            digest = hashlib.sha256(content).hexdigest()
            by_hash[digest].append(path)
        for group in by_hash.values():
            if len(group) > 1:
                groups.append(sorted(group))
    return sorted(groups, key=lambda group: group[0])
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

    def test_persistent_memo_lru_cache_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("persistent-memo-lru-cache")
        solution = r"""from collections import OrderedDict
import json


class MemoLRUCache:
    def __init__(self, capacity, file_path=""):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.file_path = file_path
        self.cache = OrderedDict()
        if self.file_path:
            self._load()

    def _cache_key(self, func_name, args=None, kwargs=None):
        args = [] if args is None else list(args)
        kwargs = {} if kwargs is None else dict(kwargs)
        return (
            func_name,
            json.dumps(args, sort_keys=True, separators=(",", ":")),
            json.dumps(kwargs, sort_keys=True, separators=(",", ":")),
        )

    def get_or_compute(self, func, args=None, kwargs=None):
        args = [] if args is None else list(args)
        kwargs = {} if kwargs is None else dict(kwargs)
        key = self._cache_key(func.__name__, args, kwargs)
        if key in self.cache:
            value = self.cache[key]
            self.cache.move_to_end(key)
            self._append(key, value)
            return value

        value = func(*args, **kwargs)
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
        self._append(key, value)
        return value

    def _append(self, key, value):
        if not self.file_path:
            return
        with open(self.file_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"key": list(key), "value": value}) + "\n")

    def _load(self):
        try:
            with open(self.file_path, encoding="utf-8") as handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    key = tuple(record["key"])
                    self.cache[key] = record["value"]
                    self.cache.move_to_end(key)
                    if len(self.cache) > self.capacity:
                        self.cache.popitem(last=False)
        except FileNotFoundError:
            pass
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

    def test_coalescing_memory_allocator_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("coalescing-memory-allocator")
        solution = r"""class Block:
    def __init__(self, start, size, free=True):
        self.start = start
        self.size = size
        self.free = free
        self.prev = None
        self.next = None


class Allocator:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.head = Block(0, capacity, True)
        self.allocated = {}

    def malloc(self, size):
        if size <= 0:
            return -1
        current = self.head
        while current:
            if current.free and current.size >= size:
                if current.size > size:
                    remainder = Block(current.start + size, current.size - size, True)
                    remainder.next = current.next
                    remainder.prev = current
                    if current.next:
                        current.next.prev = remainder
                    current.next = remainder
                    current.size = size
                current.free = False
                self.allocated[current.start] = current
                return current.start
            current = current.next
        return -1

    def free(self, address):
        current = self.allocated.pop(address, None)
        if current is None:
            return False
        current.free = True
        self._coalesce(current)
        return True

    def _coalesce(self, current):
        if current.prev and current.prev.free:
            left = current.prev
            left.size += current.size
            left.next = current.next
            if current.next:
                current.next.prev = left
            current = left
        if current.next and current.next.free:
            right = current.next
            current.size += right.size
            current.next = right.next
            if right.next:
                right.next.prev = current

    def snapshot(self):
        out = []
        current = self.head
        while current:
            out.append((current.start, current.size, current.free))
            current = current.next
        return out
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

    def test_monster_battle_simulator_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("monster-battle-simulator")
        solution = r"""from copy import deepcopy


def _first_alive(team):
    for monster in team:
        if monster["hp"] > 0:
            return monster
    return None


def _effective_damage(attack, defender, type_rules):
    multiplier = type_rules.get((attack["type"], defender["type"]), 1.0)
    return int(attack["damage"] * multiplier)


def simulate_battle(team_a, team_b, type_rules):
    teams = [deepcopy(team_a), deepcopy(team_b)]
    log = []
    turn = 0
    while _first_alive(teams[0]) and _first_alive(teams[1]):
        attacker_team = turn % 2
        defender_team = 1 - attacker_team
        attacker = _first_alive(teams[attacker_team])
        defender = _first_alive(teams[defender_team])
        attack = max(
            attacker["attacks"],
            key=lambda item: _effective_damage(item, defender, type_rules),
        )
        damage = _effective_damage(attack, defender, type_rules)
        defender["hp"] = max(0, defender["hp"] - damage)
        log.append((attacker["name"], attack["name"], defender["name"], damage, defender["hp"]))
        turn += 1
    return 0 if _first_alive(teams[0]) else 1, log
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

    def test_glean_document_indexing_queue_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("glean-document-indexing-queue")
        solution = r"""from heapq import heappop, heappush


class AvailableIndexers:
    def __init__(self, m):
        self.m = m
        self.size = 1
        while self.size < m:
            self.size *= 2
        self.tree = [0] * (2 * self.size)
        for idx in range(m):
            self.tree[self.size + idx] = 1
        for idx in range(self.size - 1, 0, -1):
            self.tree[idx] = self.tree[2 * idx] + self.tree[2 * idx + 1]

    def add(self, idx):
        self._set(idx, 1)

    def remove(self, idx):
        self._set(idx, 0)

    def first_at_or_after(self, start):
        if self.tree[1] == 0:
            return -1
        candidate = self._first_in_range(start, self.m - 1)
        if candidate != -1:
            return candidate
        return self._first_in_range(0, start - 1)

    def _set(self, idx, value):
        pos = self.size + idx
        self.tree[pos] = value
        pos //= 2
        while pos:
            self.tree[pos] = self.tree[2 * pos] + self.tree[2 * pos + 1]
            pos //= 2

    def _first_in_range(self, left, right):
        if left > right:
            return -1
        return self._first(1, 0, self.size - 1, left, right)

    def _first(self, node, lo, hi, ql, qr):
        if hi < ql or qr < lo or self.tree[node] == 0:
            return -1
        if lo == hi:
            return lo if lo < self.m else -1
        mid = (lo + hi) // 2
        left = self._first(2 * node, lo, mid, ql, qr)
        if left != -1:
            return left
        return self._first(2 * node + 1, mid + 1, hi, ql, qr)


def document_indexing_queue(m, queue_time, processing_time, k):
    if m <= 0:
        return 0, None, [], 0.0
    if len(queue_time) != len(processing_time):
        raise ValueError("queue_time and processing_time must have the same length")

    available = AvailableIndexers(m)
    busy = []
    counts = [0] * m
    processed = 0

    for i, (arrival, duration) in enumerate(zip(queue_time, processing_time)):
        while busy and busy[0][0] <= arrival:
            _, indexer = heappop(busy)
            available.add(indexer)
        indexer = available.first_at_or_after(i % m)
        if indexer == -1:
            continue
        available.remove(indexer)
        heappush(busy, (arrival + duration, indexer))
        counts[indexer] += 1
        processed += 1

    ordered = sorted(range(m), key=lambda idx: (-counts[idx], idx))
    top_k = ordered[: min(k, m)]
    busiest = top_k[0] if processed else None
    top_k_processed = sum(counts[idx] for idx in top_k)
    percentage = top_k_processed / processed * 100.0 if processed else 0.0
    return processed, busiest, top_k, percentage
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

    def test_data_labeling_task_scheduler_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("data-labeling-task-scheduler")
        solution = r"""from collections import Counter


def _imbalance(counter, keys):
    values = [counter[key] for key in keys]
    return max(values) - min(values) if values else 0


def _worst_group_imbalance(counter, groups):
    return max((_imbalance(counter, group) for group in groups), default=0)


def build_schedule(tasks, models, humans, k):
    tasks = list(tasks)
    models = list(models)
    humans = list(humans)
    if k < 0:
        raise ValueError("k must be non-negative")
    if not humans:
        return []
    if not tasks or not models:
        if k == 0:
            return []
        raise ValueError("tasks and models are required when k is positive")
    needed = k * len(humans)
    if needed > len(tasks) * len(humans):
        raise ValueError("not enough unique task-human pairs")

    task_model_groups = [[(task, model) for model in models] for task in tasks]
    task_human_groups = [[(task, human) for human in humans] for task in tasks]
    task_model_counts = Counter()
    task_human_counts = Counter()
    human_counts = Counter()
    used_task_human = set()
    schedule = []

    while len(schedule) < needed:
        best = None
        best_score = None
        for task in tasks:
            for human in humans:
                if (task, human) in used_task_human:
                    continue
                for model in models:
                    task_model_counts[(task, model)] += 1
                    task_human_counts[(task, human)] += 1
                    human_counts[human] += 1
                    score = (
                        max(human_counts[h] for h in humans),
                        _worst_group_imbalance(task_model_counts, task_model_groups),
                        _worst_group_imbalance(task_human_counts, task_human_groups),
                        max(human_counts[h] for h in humans) - min(human_counts[h] for h in humans),
                        task,
                        model,
                        human,
                    )
                    task_model_counts[(task, model)] -= 1
                    task_human_counts[(task, human)] -= 1
                    human_counts[human] -= 1
                    if best_score is None or score < best_score:
                        best_score = score
                        best = (task, model, human)
        if best is None:
            raise ValueError("no legal assignment remains")
        task, model, human = best
        schedule.append(best)
        task_model_counts[(task, model)] += 1
        task_human_counts[(task, human)] += 1
        human_counts[human] += 1
        used_task_human.add((task, human))
    return schedule
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

    def test_resumable_list_iterator_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("resumable-list-iterator")
        solution = r"""class ResumableIterator:
    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def set_state(self, state):
        raise NotImplementedError


class ListIterator(ResumableIterator):
    def __init__(self, items):
        self.items = list(items)
        self.index = 0

    def next(self):
        if self.index >= len(self.items):
            raise StopIteration
        value = self.items[self.index]
        self.index += 1
        return value

    def get_state(self):
        return {"index": self.index}

    def set_state(self, state):
        index = state.get("index")
        if not isinstance(index, int) or index < 0 or index > len(self.items):
            raise ValueError("invalid iterator state")
        self.index = index


class CompositeIterator(ResumableIterator):
    def __init__(self, iterators):
        self.iterators = list(iterators)
        self.active = 0

    def next(self):
        while self.active < len(self.iterators):
            try:
                return self.iterators[self.active].next()
            except StopIteration:
                self.active += 1
        raise StopIteration

    def get_state(self):
        return {
            "active": self.active,
            "children": [iterator.get_state() for iterator in self.iterators],
        }

    def set_state(self, state):
        active = state.get("active")
        children = state.get("children")
        if not isinstance(active, int) or active < 0 or active > len(self.iterators):
            raise ValueError("invalid iterator state")
        if not isinstance(children, list) or len(children) != len(self.iterators):
            raise ValueError("invalid iterator state")
        self.active = active
        for iterator, child_state in zip(self.iterators, children):
            iterator.set_state(child_state)
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

    def test_linux_cd_path_resolution_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("linux-cd-path-resolution")
        solution = r"""def _normalize(path):
    parts = []
    for part in path.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/" + "/".join(parts)


def _expand_home(path, home, home_map):
    if not path.startswith("~"):
        return path
    if path == "~" or path.startswith("~/"):
        suffix = path[1:]
        return home + suffix
    name, _, suffix = path[1:].partition("/")
    if name not in home_map:
        raise ValueError("unknown home alias")
    return home_map[name] + ("/" + suffix if suffix else "")


def _apply_links(path, links):
    seen = set()
    current = path
    while True:
        if current in seen:
            raise ValueError("symlink cycle detected")
        seen.add(current)
        match = None
        for source in links:
            source_norm = _normalize(source)
            if current == source_norm or current.startswith(source_norm + "/"):
                if match is None or len(source_norm) > len(match):
                    match = source_norm
        if match is None:
            return current
        target = _normalize(links[match])
        suffix = current[len(match):]
        current = _normalize(target + suffix)


def cd(current_dir, new_dir, home="/home/me", links=None, home_map=None):
    links = {} if links is None else dict(links)
    home_map = {} if home_map is None else dict(home_map)
    destination = _expand_home(new_dir, home, home_map)
    if not destination.startswith("/"):
        destination = current_dir.rstrip("/") + "/" + destination
    normalized = _normalize(destination)
    normalized_links = {_normalize(key): value for key, value in links.items()}
    return _apply_links(normalized, normalized_links)
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

    def test_spreadsheet_dependency_cycle_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("spreadsheet-dependency-cycle")
        solution = r"""def find_circular_dependency(dependencies):
    visiting = {}
    stack = []

    def dfs(cell):
        state = visiting.get(cell, 0)
        if state == 1:
            index = stack.index(cell)
            return stack[index:] + [cell]
        if state == 2:
            return []
        visiting[cell] = 1
        stack.append(cell)
        for neighbor in dependencies.get(cell, []):
            if neighbor not in dependencies:
                continue
            cycle = dfs(neighbor)
            if cycle:
                return cycle
        stack.pop()
        visiting[cell] = 2
        return []

    for cell in dependencies:
        cycle = dfs(cell)
        if cycle:
            return cycle
    return []
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

    def test_markdown_header_chunker_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("markdown-header-chunker")
        solution = r"""def _heading_level(line):
    stripped = line.lstrip()
    if len(stripped) == len(line) and stripped.startswith("#"):
        hashes = len(stripped) - len(stripped.lstrip("#"))
        if 1 <= hashes <= 6 and len(stripped) > hashes and stripped[hashes] == " ":
            return hashes
    return 0


def _header_context(headers):
    return "\n".join(headers) + "\n\n" if headers else ""


def _append_piece(chunks, piece, headers, max_chars):
    if not piece:
        return
    context = _header_context(headers)
    if len(context) > max_chars:
        raise ValueError("header context does not fit")
    if len(piece) <= max_chars:
        chunks.append(piece)
        return
    if not context:
        for start in range(0, len(piece), max_chars):
            chunks.append(piece[start:start + max_chars])
        return
    budget = max_chars - len(context)
    if budget <= 0:
        raise ValueError("header context does not fit")
    body = piece[len(context):] if piece.startswith(context) else piece
    for start in range(0, len(body), budget):
        chunks.append(context + body[start:start + budget])


def chunk_markdown(markdown, max_chars):
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    blocks = markdown.split("\n\n") if markdown else []
    chunks = []
    current = ""
    headers = []
    in_fence = False

    for block in blocks:
        lines = block.split("\n")
        for line in lines:
            if line.startswith("```"):
                in_fence = not in_fence
            level = 0 if in_fence else _heading_level(line)
            if level:
                headers = headers[: level - 1] + [line]
        prefix = "" if not current else "\n\n"
        candidate = current + prefix + block if current else block
        if len(candidate) <= max_chars:
            current = candidate
            continue
        headers_only = current == "\n".join(headers)
        if current and not headers_only:
            _append_piece(chunks, current, headers, max_chars)
        context = _header_context(headers)
        next_piece = block if block in headers else context + block
        if len(next_piece) <= max_chars:
            current = next_piece
        else:
            _append_piece(chunks, next_piece, headers, max_chars)
            current = ""

    if current:
        _append_piece(chunks, current, headers, max_chars)
    return chunks
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

    def test_bootloader_instruction_interpreter_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("bootloader-instruction-interpreter")
        solution = r"""def _parse(line):
    parts = line.split()
    if len(parts) != 2 or parts[0] not in {"plus", "jump", "next"}:
        raise ValueError("malformed instruction")
    try:
        value = int(parts[1])
    except ValueError as exc:
        raise ValueError("malformed instruction") from exc
    return parts[0], value


def run_bootloader(lines):
    instructions = [_parse(line) for line in lines]
    acc = 0
    pc = 0
    seen = set()
    while 0 <= pc < len(instructions):
        if pc in seen:
            return {"status": "loop", "acc": acc, "pc": pc}
        seen.add(pc)
        op, value = instructions[pc]
        if op == "plus":
            acc += value
            pc += 1
        elif op == "jump":
            pc += value
        else:
            pc += 1
    if pc != len(instructions):
        raise ValueError("program counter left the program")
    return {"status": "terminated", "acc": acc, "pc": pc}


def fix_bootloader(lines):
    parsed = [_parse(line) for line in lines]
    for idx, (op, value) in enumerate(parsed):
        if op == "plus":
            continue
        replacement = "next" if op == "jump" else "jump"
        candidate = list(lines)
        candidate[idx] = f"{replacement} {value:+d}"
        try:
            result = run_bootloader(candidate)
        except ValueError:
            continue
        if result["status"] == "terminated":
            return result["acc"]
    raise ValueError("no single-instruction fix found")
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

    def test_contiguous_one_blocks_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("contiguous-one-blocks")
        solution = r"""def label_one_blocks(bits):
    is_string_input = isinstance(bits, str)
    labels = []
    block = -1
    in_block = False
    for bit in bits:
        if (is_string_input and bit == "1") or (not is_string_input and bit == 1):
            if not in_block:
                block += 1
                in_block = True
            labels.append(block)
        elif (is_string_input and bit == "0") or (not is_string_input and bit == 0):
            in_block = False
            labels.append(-1)
        else:
            raise ValueError("bits must contain only 0 and 1")
    return labels
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

    def test_two_layer_numpy_network_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("two-layer-numpy-network")
        solution = r"""import numpy as np


class TwoLayerNet:
    def __init__(self, input_dim, hidden_dim, output_dim, seed=0, weight_scale=0.1):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0.0, weight_scale, size=(input_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.W2 = rng.normal(0.0, weight_scale, size=(hidden_dim, output_dim))
        self.b2 = np.zeros(output_dim)

    def forward(self, X):
        X = np.asarray(X, dtype=float)
        hidden_linear = X @ self.W1 + self.b1
        hidden = np.maximum(hidden_linear, 0.0)
        logits = hidden @ self.W2 + self.b2
        shifted = logits - logits.max(axis=1, keepdims=True)
        exp_scores = np.exp(shifted)
        probs = exp_scores / exp_scores.sum(axis=1, keepdims=True)
        return probs

    def loss(self, X, y):
        probs = self.forward(X)
        y = np.asarray(y, dtype=int)
        return float(-np.mean(np.log(probs[np.arange(len(y)), y] + 1e-12)))

    def train_step(self, X, y, learning_rate=0.1):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=int)
        n = X.shape[0]
        hidden_linear = X @ self.W1 + self.b1
        hidden = np.maximum(hidden_linear, 0.0)
        logits = hidden @ self.W2 + self.b2
        shifted = logits - logits.max(axis=1, keepdims=True)
        exp_scores = np.exp(shifted)
        probs = exp_scores / exp_scores.sum(axis=1, keepdims=True)
        grad_logits = probs.copy()
        grad_logits[np.arange(n), y] -= 1.0
        grad_logits /= n
        grad_W2 = hidden.T @ grad_logits
        grad_b2 = grad_logits.sum(axis=0)
        grad_hidden = grad_logits @ self.W2.T
        grad_hidden[hidden_linear <= 0.0] = 0.0
        grad_W1 = X.T @ grad_hidden
        grad_b1 = grad_hidden.sum(axis=0)
        self.W1 -= learning_rate * grad_W1
        self.b1 -= learning_rate * grad_b1
        self.W2 -= learning_rate * grad_W2
        self.b2 -= learning_rate * grad_b2
        return self.loss(X, y)
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

    def test_extra_tree_classifier_reference_solution_passes(self):
        problem = ProblemStore(ROOT / "problems").get_problem("extra-tree-classifier")
        solution = r"""import numpy as np


class Node:
    def __init__(self, prediction, feature=None, threshold=None, left=None, right=None):
        self.prediction = prediction
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right


def _gini(y):
    if len(y) == 0:
        return 0.0
    _, counts = np.unique(y, return_counts=True)
    probabilities = counts / len(y)
    return float(1.0 - np.sum(probabilities * probabilities))


def _majority(y):
    values, counts = np.unique(y, return_counts=True)
    return values[np.argmax(counts)]


class ExtraTreeClassifier:
    def __init__(self, max_depth=5, min_leaf=1, n_features=None, n_thresholds=1, seed=0):
        self.max_depth = max_depth
        self.min_leaf = min_leaf
        self.n_features = n_features
        self.n_thresholds = n_thresholds
        self.rng = np.random.default_rng(seed)
        self.root = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)
        self.root = self._build(X, y, 0)
        return self

    def _build(self, X, y, depth):
        prediction = _majority(y)
        if depth >= self.max_depth or len(y) < 2 * self.min_leaf or _gini(y) == 0.0:
            return Node(prediction)

        n_rows, n_cols = X.shape
        n_features = self.n_features or max(1, int(np.sqrt(n_cols)))
        features = self.rng.choice(n_cols, size=min(n_features, n_cols), replace=False)
        parent_impurity = _gini(y)
        best = None

        for feature in features:
            low = X[:, feature].min()
            high = X[:, feature].max()
            if low == high:
                continue
            thresholds = self.rng.uniform(low, high, size=self.n_thresholds)
            for threshold in thresholds:
                left_mask = X[:, feature] <= threshold
                left_count = int(left_mask.sum())
                right_count = n_rows - left_count
                if left_count < self.min_leaf or right_count < self.min_leaf:
                    continue
                gain = parent_impurity
                gain -= (left_count / n_rows) * _gini(y[left_mask])
                gain -= (right_count / n_rows) * _gini(y[~left_mask])
                if best is None or gain > best[0]:
                    best = (gain, feature, float(threshold), left_mask)

        if best is None:
            return Node(prediction)
        _, feature, threshold, left_mask = best
        left = self._build(X[left_mask], y[left_mask], depth + 1)
        right = self._build(X[~left_mask], y[~left_mask], depth + 1)
        return Node(prediction, feature, threshold, left, right)

    def predict_one(self, x):
        if self.root is None:
            raise ValueError("model must be fitted before prediction")
        node = self.root
        while node.feature is not None:
            node = node.left if x[node.feature] <= node.threshold else node.right
        return node.prediction

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return np.array([self.predict_one(row) for row in X])
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
