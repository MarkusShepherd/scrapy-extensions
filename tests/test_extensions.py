"""Tests for :mod:`scrapy_extensions.extensions`."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import Mock

from scrapy import Spider
from scrapy.extensions.throttle import AutoThrottle
from scrapy.http import Response
from scrapy.utils.test import get_crawler

from scrapy_extensions.extensions import LoopingExtension, NicerAutoThrottle

if TYPE_CHECKING:
    import pytest
    from scrapy.core.downloader import Slot


def _slot(delay: float) -> Slot:
    return cast("Slot", SimpleNamespace(delay=delay))


def _throttle(codes: list[object]) -> NicerAutoThrottle:
    crawler = get_crawler(
        Spider,
        {"AUTOTHROTTLE_ENABLED": True, "AUTOTHROTTLE_HTTP_CODES": codes},
    )
    return NicerAutoThrottle.from_crawler(crawler)


class TestNicerAutoThrottle:
    def test_from_crawler_parses_http_codes(self) -> None:
        assert _throttle(["429", "503"]).http_codes == frozenset({429, 503})

    def test_from_crawler_with_invalid_http_codes(self) -> None:
        assert _throttle(["not-a-code"]).http_codes == frozenset()

    def test_adjust_delay_doubles_on_matching_status(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AutoThrottle, "_adjust_delay", lambda *a, **kw: None)
        throttle = _throttle([429])
        throttle.maxdelay = 60.0
        slot = _slot(2.0)
        throttle._adjust_delay(slot, 1.0, Response("https://e.com", status=429))
        assert slot.delay == 4.0

    def test_adjust_delay_respects_maxdelay(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AutoThrottle, "_adjust_delay", lambda *a, **kw: None)
        throttle = _throttle([429])
        throttle.maxdelay = 5.0
        slot = _slot(4.0)
        throttle._adjust_delay(slot, 1.0, Response("https://e.com", status=429))
        assert slot.delay == 5.0

    def test_adjust_delay_ignores_other_status(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AutoThrottle, "_adjust_delay", lambda *a, **kw: None)
        throttle = _throttle([429])
        throttle.maxdelay = 60.0
        slot = _slot(2.0)
        throttle._adjust_delay(slot, 1.0, Response("https://e.com", status=200))
        assert slot.delay == 2.0


class TestLoopingExtension:
    def test_setup_connects_signals(self) -> None:
        ext = LoopingExtension()
        task = Mock()
        ext.setup_looping_task(task, get_crawler(Spider), 30.0)
        assert ext._interval == 30.0
        assert ext.task is task

    def test_spider_closed_without_task_warns(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        ext = LoopingExtension()
        ext._spider_closed()
        assert "No task was started" in caplog.text

    def test_open_starts_task_and_close_stops_it(self) -> None:
        ext = LoopingExtension()
        ext.setup_looping_task(Mock(), get_crawler(Spider), 3600.0)
        ext._spider_opened(Spider("test"))
        assert ext._task is not None
        assert ext._task.running
        ext._spider_closed()
        assert not ext._task.running
