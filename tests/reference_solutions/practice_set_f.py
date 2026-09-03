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


def minimum_menu_order_cost(menu, userWants):
    bit_for = {item: 1 << index for index, item in enumerate(userWants)}
    if not bit_for:
        return [[]]

    full_mask = (1 << len(bit_for)) - 1
    epsilon = 1e-6
    states = {0: (0.0, {()})}

    for index, (_, raw_price, item_names) in enumerate(menu):
        bundle_mask = 0
        for item in item_names.split(","):
            bundle_mask |= bit_for.get(item.strip(), 0)
        if not bundle_mask:
            continue

        price = float(raw_price)
        next_states = {
            covered: (cost, set(combinations))
            for covered, (cost, combinations) in states.items()
        }
        for covered, (cost, combinations) in states.items():
            next_covered = covered | bundle_mask
            if next_covered == covered:
                continue

            candidate_cost = cost + price
            candidate_combinations = {
                combination + (index,)
                for combination in combinations
            }
            existing = next_states.get(next_covered)
            if existing is None or candidate_cost < existing[0] - epsilon:
                next_states[next_covered] = (candidate_cost, candidate_combinations)
            elif abs(candidate_cost - existing[0]) <= epsilon:
                existing[1].update(candidate_combinations)
        states = next_states

    result = states.get(full_mask)
    if result is None:
        return []

    _, combinations = result
    return [
        [menu[index][0] for index in combination]
        for combination in sorted(combinations)
    ]
