# -*- coding: utf-8 -*-

"""Generic spiders."""

import json
import re

from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import jmespath

from scrapy import Spider
from scrapy.utils.misc import arg_to_iter

from .loaders import ArticleLoader, WebpageLoader

ID_REGEX = re.compile(r"\W+")


def meta_dict(response) -> dict:
    """ extract meta tags from response """

    meta = (
        (
            s.xpath("@name[.]").extract_first()
            or s.xpath("@property[.]").extract_first(),
            s.xpath("@content[.]").extract_first()
            or s.xpath("@value[.]").extract_first(),
        )
        for s in response.xpath(
            "//meta[(@name[.] or @property[.]) " "and (@content[.] or @value[.])]"
        )
    )
    return {
        ID_REGEX.sub("_", key).lower(): value for key, value in meta if key and value
    }


def parsely_dict(response) -> dict:
    """ extract parsely information from response """

    result = {}

    for text in response.xpath(
        "//script[@type = 'application/ld+json']/text()"
    ).extract():
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                # TODO merge recursively
                result.update(obj)
        except Exception:
            pass

    return result


class WebsiteSpider(Spider):
    """Spider to extract meta information from websites."""

    name = "website"
    loader_cls = WebpageLoader

    def parse(self, response):
        """To be implemented by subclass."""

        yield from arg_to_iter(self.parse_page(response))

    def parse_page(self, response, item=None):
        """Parse an HTML page."""

        now = datetime.now(timezone.utc).isoformat()

        meta = meta_dict(response)
        parsely = parsely_dict(response)

        response.meta["meta"] = meta
        response.meta["parsely"] = parsely

        loader = self.loader_cls(item=item, response=response)
        loader.context["response"] = response
        loader.context["meta"] = meta
        loader.context["parsely"] = parsely

        loader.add_xpath("url_canonical", "//link[@rel = 'canonical']/@href")
        loader.add_value("url_canonical", response.url)
        loader.add_xpath("url_amp", "//link[@rel = 'amphtml']/@href")
        loader.add_xpath("url_mobile", "//link[@rel = 'alternate' and @media]/@href")
        loader.add_xpath("url_mobile", "//link[@rel = 'amphtml']/@href")
        loader.add_value("url_scraped", response.url)
        loader.add_xpath("url_alt", "//link[@rel = 'alternate']/@href")

        loader.add_value(
            "url_thumbnail", jmespath.search("thumbnailUrl[].url", parsely)
        )
        loader.add_value("url_thumbnail", jmespath.search("thumbnailUrl.url", parsely))
        loader.add_value("url_thumbnail", parsely.get("thumbnailUrl"))
        loader.add_value("url_thumbnail", jmespath.search("image[].url", parsely))
        loader.add_value("url_thumbnail", jmespath.search("image.url", parsely))
        loader.add_value("url_thumbnail", parsely.get("image"))
        loader.add_value("url_thumbnail", meta.get("parsely_image_url"))
        loader.add_value("url_thumbnail", meta.get("twitter_image"))
        loader.add_value("url_thumbnail", meta.get("thumbnail"))
        loader.add_value("url_thumbnail", meta.get("thumbnail_url"))
        loader.add_value("url_thumbnail", meta.get("image"))
        loader.add_value("url_thumbnail", meta.get("og_image"))
        loader.add_value("url_thumbnail", meta.get("sailthru_image_thumb"))
        loader.add_value("url_thumbnail", meta.get("sailthru_image_full"))
        loader.add_value("url_thumbnail", meta.get("sailthru_lead_image"))
        loader.add_xpath("url_thumbnail", "//body//img/@src")

        loader.add_value("published_at", meta.get("pub_date"))
        loader.add_value("published_at", meta.get("pubdate"))
        loader.add_value("published_at", meta.get("pdate"))
        loader.add_value("published_at", meta.get("created_date"))
        loader.add_value("published_at", meta.get("date"))
        loader.add_value("published_at", meta.get("dc_date"))
        loader.add_value("published_at", parsely.get("dateCreated"))
        loader.add_value("published_at", parsely.get("datePublished"))
        loader.add_value("published_at", meta.get("parsely_pub_date"))
        loader.add_value("published_at", meta.get("article_published"))
        loader.add_value("published_at", now)
        loader.add_value("scraped_at", now)
        # TODO updated_at

        loader.add_value("title_full", meta.get("title"))
        loader.add_xpath("title_full", "//head/title/text()")
        loader.add_xpath("title_tag", "//head/title/text()")
        loader.add_value("title_short", parsely.get("headline"))
        loader.add_value("title_short", meta.get("headline"))
        loader.add_value("title_short", meta.get("parsely_title"))
        loader.add_value("title_short", meta.get("article_headline"))
        loader.add_value("title_short", meta.get("article_origheadline"))
        loader.add_value("title_short", meta.get("og_title"))
        loader.add_value("title_short", meta.get("dcterms_title"))
        loader.add_value("title_short", meta.get("sailthru_title"))
        loader.add_value("title_short", meta.get("twitter_title"))
        loader.add_xpath("title_short", "//head/title/text()")

        loader.add_value("author", meta.get("author"))
        loader.add_value("author", meta.get("dc_creator"))
        loader.add_value("author", meta.get("dcsext_author"))
        loader.add_value("author", jmespath.search("creator[].name", parsely))
        loader.add_value("author", jmespath.search("creator.name", parsely))
        loader.add_value("author", parsely.get("creator"))
        loader.add_value("author", jmespath.search("author[].name", parsely))
        loader.add_value("author", jmespath.search("author.name", parsely))
        loader.add_value("author", parsely.get("author"))
        loader.add_value("author", meta.get("parsely_author"))
        loader.add_value("author", meta.get("article_author_name"))
        loader.add_value("author", meta.get("og_author"))
        loader.add_value("author", meta.get("og_article_author"))
        loader.add_value("author", meta.get("sailthru_author"))
        loader.add_value("author", meta.get("twitter_creator"))
        loader.add_value("author", meta.get("blogger_name"))

        loader.add_value("summary", parsely.get("description"))
        loader.add_value("summary", parsely.get("articleBody"))
        loader.add_value("summary", meta.get("description"))
        loader.add_value("summary", meta.get("dc_description"))
        loader.add_value("summary", meta.get("og_description"))
        loader.add_value("summary", meta.get("twitter_description"))
        loader.add_value("summary", meta.get("abstract"))
        loader.add_value("summary", meta.get("article_summary"))
        loader.add_value("summary", meta.get("content"))
        loader.add_value("summary", meta.get("excerpt"))
        loader.add_value("summary", meta.get("sailthru_description"))

        if hasattr(response, "text"):
            loader.add_value("full_html", response.text)
        loader.add_xpath("full_html", "/html")

        loader.add_value("category", meta.get("category"))
        loader.add_value("category", meta.get("cg"))
        loader.add_value("category", meta.get("section"))
        loader.add_value("category", meta.get("sections"))
        loader.add_value("category", parsely.get("articleSection"))
        loader.add_value("category", meta.get("parsely_section"))
        loader.add_value("category", meta.get("article_section"))
        loader.add_value("category", meta.get("article_subsection"))
        loader.add_value("category", meta.get("article_type"))
        loader.add_value("category", meta.get("article_categories"))
        loader.add_value("category", meta.get("article_page"))
        loader.add_value("category", meta.get("og_article_section"))
        loader.add_value("category", meta.get("og_section"))
        loader.add_value("category", meta.get("channel"))
        loader.add_value("category", meta.get("dcsext_contentchannel"))
        loader.add_value("category", meta.get("page_topic"))

        loader.add_value("keyword", meta.get("keywords"))
        loader.add_value("keyword", meta.get("news_keywords"))
        loader.add_value("keyword", meta.get("tag"))
        loader.add_value("keyword", meta.get("tags"))
        loader.add_value("keyword", meta.get("article_tag"))
        loader.add_value("keyword", meta.get("og_article_tag"))
        loader.add_value("keyword", parsely.get("keywords"))
        loader.add_value("keyword", meta.get("parsely_tags"))
        loader.add_value("keyword", meta.get("sailthru_tags"))

        loader.add_value("country", meta.get("country"))
        loader.add_value("country", meta.get("country_origin"))
        loader.add_value("language", meta.get("language"))
        loader.add_value("language", meta.get("og_language"))
        loader.add_value("language", meta.get("og_locale"))
        loader.add_value("language", meta.get("dc_language"))
        loader.add_value("language", meta.get("dcterms_language"))
        loader.add_xpath("language", "/html/@lang")
        # seems XPath implementation cannot handle XML namespaces
        loader.add_xpath("language", "/html/@xml:lang")
        loader.add_value(
            "location",
            {
                "lat": jmespath.search("geo.latitude", parsely),
                "lon": jmespath.search("geo.longitude", parsely),
            },
        )
        loader.add_value(
            "location",
            {
                "lat": jmespath.search("location.geo.latitude", parsely),
                "lon": jmespath.search("location.geo.longitude", parsely),
            },
        )
        loader.add_value("location", meta.get("geo_position"))
        loader.add_value(
            "location",
            {
                "lat": meta.get("place_location_latitude"),
                "lon": meta.get("place_location_longitude"),
            },
        )

        loader.add_value("meta_tags", meta)
        loader.add_value("parsely_info", parsely)

        return loader.load_item()


