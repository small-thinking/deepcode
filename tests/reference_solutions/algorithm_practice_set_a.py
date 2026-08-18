from collections import deque

import numpy as np


class MessageCooldownLogger:
    def __init__(self):
        self._last_allowed = {}

    def should_print(self, timestamp, message):
        previous = self._last_allowed.get(message)
        if previous is not None and timestamp - previous < 10:
            return False
        self._last_allowed[message] = timestamp
        return True


def _record_features(records, categories, means, scales):
    numeric = np.empty((len(records), 3), dtype=float)
    for row_index, record in enumerate(records):
        numeric[row_index] = [
            float(record["hours_spent_reading_a"]),
            float(record["hours_spent_reading_b"]),
            float(record["hours_spent_reading_c"]),
        ]
    normalized = (numeric - means) / scales
    encoded = np.zeros((len(records), len(categories)), dtype=float)
    category_index = {category: index for index, category in enumerate(categories)}
    for row_index, record in enumerate(records):
        column = category_index.get(record["current_post_category"])
        if column is not None:
            encoded[row_index, column] = 1.0
    return np.column_stack((np.ones(len(records)), normalized, encoded))


def predict_click_probabilities(train_records, test_records, learning_rate=0.2, steps=800):
    labels = np.array([int(record["click"]) for record in train_records], dtype=float)
    if np.all(labels == labels[0]):
        return [float(labels[0])] * len(test_records)

    categories = sorted({record["current_post_category"] for record in train_records})
    train_numeric = np.array(
        [
            [
                float(record["hours_spent_reading_a"]),
                float(record["hours_spent_reading_b"]),
                float(record["hours_spent_reading_c"]),
            ]
            for record in train_records
        ],
        dtype=float,
    )
    means = train_numeric.mean(axis=0)
    scales = train_numeric.std(axis=0)
    scales[scales == 0.0] = 1.0

    design = _record_features(train_records, categories, means, scales)
    weights = np.zeros(design.shape[1], dtype=float)
    for _ in range(steps):
        logits = np.clip(design @ weights, -500.0, 500.0)
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        gradient = design.T @ (probabilities - labels) / len(labels)
        weights -= learning_rate * gradient

    test_design = _record_features(test_records, categories, means, scales)
    logits = np.clip(test_design @ weights, -500.0, 500.0)
    return (1.0 / (1.0 + np.exp(-logits))).tolist()


def transform_words(start, target, words, part):
    if part not in {1, 2, 3}:
        raise ValueError("part must be 1, 2, or 3")
    if len(start) != len(target):
        return [] if part == 3 else False
    if start == target:
        return [start] if part == 3 else True

    allowed_distances = {1} if part == 1 else {1, 2}
    candidates = {word for word in words if len(word) == len(start)}
    candidates.add(target)
    candidates.discard(start)
    parents = {start: None}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        next_words = [
            candidate
            for candidate in sorted(candidates)
            if sum(left != right for left, right in zip(current, candidate))
            in allowed_distances
        ]
        for candidate in next_words:
            candidates.remove(candidate)
            parents[candidate] = current
            if candidate == target:
                if part != 3:
                    return True
                path = []
                while candidate is not None:
                    path.append(candidate)
                    candidate = parents[candidate]
                return path[::-1]
            queue.append(candidate)

    return [] if part == 3 else False
