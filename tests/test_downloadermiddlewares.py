"""Tests for :class:`scrapy_extensions.downloadermiddlewares.DelayedRetryMiddleware`."""

from __future__ import annotations

import sys
from typing import Any

import pytest
from scrapy import Request, Spider
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import NotConfigured
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.utils.test import get_crawler

from scrapy_extensions.downloadermiddlewares import DelayedRetryMiddleware

from .conftest import run


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _instant(_delay: float) -> None:
        return None

    monkeypatch.setattr(
        "scrapy_extensions.downloadermiddlewares.asyncio.sleep",
        _instant,
    )


def _mw(**settings: Any) -> DelayedRetryMiddleware:
    values: dict[Any, Any] = {"RETRY_ENABLED": True, **settings}
    return DelayedRetryMiddleware(Settings(values))


@pytest.fixture
def spider() -> Spider:
    crawler = get_crawler(Spider)
    return Spider.from_crawler(crawler, "test")


def test_invalid_http_codes_raise_not_configured() -> None:
    with pytest.raises(NotConfigured):
        _mw(DELAYED_RETRY_HTTP_CODES=["nonsense"])


def test_settings_are_parsed() -> None:
    mw = _mw(
        DELAYED_RETRY_HTTP_CODES=["555"],
        DELAYED_RETRY_DELAY=2.5,
        DELAYED_RETRY_BACKOFF=True,
    )
    assert mw.delayed_retry_http_codes == frozenset({555})
    assert mw.delayed_retry_delay == 2.5
    assert mw.delayed_retry_backoff is True
    assert mw.delayed_retry_backoff_max_delay == 25.0


def test_process_response_honours_dont_retry(spider: Spider) -> None:
    mw = _mw(DELAYED_RETRY_HTTP_CODES=["555"])
    request = Request("https://example.com", meta={"dont_retry": True})
    response = Response("https://example.com", status=555, request=request)
    assert run(mw.process_response(request, response, spider)) is response


def test_process_response_delegates_for_other_status(spider: Spider) -> None:
    mw = _mw(DELAYED_RETRY_HTTP_CODES=["555"])
    request = Request("https://example.com")
    response = Response("https://example.com", status=200, request=request)
    assert run(mw.process_response(request, response, spider)) is response


def test_process_response_returns_retry_request(spider: Spider) -> None:
    mw = _mw(DELAYED_RETRY_HTTP_CODES=["555"], DELAYED_RETRY_DELAY=1.0)
    request = Request("https://example.com")
    response = Response("https://example.com", status=555, request=request)
    result = run(mw.process_response(request, response, spider))
    assert isinstance(result, Request)
    assert result.meta["retry_delay"] == 1.0
    assert result.meta["retry_times"] == 1


def test_backoff_doubles_retry_delay(spider: Spider) -> None:
    mw = _mw(
        DELAYED_RETRY_HTTP_CODES=["555"],
        DELAYED_RETRY_DELAY=1.0,
        DELAYED_RETRY_BACKOFF=True,
    )
    request = Request("https://example.com", meta={"retry_delay": 3.0})
    response = Response("https://example.com", status=555, request=request)
    result = run(mw.process_response(request, response, spider))
    assert isinstance(result, Request)
    assert result.meta["retry_delay"] == 6.0


def test_returns_response_when_retries_exhausted(spider: Spider) -> None:
    mw = _mw(DELAYED_RETRY_HTTP_CODES=["555"], DELAYED_RETRY_TIMES=0)
    request = Request("https://example.com", meta={"max_retry_times": 0})
    response = Response("https://example.com", status=555, request=request)
    result = run(mw.process_response(request, response, spider))
    assert result is response


def test_awaits_coroutine_returned_by_parent(
    spider: Spider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Current Scrapy's RetryMiddleware.process_response is synchronous; this
    # exercises the defensive branch that awaits a coroutine result should a
    # future (or subclassed) parent return one.
    sentinel = Response("https://example.com")

    async def _async_parent(*_args: object, **_kwargs: object) -> Response:
        return sentinel

    monkeypatch.setattr(RetryMiddleware, "process_response", _async_parent)
    mw = _mw(DELAYED_RETRY_HTTP_CODES=["555"])
    request = Request("https://example.com")
    response = Response("https://example.com", status=200, request=request)
    assert run(mw.process_response(request, response, spider)) is sentinel


def test_negative_retry_times_means_unbounded(spider: Spider) -> None:
    mw = _mw(DELAYED_RETRY_HTTP_CODES=["555"], DELAYED_RETRY_TIMES=-1)
    request = Request("https://example.com", meta={"retry_times": sys.maxsize - 1})
    response = Response("https://example.com", status=555, request=request)
    result = run(mw.process_response(request, response, spider))
    assert isinstance(result, Request)
