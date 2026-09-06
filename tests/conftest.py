"""Shared fixtures for the test suite."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pytest
from PIL import Image
from scrapy.utils.reactor import install_reactor

install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from pathlib import Path


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine to completion from a synchronous test."""
    return asyncio.run(coro)


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    """A small on-disk PNG image."""
    path = tmp_path / "image.png"
    Image.new("RGB", (64, 48), color=(120, 30, 200)).save(path)
    return path
