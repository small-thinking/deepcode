import numpy as np


# PROVIDED: keep the source interface's spelling.
class Regularizer:
    def loss_penalty(self, coefficients):
        raise NotImplementedError

    def gradiate_penalty(self, coefficients):
        raise NotImplementedError


# PROVIDED: numerically stable prediction for a model with no intercept.
def predict_logistic(features, coefficients, threshold=0.5):
    z = np.asarray(features, dtype=float) @ coefficients
    probabilities = np.exp(-np.logaddexp(0.0, -z))
    return (probabilities > threshold).astype(int)


class L2Regularizer(Regularizer):
    def __init__(self, lambda_param):
        self.lambda_param = lambda_param

    def loss_penalty(self, coefficients):
        return self.lambda_param * np.dot(coefficients, coefficients)

    def gradiate_penalty(self, coefficients):
        return 2 * self.lambda_param * coefficients


def train_logistic(features, targets, regularizer=None, epochs=8,
                   learning_rate=0.01, batch_size=32, seed=42):
    # PROVIDED: data preparation, zero initialization, and shuffled minibatches.
    x = np.asarray(features, dtype=float)
    y = np.asarray(targets, dtype=float)
    coefficients = np.zeros(x.shape[1], dtype=float)
    losses = []
    rng = np.random.default_rng(seed)
    for _ in range(epochs):
        order = rng.permutation(len(x))
        for start in range(0, len(x), batch_size):
            indices = order[start:start + batch_size]
            xb, yb = x[indices], y[indices]
            logits = xb @ coefficients
            probabilities = np.exp(-np.logaddexp(0.0, -logits))
            gradient = xb.T @ (probabilities - yb) / len(indices)
            if regularizer is not None:
                gradient = gradient + regularizer.gradiate_penalty(coefficients)
            coefficients = coefficients - learning_rate * gradient
        logits = x @ coefficients
        loss = float(np.mean(np.logaddexp(0.0, logits) - y * logits))
        if regularizer is not None:
            loss += float(regularizer.loss_penalty(coefficients))
        losses.append(loss)
    return coefficients, losses
