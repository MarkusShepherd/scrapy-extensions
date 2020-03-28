# -*- coding: utf-8 -*-

"""Scrapy item loaders."""

import json

import jmespath

from pytility import normalize_space
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Identity, MapCompose, TakeFirst
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import flatten

from .items import WebpageItem


class JsonLoader(ItemLoader):
    """ enhance ItemLoader with JMESPath capabilities """

    def __init__(self, response=None, json_obj=None, **kwargs):
        response = response if hasattr(response, "text") else None
        super().__init__(response=response, **kwargs)

        if json_obj is None and response is not None:
            json_obj = json.loads(response.text)

        self.json_obj = json_obj
        self.context.setdefault("json", json_obj)

    def _get_jmes_values(self, jmes_paths):
        jmes_paths = arg_to_iter(jmes_paths)
        return flatten(
            jmespath.search(jmes_path, self.json_obj) for jmes_path in jmes_paths
        )

    def add_jmes(self, field_name, jmes, *processors, **kw):
        """ add values through JMESPath """

        values = self._get_jmes_values(jmes)
        self.add_value(field_name, values, *processors, **kw)

    def replace_jmes(self, field_name, jmes, *processors, **kw):
        """ replace values through JMESPath """

        values = self._get_jmes_values(jmes)
        self.replace_value(field_name, values, *processors, **kw)

    def get_jmes(self, jmes, *processors, **kw):
        """ get values through JMESPath """

        values = self._get_jmes_values(jmes)
        return self.get_value(values, *processors, **kw)


class WebpageLoader(ItemLoader):
    """Webpage item loader."""

    default_item_class = WebpageItem
    default_input_processor = MapCompose(Identity(), str, normalize_space)
    default_output_processor = TakeFirst()
