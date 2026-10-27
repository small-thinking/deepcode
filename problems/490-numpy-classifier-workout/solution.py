import torch


def combine_batches(parts):
    return torch.cat(parts, dim=0)


def filter_rows(X, y, keep):
    return X[keep], y[keep]


def fit_standardizer(X):
    mean = X.mean(dim=0, keepdim=True)
    scale = X.std(dim=0, correction=0, keepdim=True)
    return mean, torch.where(scale < 1e-8, torch.ones_like(scale), scale)


def standardize(X, mean, scale):
    return (X - mean) / scale


def make_minibatches(X, y, batch_size, seed):
    generator = torch.Generator().manual_seed(seed)
    order = torch.randperm(len(X), generator=generator).to(X.device)
    return [(X[idx], y[idx]) for start in range(0, len(X), batch_size)
            for idx in [order[start:start+batch_size]]]


def linear_logits(X, W, b):
    return X @ W + b


def softmax(logits):
    shifted = logits - logits.amax(dim=1, keepdim=True)
    exps = shifted.exp()
    return exps / exps.sum(dim=1, keepdim=True)


def one_hot(y, n_classes):
    return torch.eye(n_classes, dtype=torch.long, device=y.device)[y]


def cross_entropy(probs, y):
    selected = probs.gather(1, y[:, None]).squeeze(1)
    return -selected.clamp(1e-12, 1.).log().mean()


def linear_gradients(X, probs, y):
    residual = probs - one_hot(y, probs.shape[1])
    return X.T @ residual / len(X), residual.mean(dim=0)


def sgd_step(W, b, dW, db, lr):
    return W - lr * dW, b - lr * db


def classification_metrics(probs, y, k):
    order = torch.argsort(probs, dim=1, descending=True, stable=True)
    predictions, top_k = order[:, 0], order[:, :k]
    classes = probs.shape[1]
    confusion = torch.bincount(y*classes+predictions, minlength=classes*classes).reshape(classes, classes)
    return {"predictions": predictions, "top_k": top_k,
            "accuracy": (predictions == y).sum().item() / len(y),
            "top_k_accuracy": (top_k == y[:, None]).any(dim=1).sum().item() / len(y),
            "confusion": confusion}


def train_epoch(X, y, W, b, lr, batch_size, seed):
    W_new, b_new = W.clone(), b.clone()
    for Xb, yb in make_minibatches(X, y, batch_size, seed):
        probs = softmax(linear_logits(Xb, W_new, b_new))
        dW, db = linear_gradients(Xb, probs, yb)
        W_new, b_new = sgd_step(W_new, b_new, dW, db, lr)
    return W_new, b_new
