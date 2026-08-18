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
    def __init__(self, values):
        array = np.asarray(values, dtype=float)
        if array.ndim != 2:
            raise ValueError("Matrix values must be two-dimensional")
        self._values = array.copy()

    @classmethod
    def zeros(cls, rows, columns):
        return cls(np.zeros((rows, columns), dtype=float))

    @classmethod
    def from_ndarray(cls, values):
        if not isinstance(values, np.ndarray):
            raise TypeError("values must be a NumPy array")
        return cls(values)

    def to_ndarray(self):
        return self._values.copy()

    def set(self, row, column, value):
        self._values[row, column] = value

    def transpose(self):
        return Matrix(self._values.T)

    def sum(self, axis=None):
        if axis not in {None, 0, 1}:
            raise ValueError("axis must be None, 0, or 1")
        result = self._values.sum(axis=axis)
        return float(result) if axis is None else result

    def copy(self):
        return Matrix(self._values)


def _pool_plane(plane, kernel_h, kernel_w, stride_h, stride_w, channel=None):
    height = len(plane)
    width = len(plane[0])
    if height == 0 or width == 0 or any(len(row) != width for row in plane):
        raise ValueError("each plane must be a non-empty rectangle")

    pooled = []
    locations = []
    for start_row in range(0, height, stride_h):
        values_row = []
        locations_row = []
        for start_column in range(0, width, stride_w):
            end_row = min(start_row + kernel_h, height)
            end_column = min(start_column + kernel_w, width)
            best_value = plane[start_row][start_column]
            best_row = start_row
            best_column = start_column
            for row in range(start_row, end_row):
                for column in range(start_column, end_column):
                    value = plane[row][column]
                    if value > best_value:
                        best_value = value
                        best_row = row
                        best_column = column
            values_row.append(best_value)
            if channel is None:
                locations_row.append((best_row, best_column))
            else:
                locations_row.append((channel, best_row, best_column))
        pooled.append(values_row)
        locations.append(locations_row)
    return pooled, locations


def max_pool_with_locations(values, kernel_h, kernel_w, stride_h, stride_w, is_tensor=False):
    if min(kernel_h, kernel_w, stride_h, stride_w) <= 0:
        raise ValueError("kernel dimensions and strides must be positive")

    if not is_tensor:
        return _pool_plane(values, kernel_h, kernel_w, stride_h, stride_w)

    if not values:
        raise ValueError("tensor must contain at least one channel")
    pooled_channels = []
    location_channels = []
    for channel, plane in enumerate(values):
        pooled, locations = _pool_plane(plane, kernel_h, kernel_w, stride_h, stride_w, channel)
        pooled_channels.append(pooled)
        location_channels.append(locations)
    return pooled_channels, location_channels
