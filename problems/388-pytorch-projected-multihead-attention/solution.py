import math
import torch
from torch import nn


class MHA(nn.Module):
    def __init__(self, n_heads, dim):
        super().__init__()
        assert n_heads > 0 and dim > 0 and dim % n_heads == 0, (
            "positive dim must be divisible by positive n_heads"
        )
        self.n_heads = n_heads
        self.dim = dim
        self.head_dim = dim // n_heads
        self.W_qkv = nn.Linear(dim, 3 * dim)
        self.W_o = nn.Linear(dim, dim)

    def forward(self, x, mask=None):
        b, t, c = x.shape
        q, k, v = self.W_qkv(x).reshape(b, t, 3, self.n_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))
        out = (scores.softmax(dim=-1) @ v).transpose(1, 2).reshape(b, t, c)
        return self.W_o(out)
