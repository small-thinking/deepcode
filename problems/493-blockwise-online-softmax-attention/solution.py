import math

import torch


def blockwise_attention(Q, K, V, block_size):
    tensors = [torch.as_tensor(x) for x in (Q, K, V)]
    Q, K, V = [x if x.is_floating_point() else x.to(torch.get_default_dtype()) for x in tensors]
    assert type(block_size) is int and block_size > 0
    assert all(x.ndim == 2 and all(x.shape) for x in (Q, K, V))
    assert Q.shape[1] == K.shape[1] and K.shape[0] == V.shape[0]
    assert Q.dtype == K.dtype == V.dtype and Q.device == K.device == V.device
    output_tiles = []
    scale = math.sqrt(Q.shape[1])
    for start in range(0, Q.shape[0], block_size):
        queries = Q[start:start + block_size]
        rows = queries.shape[0]
        maximum = Q.new_full((rows, 1), -torch.inf)
        denominator = Q.new_zeros((rows, 1))
        numerator = Q.new_zeros((rows, V.shape[1]))
        for col in range(0, K.shape[0], block_size):
            scores = queries @ K[col:col + block_size].T / scale
            new_maximum = torch.maximum(maximum, scores.amax(dim=1, keepdim=True))
            old_scale = (maximum - new_maximum).exp()
            tile_weights = (scores - new_maximum).exp()
            numerator = numerator * old_scale + tile_weights @ V[col:col + block_size]
            denominator = denominator * old_scale + tile_weights.sum(dim=1, keepdim=True)
            maximum = new_maximum
        output_tiles.append(numerator / denominator)
    return torch.cat(output_tiles, dim=0)
