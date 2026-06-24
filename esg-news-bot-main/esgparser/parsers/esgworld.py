import feedparser
from datetime import datetime


class ESGWorldParser:
    def __init__(self, config):
        self.config = config

    def fetch(self):
        all_news = []

        for url in self.config.get("feed_urls", []):
            feed = feedparser.parse(url)

            for entry in feed.entries[: self.config.get("max_items_per_feed", 10)]:
                news = {
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "summary": entry.get("summary", ""),
                    "published": self.parse_date(entry),
                    "lang": self.config.get("lang", "ru"),
                }
                all_news.append(news)

        print(f"[ESGWORLD] найдено: {len(all_news)}")
        return all_news

    def parse_date(self, entry):
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        return datetime.utcnow()