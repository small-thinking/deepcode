import math

import torch


def grouped_query_attention(query, key, value):
    try:
        tensors = [torch.as_tensor(x) for x in (query, key, value)]
        query, key, value = [x if x.is_floating_point() else x.to(torch.get_default_dtype()) for x in tensors]
    except (TypeError, ValueError, RuntimeError) as error:
        raise AssertionError("attention inputs must be numeric") from error
    assert all(x.ndim == 4 and all(x.shape) for x in (query, key, value))
    batch, query_heads, query_tokens, width = query.shape
    assert key.shape == value.shape
    assert key.shape[0] == batch and key.shape[3] == width
    assert query_heads % key.shape[1] == 0
    assert query.dtype == key.dtype == value.dtype
    assert query.device == key.device == value.device
    repeat = query_heads // key.shape[1]
    selected_key = key.repeat_interleave(repeat, dim=1)
    selected_value = value.repeat_interleave(repeat, dim=1)
    scores = query @ selected_key.transpose(-1, -2) / math.sqrt(width)
    return scores.softmax(dim=-1) @ selected_value
