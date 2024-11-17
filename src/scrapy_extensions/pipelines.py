"""Scrapy item pipelines"""

from __future__ import annotations

import logging
from functools import lru_cache
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any

from itemadapter.adapter import ItemAdapter
from scrapy.exceptions import NotConfigured
from scrapy.utils.misc import arg_to_iter

if TYPE_CHECKING:
    from scrapy import Spider
    from scrapy.crawler import Crawler

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1024)
def _calculate_blurhash(
    path: Path,
    x_components: int,
    y_components: int,
) -> str | None:
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


class BlurHashPipeline:
    """Calculate the BlurHashes of the downloaded images."""

    images_store: Path
    source_field: str
    target_field: str
    x_components: int
    y_components: int

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> BlurHashPipeline:
        """Init from crawler."""

        images_store = crawler.settings.get("IMAGES_STORE")
        source_field = crawler.settings.get("IMAGES_RESULT_FIELD")
        target_field = crawler.settings.get("BLURHASH_FIELD")

        if not images_store or not source_field or not target_field:
            raise NotConfigured

        if not find_spec("scrapy_extensions.utils", "calculate_blurhash"):
            LOGGER.error(
                "Unable to import libraries required for BlurHash, "
                "install with `blurhash` option",
            )
            raise NotConfigured

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
        images_store: str | Path,
        source_field: str,
        target_field: str,
        x_components: int = 4,
        y_components: int = 4,
    ) -> None:
        self.images_store = Path(images_store).resolve()
        self.source_field = source_field
        self.target_field = target_field
        self.x_components = x_components
        self.y_components = y_components

    def process_image_obj(
        self,
        image_obj: dict[str, Any],
        x_components: int = 4,
        y_components: int = 4,
    ) -> dict[str, Any]:
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

        image_obj["blurhash"] = _calculate_blurhash(
            path=image_full_path,
            x_components=x_components,
            y_components=y_components,
        )

        return image_obj

    def process_item(self, item: Any, spider: Spider) -> Any:  # noqa: ARG002
        """Calculate the BlurHashes of the downloaded images."""

        adapter = ItemAdapter(item)

        image_objs = tuple(arg_to_iter(adapter.get(self.source_field)))
        if not image_objs:
            return item

        try:
            adapter[self.target_field] = [
                self.process_image_obj(image_obj) for image_obj in image_objs
            ]
        except Exception:
            LOGGER.exception("Unable to add field <%s> to the item", self.target_field)

        return item
