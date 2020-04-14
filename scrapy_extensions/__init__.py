# -*- coding: utf-8 -*-

"""Initialisations."""

from .__version__ import VERSION, __version__
from .extensions import (
    DumpStatsExtension,
    LoopingExtension,
    MonitorDownloadsExtension,
    MultiFeedExporter,
    NicerAutoThrottle,
)
from .items import URL_PROCESSOR, DATE_PROCESSOR, ArticleItem, TypedItem, WebpageItem
from .loaders import ArticleLoader, JsonLoader, WebpageLoader
from .loggers import QuietLogFormatter
from .middleware import DelayedRetry
from .pipelines import ValidatePipeline
from .spiders import ArticleSpider, WebsiteSpider
