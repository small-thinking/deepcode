import numpy as np


def blockwise_attention(Q, K, V, block_size):
    Q = np.asarray(Q, dtype=float)
    K = np.asarray(K, dtype=float)
    V = np.asarray(V, dtype=float)
    output = np.empty((Q.shape[0], V.shape[1]), dtype=float)
    scale = np.sqrt(Q.shape[1])
    for start in range(0, Q.shape[0], block_size):
        queries = Q[start:start + block_size]
        rows = len(queries)
        maximum = np.full((rows, 1), -np.inf)
        denominator = np.zeros((rows, 1))
        numerator = np.zeros((rows, V.shape[1]))
        for col in range(0, K.shape[0], block_size):
            scores = queries @ K[col:col + block_size].T / scale
            new_maximum = np.maximum(maximum, scores.max(axis=1, keepdims=True))
            old_scale = np.exp(maximum - new_maximum)
            tile_weights = np.exp(scores - new_maximum)
            numerator = numerator * old_scale + tile_weights @ V[col:col + block_size]
            denominator = denominator * old_scale + tile_weights.sum(axis=1, keepdims=True)
            maximum = new_maximum
        output[start:start + rows] = numerator / denominator
    return output
