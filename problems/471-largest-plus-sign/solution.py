def largest_plus_sign(n, mines):
    blocked = {tuple(mine) for mine in mines}
    arm = [[n] * n for _ in range(n)]

    for row in range(n):
        run = 0
        for col in range(n):
            run = 0 if (row, col) in blocked else run + 1
            arm[row][col] = min(arm[row][col], run)
        run = 0
        for col in range(n - 1, -1, -1):
            run = 0 if (row, col) in blocked else run + 1
            arm[row][col] = min(arm[row][col], run)

    best = 0
    for col in range(n):
        run = 0
        for row in range(n):
            run = 0 if (row, col) in blocked else run + 1
            arm[row][col] = min(arm[row][col], run)
        run = 0
        for row in range(n - 1, -1, -1):
            run = 0 if (row, col) in blocked else run + 1
            arm[row][col] = min(arm[row][col], run)
            best = max(best, arm[row][col])
    return best
