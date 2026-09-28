import math
import random


class WeightedSampler:
    def __init__(self, values, weights, rng=random.random):
        assert len(values) == len(weights) and len(values) > 0
        assert all(math.isfinite(weight) and weight >= 0 for weight in weights)
        self.values = list(values)
        self.cumulative = []
        total = 0
        for weight in weights:
            total += weight
            self.cumulative.append(total)
        assert total > 0 and math.isfinite(total)
        self.total = total
        self.rng = rng

    def sample(self):
        unit = self.rng()
        assert 0 <= unit < 1
        target = unit * self.total
        left, right = 0, len(self.cumulative)
        while left < right:
            mid = (left + right) // 2
            if self.cumulative[mid] <= target:
                left = mid + 1
            else:
                right = mid
        return self.values[left]
