from collections import deque


class WindowKth:
    """O(1) amortized add, O(n log n) query, O(n) active-window space."""

    def __init__(self, window_size):
        self.window_size = window_size
        self.events = deque()

    def _expire(self, now):
        oldest = now - self.window_size
        while self.events and self.events[0][0] < oldest:
            self.events.popleft()

    def add(self, timestamp, value):
        self._expire(timestamp)
        self.events.append((timestamp, value))

    def kth(self, now, k, order='smallest'):
        self._expire(now)
        values = sorted((value for _, value in self.events), reverse=(order == 'largest'))
        if k > len(values):
            return None
        return values[k - 1]
