from collections import Counter, defaultdict, deque
from heapq import heappop, heappush
from itertools import count


def shortest_paths(source, targets, edges):
    requested_targets = list(targets)
    adjacency = defaultdict(list)
    for start, end, weight in edges:
        if weight < 0:
            raise ValueError("edge weights must be nonnegative")
        adjacency[start].append((end, weight))

    pending_targets = set(requested_targets)
    distances = {}
    frontier = [(0, 0, source)]
    serial = count(1)

    while frontier and pending_targets:
        distance, _, node = heappop(frontier)
        if node in distances:
            continue
        distances[node] = distance
        pending_targets.discard(node)

        for neighbor, weight in adjacency[node]:
            if neighbor not in distances:
                heappush(frontier, (distance + weight, next(serial), neighbor))

    return [distances.get(target) for target in requested_targets]


def is_valid_forest(edges):
    adjacency = defaultdict(list)
    indegree = defaultdict(int)
    nodes = set()
    seen_edges = set()

    for parent, child in edges:
        edge = (parent, child)
        if parent == child or edge in seen_edges:
            return False
        seen_edges.add(edge)
        nodes.add(parent)
        nodes.add(child)
        adjacency[parent].append(child)
        indegree[child] += 1
        if indegree[child] > 1:
            return False

    ready = deque(node for node in nodes if indegree[node] == 0)
    visited = 0
    while ready:
        node = ready.popleft()
        visited += 1
        for child in adjacency[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    return visited == len(nodes)


def subarray_metric(nums, mode, value):
    if mode == "count_target":
        prefix_counts = Counter({0: 1})
        prefix_sum = 0
        total = 0
        for number in nums:
            prefix_sum += number
            total += prefix_counts[prefix_sum - value]
            prefix_counts[prefix_sum] += 1
        return total

    if mode == "longest_target":
        first_index = {0: -1}
        prefix_sum = 0
        longest = 0
        for index, number in enumerate(nums):
            prefix_sum += number
            start = first_index.get(prefix_sum - value)
            if start is not None:
                longest = max(longest, index - start)
            first_index.setdefault(prefix_sum, index)
        return longest

    if mode == "count_divisible":
        divisor = abs(value)
        if divisor == 0:
            raise ValueError("divisor must be nonzero")
        remainder_counts = Counter({0: 1})
        prefix_sum = 0
        total = 0
        for number in nums:
            prefix_sum += number
            remainder = prefix_sum % divisor
            total += remainder_counts[remainder]
            remainder_counts[remainder] += 1
        return total

    raise ValueError("unknown mode")


def racecar(target):
    if isinstance(target, bool) or not isinstance(target, int) or target < 0:
        raise ValueError("target must be a nonnegative integer")

    best = [0] * (target + 1)
    for distance in range(1, target + 1):
        accelerations = distance.bit_length()
        full_run = (1 << accelerations) - 1
        if full_run == distance:
            best[distance] = accelerations
            continue

        minimum = accelerations + 1 + best[full_run - distance]
        partial_run = (1 << (accelerations - 1)) - 1
        for reverse_accelerations in range(accelerations - 1):
            backward_run = (1 << reverse_accelerations) - 1
            remaining = distance - (partial_run - backward_run)
            minimum = min(minimum, accelerations + reverse_accelerations + 1 + best[remaining])
        best[distance] = minimum
    return best[target]


def sort_transformed(nums, a, b, c):
    def transform(value):
        return a * value * value + b * value + c

    result = [0] * len(nums)
    left = 0
    right = len(nums) - 1

    if a >= 0:
        write = len(nums) - 1
        while left <= right:
            left_value = transform(nums[left])
            right_value = transform(nums[right])
            if left_value > right_value:
                result[write] = left_value
                left += 1
            else:
                result[write] = right_value
                right -= 1
            write -= 1
    else:
        write = 0
        while left <= right:
            left_value = transform(nums[left])
            right_value = transform(nums[right])
            if left_value < right_value:
                result[write] = left_value
                left += 1
            else:
                result[write] = right_value
                right -= 1
            write += 1
    return result
