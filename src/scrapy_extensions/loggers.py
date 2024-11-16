"""Logging classes."""

from __future__ import annotations

from typing import Any

import scrapy
import scrapy.http
import scrapy.logformatter


class QuietLogFormatter(scrapy.logformatter.LogFormatter):
    """Be quieter about scraped items."""

    def scraped(
        self,
        item: Any,
        response: scrapy.http.Response,
        spider: scrapy.Spider,
    ) -> dict[str, Any] | None:
        return (
            super().scraped(item, response, spider)
            if spider.settings.getbool("LOG_SCRAPED_ITEMS")
            else None
        )
