import json
import requests
import lxml
from bs4 import BeautifulSoup
from esgparser.core.ParsClasses import NewsClass
from esgparser.core.net import safe_get

GovKzUrl = 'https://www.gov.kz/'
GovKzApiUrl = 'https://www.gov.kz/api/v1/public/content-manager/news?sort-by=created_date:DESC&page=1&size=5&directions=14993'

headersRu = {'User-Agent': 'My User Agent 1.0', 'Accept-Language': 'ru'}
headersKz = {'User-Agent': 'My User Agent 1.0', 'Accept-Language': 'kk'}


class GovkzNews(NewsClass):
    def __init__(self, a: json, lang, siteUrl):
        super().__init__()
        self.title = a['title']
        try:
            self.image_url = 'https://www.gov.kz' + BeautifulSoup(a.get('body', ''), 'lxml').find('img')['src']
        except:
            self.image_url = None
        
        self.digest = BeautifulSoup(a.get('body', ''), 'lxml').find('p').text.strip() if BeautifulSoup(a.get('body', ''), 'lxml').find('p') else a.get('title', '')
        url_base = 'https://www.gov.kz/memleket/entities/ardfm/press/news/details/'
        self.url = url_base + str(a['id']) + '?lang=' + lang
        self.date = a['created_date']
        self.site_url = siteUrl
        self.lang = lang

    def getExtra(self, session):
        """Получить дополнительную информацию"""
        pass


def Parse_GovkznewsBase(header):
    raw = safe_get(GovKzApiUrl, headers=header)
    data = raw.json()
    article_json_list = data.get("content", [])

    return article_json_list


def Parse_GovkznewsRu():
    article_json_list = Parse_GovkznewsBase(headersRu)
    article_list = [GovkzNews(a, 'ru', GovKzUrl) for a in article_json_list]

    return article_list


def Parse_GovkznewsKz():
    article_json_list = Parse_GovkznewsBase(headersKz)
    article_list = [GovkzNews(a, 'kk', GovKzUrl) for a in article_json_list]

    return article_list
