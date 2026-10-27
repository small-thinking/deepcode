import torch


def _logits_tensor(logits):
    values = torch.as_tensor(logits)
    if not values.is_floating_point():
        values = values.to(torch.get_default_dtype())
    if values.ndim != 1 or values.numel() == 0:
        raise ValueError("logits must be a non-empty 1D input")
    return values


def entropy_from_logits(logits):
    values = _logits_tensor(logits)
    shifted = values - values.max()
    weights = shifted.exp()
    total = weights.sum()
    return total.log() - (weights * shifted).sum() / total


def streaming_entropy(blocks):
    maximum = total = moment = None
    for block in blocks:
        values = _logits_tensor(block)
        if maximum is not None and (values.dtype != maximum.dtype or values.device != maximum.device):
            raise ValueError("blocks must share dtype and device")
        block_maximum = values.max()
        new_maximum = block_maximum if maximum is None else torch.maximum(maximum, block_maximum)
        shifted = values - new_maximum
        weights = shifted.exp()
        block_total = weights.sum()
        block_moment = (weights * shifted).sum()
        if maximum is None:
            total, moment = block_total, block_moment
        else:
            delta = maximum - new_maximum
            rescale = delta.exp()
            # Center the weighted moment at the running maximum to avoid
            # subtracting two huge, nearly equal raw-logit expectations.
            moment = rescale * (moment + delta * total) + block_moment
            total = rescale * total + block_total
        maximum = new_maximum
    if maximum is None:
        raise ValueError("blocks must contain at least one block")
    return total.log() - moment / total
