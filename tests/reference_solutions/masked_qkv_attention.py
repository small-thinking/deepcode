import math
import torch


def scaled_dot_product_attention(q, k, v, mask=None):
    output_dtype = q.dtype
    if output_dtype in (torch.float16, torch.bfloat16):
        q, k, v = q.float(), k.float(), v.float()
    logits = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None:
        logits = logits.masked_fill(~mask, float('-inf'))
    weights = logits.softmax(dim=-1)
    output = weights @ v
    return output.to(output_dtype)
