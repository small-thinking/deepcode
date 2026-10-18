from collections import Counter


def consensus_labels(labels, excluded=()):
    excluded = set(excluded)
    result = []
    for row in labels:
        values = [value for index, value in enumerate(row) if index not in excluded and value is not None]
        if not values:
            result.append(None)
            continue
        counts = Counter(values)
        result.append(next(value for value in values if counts[value] == max(counts.values())))
    return result


def agreement_rates(labels, min_labels=1):
    width = len(labels[0]) if labels else 0
    consensus = consensus_labels(labels)
    rates = []
    for index in range(width):
        observed = [row[index] == consensus[row_index] for row_index, row in enumerate(labels) if row[index] is not None and sum(value is not None for value in row) >= min_labels and consensus[row_index] is not None]
        rates.append(sum(observed) / len(observed) if observed else 1.0)
    return rates


def select_rejected_annotators(labels, threshold=0.7, min_labels=1, max_removed_fraction=0.5, min_remaining=1):
    width = len(labels[0]) if labels else 0
    capacity = min(int(width * max_removed_fraction), max(0, width - min_remaining))
    candidates = [index for index, rate in enumerate(agreement_rates(labels, min_labels)) if rate < threshold]
    return candidates[:capacity]


def mask_annotators(labels, rejected):
    rejected = set(rejected)
    return [[None if index in rejected else value for index, value in enumerate(row)] for row in labels]
