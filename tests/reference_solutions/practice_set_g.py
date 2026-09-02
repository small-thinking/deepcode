def best_capacity_subset(properties, group_size, neighborhood=None):
    if group_size < 0:
        raise ValueError("group_size must be nonnegative")

    indexed = list(enumerate(properties))
    for _, property_ in indexed:
        if property_["capacity"] < 0:
            raise ValueError("capacities must be nonnegative")

    eligible = [
        (index, property_)
        for index, property_ in indexed
        if neighborhood is None or property_.get("neighborhood") == neighborhood
    ]
    if group_size == 0:
        return []

    best_key = None
    best_indices = ()
    for subset in range(1 << len(eligible)):
        total = 0
        indices = []
        for position, (index, property_) in enumerate(eligible):
            if subset & (1 << position):
                total += property_["capacity"]
                indices.append(index)
        if total < group_size:
            continue
        key = (total, len(indices), tuple(indices))
        if best_key is None or key < best_key:
            best_key = key
            best_indices = tuple(indices)

    return [properties[index] for index in best_indices]


def smallest_number(digits, lower_bound=None):
    counts = [0] * 10
    for digit in digits:
        if isinstance(digit, bool) or not isinstance(digit, int) or not 0 <= digit <= 9:
            raise ValueError("digits must be integers from 0 through 9")
        counts[digit] += 1

    if lower_bound is None:
        result = "".join(str(digit) * counts[digit] for digit in range(1, 10))
        return result or "0"

    if isinstance(lower_bound, bool) or not isinstance(lower_bound, int) or lower_bound < 0:
        raise ValueError("lower_bound must be a nonnegative integer")
    if sum(counts[1:]) == 0:
        return "0" if lower_bound == 0 else "-1"

    digit_count = sum(counts)
    bound = str(lower_bound)
    if len(bound) > digit_count:
        return "-1"

    def sorted_remainder():
        return "".join(
            str(digit) * counts[digit]
            for digit in range(10)
        )

    def smallest_unconstrained():
        for first in range(1, 10):
            if counts[first]:
                counts[first] -= 1
                result = str(first) + sorted_remainder()
                counts[first] += 1
                return result
        return "-1"

    if len(bound) < digit_count:
        return smallest_unconstrained()

    def search(position):
        if position == digit_count:
            return ""
        required = int(bound[position])
        for digit in range(required, 10):
            if not counts[digit] or (position == 0 and digit == 0):
                continue
            counts[digit] -= 1
            if digit > required:
                suffix = sorted_remainder()
            else:
                suffix = search(position + 1)
            counts[digit] += 1
            if suffix is not None:
                return str(digit) + suffix
        return None

    result = search(0)
    return result if result is not None else "-1"


def format_articles(articles, width):
    if width <= 0:
        raise ValueError("width must be positive")

    punctuation = set(".,;:!?")
    result = []
    for article_index, article in enumerate(articles):
        line_parts = []
        line_length = 0
        for word in article.split():
            if line_parts and word[0] in punctuation:
                line_parts.append(word)
                line_length += 1 + len(word)
            elif not line_parts:
                line_parts = [word]
                line_length = len(word)
            elif line_length + 1 + len(word) <= width:
                line_parts.append(word)
                line_length += 1 + len(word)
            else:
                result.append(" ".join(line_parts))
                line_parts = [word]
                line_length = len(word)

        if line_parts:
            result.append(" ".join(line_parts))
        if article_index != len(articles) - 1:
            result.append("----")
    return result
