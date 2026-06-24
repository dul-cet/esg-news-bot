import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

from esgparser.core.ParsClasses import NewsClass
from esgparser.core.net import safe_get


class ESGWorldArticle(NewsClass):
    def __init__(self, soup, lang, site_url):
        super().__init__()

        # Заголовок
        self.title = soup.text.strip()

        # Ссылка
        self.url = soup.find('a')['href']

        if not self.url.startswith('http'):
            self.url = site_url.rstrip('/') + self.url

        # Дата (примерная, если не найдена)
        self.date = pytz.utc.localize(datetime.utcnow())

        self.site_url = site_url
        self.lang = lang

    def getExtra(self, session):
        time.sleep(0.1)

        try:
            raw = safe_get(self.url, session=session)
            soup = BeautifulSoup(raw.text, 'lxml')

            # Описание
            p = soup.find('p')
            if p:
                self.digest = p.text.strip()

            # Картинка
            img = soup.find('img')
            if img and img.get('src'):
                self.image_url = img['src']

        except Exception as e:
            print("ESGWorld extra error:", e)


def Parse_ESGWorld():
    url = "https://esgworld.news/"
    articles = []

    try:
        raw = safe_get(url)
        soup = BeautifulSoup(raw.text, 'lxml')

        blocks = soup.select('h2.entry-title')

        for block in blocks:
            try:
                article = ESGWorldArticle(block, 'ru', url)
                articles.append(article)
            except:
                continue

    except Exception as e:
        print("ESGWorld parse error:", e)

    return articles