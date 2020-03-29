# -*- coding: utf-8 -*-

"""Generic spiders."""

import json
import re

from datetime import datetime, timezone

import jmespath

from pytility import normalize_space
from scrapy import Spider
from scrapy.utils.misc import arg_to_iter

from .loaders import WebpageLoader

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

        url_canonical = response.urljoin(
            normalize_space(
                response.xpath("//link[@rel = 'canonical']/@href[.]").extract_first()
            )
            or response.url
        )
        url_amp = normalize_space(
            response.xpath("//link[@rel = 'amphtml']/@href[.]").extract_first()
        )
        url_amp = response.urljoin(url_amp) if url_amp else None
        url_mobile = normalize_space(
            response.xpath(
                "//link[@rel = 'alternate' and @media]/@href[.]"
            ).extract_first()
        )
        url_mobile = response.urljoin(url_mobile) if url_mobile else url_amp
        url_alt = (
            normalize_space(url)
            for url in response.xpath("//link[@rel = 'alternate']/@href[.]").extract()
        )
        url_alt = [response.urljoin(url) for url in url_alt if url]

        meta = meta_dict(response)
        parsely = parsely_dict(response)

        loader = self.loader_cls(item=item, response=response)

        loader.add_value("url_canonical", url_canonical)
        loader.add_value("url_mobile", url_mobile)
        loader.add_value("url_amp", url_amp)
        loader.add_value("url_scraped", response.url)
        loader.add_value("url_alt", url_alt)
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
        loader.add_xpath("url_thumbnail", "//body//img/@src[.]")

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
        loader.add_xpath("title_full", "//head/title")
        loader.add_xpath("title_tag", "//head/title")
        loader.add_value("title_short", parsely.get("headline"))
        loader.add_value("title_short", meta.get("headline"))
        loader.add_value("title_short", meta.get("parsely_title"))
        loader.add_value("title_short", meta.get("article_headline"))
        loader.add_value("title_short", meta.get("article_origheadline"))
        loader.add_value("title_short", meta.get("og_title"))
        loader.add_value("title_short", meta.get("dcterms_title"))
        loader.add_value("title_short", meta.get("sailthru_title"))
        loader.add_value("title_short", meta.get("twitter_title"))
        loader.add_xpath("title_short", "//head/title")

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
