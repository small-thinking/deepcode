import math


def triangle_flags(sides):
    return [
        int(a + b > c and a + c > b and b + c > a)
        for a, b, c in zip(sides, sides[1:], sides[2:])
    ]


def closest_pair_distance(points):
    by_x = sorted((x, y) for x, y in points)
    if any(first == second for first, second in zip(by_x, by_x[1:])):
        return 0.0

    by_y = by_x.copy()
    scratch = [None] * len(by_x)

    def squared_distance(first, second):
        return (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2

    def solve(left, right):
        if right - left <= 3:
            best = math.inf
            for i in range(left, right):
                for j in range(i + 1, right):
                    best = min(best, squared_distance(by_x[i], by_x[j]))
            by_y[left:right] = sorted(by_y[left:right], key=lambda point: point[1])
            return best

        middle = (left + right) // 2
        middle_x = by_x[middle][0]
        best = min(solve(left, middle), solve(middle, right))

        i, j, output = left, middle, left
        while i < middle and j < right:
            if by_y[i][1] <= by_y[j][1]:
                scratch[output] = by_y[i]
                i += 1
            else:
                scratch[output] = by_y[j]
                j += 1
            output += 1
        while i < middle:
            scratch[output] = by_y[i]
            i += 1
            output += 1
        while j < right:
            scratch[output] = by_y[j]
            j += 1
            output += 1
        by_y[left:right] = scratch[left:right]

        strip = []
        for point in by_y[left:right]:
            if (point[0] - middle_x) ** 2 >= best:
                continue
            for other in reversed(strip):
                if (point[1] - other[1]) ** 2 >= best:
                    break
                best = min(best, squared_distance(point, other))
            strip.append(point)
        return best

    return math.sqrt(solve(0, len(by_x)))
