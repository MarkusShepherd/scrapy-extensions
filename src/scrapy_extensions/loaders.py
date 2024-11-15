"""Scrapy item loaders."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable, Self

import jmespath
import scrapy
from scrapy.loader import ItemLoader
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import flatten

if TYPE_CHECKING:
    from collections.abc import Iterable

    import scrapy.responsetypes


class JsonLoader(ItemLoader):
    """enhance ItemLoader with JMESPath capabilities"""

    def __init__(
        self,
        response: scrapy.responsetypes.Response | None = None,
        json_obj: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        response = response if hasattr(response, "text") else None
        super().__init__(response=response, **kwargs)

        if json_obj is None and response is not None:
            json_obj = json.loads(response.text)

        self.json_obj = json_obj
        self.context.setdefault("json", json_obj)

    def _get_jmes_values(self, jmes_paths: str | Iterable[str]) -> list[Any]:
        jmes_paths = arg_to_iter(jmes_paths)
        result = flatten(
            jmespath.search(jmes_path, self.json_obj) for jmes_path in jmes_paths
        )
        assert isinstance(result, list)
        return result

    def add_jmes(
        self,
        field_name: str,
        jmes: str | Iterable[str],
        *processors: Callable[..., Any],
        **kw: Any,
    ) -> Self:
        """add values through JMESPath"""

        values = self._get_jmes_values(jmes)
        self.add_value(field_name, values, *processors, **kw)
        return self

    def replace_jmes(
        self,
        field_name: str,
        jmes: str | Iterable[str],
        *processors: Callable[..., Any],
        **kw: Any,
    ) -> Self:
        """replace values through JMESPath"""

        values = self._get_jmes_values(jmes)
        self.replace_value(field_name, values, *processors, **kw)
        return self

    def get_jmes(
        self,
        jmes: str | Iterable[str],
        *processors: Callable[..., Any],
        **kw: Any,
    ) -> Any:
        """get values through JMESPath"""

        values = self._get_jmes_values(jmes)
        return self.get_value(values, *processors, **kw)
