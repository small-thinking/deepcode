def find_route(api):
    start = api.current()
    if api.is_goal():
        return [start]

    visited = {start}
    route = [start]

    def backtrack_to(parent):
        for direction, destination in api.neighbors().items():
            if destination == parent:
                api.move(direction)
                return
        raise RuntimeError("maze edge has no reverse move")

    def dfs():
        current = api.current()
        for direction, destination in api.neighbors().items():
            if destination in visited:
                continue
            api.move(direction)
            visited.add(destination)
            route.append(destination)
            if api.is_goal():
                return route.copy()

            found = dfs()
            if found is not None:
                return found

            backtrack_to(current)
            route.pop()
        return None

    return dfs()


def generate_grid(rows, cols, rng):
    if rows <= 0 or cols <= 0 or (rows * cols) % 4:
        raise ValueError("rows and cols must have positive area divisible by four")

    labels = [1, 2, 3, 4]
    rng.shuffle(labels)
    cells = []
    for row in range(rows):
        columns = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
        cells.extend((row, column) for column in columns)

    grid = [[0] * cols for _ in range(rows)]
    quota = rows * cols // 4
    for index, (row, column) in enumerate(cells):
        grid[row][column] = labels[index // quota]
    return grid


def build_expression(values, target):
    dead_states = set()

    def search(items):
        key = tuple(sorted(value for value, _ in items))
        if key in dead_states:
            return None
        if len(items) == 1:
            value, expression = items[0]
            return expression if value == target else None

        for left_index in range(len(items)):
            for right_index in range(left_index + 1, len(items)):
                left_value, left_expression = items[left_index]
                right_value, right_expression = items[right_index]
                rest = [
                    item
                    for index, item in enumerate(items)
                    if index not in {left_index, right_index}
                ]
                candidates = (
                    (
                        left_value + right_value,
                        f"({left_expression}+{right_expression})",
                    ),
                    (
                        left_value - right_value,
                        f"({left_expression}-{right_expression})",
                    ),
                    (
                        right_value - left_value,
                        f"({right_expression}-{left_expression})",
                    ),
                    (
                        left_value * right_value,
                        f"({left_expression}*{right_expression})",
                    ),
                )
                tried_values = set()
                for value, expression in candidates:
                    if value in tried_values:
                        continue
                    tried_values.add(value)
                    result = search(rest + [(value, expression)])
                    if result is not None:
                        return result

        dead_states.add(key)
        return None

    return search([(value, str(value)) for value in values])


def contains_nearby_almost_duplicate(nums, index_gap, value_gap):
    if index_gap <= 0:
        return False

    width = value_gap + 1
    buckets = {}
    for index, value in enumerate(nums):
        if index > index_gap:
            outgoing = nums[index - index_gap - 1]
            del buckets[outgoing // width]

        bucket = value // width
        if bucket in buckets:
            return True
        for neighbor in (bucket - 1, bucket + 1):
            if neighbor in buckets and abs(value - buckets[neighbor]) <= value_gap:
                return True
        buckets[bucket] = value
    return False


def decode_suffix_repeats(text):
    stack = [[]]
    index = 0
    while index < len(text):
        character = text[index]
        if character == "(":
            stack.append([])
            index += 1
        elif character == ")":
            group = stack.pop()
            index += 1
            count = 1
            if index < len(text) and text[index] == "{":
                index += 1
                start = index
                while text[index].isdigit():
                    index += 1
                count = int(text[start:index])
                index += 1
            stack[-1].extend(group * count)
        else:
            stack[-1].append(character)
            index += 1
    return "".join(stack[0])
