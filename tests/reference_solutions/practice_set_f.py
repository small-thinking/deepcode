from decimal import Decimal
from urllib.parse import unquote


def _tenths(value):
    scaled = Decimal(str(value)) * 10
    if scaled != scaled.to_integral_value():
        raise ValueError("values must have at most one decimal place")
    return int(scaled)


def min_exact_items(durations, target):
    target_units = _tenths(target)
    if target_units < 0:
        raise ValueError("target must be nonnegative")
    if target_units == 0:
        return 0

    usable = set()
    for duration in durations:
        units = _tenths(duration)
        if units <= 0:
            raise ValueError("durations must be positive")
        if units <= target_units:
            usable.add(units)

    best = [target_units + 1] * (target_units + 1)
    best[0] = 0
    for subtotal in range(1, target_units + 1):
        for units in usable:
            if units <= subtotal:
                best[subtotal] = min(best[subtotal], best[subtotal - units] + 1)
    return 0 if best[target_units] > target_units else best[target_units]


def intersect(head_a, head_b):
    reachable_from_a = set()
    node = head_a
    while node is not None and id(node) not in reachable_from_a:
        reachable_from_a.add(id(node))
        node = node.next

    seen_b = set()
    node = head_b
    while node is not None and id(node) not in seen_b:
        if id(node) in reachable_from_a:
            return True
        seen_b.add(id(node))
        node = node.next
    return False


def parse_query(url):
    clean_url = url.split("#", 1)[0]
    if "?" not in clean_url:
        return {}

    result = {}
    for segment in clean_url.split("?", 1)[1].split("&"):
        if not segment:
            continue
        if "=" in segment:
            raw_key, raw_value = segment.split("=", 1)
            value = unquote(raw_value)
        else:
            raw_key = segment
            value = True
        key = unquote(raw_key)
        if key not in result:
            result[key] = value
        elif isinstance(result[key], list):
            result[key].append(value)
        else:
            result[key] = [result[key], value]
    return result


def minimum_cover(menu, wanted):
    bundles = list(menu)
    bit_for = {}
    for item in wanted:
        if item not in bit_for:
            bit_for[item] = 1 << len(bit_for)

    full_mask = (1 << len(bit_for)) - 1
    if full_mask == 0:
        return 0, []

    useful = []
    for index, (items, price) in enumerate(bundles):
        if price < 0:
            raise ValueError("prices must be nonnegative")
        mask = 0
        for item in items:
            mask |= bit_for.get(item, 0)
        if mask:
            useful.append((index, mask, price))

    zero_counts = (0,) * len(bundles)
    states = {0: (0, zero_counts)}
    for covered in range(full_mask + 1):
        state = states.get(covered)
        if state is None:
            continue
        cost, counts = state
        for index, bundle_mask, price in useful:
            next_covered = covered | bundle_mask
            if next_covered == covered:
                continue
            next_counts = list(counts)
            next_counts[index] = 1
            candidate = (cost + price, tuple(next_counts))
            existing = states.get(next_covered)
            if existing is None or candidate < existing:
                states[next_covered] = candidate

    result = states.get(full_mask)
    if result is None:
        return -1, []
    cost, counts = result
    return cost, [(index, 1) for index, count in enumerate(counts) if count]
