import math
import torch


def masked_qkv_attention(q, k, v, mask=None):
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None:
        scores = scores.masked_fill(~mask, float('-inf'))
    return scores.softmax(dim=-1) @ v
