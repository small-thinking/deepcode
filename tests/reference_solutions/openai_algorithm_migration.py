from collections import deque


def infection_metrics(n, edges, sources):
    adjacency = [[] for _ in range(n)]
    seen_edges = set()
    for left, right in edges:
        edge = (left, right) if left <= right else (right, left)
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        adjacency[left].append(right)
        adjacency[right].append(left)

    initial = set(sources)
    if not initial:
        return (-1, 0) if n else (0, 0)

    infected_at = [-1] * n
    queue = deque()
    for source in initial:
        infected_at[source] = 0
        queue.append(source)

    wave_sizes = []
    while queue:
        node = queue.popleft()
        next_time = infected_at[node] + 1
        while len(wave_sizes) < next_time:
            wave_sizes.append(0)
        for neighbor in adjacency[node]:
            if infected_at[neighbor] != -1:
                continue
            infected_at[neighbor] = next_time
            wave_sizes[next_time - 1] += 1
            queue.append(neighbor)

    if any(time == -1 for time in infected_at):
        finish_time = -1
    else:
        finish_time = max(infected_at, default=0)
    return finish_time, max(wave_sizes, default=0)


class _CoverageTree:
    def __init__(self, size):
        self.size = size
        self.minimum = [0] * (size * 4)
        self.lazy = [0] * (size * 4)

    def _push(self, node):
        delta = self.lazy[node]
        if not delta:
            return
        for child in (node * 2, node * 2 + 1):
            self.minimum[child] += delta
            self.lazy[child] += delta
        self.lazy[node] = 0

    def add(self, left, right):
        def visit(node, start, end):
            if right <= start or end <= left:
                return
            if left <= start and end <= right:
                self.minimum[node] += 1
                self.lazy[node] += 1
                return
            self._push(node)
            middle = (start + end) // 2
            visit(node * 2, start, middle)
            visit(node * 2 + 1, middle, end)
            self.minimum[node] = min(self.minimum[node * 2], self.minimum[node * 2 + 1])

        visit(1, 0, self.size)

    def first_below(self, left, right, limit):
        def visit(node, start, end):
            if right <= start or end <= left or self.minimum[node] >= limit:
                return None
            if end - start == 1:
                return start
            self._push(node)
            middle = (start + end) // 2
            candidate = visit(node * 2, start, middle)
            if candidate is not None:
                return candidate
            return visit(node * 2 + 1, middle, end)

        return visit(1, 0, self.size)


def rebalance_shards(limit, shards):
    parsed = []
    for encoded in shards:
        shard_id, start, end = encoded.split(":")
        parsed.append((shard_id, int(start), int(end)))
    if not parsed:
        return []

    parsed.sort(key=lambda shard: (shard[1], shard[2], shard[0]))
    global_min = parsed[0][1]
    global_max = max(end for _shard_id, _start, end in parsed)
    coordinates = sorted({point for _shard_id, start, end in parsed for point in (start, end + 1)})
    coordinate_index = {point: index for index, point in enumerate(coordinates)}
    coverage = _CoverageTree(len(coordinates) - 1)
    kept = []

    for shard_id, start, end in parsed:
        first = coverage.first_below(
            coordinate_index[start], coordinate_index[end + 1], limit
        )
        if first is None:
            continue
        adjusted_start = coordinates[first]
        kept.append([shard_id, adjusted_start, end])
        coverage.add(first, coordinate_index[end + 1])

    previous = None
    current_end = global_min - 1
    for shard in kept:
        if shard[1] > current_end + 1:
            previous[2] = shard[1] - 1
        current_end = max(current_end, shard[2])
        previous = shard
    if previous is not None and current_end < global_max:
        previous[2] = global_max

    return [f"{shard_id}:{start}:{end}" for shard_id, start, end in kept]


def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def game_of_life(rows, cols, steps, grid):
    board = [list(row) for row in grid]
    directions = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )
    for _ in range(steps):
        next_board = [["0"] * cols for _row in range(rows)]
        for row in range(rows):
            for col in range(cols):
                neighbors = sum(
                    0 <= row + dr < rows
                    and 0 <= col + dc < cols
                    and board[row + dr][col + dc] == "1"
                    for dr, dc in directions
                )
                if neighbors == 3 or (board[row][col] == "1" and neighbors == 2):
                    next_board[row][col] = "1"
        board = next_board
    return ["".join(row) for row in board]
