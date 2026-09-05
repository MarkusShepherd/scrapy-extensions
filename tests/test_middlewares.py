"""Tests for :class:`scrapy_extensions.middlewares.AuthHeaderMiddleware`."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest
from scrapy import Request, Spider
from scrapy.exceptions import NotConfigured
from scrapy.utils.test import get_crawler

from scrapy_extensions.middlewares import AuthHeaderMiddleware


def _spider(token: str) -> Spider:
    return cast("Spider", SimpleNamespace(auth_token=token))


def test_from_crawler_disabled_by_default() -> None:
    crawler = get_crawler(Spider)
    with pytest.raises(NotConfigured):
        AuthHeaderMiddleware.from_crawler(crawler)


def test_from_crawler_reads_settings() -> None:
    crawler = get_crawler(
        Spider,
        {
            "AUTH_HEADER_ENABLED": True,
            "AUTH_HEADER_NAME": "X-Api-Key",
            "AUTH_TOKEN_ATTR": "api_token",
        },
    )
    mw = AuthHeaderMiddleware.from_crawler(crawler)
    assert mw.header_name == "X-Api-Key"
    assert mw.auth_token_attr == "api_token"


def test_process_request_sets_bearer_header() -> None:
    mw = AuthHeaderMiddleware(header_name="Authorization")
    spider = _spider("secret")
    request = Request("https://example.com")
    mw.process_request(request, spider)
    assert request.headers[b"Authorization"] == b"Bearer secret"


def test_process_request_without_token_does_nothing() -> None:
    mw = AuthHeaderMiddleware(header_name="Authorization")
    spider = _spider("")
    request = Request("https://example.com")
    mw.process_request(request, spider)
    assert b"Authorization" not in request.headers


def test_process_request_does_not_clobber_explicit_header() -> None:
    mw = AuthHeaderMiddleware(header_name="Authorization")
    spider = _spider("secret")
    request = Request("https://example.com", headers={"Authorization": "Basic abc"})
    mw.process_request(request, spider)
    assert request.headers[b"Authorization"] == b"Basic abc"
