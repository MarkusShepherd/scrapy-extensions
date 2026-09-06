"""Tests for :class:`scrapy_extensions.pipelines.BlurHashPipeline`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from scrapy import Spider
from scrapy.exceptions import NotConfigured
from scrapy.utils.test import get_crawler

from scrapy_extensions import pipelines
from scrapy_extensions.pipelines import BlurHashPipeline

if TYPE_CHECKING:
    from pathlib import Path

_SPIDER = Spider("test")

_FULL_SETTINGS = {
    "IMAGES_STORE": "images",
    "IMAGES_RESULT_FIELD": "images",
    "BLURHASH_FIELD": "blurhashes",
}


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    pipelines._calculate_blurhash.cache_clear()


def test_from_crawler_requires_settings() -> None:
    crawler = get_crawler(Spider, {"IMAGES_STORE": "images"})
    with pytest.raises(NotConfigured):
        BlurHashPipeline.from_crawler(crawler)


def test_from_crawler_builds_pipeline(tmp_path: Path) -> None:
    crawler = get_crawler(Spider, {**_FULL_SETTINGS, "IMAGES_STORE": str(tmp_path)})
    pipe = BlurHashPipeline.from_crawler(crawler)
    assert pipe.source_field == "images"
    assert pipe.target_field == "blurhashes"
    assert pipe.x_components == 4


def _pipeline(store: Path) -> BlurHashPipeline:
    return BlurHashPipeline(
        images_store=store,
        source_field="images",
        target_field="blurhashes",
    )


def test_process_image_obj_without_path_is_unchanged(tmp_path: Path) -> None:
    pipe = _pipeline(tmp_path)
    assert pipe.process_image_obj({"checksum": "abc"}) == {"checksum": "abc"}


def test_process_image_obj_missing_file_is_unchanged(tmp_path: Path) -> None:
    pipe = _pipeline(tmp_path)
    obj = {"path": "does-not-exist.jpg"}
    assert pipe.process_image_obj(obj) == obj


def test_process_image_obj_adds_blurhash(tmp_path: Path, image_file: Path) -> None:
    pipe = _pipeline(image_file.parent)
    result = pipe.process_image_obj({"path": image_file.name})
    assert isinstance(result["blurhash"], str)
    assert result["blurhash"]


def test_process_item_without_images_is_unchanged(tmp_path: Path) -> None:
    pipe = _pipeline(tmp_path)
    item = {"name": "thing"}
    assert pipe.process_item(item, _SPIDER) == {"name": "thing"}


def test_process_item_populates_target_field(tmp_path: Path, image_file: Path) -> None:
    pipe = _pipeline(image_file.parent)
    item = {"images": [{"path": image_file.name}]}
    result = pipe.process_item(item, _SPIDER)
    assert isinstance(result["blurhashes"][0]["blurhash"], str)


def test_blurhash_libs_available_is_true_with_extra_installed() -> None:
    # The test environment installs the `blurhash` extra.
    assert pipelines._blurhash_libs_available() is True


def test_blurhash_libs_available_detects_missing_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_find_spec(name: str) -> object:
        return None if name == "numpy" else object()

    monkeypatch.setattr(pipelines, "find_spec", fake_find_spec)
    assert pipelines._blurhash_libs_available() is False


def test_blurhash_libs_available_handles_missing_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_a: object, **_kw: object) -> object:
        raise ModuleNotFoundError

    monkeypatch.setattr(pipelines, "find_spec", boom)
    assert pipelines._blurhash_libs_available() is False


def test_from_crawler_not_configured_without_blurhash_libs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pipelines, "_blurhash_libs_available", lambda: False)
    crawler = get_crawler(Spider, {**_FULL_SETTINGS, "IMAGES_STORE": str(tmp_path)})
    with pytest.raises(NotConfigured):
        BlurHashPipeline.from_crawler(crawler)


def test_process_image_obj_handles_unreadable_image(tmp_path: Path) -> None:
    not_an_image = tmp_path / "broken.jpg"
    not_an_image.write_text("definitely not an image")
    pipe = _pipeline(tmp_path)
    result = pipe.process_image_obj({"path": "broken.jpg"})
    assert result["blurhash"] is None


def test_process_item_swallows_errors(
    tmp_path: Path,
    image_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipe = _pipeline(image_file.parent)

    def _boom(*_a: object, **_kw: object) -> None:
        raise RuntimeError

    monkeypatch.setattr(pipe, "process_image_obj", _boom)
    item = {"images": [{"path": image_file.name}]}
    result = pipe.process_item(item, _SPIDER)
    assert "blurhashes" not in result
