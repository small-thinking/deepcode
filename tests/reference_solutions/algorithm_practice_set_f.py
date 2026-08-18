from collections import defaultdict, deque


def find_split_pairs(listings, start_day, end_day):
    if start_day >= end_day:
        return []

    names = sorted(listings)
    available = {name: set(days) for name, days in listings.items()}
    prefix_end = {}
    suffix_start = {}

    for name in names:
        days = available[name]

        day = start_day
        while day <= end_day and day in days:
            day += 1
        prefix_end[name] = day - 1

        day = end_day
        while day >= start_day and day in days:
            day -= 1
        suffix_start[name] = day + 1

    pairs = []
    for first_index, first_name in enumerate(names):
        for second_name in names[first_index + 1 :]:
            first_then_second = max(start_day, suffix_start[second_name] - 1) <= min(
                end_day - 1, prefix_end[first_name]
            )
            second_then_first = max(start_day, suffix_start[first_name] - 1) <= min(
                end_day - 1, prefix_end[second_name]
            )
            if first_then_second or second_then_first:
                pairs.append((first_name, second_name))
    return pairs


def pour_and_render(heights, units, source):
    water = [0] * len(heights)

    def resting_height(index):
        return heights[index] + water[index]

    for _ in range(units):
        source_height = resting_height(source)

        left_minimum = None
        index = source - 1
        while index >= 0 and resting_height(index) < source_height:
            value = resting_height(index)
            left_minimum = value if left_minimum is None else min(left_minimum, value)
            index -= 1

        right_minimum = None
        index = source + 1
        while index < len(heights) and resting_height(index) < source_height:
            value = resting_height(index)
            right_minimum = value if right_minimum is None else min(right_minimum, value)
            index += 1

        if left_minimum is None and right_minimum is None:
            water[source] += 1
            continue

        direction = -1 if right_minimum is None or (
            left_minimum is not None and left_minimum <= right_minimum
        ) else 1
        position = source
        next_position = position + direction
        while 0 <= next_position < len(heights) and resting_height(next_position) < resting_height(position):
            position = next_position
            next_position = position + direction
        water[position] += 1

    final_heights = [height + added_water for height, added_water in zip(heights, water)]
    rows = []
    for row in range(max(final_heights, default=0), 0, -1):
        cells = []
        for index, height in enumerate(heights):
            if row <= height:
                cells.append("+")
            elif row <= final_heights[index]:
                cells.append("W")
            else:
                cells.append(" ")
        rows.append("".join(cells).rstrip())
    return "\n".join(rows)


def find_duplicate_indices(records):
    claimed = defaultdict(set)
    duplicates = []

    for index, record in enumerate(records):
        if any(value in claimed[field] for field, value in record.items()):
            duplicates.append(index)
            continue
        for field, value in record.items():
            claimed[field].add(value)

    return duplicates


def board_score(grid):
    if not grid or not grid[0]:
        return 0

    rows = len(grid)
    columns = len(grid[0])
    visited = [[False] * columns for _ in range(rows)]
    total = 0

    for start_row in range(rows):
        for start_column in range(columns):
            if visited[start_row][start_column]:
                continue

            terrain = grid[start_row][start_column][0]
            queue = deque([(start_row, start_column)])
            visited[start_row][start_column] = True
            cell_count = 0
            crown_total = 0

            while queue:
                row, column = queue.popleft()
                cell_count += 1
                crown_total += int(grid[row][column][1])

                for row_delta, column_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = row + row_delta
                    next_column = column + column_delta
                    if (
                        0 <= next_row < rows
                        and 0 <= next_column < columns
                        and not visited[next_row][next_column]
                        and grid[next_row][next_column][0] == terrain
                    ):
                        visited[next_row][next_column] = True
                        queue.append((next_row, next_column))

            total += cell_count * crown_total

    return total
