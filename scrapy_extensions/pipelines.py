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

        fields = getattr(item, "fields", {})
        missing = [
            field
            for field, info in fields.items()
            if info.get("required") and not item.get(field)
        ]

        if missing:
            raise DropItem(f"required fields missing {missing} from item {item}")

        return item
