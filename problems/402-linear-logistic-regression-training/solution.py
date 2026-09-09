import numpy as np


def train_regression(X, y, kind="linear", lr=0.05, epochs=1000, l2=0.0, tol=None):
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    w, b = np.zeros(X.shape[1]), 0.0
    def loss():
        z = X @ w + b
        data = np.mean((z-y)**2) if kind == "linear" else np.mean(np.logaddexp(0,z)-y*z)
        return float(data + l2 * np.dot(w,w) / 2)
    losses = [loss()]
    for _ in range(epochs):
        z = X @ w + b
        if kind == "linear":
            residual = 2 * (z-y)
        else:
            e = np.exp(-np.abs(z))
            residual = np.where(z >= 0, 1/(1+e), e/(1+e)) - y
        dw = X.T @ residual / len(y) + l2*w
        db = residual.mean()
        w = w - lr*dw
        b = float(b - lr*db)
        losses.append(loss())
        if tol is not None and abs(losses[-1]-losses[-2]) <= tol:
            break
    return w, b, losses
