from bisect import bisect_right
from collections import defaultdict, deque


def max_net_score(travel, points):
    rewards = {node: int(reward) for node, reward in points}
    graph = defaultdict(list)
    nodes = set(rewards)
    indegree = defaultdict(int)

    for source, cost, destination in travel:
        nodes.add(source)
        nodes.add(destination)
        graph[source].append((destination, int(cost)))
        indegree[destination] += 1
        indegree.setdefault(source, 0)

    ready = deque(node for node in nodes if indegree[node] == 0)
    order = []
    while ready:
        node = ready.popleft()
        order.append(node)
        for destination, _ in graph[node]:
            indegree[destination] -= 1
            if indegree[destination] == 0:
                ready.append(destination)

    scores = {"start": 0}
    for source in order:
        if source not in scores:
            continue
        for destination, cost in graph[source]:
            candidate = scores[source] + rewards.get(destination, 0) - cost
            if destination not in scores or candidate > scores[destination]:
                scores[destination] = candidate

    return max(score for node, score in scores.items() if node.startswith("END"))


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
