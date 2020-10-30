# -*- coding: utf-8 -*-

"""Utility functions."""

import json
import logging
import re

from datetime import timezone
from pathlib import Path
from urllib.parse import ParseResult, urlparse
from typing import Any, Dict, Iterable, Optional, Pattern, Tuple, Union

from pytility import parse_date, to_str
from scrapy.utils.misc import arg_to_iter

LOGGER = logging.getLogger(__name__)
DEFAULT_SEP = re.compile(r"\s*[,;:/|]\s*")


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


def serialize_date(date: Any, tzinfo: Optional[timezone] = None) -> Optional[str]:
    """Seralize a date into ISO format if possible."""

    parsed = parse_date(date, tzinfo)
    return (
        parsed.isoformat(timespec="seconds") if parsed else str(date) if date else None
    )


def _valid_geo(geo):
    if geo is None or geo.get("lat") is None or geo.get("lon") is None:
        return False

    try:
        return -90 <= geo["lat"] <= 90 and -180 <= geo["lon"] <= 180
    except Exception:
        LOGGER.exception("Invalid geo data: %s", geo)

    return False


def parse_geo(geo: Any) -> Optional[Dict[str, float]]:
    """Parse geo strings and objects."""

    if not geo:
        return None

    try:
        json_geo = json.loads(geo)
    except Exception:
        pass
    else:
        geo = json_geo

    try:
        result = {"lat": float(geo.get("lat")), "lon": float(geo.get("lon"))}
        return result if _valid_geo(result) else None
    except Exception:
        pass

    try:
        lat, lon = DEFAULT_SEP.split(geo)
        result = {"lat": float(lat), "lon": float(lon)}
        return result if _valid_geo(result) else None
    except Exception:
        pass

    try:
        import geohash

        lat, lon = geohash.decode(geo)
        result = {"lat": lat, "lon": lon}
        return result if _valid_geo(result) else None
    except Exception:
        pass

    try:
        # note that string geo-points are ordered as lat,lon,
        # while array geo-points are ordered as the reverse: lon,lat
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/geo-point.html
        lon, lat = geo
        result = {"lat": float(lat), "lon": float(lon)}
        return result if _valid_geo(result) else None
    except Exception:
        pass

    return None


def serialize_geo(geo: Any) -> Optional[str]:
    """Serialize geo object into "lat,lon" format if possible."""

    geo = parse_geo(geo)
    return "{lat:f},{lon:f}".format(**geo) if geo else None


def calculate_blurhash(
    image_path: Union[str, Path], x_components: int = 4, y_components: int = 4,
) -> str:
    """Calculate the blurhash of a given image."""

    import numpy as np
    from blurhash_numba import encode
    from PIL import Image, ImageOps

    image = Image.open(image_path)
    image = ImageOps.fit(image=image, size=(128, 128), centering=(0.5, 0))
    image_array = np.array(image.convert("RGB"), dtype=np.float)

    return encode(
        image=image_array, x_components=x_components, y_components=y_components
    )
