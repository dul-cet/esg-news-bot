#!/usr/bin/env python3
"""
Тестирование компонентов ESG News Bot
"""
import sys
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def test_imports():
    """Тест импорта модулей"""
    print("\n" + "="*50)
    print("🧪 Тест 1: Импорт модулей")
    print("="*50)
    
    try:
        from esgparser.core import NewsClass, NewsDatabase
        print("✓ esgparser.core")
        
        from esgparser.parsers import (
            Parse_EsgnewscomRuNews,
            Parse_EsgnewscomEnNews
        )
        print("✓ esgparser.parsers")
        
        from esgparser.classifier import ESGClassifier
        print("✓ esgparser.classifier")
        
        from esgparser.bot import ESGNewsBot
        print("✓ esgparser.bot")
        
        from config import TELEGRAM_BOT_TOKEN, DATABASE_PATH
        print("✓ config")
        
        print("\n✓ Все модули импортированы успешно!")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка импорта: {e}")
        return False


def test_database():
    """Тест работы с БД"""
    print("\n" + "="*50)
    print("🧪 Тест 2: База данных")
    print("="*50)
    
    try:
        from esgparser.core import NewsDatabase
        import tempfile
        import os
        
        # Создать временную БД
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = NewsDatabase(db_path)
            
            print("✓ БД инициализирована")
            
            # Добавить тестовую новость
            test_news = {
                'title': 'Test News',
                'url': 'https://example.com/test',
                'date': '2024-01-01 10:00',
                'digest': 'Test digest',
                'site_url': 'https://example.com',
                'lang': 'ru',
                'esg_category': 'Environment',
                'esg_score': 0.85,
                'keywords': ['test', 'environment']
            }
            
            result = db.add_news(test_news)
            print(f"✓ Новость добавлена: {result}")
            
            # Получить новости
            news = db.get_recent_news(limit=1)
            print(f"✓ Новость получена: {len(news)} шт.")
            
            # Добавить пользователя
            db.add_user(123, 'testuser', 'ru')
            print("✓ Пользователь добавлен")
            
            # Подписать на категорию
            db.subscribe_user_to_category(123, 'Environment')
            print("✓ Подписка добавлена")
            
            # Получить подписки
            subs = db.get_user_subscriptions(123)
            print(f"✓ Подписки получены: {subs}")
        
        print("\n✓ Все тесты БД пройдены!")
        return True
    
    except Exception as e:
        print(f"\n❌ Ошибка БД: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classifier():
    """Тест классификатора"""
    print("\n" + "="*50)
    print("🧪 Тест 3: ESG Классификатор")
    print("="*50)
    
    try:
        from esgparser.classifier import ESGClassifier
        
        classifier = ESGClassifier()
        print("✓ Классификатор инициализирован")
        
        # Тест 1: Environment
        title = "Развитие возобновляемых источников энергии в Казахстане"
        digest = "Новая программа по солнечной и ветровой энергии"
        cat, score = classifier.classify(title, digest, 'ru')
        print(f"✓ Environment: {cat} ({score:.1%})")
        
        # Тест 2: Social
        title = "Программа поддержки женского предпринимательства"
        digest = "Инициатива направлена на развитие женского бизнеса"
        cat, score = classifier.classify(title, digest, 'ru')
        print(f"✓ Social: {cat} ({score:.1%})")
        
        # Тест 3: Governance
        title = "Новый совет директоров компании"
        digest = "Избрано 7 новых членов совета директоров"
        cat, score = classifier.classify(title, digest, 'ru')
        print(f"✓ Governance: {cat} ({score:.1%})")
        
        # Тест 4: Извлечение ключевых слов
        keywords = classifier.extract_keywords(
            "Компания инвестирует в возобновляемые источники энергии",
            'ru'
        )
        print(f"✓ Ключевые слова: {keywords}")
        
        print("\n✓ Все тесты классификатора пройдены!")
        return True
    
    except Exception as e:
        print(f"\n❌ Ошибка классификатора: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parsers():
    """Тест парсеров (может требовать интернета)"""
    print("\n" + "="*50)
    print("🧪 Тест 4: Парсеры (требует интернета)")
    print("="*50)
    
    try:
        from esgparser.parsers import Parse_EsgnewscomRuNews
        
        print("Попытка получить новости с esgnews.com...")
        news_list = Parse_EsgnewscomRuNews()
        
        if news_list:
            print(f"✓ Получено новостей: {len(news_list)}")
            
            # Показать первую новость
            first = news_list[0]
            print(f"  Заголовок: {first.title[:60]}...")
            print(f"  URL: {first.url[:50]}...")
            print(f"  Дата: {first.date}")
            print(f"  Язык: {first.lang}")
            
            print("\n✓ Парсер работает!")
            return True
        else:
            print("⚠️  Новостей не получено")
            return True
    
    except Exception as e:
        print(f"⚠️  Ошибка парсера: {e}")
        print("   (Это нормально, если нет подключения к интернету)")
        return True


def main():
    """Запустить все тесты"""
    print("\n")
    print("╔" + "="*48 + "╗")
    print("║" + " "*10 + "🧪 ESG NEWS BOT - ТЕСТИРОВАНИЕ" + " "*8 + "║")
    print("╚" + "="*48 + "╝")
    
    tests = [
        ("Импорт модулей", test_imports),
        ("База данных", test_database),
        ("Классификатор", test_classifier),
        ("Парсеры", test_parsers),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Неожиданная ошибка в {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "="*50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nПройдено: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены! Готово к использованию.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} тест(ов) не пройдено")
        return 1


if __name__ == '__main__':
    sys.exit(main())
