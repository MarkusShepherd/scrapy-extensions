# TODO:
# - QuietLogFormatter
# - DelayedRetry
# - NicerAutoThrottle
# - ValidatePipeline
# - BlurHashPipeline

# Implemented by now:
# - https://doc.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_jmes
# - https://docs.scrapy.org/en/latest/topics/extensions.html?highlight=periodiclog#periodic-log-extension
# - https://docs.scrapy.org/en/latest/topics/feed-exports.html?highlight=feedexporter#feeds

from scrapy_extensions.extensions import LoopingExtension

__all__ = [
    "LoopingExtension",
]
