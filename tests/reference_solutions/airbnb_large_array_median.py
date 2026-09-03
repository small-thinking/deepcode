from random import randrange


def find_median(nums):
    size = len(nums)
    upper = _select(nums, size // 2)
    if size % 2:
        return float(upper)
    lower = _select(nums, size // 2 - 1)
    return (lower + upper) / 2.0


def _select(values, rank):
    left = 0
    right = len(values) - 1

    while left < right:
        pivot = values[randrange(left, right + 1)]
        lower = left
        current = left
        upper = right

        while current <= upper:
            if values[current] < pivot:
                values[lower], values[current] = values[current], values[lower]
                lower += 1
                current += 1
            elif values[current] > pivot:
                values[current], values[upper] = values[upper], values[current]
                upper -= 1
            else:
                current += 1

        if rank < lower:
            right = lower - 1
        elif rank > upper:
            left = upper + 1
        else:
            return values[rank]

    return values[left]
