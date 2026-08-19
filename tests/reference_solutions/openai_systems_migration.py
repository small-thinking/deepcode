import heapq
import ipaddress
from collections import deque


class EventTimeCreditLedger:
    def __init__(self):
        self._writes = []
        self._windows = []

    def add_credit(self, label, amount, start, duration):
        end = start + duration
        self._writes.append(("add", amount, start, end, len(self._writes)))
        self._windows.append((start, end))

    def debit(self, amount, timestamp):
        self._writes.append(("debit", amount, timestamp, None, len(self._writes)))

    def get_balance(self, timestamp):
        events = sorted(
            (write for write in self._writes if write[2] <= timestamp),
            key=lambda write: (write[2], write[4]),
        )
        active = []
        active_total = 0
        debt = 0

        for kind, amount, event_time, expiration, sequence in events:
            while active and active[0][0] < event_time:
                _end, _sequence, remaining = heapq.heappop(active)
                active_total -= remaining

            if kind == "add":
                paid = min(debt, amount)
                debt -= paid
                remaining = amount - paid
                if remaining:
                    heapq.heappush(active, (expiration, sequence, remaining))
                    active_total += remaining
                continue

            needed = amount
            while needed and active:
                end, grant_sequence, remaining = heapq.heappop(active)
                used = min(needed, remaining)
                needed -= used
                remaining -= used
                active_total -= used
                if remaining:
                    heapq.heappush(active, (end, grant_sequence, remaining))
            debt += needed

        while active and active[0][0] < timestamp:
            _end, _sequence, remaining = heapq.heappop(active)
            active_total -= remaining

        if not any(start <= timestamp <= end for start, end in self._windows):
            return None
        balance = active_total - debt
        return balance if balance >= 0 else None


class IPv4Iterator:
    def __init__(self, ip_or_cidr, reverse=False):
        address_text, separator, prefix_text = ip_or_cidr.partition("/")
        current = int(ipaddress.IPv4Address(address_text))
        if separator:
            prefix_length = int(prefix_text)
            mask = ((1 << 32) - 1) ^ ((1 << (32 - prefix_length)) - 1)
            low = current & mask
            high = low + (1 << (32 - prefix_length)) - 1
        else:
            low, high = 0, (1 << 32) - 1
        self._current = current
        self._reverse = reverse
        self._boundary = low if reverse else high

    def __iter__(self):
        return self

    def __next__(self):
        if (not self._reverse and self._current > self._boundary) or (
            self._reverse and self._current < self._boundary
        ):
            raise StopIteration
        result = str(ipaddress.IPv4Address(self._current))
        self._current += -1 if self._reverse else 1
        return result


class CreditAccounts:
    def __init__(self):
        self._balances = {}
        self._failed = set()

    def add(self, user_id, amount):
        self._balances[user_id] = self._balances.get(user_id, 0) + amount
        self._failed.discard(user_id)

    def subtract(self, user_id, amount):
        balance = self._balances.get(user_id, 0)
        if amount <= balance:
            self._balances[user_id] = balance - amount
            self._failed.discard(user_id)
        else:
            self._failed.add(user_id)

    def get_balance(self, user_id):
        if user_id in self._failed:
            return None
        return self._balances.get(user_id, 0)


def analyze_topology(n, edges, reachability_queries, failure_queries):
    dependencies = [[] for _ in range(n)]
    dependents = [[] for _ in range(n)]
    unresolved = [0] * n
    for dependent, dependency in edges:
        dependencies[dependent].append(dependency)
        dependents[dependency].append(dependent)
        unresolved[dependent] += 1

    ready = deque(node for node, degree in enumerate(unresolved) if degree == 0)
    startup_order = []
    while ready:
        node = ready.popleft()
        startup_order.append(node)
        for dependent in dependents[node]:
            unresolved[dependent] -= 1
            if unresolved[dependent] == 0:
                ready.append(dependent)
    has_cycle = len(startup_order) != n
    if has_cycle:
        startup_order = []

    reachability_answers = []
    for source, target in reachability_queries:
        if source == target:
            reachability_answers.append(True)
            continue
        visited = {source}
        stack = [source]
        while stack:
            node = stack.pop()
            for dependency in dependencies[node]:
                if dependency == target:
                    stack.clear()
                    visited.add(target)
                    break
                if dependency not in visited:
                    visited.add(dependency)
                    stack.append(dependency)
        reachability_answers.append(target in visited)

    failure_impacts = []
    for initial_failures in failure_queries:
        failed = set(initial_failures)
        queue = deque(failed)
        while queue:
            failed_node = queue.popleft()
            for dependent in dependents[failed_node]:
                if dependent not in failed:
                    failed.add(dependent)
                    queue.append(dependent)
        failure_impacts.append(len(failed))

    return has_cycle, startup_order, reachability_answers, failure_impacts
