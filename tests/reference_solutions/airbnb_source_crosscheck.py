import heapq


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


def minimum_number(digits):
    counts = [0] * 10
    for digit in digits:
        if isinstance(digit, bool) or not isinstance(digit, int) or not 0 <= digit <= 9:
            raise ValueError("digits must be integers from 0 through 9")
        counts[digit] += 1

    for first in range(1, 10):
        if counts[first]:
            counts[first] -= 1
            return str(first) + "0" * counts[0] + "".join(
                str(digit) * counts[digit] for digit in range(1, 10)
            )
    raise ValueError("digits must contain at least one nonzero digit")
