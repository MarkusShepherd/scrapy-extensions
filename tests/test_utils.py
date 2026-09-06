"""Tests for :mod:`scrapy_extensions.utils`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image

from scrapy_extensions.utils import calculate_blurhash

if TYPE_CHECKING:
    from pathlib import Path


def test_calculate_blurhash_from_path(image_file: Path) -> None:
    blurhash = calculate_blurhash(image_file, x_components=4, y_components=3)
    assert isinstance(blurhash, str)
    assert blurhash


def test_calculate_blurhash_from_image_object(image_file: Path) -> None:
    with Image.open(image_file) as image:
        blurhash = calculate_blurhash(image)
    assert isinstance(blurhash, str)
    assert blurhash
