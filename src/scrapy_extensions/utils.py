"""Utility functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import PIL.Image

LOGGER = logging.getLogger(__name__)


def calculate_blurhash(
    image: str | Path | PIL.Image.Image,
    x_components: int = 4,
    y_components: int = 4,
) -> str:
    """Calculate the blurhash of a given image."""

    import numpy as np
    from blurhash_numba import encode
    from PIL import Image, ImageOps

    image = image if isinstance(image, Image.Image) else Image.open(image)
    image = ImageOps.fit(
        image=image,
        size=(32 * x_components, 32 * y_components),
        centering=(0.5, 0),
    )
    image_array = np.array(image.convert("RGB"), dtype=float)

    blurhash = encode(
        image=image_array,
        x_components=x_components,
        y_components=y_components,
    )
    assert isinstance(blurhash, str)
    return blurhash
