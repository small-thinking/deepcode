import numpy as np


def batched_multihead_attention(query, key, value):
    query = np.asarray(query)
    key = np.asarray(key)
    value = np.asarray(value)

    if query.ndim != 4 or key.ndim != 4 or value.ndim != 4:
        raise AssertionError("query, key, and value must be rank-4 tensors")

    batch, heads, query_tokens, key_dim = query.shape
    key_batch, key_heads, key_tokens, key_width = key.shape
    value_batch, value_heads, value_tokens, value_dim = value.shape
    if any(dimension == 0 for dimension in query.shape + key.shape + value.shape):
        raise AssertionError("attention tensor dimensions must be non-empty")
    if (batch, heads) != (key_batch, key_heads) or (batch, heads) != (value_batch, value_heads):
        raise AssertionError("batch and head dimensions must agree")
    if key_dim != key_width:
        raise AssertionError("query and key feature widths must agree")
    if key_tokens != value_tokens:
        raise AssertionError("key and value token counts must agree")

    scores = np.einsum("bhqd,bhkd->bhqk", query, key, optimize=True)
    scores = scores / np.sqrt(key_dim)
    shifted_scores = scores - scores.max(axis=-1, keepdims=True)
    unnormalized = np.exp(shifted_scores)
    weights = unnormalized / unnormalized.sum(axis=-1, keepdims=True)
    output = np.einsum("bhqk,bhkv->bhqv", weights, value, optimize=True)
    return output, weights
