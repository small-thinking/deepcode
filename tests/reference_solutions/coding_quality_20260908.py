"""Small reference implementations for the audited Coding contracts."""
import heapq
from itertools import combinations


def zigzag_matrix_rows(matrix):
    return [value for index, row in enumerate(matrix) for value in (row if index % 2 == 0 else row[::-1])]


def select_group_listings(listings, group_size, neighborhood):
    eligible = [index for index, listing in enumerate(listings) if listing['neighborhood'] == neighborhood]
    for count in range(len(eligible) + 1):
        feasible = []
        for indices in combinations(eligible, count):
            capacity = sum(listings[index]['capacity'] for index in indices)
            if capacity >= group_size:
                feasible.append((capacity, indices))
        if feasible:
            _, selected = min(feasible)
            return [listings[index]['id'] for index in selected]
    return []


def deadline_reward_schedule(tasks):
    selected = []
    for task_id, deadline, reward in sorted(tasks, key=lambda task: task[1]):
        heapq.heappush(selected, (reward, task_id, deadline))
        if len(selected) > deadline:
            heapq.heappop(selected)
    scheduled = sorted(selected, key=lambda task: (task[2], task[1]))
    return [task_id for _, task_id, _ in scheduled], sum(
        reward for reward, _, _ in scheduled
    )
