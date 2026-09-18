def k_medians(points, k):
    def distance(point, center):
        return abs(point[0] - center[0]) + abs(point[1] - center[1])

    def coordinate_median(cluster):
        xs = sorted(point[0] for point in cluster)
        ys = sorted(point[1] for point in cluster)
        middle = (len(cluster) - 1) // 2
        return xs[middle], ys[middle]

    centers = [points[0]]
    selected_indices = {0}
    while len(centers) < k:
        _, negated_index = max(
            (min(distance(point, center) for center in centers), -index)
            for index, point in enumerate(points)
            if index not in selected_indices
        )
        next_index = -negated_index
        selected_indices.add(next_index)
        centers.append(points[next_index])
        centers.sort()

    seen = set()
    while tuple(centers) not in seen:
        seen.add(tuple(centers))
        clusters = [[] for _ in centers]
        for point in points:
            nearest = min(range(k), key=lambda index: (distance(point, centers[index]), index))
            clusters[nearest].append(point)
        updated = [
            coordinate_median(cluster) if cluster else centers[index]
            for index, cluster in enumerate(clusters)
        ]
        updated.sort()
        if updated == centers:
            break
        centers = updated

    total_cost = sum(min(distance(point, center) for center in centers) for point in points)
    return centers, total_cost
