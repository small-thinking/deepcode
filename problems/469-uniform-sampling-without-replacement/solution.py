def sample_without_replacement(items, k, rng):
    """Return a uniform size-k sample, using k draws and swaps."""
    n = len(items)
    for i in range(k):
        j = i + rng.randrange(n - i)
        items[i], items[j] = items[j], items[i]
    return items[:k]
