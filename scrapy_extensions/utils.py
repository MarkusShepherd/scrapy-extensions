# -*- coding: utf-8 -*-

"""Utility functions."""

from urllib.parse import ParseResult, urlparse
from typing import Iterable, Optional, Pattern, Union

from scrapy.utils.misc import arg_to_iter


def _match(string: str, comparison: Union[str, Pattern]) -> bool:
    return (
        string == comparison
        if isinstance(comparison, str)
        else bool(comparison.match(string))
    )


def parse_url(
    url: Union[str, ParseResult, None],
    hostnames: Optional[Iterable[Union[str, Pattern]]] = None,
) -> Optional[ParseResult]:
    """Parse URL and optionally filter for hosts."""
    url = urlparse(url) if isinstance(url, str) else url
    hostnames = tuple(arg_to_iter(hostnames))
    return (
        url
        if url
        and url.hostname
        and url.path
        and (
            not hostnames
            or any(_match(url.hostname, hostname) for hostname in hostnames)
        )
        else None
    )


def validate_url(
    url: Union[str, ParseResult, None],
    hostnames: Optional[Iterable[Union[str, Pattern]]] = None,
    schemes: Optional[Iterable[Union[str, Pattern]]] = None,
) -> Optional[str]:
    """Returns cleaned up URL iff valid with scheme, hostname, and path."""
    url = parse_url(url=url, hostnames=hostnames)
    schemes = frozenset(arg_to_iter(schemes))
    return (
        url.geturl()
        if url is not None and url.scheme and (not schemes or url.scheme in schemes)
        else None
    )
