import numpy as np


def combine_batches(parts):
    return np.concatenate(parts, axis=0)


def filter_rows(X, y, keep):
    return X[keep], y[keep]


def fit_standardizer(X):
    mean = X.mean(axis=0, keepdims=True)
    scale = X.std(axis=0, keepdims=True)
    scale = np.where(scale < 1e-8, 1.0, scale)
    return mean, scale


def standardize(X, mean, scale):
    return (X - mean) / scale


def make_minibatches(X, y, batch_size, seed):
    order = np.random.default_rng(seed).permutation(len(X))
    batches = []
    for start in range(0, len(X), batch_size):
        idx = order[start:start + batch_size]
        batches.append((X[idx], y[idx]))
    return batches


def linear_logits(X, W, b):
    return X @ W + b


def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exps = np.exp(shifted)
    return exps / exps.sum(axis=1, keepdims=True)


def one_hot(y, n_classes):
    return np.eye(n_classes)[y]


def cross_entropy(probs, y):
    selected = probs[np.arange(len(y)), y]
    return float(-np.log(np.clip(selected, 1e-12, 1.0)).mean())


def linear_gradients(X, probs, y):
    residual = probs - one_hot(y, probs.shape[1])
    return X.T @ residual / len(X), residual.mean(axis=0)


def sgd_step(W, b, dW, db, lr):
    return W - lr * dW, b - lr * db


def classification_metrics(probs, y, k):
    predictions = probs.argmax(axis=1)
    top_k = np.argsort(-probs, axis=1, kind="stable")[:, :k]
    C = probs.shape[1]
    confusion = (one_hot(y, C).T @ one_hot(predictions, C)).astype(int)
    return {
        "predictions": predictions,
        "top_k": top_k,
        "accuracy": float(np.mean(predictions == y)),
        "top_k_accuracy": float(np.mean(np.any(top_k == y[:, None], axis=1))),
        "confusion": confusion,
    }


def train_epoch(X, y, W, b, lr, batch_size, seed):
    W_new, b_new = W.copy(), b.copy()
    for Xb, yb in make_minibatches(X, y, batch_size, seed):
        probs = softmax(linear_logits(Xb, W_new, b_new))
        dW, db = linear_gradients(Xb, probs, yb)
        W_new, b_new = sgd_step(W_new, b_new, dW, db, lr)
    return W_new, b_new
