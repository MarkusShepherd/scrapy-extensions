"""Logging classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.logformatter import LogFormatter

if TYPE_CHECKING:
    from scrapy import Spider
    from scrapy.http import Response
    from scrapy.logformatter import LogFormatterResult


class QuietLogFormatter(LogFormatter):
    """Be quieter about scraped items."""

    def scraped(  # type: ignore[override]
        self,
        item: Any,
        response: Response,
        spider: Spider,
    ) -> LogFormatterResult | None:
        return (
            super().scraped(item, response, spider)
            if spider.settings.getbool("LOG_SCRAPED_ITEMS")
            else None
        )
