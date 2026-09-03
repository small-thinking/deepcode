from bisect import bisect_left, bisect_right
from collections import OrderedDict
from collections.abc import Iterable, Mapping
import math
import numbers

import numpy as np
import torch
from torch import nn


def sanitize_image(image):
    if not isinstance(image, np.ndarray) or image.ndim != 1 or image.size == 0:
        raise ValueError("image must be a non-empty one-dimensional NumPy array")
    if image.dtype != np.uint8:
        raise ValueError("image must have dtype uint8")
    side = math.isqrt(image.size)
    if side * side != image.size:
        raise ValueError("image length must be a perfect square")
    result = image.astype(np.float32, copy=True)
    minimum = result.min()
    maximum = result.max()
    if maximum != minimum:
        result = (result - minimum) / (maximum - minimum)
    else:
        result.fill(0.0)
    return result.reshape(side, side)


class TransientDownloadError(Exception):
    pass


class ImagePredictionService:
    def __init__(self, downloader, sanitizer, models, capacity, max_retries=0):
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if type(max_retries) is not int or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        if not callable(downloader) or not callable(sanitizer) or not isinstance(models, Mapping):
            raise ValueError("dependencies must be callable and models must be a mapping")
        self._downloader = downloader
        self._sanitizer = sanitizer
        self._models = models
        self._capacity = capacity
        self._max_retries = max_retries
        self._cache = OrderedDict()

    def predict(self, image_id, model_key):
        if model_key not in self._models:
            raise ValueError("unknown model key")
        cache_key = (model_key, image_id)
        if cache_key in self._cache:
            prediction = self._cache.pop(cache_key)
            self._cache[cache_key] = prediction
            return prediction

        for attempt in range(self._max_retries + 1):
            try:
                raw = self._downloader(image_id)
                break
            except TransientDownloadError:
                if attempt == self._max_retries:
                    raise
        sanitized = self._sanitizer(raw)
        prediction = self._models[model_key].predict(sanitized)
        self._cache[cache_key] = prediction
        if len(self._cache) > self._capacity:
            self._cache.popitem(last=False)
        return prediction


