def k_medoids(points, k):
    n = len(points)
    if not n:
        return [], 0
    def cost(indices):
        return sum(min(abs(x-points[j][0]) + abs(y-points[j][1])
                       for j in indices) for x, y in points)
    selected = []
    for _ in range(min(k, n)):
        _, selected = min((cost(selected + [j]), sorted(selected + [j]))
                          for j in range(n) if j not in selected)
    current = cost(selected)
    while True:
        candidates = [(cost(trial), trial)
                      for old in selected for new in range(n) if new not in selected
                      for trial in [sorted([j for j in selected if j != old] + [new])]]
        best_cost, best = min(candidates, default=(current, selected))
        if best_cost >= current:
            return selected, current
        selected, current = best, best_cost