class ArticleSpider(WebsiteSpider):
    """Spider to extract the main content of a webpage along with meta data."""

    name = "article"
    loader_cls = ArticleLoader

    def __init__(self, *args, **kwargs):
        from html2text import HTML2Text
        from readability import Document

        super().__init__(*args, **kwargs)

        self.document_cls = Document
        self.markdown_cls = HTML2Text

        self.readability_args = {}  # TODO

    def get_content(self, html):
        """Extract main content with readability."""

        if not html:
            return {}

        try:
            doc = self.document_cls(html, **self.readability_args)
            return {
                "content": doc.summary(html_partial=True),
                "title": doc.title(),
                "title_short": doc.short_title(),
            }

        except Exception:
            self.logger.exception("Unable to create summary")

        return {}

    def to_markdown(self, html):
        """Turn HTML into Markdown."""

        if not html:
            return None

        markdown_maker = self.markdown_cls(bodywidth=0)

        markdown_maker.ignore_emphasis = True
        markdown_maker.ignore_images = True
        markdown_maker.ignore_links = True
        markdown_maker.ignore_tables = True

        result = markdown_maker.handle(html)

        try:
            markdown_maker.close()
        except Exception:
            self.logger.exception("There was an error in HTML2Text")
        finally:
            del markdown_maker

        return result

    def parse(self, response):
        """To be implemented by subclass."""

        yield from arg_to_iter(self.parse_article(response))

    def parse_article(self, response, item=None):
        """Parses an article."""

        meta = response.meta.get("meta") or meta_dict(response)
        parsely = response.meta.get("parsely") or parsely_dict(response)

        item = self.parse_page(response=response, item=item)
        url_canonical = urlparse(item.get("url_canonical") or response.url)
        title_full = item.get("title_full")
        title_short = item.get("title_short")
        summary = item.get("summary")

        loader = self.loader_cls(item=item, response=response)
        loader.context["response"] = response

        main_content = self.get_content(response.text)

        content_html = main_content.get("content") or ""
        content = self.to_markdown(content_html)

        loader.add_value("content", content)
        loader.add_value("content", summary)
        loader.add_value("content_html", content_html)

        loader.replace_value("title_full", main_content.get("title"))
        loader.add_value("title_full", title_full)
        loader.replace_value("title_short", main_content.get("title_short"))
        loader.add_value("title_short", title_short)

        # TODO add article and source info

        loader.add_value("source_name", jmespath.search("publisher.name", parsely))
        loader.add_value("source_name", meta.get("og_site_name"))
        loader.add_value("source_name", meta.get("dcsext_websitename"))
        loader.add_value("source_name", meta.get("page_site"))
        loader.add_value("source_name", meta.get("ms_sitename"))
        loader.add_value("source_name", meta.get("shareaholic_site_name"))
        loader.add_value("source_name", meta.get("twitter_app_name_googleplay"))
        loader.add_value("source_name", meta.get("twitter_app_name_iphone"))
        loader.add_value("source_name", meta.get("twitter_app_name_ipad"))
        loader.add_value("source_name", url_canonical.hostname)

        loader.add_value(
            "source_url",
            urlunparse((url_canonical.scheme, url_canonical.netloc, "/", "", "", "")),
        )

        return loader.load_item()
