import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def Parse_ESGWorld():
    url = "https://esgworld.news/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    seen = set()

    # ищем все ссылки
    for a in soup.find_all("a", href=True):
        link = a["href"]

        # нормализуем ссылку
        if not link.startswith("http"):
            link = urljoin(url, link)

        # фильтр — только статьи
        if "esgworld.news" not in link:
            continue
        if "/tag/" in link or "/category/" in link:
            continue

        # убираем дубликаты
        if link in seen:
            continue
        seen.add(link)

        title = a.get_text(strip=True)

        # пропускаем пустые
        if not title or len(title) < 20:
            continue

        articles.append({
            "title": title,
            "link": link,
            "description": "",
            "lang": "ru"
        })

        if len(articles) >= 20:
            break

    print(f"[ESGWORLD] найдено статей: {len(articles)}")
    return articles