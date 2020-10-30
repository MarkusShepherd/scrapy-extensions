# -*- coding: utf-8 -*-

""" Scrapy item pipelines """

import logging

from typing import Dict

from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.misc import arg_to_iter

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


class BlurImagesPipeline(ImagesPipeline):
    """Calculate the blurhash of a given image."""

    cache: Dict[str, str]

    # TODO persistent cache, e.g., https://docs.python.org/3/library/dbm.html

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}

    # pylint: disable=no-self-use
    def calculate_blurhash(self, image, x_components=4, y_components=4):
        """Calculate the blurhash of a given image."""
        try:
            from .utils import calculate_blurhash

            return calculate_blurhash(image, x_components, y_components)

        except Exception:
            pass

        return None

    def blurhash_for_path(self, image_path):
        """Find blurhash in cache, or else load image and calculate it."""

        blurhash = self.cache.get(image_path)

        if blurhash:
            return blurhash

        try:
            full_path = self.store._get_filesystem_path(image_path)
            self.cache[image_path] = self.calculate_blurhash(full_path)
            LOGGER.debug("blurhash: %s = %s", full_path, self.cache[image_path])
        except Exception:
            self.cache[image_path] = None

        return self.cache[image_path]

    def add_blurhash(self, image_obj):
        """Add blurhash to image objects."""
        image_obj["blurhash"] = self.blurhash_for_path(image_obj.get("path"))
        return image_obj

    def get_images(self, response, request, info, *, item=None):
        for path, image, buf in super().get_images(
            response=response, request=request, info=info, item=item
        ):
            self.cache[path] = self.calculate_blurhash(image)
            LOGGER.debug("blurhash: %s = %s", path, self.cache[path])
            yield path, image, buf

    def item_completed(self, results, item, info):
        item = super().item_completed(results, item, info)

        if hasattr(item, "fields") and self.images_result_field not in item.fields:
            return item

        item[self.images_result_field] = [
            self.add_blurhash(image_obj)
            for image_obj in arg_to_iter(item.get(self.images_result_field))
        ]

        return item
