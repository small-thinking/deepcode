def flip_invert_smooth(image):
    rows, cols = len(image), len(image[0])
    transformed = [
        [1 - image[row][cols - 1 - col] for col in range(cols)]
        for row in range(rows)
    ]
    result = [[0] * cols for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            total = 0
            count = 0
            for neighbor_row in range(max(0, row - 1), min(rows, row + 2)):
                for neighbor_col in range(max(0, col - 1), min(cols, col + 2)):
                    total += transformed[neighbor_row][neighbor_col]
                    count += 1
            result[row][col] = total // count
    return result
