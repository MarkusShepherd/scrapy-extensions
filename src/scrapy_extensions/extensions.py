"""Extensions."""

from __future__ import annotations

import logging
from typing import Callable

import scrapy
from twisted.internet.task import LoopingCall

LOGGER = logging.getLogger(__name__)


# see https://github.com/scrapy/scrapy/issues/2173
class LoopingExtension:
    """Run a task in a loop."""

    task: Callable[..., object]
    _task: LoopingCall | None = None
    _interval: float

    def setup_looping_task(
        self,
        task: Callable[..., object],
        crawler: scrapy.crawler.Crawler,
        interval: float,
    ) -> None:
        """Setup task to run periodically at a given interval."""

        self.task = task
        self._interval = interval
        crawler.signals.connect(
            self._spider_opened,
            signal=scrapy.signals.spider_opened,
        )
        crawler.signals.connect(
            self._spider_closed,
            signal=scrapy.signals.spider_closed,
        )

    def _spider_opened(self, spider: scrapy.Spider) -> None:
        if self._task is None:
            self._task = LoopingCall(self.task, spider=spider)
        self._task.start(self._interval, now=False)

    def _spider_closed(self) -> None:
        if self._task is None:
            LOGGER.warning("No task was started")
            return

        if self._task.running:
            self._task.stop()
