import torch


def sample_token(logits, top_k=None, top_p=1.0, temperature=1.0):
    ordered = torch.argsort(logits, descending=True, stable=True)
    if top_k is not None and top_k > 0:
        ordered = ordered[:top_k]
    selected = logits[ordered].to(torch.float64)
    scaled = selected / temperature
    if not torch.isfinite(scaled).all():
        scaled = (selected - selected.max()) / temperature
    probabilities = torch.softmax(scaled, dim=-1)
    count = ordered.numel()
    if top_p < 1.0:
        count = min(count, int((probabilities.cumsum(0) < top_p).sum().item()) + 1)
    kept_probs = probabilities[:count]
    kept_probs = kept_probs / kept_probs.sum()
    sampled = torch.multinomial(kept_probs, 1)
    return int(ordered[sampled].item())


def top_k_sample(logits, top_k, temperature=1.0):
    return sample_token(logits, top_k=top_k, temperature=temperature)


def top_p_sample(logits, top_p, temperature=1.0):
    return sample_token(logits, top_p=top_p, temperature=temperature)
