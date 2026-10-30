from bisect import bisect_right
from collections import deque
import heapq


class MovingAverage:
    def __init__(self, size):
        self.size = size
        self.values = deque()
        self.total = 0

    def next(self, value):
        self.values.append(value)
        self.total += value
        if len(self.values) > self.size:
            self.total -= self.values.popleft()
        return self.total / len(self.values)


class WeightedMovingAverage:
    def __init__(self, size):
        self.size = size
        self.values = deque()
        self.total = 0
        self.weighted = 0

    def next(self, value):
        if len(self.values) == self.size:
            # Shift every old weight down by one, dropping the oldest.
            self.weighted -= self.total
            self.total -= self.values.popleft()
        self.values.append(value)
        self.total += value
        m = len(self.values)
        self.weighted += m * value
        return self.weighted / (m * (m + 1) / 2)


def assign_courts(bookings, maintenance=0):
    releases = []
    plan = [0] * len(bookings)
    count = 0
    for index, (start, finish) in sorted(enumerate(bookings), key=lambda pair: pair[1][0]):
        if releases and releases[0][0] <= start:
            _, court = heapq.heappop(releases)
        else:
            court = count
            count += 1
        plan[index] = court
        heapq.heappush(releases, (finish + maintenance, court))
    return plan


class CommodityPrices:
    def __init__(self):
        self.checkpoint = 0
        self.current = {}
        self.versions = {}
        self.maximum = []

    def upsert(self, timestamp, price):
        self.checkpoint += 1
        self.current[timestamp] = price
        self.versions.setdefault(timestamp, []).append((self.checkpoint, price))
        heapq.heappush(self.maximum, (-price, timestamp))
        return self.checkpoint

    def max_price(self):
        while self.maximum:
            negative, timestamp = self.maximum[0]
            if self.current[timestamp] == -negative:
                return -negative
            heapq.heappop(self.maximum)
        return None

    def get_price(self, timestamp, checkpoint):
        history = self.versions.get(timestamp, [])
        index = bisect_right(history, checkpoint, key=lambda version: version[0])
        return history[index - 1][1] if index else None


class Node:
    def __init__(self, name, children=None):
        self.name = name
        self.children = list(children) if children is not None else []


def closest_common_group(root, employees):
    targets = set(employees)
    answer = None

    def visit(node):
        nonlocal answer
        if not node.children:
            return int(node in targets)
        count = sum(visit(child) for child in node.children)
        if count == len(targets) and answer is None:
            answer = node
        return count

    visit(root)
    return answer
