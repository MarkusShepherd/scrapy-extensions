"""Logging classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.logformatter import LogFormatter

if TYPE_CHECKING:
    from scrapy import Spider
    from scrapy.http import Response


class QuietLogFormatter(LogFormatter):
    """Be quieter about scraped items."""

    def scraped(
        self,
        item: Any,
        response: Response,
        spider: Spider,
    ) -> dict[str, Any] | None:
        return (
            super().scraped(item, response, spider)
            if spider.settings.getbool("LOG_SCRAPED_ITEMS")
            else None
        )
