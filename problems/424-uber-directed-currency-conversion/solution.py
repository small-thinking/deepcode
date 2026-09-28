def solution(pairs, ratios, src, dst):
    assert len(pairs) == len(ratios)
    if src == dst:
        return 1.0

    graph = {}
    for (start, end), ratio in zip(pairs, ratios):
        assert ratio > 0
        graph.setdefault(start, []).append((end, ratio))

    stack = [(src, 1.0)]
    seen = {src}
    while stack:
        currency, value = stack.pop()
        for neighbor, ratio in graph.get(currency, ()):
            if neighbor in seen:
                continue
            converted = value * ratio
            if neighbor == dst:
                return converted
            seen.add(neighbor)
            stack.append((neighbor, converted))
    return -1.0
