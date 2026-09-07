"""Practice reconstruction reference: controlled sample-wise regression experiment."""
import numbers

import numpy as np


def _integer(value, low, high):
    return (isinstance(value, numbers.Integral)
            and not isinstance(value, (bool, np.bool_)) and low <= value <= high)


def _real(value, low, high):
    if not isinstance(value, numbers.Real) or isinstance(value, (bool, np.bool_)):
        return False
    try:
        return np.isfinite(float(value)) and low <= value <= high
    except (OverflowError, ValueError):
        return False


def _sequence(value, low, high):
    if not isinstance(value, (list, tuple, np.ndarray)):
        raise ValueError('expected a sequence')
    if isinstance(value, np.ndarray) and value.ndim != 1:
        raise ValueError('expected a one-dimensional sequence')
    if not low <= len(value) <= high:
        raise ValueError('sequence length out of bounds')
    return list(value)


def sample_wise_experiment(feature_dim, sample_counts, ridge_lambdas, seeds,
                           n_test=128, noise_std=0.5):
    if not _integer(feature_dim, 2, 64) or not _integer(n_test, 1, 512):
        raise ValueError('invalid dimension or test size')
    if not _real(noise_std, 0, 10):
        raise ValueError('invalid noise standard deviation')
    counts = _sequence(sample_counts, 3, 16)
    penalties = _sequence(ridge_lambdas, 1, 8)
    seed_values = _sequence(seeds, 1, 8)
    if (not all(_integer(n, 1, 256) for n in counts)
            or any(a >= b for a, b in zip(counts, counts[1:]))
            or feature_dim not in counts
            or not counts[0] < feature_dim < counts[-1]):
        raise ValueError('invalid sample grid')
    if (not all(_real(lam, 0, np.inf) and lam > 0 for lam in penalties)
            or len(set(penalties)) != len(penalties)):
        raise ValueError('invalid ridge penalties')
    if (not all(_integer(seed, 0, 2**32 - 1) for seed in seed_values)
            or len(set(seed_values)) != len(seed_values)):
        raise ValueError('invalid seeds')

    penalties = [float(lam) for lam in penalties]
    shape = (len(seed_values), len(counts), len(penalties) + 1)
    train = np.empty(shape, dtype=np.float64)
    test = np.empty(shape, dtype=np.float64)
    beta = np.ones(feature_dim, dtype=np.float64) / np.sqrt(feature_dim)
    for si, seed in enumerate(seed_values):
        rng = np.random.default_rng(seed)
        pool = rng.standard_normal((counts[-1], feature_dim))
        pool_noise = rng.standard_normal(counts[-1])
        heldout = rng.standard_normal((n_test, feature_dim))
        test_noise = rng.standard_normal(n_test)
        targets = pool @ beta + noise_std * pool_noise
        heldout_targets = heldout @ beta + noise_std * test_noise
        for ni, n in enumerate(counts):
            X, y = pool[:n], targets[:n]
            weights = [np.linalg.lstsq(X, y, rcond=None)[0]]
            # Augmentation avoids squaring the condition number in a Gram solve.
            for lam in penalties:
                augmented_X = np.vstack((X, (np.sqrt(n) * np.sqrt(lam)) * np.eye(feature_dim)))
                augmented_y = np.concatenate((y, np.zeros(feature_dim)))
                weights.append(np.linalg.lstsq(augmented_X, augmented_y, rcond=None)[0])
            for li, w in enumerate(weights):
                train[si, ni, li] = np.mean((X @ w - y) ** 2)
                test[si, ni, li] = np.mean((heldout @ w - heldout_targets) ** 2)
    return {
        'sample_counts': np.array(counts, dtype=np.int64),
        'lambdas': np.array([0.0, *penalties], dtype=np.float64),
        'seeds': np.array(seed_values, dtype=np.int64),
        'train_mse': train, 'test_mse': test,
        'train_mean': train.mean(axis=0), 'test_mean': test.mean(axis=0),
        'train_std': train.std(axis=0, ddof=0), 'test_std': test.std(axis=0, ddof=0),
    }
