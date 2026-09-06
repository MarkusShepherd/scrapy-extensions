"""Tests for the package's public surface."""

from __future__ import annotations

import scrapy_extensions


def test_public_exports() -> None:
    for name in scrapy_extensions.__all__:
        assert hasattr(scrapy_extensions, name)


def test_all_is_sorted_and_unique() -> None:
    assert scrapy_extensions.__all__ == sorted(set(scrapy_extensions.__all__))
