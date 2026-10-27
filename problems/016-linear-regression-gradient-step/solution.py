import torch


def linear_regression_step(X, y, weights, bias, learning_rate):
    errors = X @ weights + bias - y
    weight_gradient = (2 / X.shape[0]) * (X.T @ errors)
    bias_gradient = 2 * errors.mean()
    return weights - learning_rate * weight_gradient, torch.as_tensor(bias, dtype=X.dtype, device=X.device) - learning_rate * bias_gradient
