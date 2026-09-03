from bisect import bisect_right
from collections import deque
from numbers import Number


def max_ski_score(travel, points):
    try:
        travel = list(travel)
        points = list(points)
    except TypeError as error:
        raise ValueError("travel and points must be iterable") from error

    rewards = {}
    for point in points:
        try:
            node, reward = point
        except (TypeError, ValueError) as error:
            raise ValueError("each point must be a (node, reward) pair") from error
        if (
            not isinstance(node, str)
            or node == "START"
            or node in rewards
            or not isinstance(reward, Number)
            or isinstance(reward, bool)
        ):
            raise ValueError("points must give each non-START node one numeric reward")
        rewards[node] = reward

    graph = {"START": []}
    indegree = {"START": 0}
    for node in rewards:
        graph[node] = []
        indegree[node] = 0

    for edge in travel:
        try:
            source, cost, destination = edge
        except (TypeError, ValueError) as error:
            raise ValueError("each travel record must be a (from_node, cost, to_node) triple") from error
        if (
            not isinstance(source, str)
            or not isinstance(destination, str)
            or source not in graph
            or destination not in graph
            or not isinstance(cost, Number)
            or isinstance(cost, bool)
            or cost < 0
        ):
            raise ValueError("travel must use known nodes and non-negative numeric costs")
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

    if len(order) != len(graph):
        raise ValueError("graph must be a DAG")

    best_scores = {"START": 0}
    for source in order:
        if source not in best_scores:
            continue
        for destination, cost in graph[source]:
            candidate = best_scores[source] + rewards[destination] - cost
            if destination not in best_scores or candidate > best_scores[destination]:
                best_scores[destination] = candidate

    terminal_scores = [
        score for node, score in best_scores.items() if node.startswith("END")
    ]
    return max(terminal_scores, default=None)


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
