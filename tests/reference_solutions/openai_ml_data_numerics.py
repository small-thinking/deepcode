import math
from collections import Counter, defaultdict

import numpy as np


def consensus_labels(labels, excluded=()):
    excluded = set(excluded)
    result = []
    for row in labels:
        values = [value for index, value in enumerate(row) if index not in excluded and value is not None]
        if not values:
            result.append(None)
            continue
        counts = Counter(values)
        result.append(next(value for value in values if counts[value] == max(counts.values())))
    return result


def agreement_rates(labels, min_labels=1):
    width = len(labels[0]) if labels else 0
    consensus = consensus_labels(labels)
    rates = []
    for index in range(width):
        observed = [row[index] == consensus[row_index] for row_index, row in enumerate(labels) if row[index] is not None and sum(value is not None for value in row) >= min_labels and consensus[row_index] is not None]
        rates.append(sum(observed) / len(observed) if observed else 1.0)
    return rates


def select_rejected_annotators(labels, threshold=0.7, min_labels=1, max_removed_fraction=0.5, min_remaining=1):
    width = len(labels[0]) if labels else 0
    capacity = min(int(width * max_removed_fraction), max(0, width - min_remaining))
    candidates = [index for index, rate in enumerate(agreement_rates(labels, min_labels)) if rate < threshold]
    return candidates[:capacity]


def mask_annotators(labels, rejected):
    rejected = set(rejected)
    return [[None if index in rejected else value for index, value in enumerate(row)] for row in labels]


def double_descent_sweep(n_train, n_test, dimensions, noise_std=0.1, seed=0):
    dimensions = list(dimensions)
    if not dimensions or min(dimensions) <= 0:
        raise ValueError("dimensions must be positive")
    rng = np.random.default_rng(seed)
    max_width = max(dimensions)
    weights = rng.normal(size=max_width)
    train_x = rng.normal(size=(n_train, max_width))
    test_x = rng.normal(size=(n_test, max_width))
    train_y = train_x @ weights + rng.normal(scale=noise_std, size=n_train)
    test_y = test_x @ weights + rng.normal(scale=noise_std, size=n_test)
    rows = []
    for width in dimensions:
        coefficients = np.linalg.lstsq(train_x[:, :width], train_y, rcond=None)[0]
        train_mse = float(np.mean((train_x[:, :width] @ coefficients - train_y) ** 2))
        test_mse = float(np.mean((test_x[:, :width] @ coefficients - test_y) ** 2))
        rows.append((width, train_mse, test_mse))
    return rows


def stable_softmax(logits):
    values = np.asarray(logits, dtype=float)
    shifted = values - values.max(axis=-1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / exponentials.sum(axis=-1, keepdims=True)


def standardize_columns(X):
    values = np.asarray(X, dtype=float)
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    if np.any(std == 0):
        raise ValueError("constant column")
    return (values - mean) / std


def ridge_gradient(X, y, weights, bias, l2):
    residual = np.asarray(X) @ np.asarray(weights) + bias - np.asarray(y)
    weight_gradient = 2 * np.asarray(X).T @ residual / len(residual) + 2 * l2 * np.asarray(weights)
    return weight_gradient, float(2 * residual.mean())


class LossCurve:
    def __init__(self, values):
        self.values = np.asarray(values, dtype=float)

    def moving_average(self, window):
        if window <= 0 or window > len(self.values):
            raise ValueError("invalid window")
        prefix = np.concatenate(([0.0], np.cumsum(self.values)))
        return (prefix[window:] - prefix[:-window]) / window

    def best_window(self, window):
        return int(np.argmin(self.moving_average(window)))


def _valid_rows(rows):
    return [row for row in rows if row.get("variant") in {"A", "B"} and row.get("exposed") and row.get("metric") is not None]


def _lift(rows):
    a = [float(row["metric"]) for row in rows if row["variant"] == "A"]
    b = [float(row["metric"]) for row in rows if row["variant"] == "B"]
    if not a or not b or np.mean(a) == 0:
        return math.nan
    return float((np.mean(b) - np.mean(a)) / np.mean(a))


def ab_summary(rows):
    valid = _valid_rows(rows)
    a = np.array([float(row["metric"]) for row in valid if row["variant"] == "A"])
    b = np.array([float(row["metric"]) for row in valid if row["variant"] == "B"])
    lift = _lift(valid)
    if len(a) < 2 or len(b) < 2:
        return {"lift": lift, "p_value": math.nan}
    standard_error = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    if standard_error == 0:
        p_value = 0.0 if a.mean() != b.mean() else 1.0
    else:
        p_value = math.erfc(abs((b.mean() - a.mean()) / standard_error) / math.sqrt(2))
    return {"lift": lift, "p_value": float(p_value)}


class SegmentLiftReport:
    def __init__(self, rows):
        self.groups = defaultdict(list)
        for row in _valid_rows(rows):
            if row.get("country") is not None:
                self.groups[row["country"]].append(row)

    def lift(self, country):
        return _lift(self.groups.get(country, []))


def analyze_image_dataset(images):
    types, noisy_indices, cleaned = [], [], []
    for index, image in enumerate(images):
        value = np.asarray(image)
        if value.ndim == 2 or (value.ndim >= 3 and value.shape[-1] == 1):
            kind = "gray"
        elif value.ndim >= 3 and value.shape[-1] == 3:
            kind = "color"
        else:
            kind = "unknown"
        types.append(kind)
        finite = np.isfinite(value)
        if not finite.all():
            noisy_indices.append(index)
        repaired = value.astype(float, copy=True)
        fill = float(repaired[finite].mean()) if finite.any() else 0.0
        repaired[~finite] = fill
        cleaned.append(repaired)
    return {
        "types": types,
        "noisy_indices": noisy_indices,
        "noisy_rate": len(noisy_indices) / len(images) if images else 0.0,
        "cleaned": cleaned,
        "quality": {"total": len(images), "clean": len(images) - len(noisy_indices)},
    }
