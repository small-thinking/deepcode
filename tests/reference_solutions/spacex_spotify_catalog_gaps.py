from collections import Counter, defaultdict
from collections.abc import Mapping

import numpy as np


def patchify_channels_first(image, patch_height, patch_width):
    if not isinstance(image, np.ndarray) or image.ndim != 3:
        raise ValueError("image must be a three-dimensional NumPy array")
    if not np.issubdtype(image.dtype, np.number):
        raise ValueError("image must have a numeric dtype")
    if (
        isinstance(patch_height, bool)
        or not isinstance(patch_height, int)
        or isinstance(patch_width, bool)
        or not isinstance(patch_width, int)
        or patch_height <= 0
        or patch_width <= 0
    ):
        raise ValueError("patch dimensions must be positive integers")

    height, width, channels = image.shape
    if height <= 0 or width <= 0 or channels <= 0:
        raise ValueError("image dimensions must be positive")
    if height % patch_height or width % patch_width:
        raise ValueError("patch dimensions must divide the image dimensions")

    return image.reshape(
        height // patch_height,
        patch_height,
        width // patch_width,
        patch_width,
        channels,
    ).transpose(0, 2, 4, 1, 3)


def top_played_tracks(events, n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")

    global_counts = Counter()
    country_counts = defaultdict(Counter)
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("each event must be a mapping")
        track_id = event.get("track_id")
        country = event.get("country")
        if not isinstance(track_id, str) or not track_id:
            raise ValueError("track_id must be a non-empty string")
        if not isinstance(country, str) or not country:
            raise ValueError("country must be a non-empty string")
        global_counts[track_id] += 1
        country_counts[country][track_id] += 1

    def ranked(counts):
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:n]

    return {
        "global": ranked(global_counts),
        "by_country": {
            country: ranked(country_counts[country])
            for country in sorted(country_counts)
        },
    }
