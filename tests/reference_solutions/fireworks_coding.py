from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque


def recommend_friends(graph, user, k):
    friends = set(graph[user])
    if not friends or k == 0:
        return []
    counts = Counter()
    for friend in friends:
        for candidate in set(graph[friend]):
            if candidate != user and candidate not in friends:
                counts[candidate] += 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [(candidate, count, count / len(friends)) for candidate, count in ranked[:k]]


def detect_fanout(events, window_seconds=600, max_destinations=10):
    assert window_seconds > 0 and max_destinations >= 0
    queues = defaultdict(deque)
    counts = defaultdict(Counter)
    alerts = []
    for timestamp, source, destination in events:
        queue, active = queues[source], counts[source]
        while queue and queue[0][0] <= timestamp - window_seconds:
            _, expired = queue.popleft()
            active[expired] -= 1
            if active[expired] == 0:
                del active[expired]
        queue.append((timestamp, destination))
        active[destination] += 1
        if len(active) > max_destinations:
            alerts.append((timestamp, source))
    return alerts


def idle_intervals(tasks, query_start, query_end):
    cursor, result = query_start, []
    for start, end, _ in sorted(tasks, key=lambda task: task[0]):
        if end <= cursor:
            continue
        if start >= query_end:
            break
        if start > cursor:
            result.append((cursor, start))
        cursor = min(query_end, max(cursor, end))
        if cursor == query_end:
            break
    if cursor < query_end:
        result.append((cursor, query_end))
    return result


class BusyTimeline:
    def __init__(self):
        self.starts = []
        self.ends = []

    def add(self, start, end, node_id):
        left = bisect_left(self.ends, start)
        right = left
        while right < len(self.starts) and self.starts[right] <= end:
            start = min(start, self.starts[right])
            end = max(end, self.ends[right])
            right += 1
        self.starts[left:right] = [start]
        self.ends[left:right] = [end]

    def get_idle(self, query_start, query_end):
        index = bisect_right(self.ends, query_start)
        cursor, result = query_start, []
        while index < len(self.starts) and self.starts[index] < query_end:
            if self.starts[index] > cursor:
                result.append((cursor, self.starts[index]))
            cursor = min(query_end, max(cursor, self.ends[index]))
            index += 1
        if cursor < query_end:
            result.append((cursor, query_end))
        return result
