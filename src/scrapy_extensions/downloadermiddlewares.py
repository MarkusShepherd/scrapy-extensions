"""Scrapy downloader middleware"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Callable

from scrapy.downloadermiddlewares.retry import RetryMiddleware, get_retry_request
from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message

if TYPE_CHECKING:
    from scrapy import Request, Spider
    from scrapy.http import Response
    from scrapy.settings import Settings
    from twisted.internet import defer

LOGGER = logging.getLogger(__name__)


class DelayedRetryMiddleware(RetryMiddleware):
    """retry requests with a delay"""

    def __init__(
        self,
        settings: Settings,
    ):
        super().__init__(settings)

        delayed_retry_http_codes_settings = settings.getlist("DELAYED_RETRY_HTTP_CODES")
        try:
            delayed_retry_http_codes = (
                int(http_code) for http_code in delayed_retry_http_codes_settings
            )
        except ValueError as exc:
            LOGGER.exception(
                "Invalid http code(s) in DELAYED_RETRY_HTTP_CODES: %s",
                delayed_retry_http_codes_settings,
            )
            raise NotConfigured from exc
        self.delayed_retry_http_codes = frozenset(
            filter(None, delayed_retry_http_codes),
        )

        self.delayed_retry_max_retry_times = settings.getint("DELAYED_RETRY_TIMES", -1)
        self.delayed_retry_priority_adjust = settings.getint(
            "DELAYED_RETRY_PRIORITY_ADJUST",
            self.priority_adjust,
        )
        self.delayed_retry_delay = settings.getfloat("DELAYED_RETRY_DELAY", 1)
        self.delayed_retry_backoff = settings.getbool("DELAYED_RETRY_BACKOFF")
        self.delayed_retry_backoff_max_delay = settings.getfloat(
            "DELAYED_RETRY_BACKOFF_MAX_DELAY",
            10 * self.delayed_retry_delay,
        )

    def process_response(
        self,
        request: Request,
        response: Response,
        spider: Spider,
    ) -> Response | defer.Deferred[Callable[..., Response]]:
        """retry certain requests with delay"""

        if request.meta.get("dont_retry"):
            return response

        if response.status in self.delayed_retry_http_codes:
            reason = response_status_message(response.status)
            return self._delayed_retry(request, reason, spider) or response

        return super().process_response(request, response, spider)

    def _delayed_retry(
        self,
        request: Request,
        reason: str,
        spider: Spider,
    ) -> defer.Deferred[Callable[..., Response]] | None:
        from twisted.internet import defer, reactor

        max_retry_times = request.meta.get(
            "max_retry_times",
            self.delayed_retry_max_retry_times,
        )
        if max_retry_times < 0:
            max_retry_times = sys.maxsize
        priority_adjust = request.meta.get(
            "priority_adjust",
            self.delayed_retry_priority_adjust,
        )

        req = get_retry_request(
            request=request,
            spider=spider,
            reason=reason,
            max_retry_times=max_retry_times,
            priority_adjust=priority_adjust,
        )

        if req is None:
            return None

        delay = request.meta.get("retry_delay", self.delayed_retry_delay)
        req.meta["retry_delay"] = (
            min(2 * delay, self.delayed_retry_backoff_max_delay)
            if self.delayed_retry_backoff
            else delay
        )

        LOGGER.debug("Retry request %r in %.1f second(s)", req, delay)

        deferred: defer.Deferred[Callable[..., Response]] = defer.Deferred()
        deferred.addCallback(lambda req: req)
        reactor.callLater(delay, deferred.callback, req)  # type: ignore[attr-defined]

        return deferred
