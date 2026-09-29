import math
from collections import Counter


def reduce_shard_statistics(shards):
    counts = Counter()
    total = 0

    try:
        shard_iterator = iter(shards)
    except TypeError as error:
        raise TypeError("shards must be an iterable of iterables") from error

    for shard in shard_iterator:
        try:
            values = iter(shard)
        except TypeError as error:
            raise TypeError("each shard must be iterable") from error
        for value in values:
            if type(value) is not int:
                raise TypeError("observations must be integers, not booleans")
            counts[value] += 1
            total += 1

    if total == 0:
        raise ValueError("at least one observation is required")

    largest_count = max(counts.values())
    mode = min(value for value, count in counts.items() if count == largest_count)
    lower_rank = (total - 1) // 2
    upper_rank = total // 2
    lower_value = upper_value = None
    seen = 0

    for value in sorted(counts):
        seen += counts[value]
        if lower_value is None and seen > lower_rank:
            lower_value = value
        if seen > upper_rank:
            upper_value = value
            break

    return mode, (lower_value + upper_value) / 2.0


def tokenize_longest_match(text, vocabulary, unknown="<UNK>"):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(unknown, str):
        raise TypeError("unknown must be a string")
    if not unknown:
        raise ValueError("unknown must not be empty")
    if isinstance(vocabulary, str):
        raise TypeError("vocabulary must be an iterable of token strings")

    try:
        tokens = iter(vocabulary)
    except TypeError as error:
        raise TypeError("vocabulary must be iterable") from error

    end = object()
    trie = {}
    for token in tokens:
        if not isinstance(token, str):
            raise TypeError("vocabulary tokens must be strings")
        if not token:
            raise ValueError("vocabulary tokens must not be empty")
        node = trie
        for character in token:
            node = node.setdefault(character, {})
        node[end] = token

    output = []
    start = 0
    while start < len(text):
        node = trie
        best_token = None
        end_index = start
        cursor = start
        while cursor < len(text) and text[cursor] in node:
            node = node[text[cursor]]
            cursor += 1
            if end in node:
                best_token = node[end]
                end_index = cursor
        if best_token is None:
            output.append(unknown)
            start += 1
        else:
            output.append(best_token)
            start = end_index
    return output


def stack_samples_to_trace_events(samples, min_samples=1):
    if type(min_samples) is not int or min_samples <= 0:
        raise ValueError("min_samples must be a positive integer")

    events = []
    active = []
    streaks = []
    for timestamp, stack in samples:
        current = list(stack)
        common = 0
        while common < min(len(active), len(current)) and active[common] == current[common]:
            common += 1

        for depth in range(len(active) - 1, common - 1, -1):
            if streaks[depth] >= min_samples:
                events.append({"name": active[depth], "phase": "E", "timestamp": timestamp})

        streaks = [min(count + 1, min_samples + 1) for count in streaks[:common]]
        streaks.extend([1] * (len(current) - common))
        for depth, frame in enumerate(current):
            if streaks[depth] == min_samples:
                events.append({"name": frame, "phase": "B", "timestamp": timestamp})
        active = current
    return events


def matmul_arithmetic_intensity(m, n, k, element_bytes=4):
    for value in (m, n, k, element_bytes):
        if type(value) is not int:
            raise TypeError("dimensions and element_bytes must be integers, not booleans")
        if value <= 0:
            raise ValueError("dimensions and element_bytes must be positive")

    flops = 2 * m * n * k
    transferred_bytes = element_bytes * (m * k + k * n + m * n)
    return flops / transferred_bytes
