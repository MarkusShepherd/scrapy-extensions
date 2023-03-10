# -*- coding: utf-8 -*-

""" Scrapy item pipelines """

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Union

from scrapy.exceptions import DropItem, NotConfigured
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


class BlurHashPipeline:
    """Calculate the BlurHashes of the downloaded images."""

    images_store: Path
    source_field: str
    target_field: str
    x_components: int
    y_components: int

    @classmethod
    def from_crawler(cls, crawler):
        """Init from crawler."""

        images_store = crawler.settings.get("IMAGES_STORE")
        source_field = crawler.settings.get("IMAGES_RESULT_FIELD")
        target_field = crawler.settings.get("BLURHASH_FIELD")

        if not images_store or not source_field or not target_field:
            raise NotConfigured

        try:
            from scrapy_extensions.utils import calculate_blurhash
        except ImportError as exc:
            LOGGER.exception(
                "Unable to import libraries required for BlurHash, install with `images` option",
            )
            raise NotConfigured from exc

        x_components = crawler.settings.getint("BLURHASH_X_COMPONENTS", 4)
        y_components = crawler.settings.getint("BLURHASH_Y_COMPONENTS", 4)

        return cls(
            images_store=images_store,
            source_field=source_field,
            target_field=target_field,
            x_components=x_components,
            y_components=y_components,
        )

    def __init__(
        self,
        *,
        images_store: Union[str, Path],
        source_field: str,
        target_field: str,
        x_components: int = 4,
        y_components: int = 4,
    ):
        self.images_store = Path(images_store).resolve()
        self.source_field = source_field
        self.target_field = target_field
        self.x_components = x_components
        self.y_components = y_components

    @lru_cache(maxsize=1024)
    def _calculate_blurhash(
        self,
        *,
        path: Path,
        x_components: int,
        y_components: int,
    ) -> Optional[str]:
        try:
            from scrapy_extensions.utils import calculate_blurhash

            blurhash = calculate_blurhash(
                image=path,
                x_components=x_components,
                y_components=y_components,
            )

            LOGGER.debug("BlurHash of <%s> is <%s>", path, blurhash)

        except Exception:
            LOGGER.exception("Unable to calculate BlurHash for image <%s>", path)
            blurhash = None

        return blurhash

    def process_image_obj(
        self,
        image_obj: Dict[str, Any],
        x_components: int = 4,
        y_components: int = 4,
    ) -> Dict[str, Any]:
        """Calculate the BlurHash of a given image."""

        image_path = image_obj.get("path")
        if not image_path:
            return image_obj

        image_full_path = (self.images_store / image_path).resolve()
        if not image_full_path or not image_full_path.is_file():
            LOGGER.warning("Unable to locate image file <%s>", image_full_path)
            return image_obj

        # Don't modify the original object
        image_obj = image_obj.copy()

        image_obj["blurhash"] = self._calculate_blurhash(
            path=image_full_path,
            x_components=x_components,
            y_components=y_components,
        )

        return image_obj

    def process_item(self, item, spider):
        """Calculate the BlurHashes of the downloaded images."""

        # adding target field would result in error; return item as-is
        if hasattr(item, "fields") and self.target_field not in item.fields:
            return item

        item[self.target_field] = [
            self.process_image_obj(image_obj)
            for image_obj in arg_to_iter(item.get(self.source_field))
        ]

        return item
