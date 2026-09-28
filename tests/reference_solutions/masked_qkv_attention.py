import math
import torch


def masked_qkv_attention(q, k, v, mask=None):
    output_dtype = q.dtype
    if output_dtype in (torch.float16, torch.bfloat16):
        q, k, v = q.float(), k.float(), v.float()
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None:
        scores = scores.masked_fill(~mask, float('-inf'))
    return (scores.softmax(dim=-1) @ v).to(output_dtype)
