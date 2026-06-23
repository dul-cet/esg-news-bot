import time
from esgparser.core.ParsClasses import NewsClass
import requests
from bs4 import BeautifulSoup
import lxml
from datetime import datetime
import pytz
from esgparser.core.net import safe_get

class TengrinewsArticle(NewsClass):
    def __init__(self, soup: BeautifulSoup, lang, siteUrl):
        super().__init__()
        self.title = soup.find('a').text.strip().replace('\n', ' ')
        self.url = soup.find('a', href=True)['href']
        if not self.url.startswith('http'):
            self.url = siteUrl.rstrip('/') + self.url
        self.date = None  # Tengrinews может иметь разные форматы дат
        self.site_url = siteUrl
        self.lang = lang

    def getExtra(self, session):
        time.sleep(0.1)
        headers = {'User-Agent': 'My User Agent 1.0'}
        try:
            raw = safe_get(self.url, session=session, headers=headers)
            soup = BeautifulSoup(raw.text, 'lxml')

            # Извлечение даты
            date_elem = soup.find('time') or soup.find('span', class_='date')
            if date_elem:
                try:
                    self.date = pytz.utc.localize(datetime.fromisoformat(date_elem.get('datetime', '')))
                except:
                    pass

            # Извлечение описания
            desc_elem = soup.find('meta', {'name': 'description'}) or soup.find('p')
            if desc_elem:
                self.digest = desc_elem.get('content', desc_elem.text.strip())[:200]

            # Извлечение изображения
            img_elem = soup.find('meta', {'property': 'og:image'})
            if img_elem:
                self.image_url = img_elem.get('content')

        except Exception as e:
            print(f"Tengrinews extra error: {e}")

def Parse_Tengrinews(max_pages=3):
    """
    Парсер для Tengrinews.kz
    """
    base_url = 'https://tengrinews.kz'
    articles = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}/esg/" if page == 1 else f"{base_url}/esg/page/{page}/"

        headers = {'User-Agent': 'My User Agent 1.0'}
        try:
            response = safe_get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')

            news_blocks = soup.find_all('div', class_='tn-article-item')

            for block in news_blocks:
                try:
                    article = TengrinewsArticle(block, 'kk', base_url)  # kk - казахский
                    articles.append(article)
                except:
                    continue

        except Exception as e:
            print(f"Tengrinews page {page} error: {e}")
            break

    return articles