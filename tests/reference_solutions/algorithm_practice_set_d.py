from collections import deque


def serialize_expression(node):
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2}

    def render(current):
        if isinstance(current, str):
            return current

        operator, left, right = current

        def child_text(child, is_right_child):
            text = render(child)
            if isinstance(child, tuple):
                child_precedence = precedence[child[0]]
                if child_precedence < precedence[operator] or (
                    is_right_child and child_precedence == precedence[operator]
                ):
                    return f"({text})"
            return text

        return (
            child_text(left, False)
            + operator
            + child_text(right, True)
        )

    return render(node)


def min_knight_moves(rows, cols, start, dest, blocked):
    blocked = set(blocked)
    if start in blocked or dest in blocked:
        return None
    if start == dest:
        return 0

    moves = (
        (2, 1),
        (2, -1),
        (-2, 1),
        (-2, -1),
        (1, 2),
        (1, -2),
        (-1, 2),
        (-1, -2),
    )
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        (row, column), distance = queue.popleft()
        for row_delta, column_delta in moves:
            neighbor = (row + row_delta, column + column_delta)
            if not (0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols):
                continue
            if neighbor in blocked or neighbor in seen:
                continue
            if neighbor == dest:
                return distance + 1
            seen.add(neighbor)
            queue.append((neighbor, distance + 1))
    return None


class AxisCoverageTracker:
    def __init__(self):
        self._ranges = []

    def ingest(self, center_twice):
        left = max(0, center_twice - 1)
        right = min(100, center_twice + 1)
        if left > right:
            return self._is_complete()

        merged = []
        inserted = False
        for start, end in self._ranges:
            if end < left:
                merged.append((start, end))
            elif right < start:
                if not inserted:
                    merged.append((left, right))
                    inserted = True
                merged.append((start, end))
            else:
                left = min(left, start)
                right = max(right, end)

        if not inserted:
            merged.append((left, right))
        self._ranges = merged
        return self._is_complete()

    def _is_complete(self):
        return len(self._ranges) == 1 and self._ranges[0] == (0, 100)


def minimax_divider(left_words, right_words, total_width):
    def line_count(words, width):
        if not words:
            return 0

        lines = 1
        used = 0
        for word in words:
            needed = len(word) if used == 0 else used + 1 + len(word)
            if needed <= width:
                used = needed
            else:
                lines += 1
                used = len(word)
        return lines

    left_minimum = max((len(word) for word in left_words), default=0)
    right_minimum = max((len(word) for word in right_words), default=0)
    low = left_minimum
    high = total_width - right_minimum
    if low > high:
        return -1

    def height(divider):
        return max(
            line_count(left_words, divider),
            line_count(right_words, total_width - divider),
        )

    search_low = low
    search_high = high
    while search_low < search_high:
        middle = (search_low + search_high) // 2
        if line_count(left_words, middle) <= line_count(
            right_words, total_width - middle
        ):
            search_high = middle
        else:
            search_low = middle + 1

    crossover = search_low
    candidates = [crossover]
    if crossover > low:
        candidates.append(crossover - 1)
    best_height = min(height(divider) for divider in candidates)

    search_low = low
    search_high = crossover
    while search_low < search_high:
        middle = (search_low + search_high) // 2
        if line_count(left_words, middle) <= best_height:
            search_high = middle
        else:
            search_low = middle + 1
    return search_low


def count_square_components(cells):
    grid = {(x, y): color for x, y, color in cells}
    unvisited = set(grid)
    squares = 0

    while unvisited:
        start = next(iter(unvisited))
        color = grid[start]
        queue = [start]
        unvisited.remove(start)
        component = []

        while queue:
            x, y = queue.pop()
            component.append((x, y))
            for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if neighbor in unvisited and grid[neighbor] == color:
                    unvisited.remove(neighbor)
                    queue.append(neighbor)

        min_x = min(x for x, _ in component)
        max_x = max(x for x, _ in component)
        min_y = min(y for _, y in component)
        max_y = max(y for _, y in component)
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        if width == height and len(component) == width * height:
            squares += 1

    return squares
