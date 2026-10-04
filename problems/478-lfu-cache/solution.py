from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}  # key -> (value, frequency)
        self.by_frequency = defaultdict(OrderedDict)  # oldest key first
        self.min_frequency = 0

    def _record_use(self, key):
        value, frequency = self.entries[key]
        del self.by_frequency[frequency][key]
        if not self.by_frequency[frequency]:
            del self.by_frequency[frequency]
            if self.min_frequency == frequency:
                self.min_frequency = frequency + 1

        next_frequency = frequency + 1
        self.entries[key] = (value, next_frequency)
        self.by_frequency[next_frequency][key] = None

    def get(self, key):
        if key not in self.entries:
            return None
        self._record_use(key)
        return self.entries[key][0]

    def put(self, key, value):
        if key in self.entries:
            _, frequency = self.entries[key]
            self.entries[key] = (value, frequency)
            self._record_use(key)
            return

        if len(self.entries) == self.capacity:
            oldest_key, _ = self.by_frequency[self.min_frequency].popitem(last=False)
            del self.entries[oldest_key]
            if not self.by_frequency[self.min_frequency]:
                del self.by_frequency[self.min_frequency]

        self.entries[key] = (value, 1)
        self.by_frequency[1][key] = None
        self.min_frequency = 1
