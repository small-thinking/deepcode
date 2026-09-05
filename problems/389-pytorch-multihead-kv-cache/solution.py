import math
import torch
from torch import nn


class MHA(nn.Module):
    def __init__(self, n_heads, dim):
        super().__init__()
        assert not (n_heads <= 0 or dim <= 0 or dim % n_heads), "positive dim must be divisible by positive n_heads"
        self.n_heads = n_heads
        self.dim = dim
        self.head_dim = dim // n_heads
        self.W_qkv = nn.Linear(dim, 3 * dim)
        self.W_o = nn.Linear(dim, dim)

    def forward(self, x, mask=None, kv_cache=None):
        b, t, c = x.shape
        q, k, v = self.W_qkv(x).reshape(b, t, 3, self.n_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        if kv_cache is not None:
            k = torch.cat((kv_cache[0], k), dim=2)
            v = torch.cat((kv_cache[1], v), dim=2)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))
        out = (scores.softmax(dim=-1) @ v).transpose(1, 2).reshape(b, t, c)
        return self.W_o(out), (k, v)
