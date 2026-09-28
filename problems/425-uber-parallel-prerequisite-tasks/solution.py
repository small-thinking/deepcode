from collections import deque


def solution(n, deps):
    assert n >= 0
    followers = [[] for _ in range(n + 1)]
    indegree = [0] * (n + 1)
    for a, b in set(map(tuple, deps)):
        assert 1 <= a <= n and 1 <= b <= n
        followers[a].append(b)
        indegree[b] += 1

    ready = deque(task for task in range(1, n + 1) if indegree[task] == 0)
    finish = [1] * (n + 1)
    completed = 0
    while ready:
        task = ready.popleft()
        completed += 1
        for child in followers[task]:
            finish[child] = max(finish[child], finish[task] + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    return max(finish[1:], default=0) if completed == n else -1
