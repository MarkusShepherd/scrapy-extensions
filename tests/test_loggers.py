"""Tests for :class:`scrapy_extensions.loggers.QuietLogFormatter`."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from scrapy.http import Response

from scrapy_extensions.loggers import QuietLogFormatter

if TYPE_CHECKING:
    from scrapy import Spider


def _spider(*, log_scraped_items: bool) -> Spider:
    return cast(
        "Spider",
        SimpleNamespace(
            settings=SimpleNamespace(getbool=lambda _key: log_scraped_items),
        ),
    )


def test_scraped_is_silenced_by_default() -> None:
    formatter = QuietLogFormatter()
    response = Response("https://example.com")
    assert formatter.scraped({}, response, _spider(log_scraped_items=False)) is None


def test_scraped_is_logged_when_enabled() -> None:
    formatter = QuietLogFormatter()
    response = Response("https://example.com")
    result = formatter.scraped({}, response, _spider(log_scraped_items=True))
    assert result is not None
    assert "level" in result
