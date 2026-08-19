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


def _validate_timestamp(timestamp):
    if type(timestamp) not in (int, float):
        raise TypeError("timestamps must be finite int or float values")
    if not math.isfinite(timestamp):
        raise ValueError("timestamps must be finite")


def stack_samples_to_trace_events(samples, end_timestamp):
    _validate_timestamp(end_timestamp)
    try:
        sample_iterator = iter(samples)
    except TypeError as error:
        raise TypeError("samples must be iterable") from error

    events = []
    active = []
    previous_timestamp = None
    saw_sample = False

    for sample in sample_iterator:
        if not isinstance(sample, tuple) or len(sample) != 2:
            raise TypeError("each sample must be a (timestamp, stack) tuple")
        timestamp, stack = sample
        _validate_timestamp(timestamp)
        if previous_timestamp is not None and timestamp < previous_timestamp:
            raise ValueError("sample timestamps must be nondecreasing")
        if isinstance(stack, str):
            raise TypeError("stack must be a non-string sequence")
        if not isinstance(stack, (list, tuple)):
            raise TypeError("stack must be a non-string sequence")
        current = list(stack)
        for frame in current:
            if not isinstance(frame, str):
                raise TypeError("frame names must be strings")
            if not frame:
                raise ValueError("frame names must not be empty")

        common = 0
        while common < len(active) and common < len(current) and active[common] == current[common]:
            common += 1
        for frame in reversed(active[common:]):
            events.append({"name": frame, "phase": "E", "timestamp": timestamp})
        for frame in current[common:]:
            events.append({"name": frame, "phase": "B", "timestamp": timestamp})

        active = current
        previous_timestamp = timestamp
        saw_sample = True

    if not saw_sample:
        return []
    if end_timestamp < previous_timestamp:
        raise ValueError("end_timestamp precedes the final sample")
    for frame in reversed(active):
        events.append({"name": frame, "phase": "E", "timestamp": end_timestamp})
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
