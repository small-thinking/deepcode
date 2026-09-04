import numpy as np


def nn(x, W1, W2, b1, b2):
    x, W1, W2, b1, b2 = map(np.asarray, (x, W1, W2, b1, b2))
    z = x @ W1 + b1
    e = np.exp(-np.abs(z))
    hidden = np.where(z >= 0, 1 / (1 + e), e / (1 + e))
    return np.maximum(hidden @ W2 + b2, 0)
