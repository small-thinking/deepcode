from collections import Counter
from dataclasses import dataclass


# PROVIDED: one immutable result per label.
@dataclass(frozen=True)
class LabelMetrics:
    label: str
    num_actual_samples: int
    precision: float
    recall: float
    f1: float


# PROVIDED: rows are actual labels; columns are predicted labels.
class ConfusionMatrix:
    def __init__(self):
        self._counts = Counter()

    def add(self, actual, predicted):
        self._counts[actual, predicted] += 1

    def get(self, actual, predicted):
        return self._counts[actual, predicted]

    def all_labels(self):
        return sorted({label for pair in self._counts for label in pair})


class Evaluator:
    def __init__(self):
        self.matrix = ConfusionMatrix()

    def build_matrix(self, actuals, predictions):
        assert len(actuals) == len(predictions)
        self.matrix = ConfusionMatrix()
        for actual, predicted in zip(actuals, predictions):
            self.matrix.add(actual, predicted)

    def calculate_metrics(self):
        labels = self.matrix.all_labels()
        results = []
        for label in labels:
            tp = self.matrix.get(label, label)
            actual = sum(self.matrix.get(label, other) for other in labels)
            predicted = sum(self.matrix.get(other, label) for other in labels)
            results.append(LabelMetrics(label, actual,
                tp / predicted if predicted else 0.0,
                tp / actual if actual else 0.0,
                2 * tp / (actual + predicted) if actual + predicted else 0.0))
        return results
