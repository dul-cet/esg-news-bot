import re
from datetime import datetime
from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from esgparser.core.ParsClasses import NewsClass
from esgparser.core.net import safe_get


DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}


class GenericSiteArticle(NewsClass):
    def __init__(self, title: str, url: str, site_url: str, lang: str):
        super().__init__()
        self.title = title.strip()
        self.url = url
        self.site_url = site_url
        self.lang = lang

    def getExtra(self, session):
        try:
            raw = safe_get(self.url, session=session, headers=DEFAULT_HEADERS)
            soup = BeautifulSoup(raw.text, 'lxml')
            self.digest = _extract_digest(soup, fallback=self.title)
            self.date = _extract_date(soup)
            self.image_url = _extract_image(soup)
        except Exception:
            if not self.digest:
                self.digest = self.title


def _extract_digest(soup: BeautifulSoup, fallback: str = '') -> str:
    for attrs in (
        {'name': 'description'},
        {'property': 'og:description'},
        {'name': 'twitter:description'},
    ):
        meta = soup.find('meta', attrs=attrs)
        if meta and meta.get('content'):
            return meta.get('content').strip()

    for node in soup.find_all(['p', 'div']):
        text = node.get_text(' ', strip=True)
        if len(text) >= 80:
            return text[:400]

    return fallback[:400]


def _extract_image(soup: BeautifulSoup) -> Optional[str]:
    for attrs in (
        {'property': 'og:image'},
        {'name': 'twitter:image'},
    ):
        meta = soup.find('meta', attrs=attrs)
        if meta and meta.get('content'):
            return meta.get('content').strip()

    image = soup.find('img', src=True)
    if image:
        return image.get('src')
    return None


def _extract_date(soup: BeautifulSoup) -> Optional[datetime]:
    candidates = []
    for attrs in (
        {'property': 'article:published_time'},
        {'name': 'article:published_time'},
        {'itemprop': 'datePublished'},
        {'name': 'pubdate'},
        {'name': 'publish-date'},
    ):
        meta = soup.find('meta', attrs=attrs)
        if meta and meta.get('content'):
            candidates.append(meta.get('content').strip())

    time_node = soup.find('time')
    if time_node:
        if time_node.get('datetime'):
            candidates.append(time_node.get('datetime').strip())
        text_value = time_node.get_text(' ', strip=True)
        if text_value:
            candidates.append(text_value)

    for value in candidates:
        parsed = _parse_datetime(value)
        if parsed:
            return parsed
    return None


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.strip().replace('Z', '+00:00')
    normalized = normalized.replace(' UTC', '+00:00')
    if re.match(r'^\d{2}\.\d{2}\.\d{4}$', normalized):
        try:
            return datetime.strptime(normalized, '%d.%m.%Y')
        except Exception:
            return None

    for candidate in (normalized, normalized.split(' ')[0]):
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            continue
    return None


def Parse_GenericSite(
    start_url: str,
    lang: str = 'kk',
    include_patterns: Optional[Iterable[str]] = None,
    exclude_patterns: Optional[Iterable[str]] = None,
    max_items: int = 20,
) -> List[GenericSiteArticle]:
    raw = safe_get(start_url, headers=DEFAULT_HEADERS)
    soup = BeautifulSoup(raw.text, 'lxml')
    include_regexes = [re.compile(pattern) for pattern in (include_patterns or [])]
    exclude_regexes = [re.compile(pattern) for pattern in (exclude_patterns or [])]
    site_host = urlparse(start_url).netloc

    articles: List[GenericSiteArticle] = []
    seen_urls = set()

    for anchor in soup.find_all('a', href=True):
        href = urljoin(start_url, anchor.get('href'))
        title = anchor.get_text(' ', strip=True)
        if not title or len(title) < 20:
            continue
        if href in seen_urls:
            continue
        if urlparse(href).netloc != site_host:
            continue
        if include_regexes and not any(regex.search(href) for regex in include_regexes):
            continue
        if any(regex.search(href) for regex in exclude_regexes):
            continue

        articles.append(GenericSiteArticle(title=title, url=href, site_url=start_url, lang=lang))
        seen_urls.add(href)
        if len(articles) >= max_items:
            break

    return articles