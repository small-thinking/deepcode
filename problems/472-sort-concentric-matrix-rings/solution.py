def sort_concentric_borders(matrix):
    n = len(matrix)
    result = [row[:] for row in matrix]
    for layer in range((n + 1) // 2):
        end = n - 1 - layer
        if layer == end:
            continue

        cells = []
        cells.extend((layer, col) for col in range(layer, end + 1))
        cells.extend((row, end) for row in range(layer + 1, end + 1))
        cells.extend((end, col) for col in range(end - 1, layer - 1, -1))
        cells.extend((row, layer) for row in range(end - 1, layer, -1))

        values = sorted(matrix[row][col] for row, col in cells)
        for (row, col), value in zip(cells, values):
            result[row][col] = value
    return result
