import numpy as np


def kmeans(X, k, n_iter, seed=None):
    points = np.asarray(X, dtype=float)
    if points.ndim != 2 or points.shape[0] == 0:
        raise ValueError("X must be a non-empty two-dimensional array")
    n_samples = points.shape[0]
    if not 1 <= k <= n_samples:
        raise ValueError("k must be between 1 and the number of samples")
    if not isinstance(n_iter, int) or n_iter < 0:
        raise ValueError("n_iter must be a non-negative integer")

    rng = np.random.default_rng(seed)
    centroids = points[rng.choice(n_samples, size=k, replace=False)].copy()
    previous_labels = None

    for _ in range(n_iter):
        squared_distances = ((points[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        labels = np.argmin(squared_distances, axis=1)
        assignments = (labels[:, None] == np.arange(k)[None, :]).astype(float)
        counts = assignments.sum(axis=0)
        updated_centroids = (assignments.T @ points) / np.maximum(counts[:, None], 1.0)
        updated_centroids[counts == 0] = centroids[counts == 0]

        drift = np.linalg.norm(updated_centroids - centroids, ord="fro")
        labels_unchanged = previous_labels is not None and np.array_equal(labels, previous_labels)
        centroids = updated_centroids
        if labels_unchanged or drift < 1e-6:
            break
        previous_labels = labels

    final_squared_distances = ((points[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return centroids, np.argmin(final_squared_distances, axis=1)


class Matrix:
    def __init__(self, data):
        self.data = data

    @staticmethod
    def zeros(rows, cols):
        return Matrix([[0 for _ in range(cols)] for _ in range(rows)])


def to_ndarray(columns):
    return np.stack(columns, axis=1)


def from_ndarray(arr, chunk_size):
    return [arr[start:start + chunk_size] for start in range(0, arr.shape[0], chunk_size)]


def max_pool_with_locations(values, kernel_h, kernel_w, stride_h, stride_w):
    height, width = len(values), len(values[0])
    if kernel_h > height or kernel_w > width:
        return [], []
    pooled, locations = [], []
    for start_row in range(0, height - kernel_h + 1, stride_h):
        pooled_row, locations_row = [], []
        for start_column in range(0, width - kernel_w + 1, stride_w):
            best_value = values[start_row][start_column]
            best_row, best_column = start_row, start_column
            for row in range(start_row, start_row + kernel_h):
                for column in range(start_column, start_column + kernel_w):
                    if values[row][column] > best_value:
                        best_value = values[row][column]
                        best_row, best_column = row, column
            pooled_row.append(best_value)
            locations_row.append((best_row, best_column))
        pooled.append(pooled_row)
        locations.append(locations_row)
    return pooled, locations
