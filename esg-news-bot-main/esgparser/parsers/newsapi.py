import requests
from esgparser.core.ParsClasses import NewsClass
from datetime import datetime
import pytz
from esgparser.core.net import safe_get

class NewsAPIArticle(NewsClass):
    def __init__(self, article_data):
        super().__init__()
        self.title = article_data.get('title', '')
        self.url = article_data.get('url', '')
        self.date = datetime.fromisoformat(article_data.get('publishedAt', '').replace('Z', '+00:00')) if article_data.get('publishedAt') else None
        if self.date:
            self.date = pytz.utc.localize(self.date)
        self.site_url = 'https://newsapi.org'
        self.lang = 'en'  # NewsAPI в основном на английском
        self.digest = article_data.get('description', '')

    def getExtra(self, session):
        # NewsAPI уже предоставляет description, но можно добавить больше логики если нужно
        pass

def Parse_NewsAPI_ESG(api_key, query='ESG OR "environmental social governance"', max_pages=1):
    """
    Парсер для NewsAPI.org с фильтром по ESG темам
    """
    base_url = 'https://newsapi.org/v2/everything'
    articles = []

    for page in range(1, max_pages + 1):
        params = {
            'q': query,
            'apiKey': api_key,
            'page': page,
            'pageSize': 100,  # Максимум 100 на страницу
            'language': 'en',
            'sortBy': 'publishedAt'
        }

        try:
            response = safe_get(base_url, params=params)
        except Exception as e:
            print(f"Ошибка NewsAPI: {e}")
            break

        data = response.json()
        for article in data.get('articles', []):
            if article.get('title') and article.get('url'):
                news_item = NewsAPIArticle(article)
                articles.append(news_item)

    return articles