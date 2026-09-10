"""Small reference implementations for the audited Coding contracts."""
from itertools import combinations


def zigzag_matrix_rows(matrix):
    return [value for index, row in enumerate(matrix) for value in (row if index % 2 == 0 else row[::-1])]


def select_group_listings(listings, group_size, target_neighborhood):
    eligible = [
        index
        for index, listing in enumerate(listings)
        if listing['neighborhood'] == target_neighborhood
    ]
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
    occupied = {}
    for task in sorted(tasks, key=lambda task: (-task['reward'], task['id'])):
        day = task['deadline']
        while day in occupied:
            day -= 1
        if day > 0:
            occupied[day] = task
    selected = [occupied[day] for day in sorted(occupied)]
    return [task['id'] for task in selected], sum(task['reward'] for task in selected)
