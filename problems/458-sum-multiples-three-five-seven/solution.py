def sum_multiples(n: int) -> int:
    total = 0
    for value in range(1, n + 1):
        if value % 3 == 0 or value % 5 == 0 or value % 7 == 0:
            total += value
    return total