def binary_focal_loss(labels, probabilities, alpha=0.25, gamma=2.0, reduction="mean"):
    labels = np.asarray(labels)
    try:
        probabilities = np.asarray(probabilities, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("probabilities must be numeric") from error
    if labels.size == 0 or labels.shape != probabilities.shape:
        raise ValueError("labels and probabilities must have the same non-empty shape")
    if not np.isin(labels, [0, 1]).all():
        raise ValueError("labels must be zero or one")
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any():
        raise ValueError("probabilities must be finite values in [0, 1]")
    if isinstance(alpha, bool) or not isinstance(alpha, numbers.Real) or not 0 <= alpha <= 1:
        raise ValueError("alpha must be in [0, 1]")
    if isinstance(gamma, bool) or not isinstance(gamma, numbers.Real) or not math.isfinite(gamma) or gamma < 0:
        raise ValueError("gamma must be a non-negative finite number")
    if reduction not in {"none", "sum", "mean"}:
        raise ValueError("unknown reduction")

    positive = labels == 1
    p_t = np.where(positive, probabilities, 1.0 - probabilities)
    p_t = np.clip(p_t, 1e-15, 1.0 - 1e-15)
    alpha_t = np.where(positive, float(alpha), 1.0 - float(alpha))
    losses = -alpha_t * (1.0 - p_t) ** float(gamma) * np.log(p_t)
    if reduction == "none":
        return losses
    if reduction == "sum":
        return float(losses.sum())
    return float(losses.mean())


def grouped_query_attention(query, key, value):
    try:
        query = np.asarray(query, dtype=float)
        key = np.asarray(key, dtype=float)
        value = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("attention inputs must be numeric") from error
    if query.ndim != 4 or key.ndim != 4 or value.ndim != 4:
        raise ValueError("attention inputs must be rank four")
    if any(dimension == 0 for array in (query, key, value) for dimension in array.shape):
        raise ValueError("attention dimensions must be non-zero")
    batch, query_heads, query_tokens, width = query.shape
    key_batch, key_heads, key_tokens, key_width = key.shape
    value_batch, value_heads, value_tokens, value_width = value.shape
    if (
        batch != key_batch
        or batch != value_batch
        or key_heads != value_heads
        or width != key_width
        or width != value_width
        or key_tokens != value_tokens
        or query_heads % key_heads != 0
    ):
        raise ValueError("incompatible grouped-attention shapes")
    repeat = query_heads // key_heads
    key_value_heads = np.arange(query_heads) // repeat
    selected_key = key[:, key_value_heads, :, :]
    selected_value = value[:, key_value_heads, :, :]
    scores = np.einsum("bhtd,bhsd->bhts", query, selected_key) / math.sqrt(width)
    scores = scores - scores.max(axis=-1, keepdims=True)
    weights = np.exp(scores)
    weights /= weights.sum(axis=-1, keepdims=True)
    return np.einsum("bhts,bhsd->bhtd", weights, selected_value)


class QueryFailed(RuntimeError):
    pass


class QueryCancelled(RuntimeError):
    pass


class QueryTimeout(RuntimeError):
    pass


async def stream_query(api, sql, max_polls=100):
    if not isinstance(sql, str) or not sql or type(max_polls) is not int or max_polls <= 0:
        raise ValueError("sql must be non-empty and max_polls must be positive")
    query_id = await api.submit(sql)
    for _ in range(max_polls):
        status = await api.status(query_id)
        if status == "SUCCEEDED":
            break
        if status == "FAILED":
            raise QueryFailed(query_id)
        if status == "CANCELED":
            raise QueryCancelled(query_id)
        if status not in {"QUEUED", "RUNNING"}:
            raise ValueError("unknown query status")
    else:
        raise QueryTimeout(query_id)

    token = None
    seen_tokens = set()
    while True:
        page = await api.page(query_id, token)
        if not isinstance(page, tuple) or len(page) != 2:
            raise ValueError("page must be a (rows, next_token) tuple")
        rows, next_token = page
        if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
            raise ValueError("page rows must be an iterable of rows")
        if next_token is not None and (not isinstance(next_token, str) or not next_token):
            raise ValueError("next token must be a non-empty string or None")
        if next_token is not None:
            if next_token in seen_tokens:
                raise ValueError("repeated continuation token")
            seen_tokens.add(next_token)
        for row in rows:
            yield row
        if next_token is None:
            return
        token = next_token


def _validated_points(points, tag):
    if not isinstance(tag, str) or not tag:
        raise ValueError("tag must be a non-empty string")
    if isinstance(points, (str, bytes)) or not isinstance(points, Iterable):
        raise ValueError("points must be an iterable")
    normalized = []
    for index, point in enumerate(points):
        if not isinstance(point, (tuple, list)) or len(point) != 3:
            raise ValueError("each point must be a timestamp, value, tags triple")
        timestamp, value, tags = point
        if type(timestamp) is not int:
            raise ValueError("timestamps must be integers")
        if isinstance(value, bool) or not isinstance(value, numbers.Real) or not math.isfinite(value):
            raise ValueError("values must be finite real numbers")
        if isinstance(tags, (str, bytes)) or not isinstance(tags, Iterable):
            raise ValueError("tags must be an iterable of strings")
        tag_values = tuple(tags)
        if any(not isinstance(item, str) for item in tag_values):
            raise ValueError("tags must contain strings")
        if tag in tag_values:
            normalized.append((timestamp, index, value))
    return sorted(normalized)


def _positive_integer(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def fixed_count_moving_sums(points, tag, k):
    _positive_integer(k, "k")
    filtered = _validated_points(points, tag)
    return [sum(filtered[index + offset][2] for offset in range(k)) for index in range(len(filtered) - k + 1)]


def time_window_moving_sums(points, tag, window_seconds):
    _positive_integer(window_seconds, "window_seconds")
    filtered = _validated_points(points, tag)
    if not filtered:
        return []
    last_timestamp = filtered[-1][0]
    left = 0
    right = 0
    total = 0
    result = []
    for timestamp, _, _ in filtered:
        while left < len(filtered) and filtered[left][0] < timestamp:
            total -= filtered[left][2]
            left += 1
        while right < len(filtered) and filtered[right][0] < timestamp + window_seconds:
            total += filtered[right][2]
            right += 1
        if timestamp + window_seconds <= last_timestamp:
            result.append(total)
    return result


class LogStore:
    def __init__(self):
        self._records = []
        self._next_sequence = 0

    @staticmethod
    def _timestamp(value, name):
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")

    def add(self, timestamp, message):
        self._timestamp(timestamp, "timestamp")
        if not isinstance(message, str):
            raise ValueError("message must be a string")
        record = (timestamp, self._next_sequence, message)
        self._next_sequence += 1
        index = bisect_right(self._records, (timestamp, math.inf))
        self._records.insert(index, record)

    def iter_range(self, start, end):
        self._timestamp(start, "start")
        self._timestamp(end, "end")
        if start > end:
            raise ValueError("start must not exceed end")
        left = bisect_left(self._records, (start, -1))
        right = bisect_right(self._records, (end, math.inf))
        records = self._records
        return ((records[index][0], records[index][2]) for index in range(left, right))


class TinyDenoiser(nn.Module):
    def __init__(self, channels, hidden_channels):
        super().__init__()
        if type(channels) is not int or type(hidden_channels) is not int or channels <= 0 or hidden_channels <= 0:
            raise ValueError("channel counts must be positive integers")
        self.layers = nn.Sequential(
            nn.Conv2d(channels, hidden_channels, kernel_size=3, padding=1),
            nn.SiLU(),
            nn.Conv2d(hidden_channels, channels, kernel_size=3, padding=1),
        )

    def forward(self, noisy_images):
        return self.layers(noisy_images)


def diffusion_train_step(model, optimizer, clean_uint8, noise, alpha_bar):
    if not isinstance(clean_uint8, torch.Tensor) or clean_uint8.dtype != torch.uint8:
        raise ValueError("clean images must be uint8 tensors")
    if clean_uint8.ndim != 4 or clean_uint8.numel() == 0 or any(size == 0 for size in clean_uint8.shape):
        raise ValueError("clean images must be non-empty rank-four tensors")
    if not isinstance(noise, torch.Tensor) or not noise.is_floating_point() or noise.shape != clean_uint8.shape:
        raise ValueError("noise must be a same-shape floating tensor")
    if noise.device != clean_uint8.device or not torch.isfinite(noise).all():
        raise ValueError("noise must be finite and on the image device")
    if isinstance(alpha_bar, bool) or not isinstance(alpha_bar, numbers.Real) or not math.isfinite(alpha_bar) or not 0 <= alpha_bar <= 1:
        raise ValueError("alpha_bar must be finite and in [0, 1]")
    clean = clean_uint8.to(dtype=noise.dtype) / 127.5 - 1.0
    alpha = clean.new_tensor(float(alpha_bar))
    noisy = alpha.sqrt() * clean + (1.0 - alpha).sqrt() * noise
    prediction = model(noisy)
    if not isinstance(prediction, torch.Tensor) or prediction.shape != noise.shape:
        raise ValueError("model output must match noise shape")
    loss = torch.mean((prediction - noise) ** 2)
    if not torch.isfinite(loss):
        raise ValueError("loss must be finite")
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
    return float(loss.detach().item())


def _validated_image(image):
    if not isinstance(image, np.ndarray) or image.ndim not in {2, 3}:
        raise ValueError("image must have shape [H, W] or [H, W, C]")
    if any(dimension == 0 for dimension in image.shape):
        raise ValueError("image dimensions must be positive")
    if image.ndim == 3 and image.shape[2] not in {1, 3, 4}:
        raise ValueError("image channels must be 1, 3, or 4")
    if not (np.issubdtype(image.dtype, np.integer) or np.issubdtype(image.dtype, np.floating)):
        raise ValueError("image must have an integer or floating dtype")
    return image


def _crop_shape(image, crop_h, crop_w):
    _validated_image(image)
    if type(crop_h) is not int or type(crop_w) is not int or crop_h <= 0 or crop_w <= 0:
        raise ValueError("crop dimensions must be positive integers")
    height, width = image.shape[:2]
    if crop_h > height or crop_w > width:
        raise ValueError("crop must fit inside image")
    return height, width


def center_crop(image, crop_h, crop_w):
    height, width = _crop_shape(image, crop_h, crop_w)
    top = (height - crop_h) // 2
    left = (width - crop_w) // 2
    return image[top:top + crop_h, left:left + crop_w].copy()


def _random_origin(height, width, crop_h, crop_w, rng):
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng must be a NumPy Generator")
    return int(rng.integers(height - crop_h + 1)), int(rng.integers(width - crop_w + 1))


def random_crop(image, crop_h, crop_w, rng):
    height, width = _crop_shape(image, crop_h, crop_w)
    top, left = _random_origin(height, width, crop_h, crop_w, rng)
    return image[top:top + crop_h, left:left + crop_w].copy()


def random_crop_paste_on_white(image, crop_h, crop_w, rng):
    height, width = _crop_shape(image, crop_h, crop_w)
    crop_top, crop_left = _random_origin(height, width, crop_h, crop_w, rng)
    paste_top, paste_left = _random_origin(height, width, crop_h, crop_w, rng)
    if np.issubdtype(image.dtype, np.floating):
        canvas = np.ones(image.shape, dtype=image.dtype)
    else:
        canvas = np.full(image.shape, np.iinfo(image.dtype).max, dtype=image.dtype)
    canvas[paste_top:paste_top + crop_h, paste_left:paste_left + crop_w] = image[crop_top:crop_top + crop_h, crop_left:crop_left + crop_w]
    return canvas
