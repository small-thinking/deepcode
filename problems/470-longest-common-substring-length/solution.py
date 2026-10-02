def longest_common_substring_length(first, second):
    previous = [0] * (len(second) + 1)
    best = 0
    for char_a in first:
        current = [0] * (len(second) + 1)
        for j, char_b in enumerate(second, start=1):
            if char_a == char_b:
                current[j] = previous[j - 1] + 1
                best = max(best, current[j])
        previous = current
    return best
