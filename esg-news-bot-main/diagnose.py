#!/usr/bin/env python3
"""
Диагностический скрипт для проверки бота
"""
import logging
from config import GEMINI_API_KEY, GEMINI_CONFIG
from esgparser.core.database import NewsDatabase
from esgparser.classifier.esg_classifier import ESGClassifier

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_database():
    """Проверить БД"""
    print("\n🔍 Тест БД...")
    try:
        db = NewsDatabase()
        stats = db.get_database_stats()
        print(f"✅ БД работает. Новостей: {stats.get('news_count', 0)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

def test_classifier():
    """Проверить классификатор"""
    print("\n🔍 Тест классификатора...")
    try:
        classifier = ESGClassifier()
        category, score = classifier.classify("ESG новости", "текст о экологии", "ru")
        print(f"✅ Классификатор работает. Категория: {category}, Score: {score}")
        return True
    except Exception as e:
        print(f"❌ Ошибка классификатора: {e}")
        return False

def test_gemini():
    """Проверить базовую конфигурацию Gemini"""
    print("\n🔍 Тест Gemini конфигурации...")

    if not GEMINI_CONFIG.get('enabled'):
        print("⚠️  Gemini отключен в config.py")
        return False

    if not GEMINI_API_KEY:
        print("⚠️  Gemini API key не задан через переменные окружения")
        return False

    print(f"✅ Gemini включен. Модель: {GEMINI_CONFIG.get('model_name')}")
    return True

def main():
    print("=" * 50)
    print("🤖 Диагностика ESG News Bot")
    print("=" * 50)
    
    results = {
        'БД': test_database(),
        'Классификатор': test_classifier(),
        'Gemini': test_gemini(),
    }
    
    print("\n" + "=" * 50)
    print("📊 Результаты:")
    print("=" * 50)
    
    for name, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {name}")
    
    print("\n" + "=" * 50)
    
    if all(results.values()):
        print("✅ Все компоненты работают!")
        print("\nДля запуска бота выполните:")
        print("  python main.py")
    else:
        print("❌ Некоторые компоненты не работают.")
        print("Проверьте ошибки выше.")

if __name__ == "__main__":
    main()