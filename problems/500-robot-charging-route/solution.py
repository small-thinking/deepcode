from collections import deque
from heapq import heappop, heappush


def optimal_route(grid):
    rows, cols = len(grid), len(grid[0])
    start = destination = None
    chargers = []
    for r, row in enumerate(grid):
        for c, symbol in enumerate(row):
            if symbol == "S":
                start = (r, c)
            elif symbol == "D":
                destination = (r, c)
            elif symbol == "C":
                chargers.append((r, c))

    points = [start] + chargers + [destination]
    goal = len(points) - 1
    point_index = {point: i for i, point in enumerate(points)}
    edges = [[] for _ in points]

    for source, origin in enumerate(points[:-1]):
        queue = deque([(origin[0], origin[1], 0)])
        seen = {origin}
        while queue:
            r, c, distance = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue
                neighbor = (nr, nc)
                if neighbor in seen or grid[nr][nc] == "#":
                    continue
                seen.add(neighbor)
                next_distance = distance + 1
                if neighbor in point_index and neighbor != start:
                    edges[source].append((point_index[neighbor], next_distance))
                else:
                    queue.append((nr, nc, next_distance))

    lengths = sorted({distance for outgoing in edges for _, distance in outgoing})
    if not lengths:
        return -1

    def best_with_capacity(capacity):
        # Every edge ends at a charger (one visit) or at D (zero visits).
        best = {0: (0, 0)}
        heap = [(0, 0, 0)]
        while heap:
            charges, moves, node = heappop(heap)
            if (charges, moves) != best[node]:
                continue
            if node == goal:
                return charges, moves
            for neighbor, distance in edges[node]:
                if distance > capacity:
                    continue
                candidate = (charges + (neighbor != goal), moves + distance)
                if candidate < best.get(neighbor, (float("inf"), float("inf"))):
                    best[neighbor] = candidate
                    heappush(heap, (*candidate, neighbor))
        return None

    all_edges = best_with_capacity(lengths[-1])
    if all_edges is None:
        return -1
    minimum_charges = all_edges[0]
    lo, hi = 0, len(lengths) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        result = best_with_capacity(lengths[mid])
        if result is not None and result[0] == minimum_charges:
            hi = mid
        else:
            lo = mid + 1
    capacity = lengths[lo]
    charges, moves = best_with_capacity(capacity)
    return charges, capacity, moves
