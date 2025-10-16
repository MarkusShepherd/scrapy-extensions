"""Extensions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from scrapy.extensions.throttle import AutoThrottle
from scrapy.signals import spider_closed, spider_opened
from scrapy.utils.misc import arg_to_iter
from twisted.internet.task import LoopingCall

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from scrapy import Spider
    from scrapy.core.downloader import Slot
    from scrapy.crawler import Crawler
    from scrapy.http import Response

LOGGER = logging.getLogger(__name__)


class NicerAutoThrottle(AutoThrottle):
    """Autothrottling with exponential backoff depending on status codes."""

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> NicerAutoThrottle:
        http_codes_settings = crawler.settings.getlist("AUTOTHROTTLE_HTTP_CODES")

        try:
            http_codes = (
                int(http_code) for http_code in arg_to_iter(http_codes_settings)
            )

        except ValueError:
            LOGGER.exception("Invalid HTTP code: %s", http_codes_settings)
            http_codes = None

        return cls(crawler, http_codes)

    def __init__(
        self,
        crawler: Crawler,
        http_codes: Iterable[int] | None = None,
    ):
        super().__init__(crawler)
        self.http_codes: frozenset[int] = frozenset(
            filter(None, arg_to_iter(http_codes)),
        )
        LOGGER.info("Throttle requests on status codes: %s", sorted(self.http_codes))

    def _adjust_delay(
        self,
        slot: Slot,
        latency: float,
        response: Response,
    ) -> None:
        super()._adjust_delay(slot, latency, response)

        if response.status not in self.http_codes:
            return

        new_delay = (
            min(2 * slot.delay, self.maxdelay) if self.maxdelay else 2 * slot.delay
        )

        LOGGER.debug(
            "Status <%d> throttled from %.1fs to %.1fs: %r",
            response.status,
            slot.delay,
            new_delay,
            response,
        )

        slot.delay = new_delay


# see https://github.com/scrapy/scrapy/issues/2173
class LoopingExtension:
    """Run a task in a loop."""

    task: Callable[..., object]
    _task: LoopingCall | None = None
    _interval: float

    def setup_looping_task(
        self,
        task: Callable[..., object],
        crawler: Crawler,
        interval: float,
    ) -> None:
        """Setup task to run periodically at a given interval."""

        self.task = task
        self._interval = interval
        crawler.signals.connect(
            self._spider_opened,
            signal=spider_opened,
        )
        crawler.signals.connect(
            self._spider_closed,
            signal=spider_closed,
        )

    def _spider_opened(self, spider: Spider) -> None:
        if self._task is None:
            self._task = LoopingCall(self.task, spider=spider)
        self._task.start(self._interval, now=False)

    def _spider_closed(self) -> None:
        if self._task is None:
            LOGGER.warning("No task was started")
            return

        if self._task.running:
            self._task.stop()
