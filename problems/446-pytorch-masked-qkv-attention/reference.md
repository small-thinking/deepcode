# Reference answer

The public Prachub question record describes attention from Q, K and V in PyTorch, masks, multi-head tensors, unequal lengths, scaling, gradients and complexity. The linked candidate experience body is premium-gated. This exercise uses local practice conventions: the function name, rank-four layout, True-as-allowed boolean mask, caller-controlled causality, output-only return, and no fully masked queries. These are not claimed as the original transcript's exact API.

```python
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
```

Scaling by the square root of the key dimension keeps score variance from growing with feature width and reduces softmax saturation. Softmax normalizes over keys separately for every query and head.

Time is O(B H Lq Lk (D + Dv)); materializing scores uses O(B H Lq Lk) memory. Tiled exact attention can avoid storing the complete score matrix; sparse or windowed attention changes which keys can attend. Each option needs correctness, latency and memory evaluation.

## Published practice variants and unresolved original

The public curated specification also includes 3D inputs, additive masks, returned weights, optional dropout/custom scale, and zero outputs for fully masked rows. Its boolean mask uses True for masked-out entries, opposite to this explicitly defined local API. Discuss these as optional extensions rather than mixing the two conventions.

Float16/bfloat16 inputs need float32 score computation and softmax to avoid intermediate overflow; cast the result back without detaching gradients. The reference implements this within the existing API.

The original DIY-attention report remains premium-gated. Another search inventory describes a non-standard algorithm, but no evidence establishes that it is the same event. This exercise follows the readable curated scaled-dot-product specification; it is not a verified reconstruction of that inaccessible original algorithm.
