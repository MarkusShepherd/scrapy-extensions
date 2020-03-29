# -*- coding: utf-8 -*-

""" Scrapy items """

import json
import logging

from datetime import datetime
from functools import partial

from pytility import clear_list, normalize_space, parse_date, parse_int
from scrapy import Field, Item
from scrapy.loader.processors import Identity, MapCompose

from .utils import validate_url

IDENTITY = Identity()
LOGGER = logging.getLogger(__name__)

URL_PROCESSOR = MapCompose(
    IDENTITY,
    normalize_space,
    normalize_url,
    partial(validate_url, schemes=frozenset(("http", "https"))),
)


def parse_json(item):
    # TODO
    return json.loads(item)


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


class TypedItem(Item):
    """ Item with typed fields """

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

        field = self.fields.get(key) or {}
        dtype = field.get("dtype")
        convert = field.get("dtype_convert")

        if self[key] is None or dtype is None or isinstance(self[key], dtype):
            return

        if not convert:
            raise ValueError(
                f"field <{key}> requires type {dtype} but found type {type(self[key])}"
            )

        convert = (
            convert
            if callable(convert)
            else dtype[0]
            if isinstance(dtype, tuple)
            else dtype
        )
        value = convert(self[key])

        assert isinstance(value, dtype) or value is None

        super().__setitem__(key, value)

    @classmethod
    def parse(cls, item):
        """ parses the fields in a dict-like item and returns a TypedItem """

        article = cls()

        for key, properties in cls.fields.items():
            value = item.get(key)

            if value is None or value == "":
                continue

            try:
                article[key] = value
                continue

            except ValueError:
                pass

            parser = properties.get("parser", IDENTITY)
            article[key] = parser(value)

        return article

    @classmethod
    def clean(cls, item):
        """ cleans the fields in a dict-like item and returns a TypedItem """

        return cls({k: v for k, v in item.items() if v and k in cls.fields})


def normalize_url(url, loader_context=None):
    """Expand URL fragments."""

    # TODO other normalizations, e.g., sort parameters etc

    try:
        return loader_context["response"].urljoin(url)
    except Exception:
        pass

    return "http:" + url if url.startswith("//") else url


class WebpageItem(TypedItem):
    """Item representing a scraped webpage's meta data."""

    url_canonical = Field(dtype=str, required=True, input_processor=URL_PROCESSOR)
    url_mobile = Field(dtype=str, input_processor=URL_PROCESSOR)
    url_amp = Field(dtype=str, input_processor=URL_PROCESSOR)
    url_scraped = Field(dtype=str, required=True, input_processor=URL_PROCESSOR)
    url_alt = Field(
        dtype=list,
        input_processor=URL_PROCESSOR,
        output_processor=clear_list,
        parser=parse_json,
    )
    url_thumbnail = Field(
        dtype=list,
        input_processor=URL_PROCESSOR,
        output_processor=clear_list,
        parser=parse_json,
    )

    published_at = Field(
        dtype=datetime,
        dtype_convert=parse_date,
        required=True,
        input_processor=MapCompose(IDENTITY, str, normalize_space, parse_date),
        serializer=serialize_date,
    )
    updated_at = Field(
        dtype=datetime,
        dtype_convert=parse_date,
        required=True,
        input_processor=MapCompose(IDENTITY, str, normalize_space, parse_date),
        serializer=serialize_date,
    )
    scraped_at = Field(
        dtype=datetime,
        dtype_convert=parse_date,
        required=True,
        input_processor=MapCompose(IDENTITY, str, normalize_space, parse_date),
        serializer=serialize_date,
    )

    title_full = Field(dtype=str, required=True)
    title_tag = Field(dtype=str)
    title_short = Field(dtype=str, required=True)
    author = Field(dtype=list, output_processor=clear_list, parser=parse_json)
    summary = Field(dtype=str)

    category = Field(dtype=list, output_processor=clear_list, parser=parse_json)
    keyword = Field(dtype=list, output_processor=clear_list, parser=parse_json)
    section = Field(dtype=list, output_processor=clear_list, parser=parse_json)

    country = Field(dtype=list, output_processor=clear_list, parser=parse_json)
    language = Field(dtype=list, output_processor=clear_list, parser=parse_json)
    location = Field(
        dtype=dict,
        dtype_convert=parse_geo,
        input_processor=MapCompose(parse_geo),
        serializer=serialize_geo,
    )

    full_html = Field(
        dtype=str, input_processor=MapCompose(IDENTITY, str, normalize_space)
    )
    meta_tags = Field(dtype=dict, input_processor=IDENTITY, parser=parse_json)
    parsely_info = Field(dtype=dict, input_processor=IDENTITY, parser=parse_json)


class ArticleItem(WebpageItem):
    """Item representing a webpage with main content."""

    content = Field(dtype=str)
    content_html = Field(dtype=str)

    article_info = Field(dtype=dict, input_processor=IDENTITY, parser=parse_json)

    source_name = Field(dtype=str)
    source_category = Field(dtype=list, output_processor=clear_list, parser=parse_json)
    source_url = Field(dtype=str, input_processor=URL_PROCESSOR)
    source_ranking = Field(
        dtype=int, dtype_convert=parse_int, input_processor=MapCompose(parse_int)
    )
    source_info = Field(dtype=dict, input_processor=IDENTITY, parser=parse_json)
