from datetime import datetime
from typing import Iterable, List, Optional
import re

import feedparser
import pytz
from bs4 import BeautifulSoup

from esgparser.core.ParsClasses import NewsClass


KAZAKH_CHARS = set("әіңғүұқөһӘІҢҒҮҰҚӨҺ")
KAZAKH_HINT_WORDS = {
    "және", "үшін", "бойынша", "бүгін", "қазақстан", "ел", "жаңалық",
    "министр", "деді", "туралы", "болады", "жыл", "астана", "алматы",
}
RUSSIAN_HINT_WORDS = {
    "и", "в", "на", "по", "что", "как", "из", "для", "сегодня",
    "россии", "казахстана", "новости", "это", "будет", "году", "москва",
}


class RSSArticle(NewsClass):
    """Universal news entity created from RSS feed entries."""

    def __init__(self, entry: dict, feed_url: str, lang: str = "en"):
        super().__init__()
        self.title = (entry.get("title") or "").strip()
        self.url = entry.get("link") or ""
        raw_digest = entry.get("summary") or entry.get("description") or ""
        self.digest = _clean_text(raw_digest)
        self.date = _parse_entry_date(entry)
        self.site_url = feed_url
        self.lang = _detect_article_lang(f"{self.title} {self.digest}", default_lang=lang)
        self.image_url = _extract_image(entry)

    def getExtra(self, session):
        # RSS entries already contain most fields; no extra HTTP fetch is required.
        return


def _parse_entry_date(entry: dict) -> Optional[datetime]:
    if entry.get("published_parsed"):
        return datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
    if entry.get("updated_parsed"):
        return datetime(*entry.updated_parsed[:6], tzinfo=pytz.utc)
    return None


def _extract_image(entry: dict) -> Optional[str]:
    media = entry.get("media_content") or []
    if media and isinstance(media, list):
        first = media[0]
        if isinstance(first, dict):
            return first.get("url")

    links = entry.get("links") or []
    for link in links:
        if isinstance(link, dict) and link.get("type", "").startswith("image/"):
            return link.get("href")
    return None


def _clean_text(value: str) -> str:
    """Convert small HTML fragments from RSS into readable plain text."""
    if not value:
        return ""
    text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _detect_article_lang(text: str, default_lang: str = "en") -> str:
    """Heuristic language detection for RSS titles/descriptions.

    We especially correct the common case where Kazakhstan feeds are configured as
    'kk' but actual article text is Russian.
    """
    sample = (text or "").strip()
    if not sample:
        return default_lang

    if any(ch in KAZAKH_CHARS for ch in sample):
        return "kk"

    lower = sample.lower()
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", lower)
    if not words:
        return default_lang

    has_cyrillic = bool(re.search(r"[а-яА-ЯёЁ]", lower))
    if not has_cyrillic:
        return "en"

    kk_score = sum(1 for w in words if w in KAZAKH_HINT_WORDS)
    ru_score = sum(1 for w in words if w in RUSSIAN_HINT_WORDS)

    if kk_score > ru_score:
        return "kk"
    return "ru"


def Parse_RSSFeeds(
    feed_urls: Iterable[str],
    lang: str = "en",
    max_items_per_feed: int = 30,
) -> List[RSSArticle]:
    """Parse multiple RSS feeds and return normalized news entities."""
    articles: List[RSSArticle] = []

    for feed_url in feed_urls:
        parsed = feedparser.parse(feed_url)
        entries = parsed.get("entries", [])[:max_items_per_feed]
        for entry in entries:
            article = RSSArticle(entry, feed_url, lang=lang)
            if article.title and article.url:
                articles.append(article)

    return articles
