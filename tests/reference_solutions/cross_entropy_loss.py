import torch


def cross_entropy_loss(logits, targets, mask=None):
    if mask is not None:
        if not mask.any():
            raise ValueError("At least one included position is required")
        logits = logits[mask]
        targets = targets[mask]

    log_probs = torch.log_softmax(logits, dim=-1)
    selected = log_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    return -selected.mean()
