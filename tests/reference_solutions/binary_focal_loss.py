import torch


def binary_focal_loss(labels, probabilities, alpha=0.25, gamma=2.0, reduction="mean"):
    positive = labels == 1
    alpha_t = torch.where(positive, probabilities.new_tensor(alpha),
                          probabilities.new_tensor(1 - alpha))
    # log1p retains precision for an easy negative whose probability is tiny.
    log_p_t = torch.where(positive, probabilities.log(), torch.log1p(-probabilities))
    one_minus_p_t = torch.where(positive, 1 - probabilities, probabilities)
    losses = -alpha_t * one_minus_p_t.pow(gamma) * log_p_t
    if reduction == "none":
        return losses
    if reduction == "sum":
        return losses.sum()
    return losses.mean()
