# -*- coding: utf-8 -*-

""" Scrapy item pipelines """

import logging

from scrapy.exceptions import DropItem

LOGGER = logging.getLogger(__name__)


class ValidatePipeline:
    """Validate items for required fields."""

    # pylint: disable=no-self-use,unused-argument
    def process_item(self, item, spider):
        """Verify if all required fields are present."""

        if all(
            item.get(field)
            for field in item.fields
            if item.fields[field].get("required")
        ):
            return item

        raise DropItem("Missing required field in {}".format(item))
