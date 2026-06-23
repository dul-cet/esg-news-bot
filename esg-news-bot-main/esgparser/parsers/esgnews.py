import time
from esgparser.core.ParsClasses import NewsClass
import requests
from bs4 import BeautifulSoup
import lxml
from datetime import datetime
import pytz
from urllib.parse import urlparse
from esgparser.core.net import safe_get

EsgnewscomRu_link = 'https://esgnews.com/ru/'
EsgnewscomEn_link = 'https://esgnews.com/'

class EsgNewsArticle(NewsClass):

    def __init__(self, soup: BeautifulSoup, lang, siteUrl):
        super().__init__()
        self.title = soup.find('a').text.strip().replace('\n', ' ')
        self.url = soup.find('a', href=True)['href'] 
        self.date = pytz.utc.localize(datetime.strptime(soup.find('time')['datetime'], '%Y-%m-%d %H:%M'))
        self.site_url = siteUrl
        self.lang = lang

    def getExtra(self, s):
        if urlparse(EsgnewscomRu_link).netloc == urlparse(self.url).netloc: 
            time.sleep(0.1)
            print(self.url)
            headers = {'User-Agent': 'My User Agent 1.0', }
            raw = safe_get(self.url, session=s, headers=headers)
            soup = BeautifulSoup(raw.text, 'lxml')

            try:
                self.image_url = soup.find('figure').find('img', src=True)['src']  
            except: 
                print('Esgnews image error')

            try:
                soup = soup.find('div',
                             {'class': 'simple-text tt-content title-droid margin-big tw-text-base tw-leading-relaxed'})
                self.digest = soup.find('p').text.strip()  # получение первого обзаца
            except: 
                print('Esgnews digest error')


def Parse_EsgnewscomNewsBase(link):
    headers = {'User-Agent': 'My User Agent 1.0', }
    session = requests.Session()

    raw = safe_get(link, session=session, headers=headers)
    soup = BeautifulSoup(raw.text, 'lxml')

    list0 = soup.find_all('div',
                          {"class": "tw-flex tw-items-start tw-flex-wrap tw-relative tw-z-0 tw-max-w-3xl -tw-m-2"})

    return list0


def myFunc(l: EsgNewsArticle):
    return l.date


def MakeUniq(list2: list):
    # Сортирует по дате
    list2.sort(key=myFunc, reverse=True)

    i = 0
    while i + 1 < len(list2):
        if list2[i].title == list2[i + 1].title:
            list2.pop(i)
        else:
            i += 1

    return list2


def Parse_EsgnewscomRuNews():
    list0 = Parse_EsgnewscomNewsBase(EsgnewscomRu_link)
    list2 = [EsgNewsArticle(l, 'ru', EsgnewscomRu_link) for l in list0]

    return list2


def Parse_EsgnewscomEnNews():
    list0 = Parse_EsgnewscomNewsBase(EsgnewscomEn_link)
    list2 = [EsgNewsArticle(l, 'en', EsgnewscomEn_link) for l in list0]

    list2 = MakeUniq(list2)

    return list2
