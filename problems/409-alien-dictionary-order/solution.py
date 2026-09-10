import heapq


def alien_order(words):
    graph = {char: set() for word in words for char in word}
    indegree = {char: 0 for char in graph}

    for first, second in zip(words, words[1:]):
        if len(first) > len(second) and first.startswith(second):
            return ""
        for left, right in zip(first, second):
            if left == right:
                continue
            if right not in graph[left]:
                graph[left].add(right)
                indegree[right] += 1
            break

    ready = [char for char, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        char = heapq.heappop(ready)
        order.append(char)
        for neighbor in graph[char]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                heapq.heappush(ready, neighbor)
    return "" if len(order) != len(graph) else "".join(order)
