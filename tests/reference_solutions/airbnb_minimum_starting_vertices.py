def minimum_starting_vertices(n, edges):
    outgoing = [[] for _ in range(n)]
    incoming = [[] for _ in range(n)]
    for source, target in edges:
        outgoing[source].append(target)
        incoming[target].append(source)

    # Record DFS finishing order without depending on Python's recursion limit.
    visited = [False] * n
    order = []
    for start in range(n):
        if visited[start]:
            continue
        visited[start] = True
        stack = [(start, iter(outgoing[start]))]
        while stack:
            node, neighbors = stack[-1]
            neighbor = next(neighbors, None)
            if neighbor is None:
                order.append(node)
                stack.pop()
            elif not visited[neighbor]:
                visited[neighbor] = True
                stack.append((neighbor, iter(outgoing[neighbor])))

    # Reverse traversal groups mutually reachable vertices into components.
    component = [-1] * n
    count = 0
    for start in reversed(order):
        if component[start] != -1:
            continue
        component[start] = count
        pending = [start]
        while pending:
            node = pending.pop()
            for neighbor in incoming[node]:
                if component[neighbor] == -1:
                    component[neighbor] = count
                    pending.append(neighbor)
        count += 1

    has_incoming = [False] * count
    for source, target in edges:
        if component[source] != component[target]:
            has_incoming[component[target]] = True
    return sum(not value for value in has_incoming)
