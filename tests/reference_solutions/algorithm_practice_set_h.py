from bisect import bisect_right
from collections import deque


def best_terminal_path(start, node_scores, edges):
    if hasattr(node_scores, "items"):
        scores = dict(node_scores.items())
    else:
        scores = dict(node_scores)

    if start not in scores:
        raise ValueError("start must have a node score")

    graph = {node: [] for node in scores}
    indegree = {node: 0 for node in scores}
    for edge in edges:
        try:
            source, destination, cost = edge
        except (TypeError, ValueError) as error:
            raise ValueError("each edge must be a (from_node, to_node, cost) triple") from error
        if source not in scores or destination not in scores:
            raise ValueError("every edge endpoint must have a node score")
        graph[source].append((destination, cost))
        indegree[destination] += 1

    ready = deque(node for node, degree in indegree.items() if degree == 0)
    order = []
    while ready:
        source = ready.popleft()
        order.append(source)
        for destination, _ in graph[source]:
            indegree[destination] -= 1
            if indegree[destination] == 0:
                ready.append(destination)

    if len(order) != len(scores):
        raise ValueError("graph must be a DAG")

    best_scores = {node: None for node in scores}
    parents = {start: None}
    best_scores[start] = scores[start]
    for source in order:
        if best_scores[source] is None:
            continue
        for destination, cost in graph[source]:
            candidate = best_scores[source] + scores[destination] - cost
            if best_scores[destination] is None or candidate > best_scores[destination]:
                best_scores[destination] = candidate
                parents[destination] = source

    terminals = [
        node
        for node, score in best_scores.items()
        if str(node).startswith("_") and score is not None
    ]
    if not terminals:
        return None, []

    end = max(terminals, key=best_scores.__getitem__)
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return best_scores[end], path


def job_scheduling(start_times, end_times, profits):
    jobs = sorted(zip(start_times, end_times, profits), key=lambda job: job[1])
    end_values = [end for _, end, _ in jobs]
    best = [0] * (len(jobs) + 1)

    for index, (start, _, profit) in enumerate(jobs, start=1):
        compatible_count = bisect_right(end_values, start, 0, index - 1)
        best[index] = max(best[index - 1], profit + best[compatible_count])
    return best[-1]


def find_installation_order(n, dependencies):
    graph = [[] for _ in range(n)]
    indegree = [0] * n
    for task, prerequisite in dependencies:
        graph[prerequisite].append(task)
        indegree[task] += 1

    ready = deque(task for task in range(n) if indegree[task] == 0)
    order = []
    while ready:
        task = ready.popleft()
        order.append(task)
        for dependent in graph[task]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
    return order if len(order) == n else []


def split_stays(listings, start_day, end_day):
    if start_day >= end_day:
        return []

    names = list(listings)
    availability = {name: set(days) for name, days in listings.items()}
    prefix_end = {}
    suffix_start = {}

    for name in names:
        days = availability[name]

        day = start_day
        while day <= end_day and day in days:
            day += 1
        prefix_end[name] = day - 1

        day = end_day
        while day >= start_day and day in days:
            day -= 1
        suffix_start[name] = day + 1

    plans = []
    for first_name in names:
        latest_split = min(end_day - 1, prefix_end[first_name])
        if latest_split < start_day:
            continue
        for second_name in names:
            if first_name == second_name:
                continue
            earliest_split = max(start_day, suffix_start[second_name] - 1)
            if earliest_split <= latest_split:
                plans.append([first_name, second_name])
    return plans
