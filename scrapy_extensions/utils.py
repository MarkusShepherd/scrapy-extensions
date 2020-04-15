# -*- coding: utf-8 -*-

"""Utility functions."""

import json

from urllib.parse import ParseResult, urlparse
from typing import Any, Iterable, Optional, Pattern, Union

from pytility import parse_date, to_str
from scrapy.utils.misc import arg_to_iter


def normalize_url(url, loader_context=None):
    """Expand URL fragments."""

    # TODO other normalizations, e.g., sort parameters etc

    try:
        return loader_context["response"].urljoin(url)
    except Exception:
        pass

    return "http:" + url if url.startswith("//") else url


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


def parse_json(
    file_or_string: Any, **kwargs
) -> Union[str, float, int, list, dict, None]:
    """Safely parse JSON string."""

    if file_or_string is None:
        return None

    try:
        return json.load(file_or_string, **kwargs)
    except Exception:
        pass

    try:
        return json.loads(to_str(file_or_string), **kwargs)
    except Exception:
        pass

    return None


def serialize_date(date, tzinfo=None):
    # TODO
    date = parse_date(date, tzinfo=tzinfo)
    return str(date) if date else None


def parse_geo(item):
    # TODO
    return None


def serialize_geo(item):
    # TODO
    return None
