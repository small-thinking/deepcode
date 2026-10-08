from collections import deque


class Logger:
    def __init__(self):
        self._last_allowed = {}

    def shouldPrintMessage(self, timestamp, message):
        previous = self._last_allowed.get(message)
        if previous is not None and timestamp - previous < 10:
            return False
        self._last_allowed[message] = timestamp
        return True


def predict_clicks(train_data, test_data):
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    train = pd.DataFrame(train_data)
    test = pd.DataFrame(test_data)
    numeric = [
        "hours_spent_reading_a",
        "hours_spent_reading_b",
        "hours_spent_reading_c",
    ]
    features = numeric + ["current_post_category"]
    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("category", OneHotEncoder(handle_unknown="ignore"), ["current_post_category"]),
    ])
    model = make_pipeline(preprocessing, LogisticRegression(max_iter=1000))
    model.fit(train[features], train["click"])

    # The tiny fixture has no held-out labels; these are training diagnostics.
    training_predictions = model.predict(train[features])
    training_probabilities = model.predict_proba(train[features])[:, 1]
    return {
        "predictions": model.predict(test[features]).tolist(),
        "metrics": {
            "accuracy": float(accuracy_score(train["click"], training_predictions)),
            "f1_score": float(f1_score(train["click"], training_predictions, zero_division=0)),
            "roc_auc": float(roc_auc_score(train["click"], training_probabilities)),
        },
    }


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


def solve(start, target, words, part):
    return transform_words(start, target, words, part)
