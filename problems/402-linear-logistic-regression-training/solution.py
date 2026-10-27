import torch


def train_regression(X, y, kind="linear", lr=0.05, epochs=1000, l2=0.0, tol=None):
    generator = torch.Generator().manual_seed(0)
    w = (torch.randn(X.shape[1], generator=generator, dtype=X.dtype) * .01).to(X.device)
    b = X.new_zeros(())

    def loss():
        z = X @ w + b
        data = ((z-y)**2).mean() if kind == "linear" else (torch.logaddexp(torch.zeros_like(z), z)-y*z).mean()
        return float(data + l2 * w.square().sum() / 2)

    losses = [loss()]
    for _ in range(epochs):
        z = X @ w + b
        residual = 2 * (z-y) if kind == "linear" else z.sigmoid() - y
        dw = X.T @ residual / len(y) + l2*w
        db = residual.mean()
        w = w - lr*dw
        b = b - lr*db
        losses.append(loss())
        if tol is not None and abs(losses[-1]-losses[-2]) <= tol:
            break
    return w, b, losses
