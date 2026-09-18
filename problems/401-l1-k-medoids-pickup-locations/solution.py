from itertools import combinations


def k_medoids(points, k):

    n = len(points)
    if not n:
        return [], 0

    def cost(indices):
        return sum(min(abs(x - points[j][0]) + abs(y - points[j][1])
                       for j in indices) for x, y in points)

    candidates = combinations(range(n), min(k, n))
    best_cost, best = min((cost(indices), indices) for indices in candidates)
    return list(best), best_cost
