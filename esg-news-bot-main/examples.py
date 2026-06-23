"""
Примеры использования ESG News Bot
"""

# Пример 1: Сбор новостей вручную
from esgparser.parsers import Parse_EsgnewscomRuNews, Parse_informkzRuNews
from esgparser.core import NewsDatabase
from esgparser.classifier import ESGClassifier

def example_manual_collection():
    """Ручной сбор новостей из одного источника"""
    print("="*50)
    print("Пример 1: Ручной сбор новостей")
    print("="*50)
    
    # Получить новости с esgnews.com
    news_list = Parse_EsgnewscomRuNews()
    print(f"\nПолучено новостей: {len(news_list)}")
    
    # Инициализировать классификатор
    classifier = ESGClassifier()
    
    # Покажем первые 3 новости
    for i, news in enumerate(news_list[:3]):
        print(f"\n{i+1}. {news.title}")
        print(f"   URL: {news.url}")
        print(f"   Дата: {news.date}")
        
        # Классифицировать
        category, score = classifier.classify(news.title, news.digest, news.lang)
        print(f"   Категория: {category} ({score:.1%})")


# Пример 2: Работа с БД
def example_database():
    """Работа с базой данных"""
    print("\n" + "="*50)
    print("Пример 2: Работа с БД")
    print("="*50)
    
    db = NewsDatabase()
    
    # Получить последние новости
    recent_news = db.get_recent_news(limit=5)
    print(f"\nПоследние {len(recent_news)} новостей:")
    
    for i, news in enumerate(recent_news, 1):
        print(f"{i}. {news['title'][:60]}...")
        print(f"   Категория: {news['esg_category']}")
        print(f"   Язык: {news['lang']}")
    
    # Получить новости по категории
    env_news = db.get_news_by_category('Environment', limit=3)
    print(f"\nНовости по Environment ({len(env_news)} шт.):")
    for news in env_news:
        print(f"  • {news['title'][:50]}...")


# Пример 3: Классификация текста
def example_classification():
    """Примеры классификации новостей"""
    print("\n" + "="*50)
    print("Пример 3: Классификация новостей")
    print("="*50)
    
    classifier = ESGClassifier()
    
    texts = [
        {
            "title": "Казахстан увеличил долю возобновляемых источников энергии",
            "digest": "Новая программа развития солнечной и ветровой энергии",
            "lang": "ru"
        },
        {
            "title": "Компания внедрила программу поддержки женского предпринимательства",
            "digest": "Инициатива направлена на поддержку женщин в бизнесе",
            "lang": "ru"
        },
        {
            "title": "Новый совет директоров назначен на трехлетний срок",
            "digest": "Решение принято на годовом собрании акционеров",
            "lang": "ru"
        }
    ]
    
    for text in texts:
        category, score = classifier.classify(
            text['title'],
            text['digest'],
            text['lang']
        )
        keywords = classifier.extract_keywords(
            f"{text['title']} {text['digest']}",
            text['lang'],
            limit=3
        )
        
        print(f"\nТекст: {text['title'][:50]}...")
        print(f"Категория: {category} ({score:.1%})")
        print(f"Ключевые слова: {', '.join(keywords)}")


# Пример 4: Работа с пользователями
def example_users():
    """Работа с пользователями и подписками"""
    print("\n" + "="*50)
    print("Пример 4: Работа с пользователями")
    print("="*50)
    
    db = NewsDatabase()
    
    # Добавить пользователя
    user_id = 123456789
    db.add_user(user_id, 'testuser', 'ru')
    print(f"\nПользователь добавлен: {user_id}")
    
    # Подписать на категории
    db.subscribe_user_to_category(user_id, 'Environment')
    db.subscribe_user_to_category(user_id, 'Social')
    print("Подписан на категории: Environment, Social")
    
    # Получить подписки
    subs = db.get_user_subscriptions(user_id)
    print(f"Текущие подписки: {', '.join(subs)}")
    
    # Получить новости по подпискам
    for category in subs:
        news_list = db.get_news_by_category(category, limit=2)
        print(f"\n{category} новости ({len(news_list)} шт.):")
        for news in news_list:
            print(f"  • {news['title'][:50]}...")


# Пример 5: Полный цикл сбора и обработки
def example_full_cycle():
    """Полный цикл: сбор -> классификация -> сохранение"""
    print("\n" + "="*50)
    print("Пример 5: Полный цикл")
    print("="*50)
    
    classifier = ESGClassifier()
    db = NewsDatabase()
    
    print("\n1. Сбор новостей...")
    news_list = Parse_EsgnewscomRuNews()
    print(f"   Получено: {len(news_list)} новостей")
    
    print("\n2. Классификация...")
    added = 0
    for news in news_list[:5]:  # Обработать первые 5
        # Классифицировать
        category, score = classifier.classify(news.title, news.digest, news.lang)
        
        if score >= 0.3:  # Минимальная уверенность
            news.esg_category = category
            news.esg_score = score
            news.keywords = classifier.extract_keywords(
                f"{news.title} {news.digest}",
                news.lang,
                limit=5
            )
            
            # Добавить в БД
            if db.add_news(news.to_dict()):
                print(f"   ✓ Добавлена: {news.title[:50]}... ({category})")
                added += 1
    
    print(f"\n3. Результат: добавлено {added} новостей")
    print(f"   Всего новостей в БД: {db.count_news()}")


if __name__ == '__main__':
    try:
        example_manual_collection()
        example_classification()
        example_database()
        example_users()
        example_full_cycle()
        
        print("\n" + "="*50)
        print("Все примеры выполнены успешно!")
        print("="*50)
    
    except Exception as e:
        print(f"\nОшибка при выполнении примеров: {e}")
        print("\nУбедитесь, что:")
        print("  1. Установлены все зависимости (pip install -r requirements.txt)")
        print("  2. На компьютере есть подключение к интернету")
        print("  3. Сайты парсеров доступны")
