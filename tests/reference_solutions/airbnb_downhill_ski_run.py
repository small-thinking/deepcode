def downhill_run_scores(elevations, starts):
    if not elevations or not elevations[0]:
        raise ValueError("elevations must be nonempty")

    rows = len(elevations)
    columns = len(elevations[0])
    if any(len(row) != columns for row in elevations):
        raise ValueError("elevations must be rectangular")

    for row, column in starts:
        if not 0 <= row < rows or not 0 <= column < columns:
            raise ValueError("start must be in bounds")

    best_from = {}

    def best(row, column):
        if (row, column) in best_from:
            return best_from[(row, column)]

        result = 1
        for next_row, next_column in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            if (
                0 <= next_row < rows
                and 0 <= next_column < columns
                and elevations[next_row][next_column] < elevations[row][column]
            ):
                result = max(result, 1 + best(next_row, next_column))

        best_from[(row, column)] = result
        return result

    return [best(row, column) for row, column in starts]
