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
