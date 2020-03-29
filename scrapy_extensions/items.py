# -*- coding: utf-8 -*-

""" Scrapy items """

import logging

from scrapy import Item
from scrapy.loader.processors import Identity

IDENTITY = Identity()
LOGGER = logging.getLogger(__name__)


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
