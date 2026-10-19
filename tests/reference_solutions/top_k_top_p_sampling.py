import numpy as np


def sample_token(logits, top_k=None, top_p=1.0, temperature=1.0):
    values = np.asarray(logits, dtype=np.float64)
    # Stable descending order also breaks ties by original token index.
    ordered = np.argsort(-values, kind="stable")
    if top_k is not None and top_k > 0:
        ordered = ordered[:top_k]

    # Top-p uses probabilities normalized over the Top-k survivors.
    selected = values[ordered]
    with np.errstate(over="ignore", under="ignore"):
        scaled = selected / temperature
        if not np.isfinite(scaled).all():
            scaled = (selected - selected.max()) / temperature
        weights = np.exp(scaled - scaled.max())
    probabilities = weights / weights.sum()
    count = len(ordered)
    if top_p < 1.0:
        count = min(
            count,
            int(np.searchsorted(np.cumsum(probabilities), top_p, side="left")) + 1,
        )
    kept = ordered[:count]
    kept_probabilities = probabilities[:count]
    kept_probabilities = kept_probabilities / kept_probabilities.sum()
    return int(np.random.choice(kept, p=kept_probabilities))


def top_k_sample(logits, top_k, temperature=1.0):
    return sample_token(logits, top_k=top_k, temperature=temperature)


def top_p_sample(logits, top_p, temperature=1.0):
    return sample_token(logits, top_p=top_p, temperature=temperature)
