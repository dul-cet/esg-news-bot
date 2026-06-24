"""
Главный файл для запуска ESG News Bot
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import asyncio
import logging
import time
from datetime import datetime, timedelta
import requests
from config import (
    TELEGRAM_BOT_TOKEN,
    DATABASE_PATH,
    PARSERS_CONFIG,
    CLASSIFIER_CONFIG,
    LOG_LEVEL
)
from esgparser.core import NewsDatabase
from esgparser.classifier import ESGClassifier
from esgparser.bot import ESGNewsBot
from esgparser.parsers import (
    Parse_EsgnewscomRuNews,
    Parse_EsgnewscomEnNews,
    Parse_GovkznewsRu,
    Parse_GovkznewsKz,
    Parse_informkzRuNews,
    Parse_NewsAPI_ESG,
    Parse_Tengrinews,
    Parse_RSSFeeds,
    Parse_GenericSite,
    Parse_ESGWorld,
)

# Настройка логирования
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsAggregator:
    """Агрегатор новостей ESG"""
    
    def __init__(self):
        self.db = NewsDatabase(DATABASE_PATH)
        self.classifier = ESGClassifier(
            use_nlp=CLASSIFIER_CONFIG.get('use_nlp', False),
            db_path=DATABASE_PATH,
        )
        self.parsers = {
            'Parse_EsgnewscomRuNews': Parse_EsgnewscomRuNews,
            'Parse_EsgnewscomEnNews': Parse_EsgnewscomEnNews,
            'Parse_ESGWorld': Parse_ESGWorld,
            'Parse_GovkznewsRu': Parse_GovkznewsRu,
            'Parse_GovkznewsKz': Parse_GovkznewsKz,
            'Parse_informkzRuNews': Parse_informkzRuNews,
            'Parse_NewsAPI_ESG': Parse_NewsAPI_ESG,
            'Parse_Tengrinews': Parse_Tengrinews,
            'Parse_RSSFeeds': Parse_RSSFeeds,
            'Parse_GenericSite': Parse_GenericSite,
        }
        self.session = requests.Session()
        self._parser_last_run = {}

    def _get_parser_interval_hours(self, parser_name: str, parser_config: dict) -> int:
        """Return parser schedule interval clamped to the supported 1-6 hour range."""
        raw_interval = parser_config.get('interval_hours', 6)
        try:
            interval_hours = int(raw_interval)
        except (TypeError, ValueError):
            logger.warning(
                f"Некорректный interval_hours={raw_interval!r} для {parser_name}. Использую 6 часов."
            )
            interval_hours = 6

        clamped_interval = max(1, min(interval_hours, 6))
        if clamped_interval != interval_hours:
            logger.warning(
                f"Интервал для {parser_name} ограничен диапазоном 1-6 часов: {interval_hours} -> {clamped_interval}"
            )
        return clamped_interval

    def _is_parser_due(self, parser_name: str, parser_config: dict, now_ts: float) -> bool:
        """Check whether a parser should run now according to its configured interval."""
        interval_hours = self._get_parser_interval_hours(parser_name, parser_config)
        last_run_ts = self._parser_last_run.get(parser_name)
        if last_run_ts is None:
            return True
        return (now_ts - last_run_ts) >= interval_hours * 3600
    
    def collect_news(self, force_all: bool = True):
        """Собрать новости из всех источников."""
        logger.info("Начинается сбор новостей...")
        
        total_added = 0
        now_ts = time.time()
        
        for parser_name, parser_config in PARSERS_CONFIG.items():
            if not parser_config['enabled']:
                logger.info(f"Парсер {parser_name} отключен")
                continue

            if not force_all and not self._is_parser_due(parser_name, parser_config, now_ts):
                interval_hours = self._get_parser_interval_hours(parser_name, parser_config)
                logger.info(
                    f"Парсер {parser_name} пропущен: следующий запуск по расписанию через каждые {interval_hours} ч."
                )
                continue
            
            try:
                parser_func = self.parsers.get(parser_config['parser'])
                if not parser_func:
                    logger.warning(f"Парсер {parser_config['parser']} не найден")
                    continue
                
                logger.info(f"Запуск парсера: {parser_name}")
                
                # Вызвать парсер
                if parser_config['parser'] == 'Parse_informkzRuNews':
                    news_list = parser_func(max_pages=2)
                elif parser_config['parser'] == 'Parse_NewsAPI_ESG':
                    api_key = parser_config.get('api_key')
                    query = parser_config.get('query', 'ESG')
                    max_pages = parser_config.get('max_pages', 1)
                    if api_key and api_key != 'your_newsapi_key_here':
                        news_list = parser_func(api_key, query, max_pages)
                    else:
                        logger.warning(f"NewsAPI ключ не настроен для {parser_name}")
                        continue
                elif parser_config['parser'] == 'Parse_Tengrinews':
                    max_pages = parser_config.get('max_pages', 2)
                    news_list = parser_func(max_pages)
                elif parser_config['parser'] == 'Parse_RSSFeeds':
                    feed_urls = list(parser_config.get('feed_urls', []))
                    default_lang = parser_config.get('lang', 'en')
                    max_items_per_feed = parser_config.get('max_items_per_feed', 30)

                    # Group RSS feeds by language so each article gets correct lang.
                    feeds_by_lang = {default_lang: list(feed_urls)}

                    # Добавляем активные источники, настроенные администратором
                    managed_sources = self.db.get_active_rss_source_urls()
                    for source in managed_sources:
                        source_url = source.get('url')
                        source_lang = (source.get('lang') or default_lang).lower()
                        if not source_url:
                            continue
                        feeds_by_lang.setdefault(source_lang, [])
                        if source_url not in feeds_by_lang[source_lang]:
                            feeds_by_lang[source_lang].append(source_url)

                    has_any_feed = any(urls for urls in feeds_by_lang.values())
                    if not has_any_feed:
                        logger.warning(f"RSS feed_urls не настроены для {parser_name}")
                        continue

                    news_list = []
                    for lang, urls in feeds_by_lang.items():
                        if not urls:
                            continue
                        news_list.extend(
                            parser_func(urls, lang=lang, max_items_per_feed=max_items_per_feed)
                        )
                elif parser_config['parser'] == 'Parse_GenericSite':
                    news_list = parser_func(
                        start_url=parser_config['start_url'],
                        lang=parser_config.get('lang', 'kk'),
                        include_patterns=parser_config.get('include_patterns', []),
                        exclude_patterns=parser_config.get('exclude_patterns', []),
                        max_items=parser_config.get('max_items', 20),
                    )
                else:
                    news_list = parser_func()
                
                # Обработать каждую новость
                for news in news_list:
                    news.processing_status = 'collected'

                    # Получить дополнительную информацию
                    if hasattr(news, 'getExtra'):
                        try:
                            news.getExtra(self.session)
                        except Exception as e:
                            logger.warning(f"Ошибка при получении дополнительной информации: {e}")
                    
                    # Классифицировать новость
                    if CLASSIFIER_CONFIG['enabled']:
                        category, score = self.classifier.classify(
                            news.title,
                            news.digest,
                            news.lang
                        )
                        news.processing_status = 'classified'
                        news.esg_category = category
                        news.esg_score = score
                        
                        # Пропустить новости с низкой уверенностью
                        if score < CLASSIFIER_CONFIG['min_confidence']:
                           continue
                        # CLASSIFIER_CONFIG = {
                            #'enabled': True,
                            #'min_confidence': 0.0   # 🔥 было например 0.5
                            #}

                        allowed_categories = parser_config.get('allowed_categories') or []
                        if allowed_categories and category and category not in allowed_categories:
                            continue
                    
                    # Извлечь ключевые слова
                    keywords = self.classifier.extract_keywords(
                        f"{news.title} {news.digest}",
                        news.lang
                    )
                    news.keywords = keywords
                    news.processing_status = 'processed'
                    
                    # Добавить в БД
                    if self.db.add_news(news.to_dict()):
                        total_added += 1
                        logger.info(f"Добавлена новость: {news.title[:50]}...")

                self._parser_last_run[parser_name] = time.time()
                
                logger.info(f"Парсер {parser_name} завершен. Добавлено новостей: {len(news_list)}")
                
            except Exception as e:
                logger.error(f"Ошибка при запуске парсера {parser_name}: {e}")
        
        logger.info(f"Сбор новостей завершен. Всего добавлено: {total_added}")
        return total_added
    
    def _seconds_until_next_due(self, now_ts: float) -> int:
        """Return seconds until the nearest parser run based on interval_hours."""
        nearest = None
        for parser_name, parser_config in PARSERS_CONFIG.items():
            if not parser_config.get('enabled'):
                continue
            interval_sec = self._get_parser_interval_hours(parser_name, parser_config) * 3600
            last_run_ts = self._parser_last_run.get(parser_name)
            if last_run_ts is None:
                return 0
            remaining = max(0, int(interval_sec - (now_ts - last_run_ts)))
            nearest = remaining if nearest is None else min(nearest, remaining)
        return nearest if nearest is not None else 3600

    def schedule_collection(self):
        """Планировать сбор новостей строго по interval_hours каждого парсера."""
        logger.info("Запуск планировщика парсеров по interval_hours (1-6 часов)")
        
        while True:
            try:
                self.collect_news(force_all=False)
                sleep_seconds = max(60, self._seconds_until_next_due(time.time()))
                sleep_minutes = max(1, sleep_seconds // 60)
                logger.info(f"Следующая проверка расписания через ~{sleep_minutes} минут")
                time.sleep(sleep_seconds)
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                time.sleep(60)  # Попытка через 1 минуту
    
    def cleanup_old_news(self, days: int = 30):
        """Удалить старые новости (старше N дней)"""
        logger.info(f"Начинается очистка новостей старше {days} дней...")
        deleted = self.db.clear_old_news(days)
        logger.info(f"Удалено старых новостей: {deleted}")
        return deleted
    
    def cleanup_all_news(self):
        """Удалить все новости из БД"""
        logger.warning("⚠️  Удаление всех новостей из БД...")
        deleted = self.db.clear_all_news()
        logger.info(f"Удалено новостей: {deleted}")
        return deleted
    
    def cleanup_database(self):
        """Полностью очистить БД"""
        logger.warning("⚠️  ВНИМАНИЕ: Полная очистка БД (все таблицы будут удалены и переинициализированы)...")
        success = self.db.clear_all_data()
        if success:
            logger.info("БД успешно очищена")
        else:
            logger.error("Ошибка при очистке БД")
        return success
    
    def get_stats(self):
        """Получить статистику БД"""
        stats = self.db.get_database_stats()
        logger.info(f"Статистика БД: {stats}")
        return stats
    
    def search(self, query: str, use_ai: bool = False, top_k: int = 10):
        """Найти новости по запросу (SQL-поиск по базе)."""
        return self.db.search_news(query, limit=top_k)


def main():
    """Главная функция"""
    import sys
    
    logger.info("="*50)
    logger.info("Запуск ESG News Aggregator Bot")
    logger.info("="*50)
    
    # Инициализировать агрегатор
    aggregator = NewsAggregator()
    
    # Проверить аргументы командной строки
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'search':
            # Поиск новостей по запросу
            if len(sys.argv) < 3:
                logger.error("Не указан поисковый запрос")
                print_help()
                return
            query = sys.argv[2]
            use_ai = '--ai' in sys.argv
            top_k = 10
            for arg in sys.argv[3:]:
                if arg.isdigit():
                    top_k = int(arg)
            results = aggregator.search(query, use_ai=use_ai, top_k=top_k)
            logger.info(f"Найдено {len(results)} результатов")
            for idx, news in enumerate(results, 1):
                print(f"{idx}. {news.get('title')} ({news.get('date')})")
                print(f"   {news.get('url')}")
            return
        
        elif command == 'cleanup-old':
            # Очистить старые новости (default 30 дней)
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            aggregator.cleanup_old_news(days)
            return
        
        elif command == 'cleanup-all':
            # Очистить все новости
            confirm = input("Вы уверены что хотите удалить ВСЕ новости? (yes/no): ")
            if confirm.lower() == 'yes':
                aggregator.cleanup_all_news()
            else:
                logger.info("Очистка отменена")
            return
        
        elif command == 'cleanup-db':
            # Полная очистка БД
            confirm = input("Вы уверены что хотите полностью очистить БД? (yes/no): ")
            if confirm.lower() == 'yes':
                aggregator.cleanup_database()
            else:
                logger.info("Очистка БД отменена")
            return
        
        elif command == 'stats':
            # Вывести статистику БД
            aggregator.get_stats()
            return
        
        elif command == 'collect':
            # Запустить сбор новостей один раз
            aggregator.collect_news()
            return
        
        elif command == 'help':
            print_help()
            return
    
    # Режим нормального запуска
    # Инициализировать бот
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_telegram_bot_token':
        logger.warning("⚠️  ВНИМАНИЕ: Установите TELEGRAM_BOT_TOKEN в config.py или переменные окружения!")
        logger.info("Запуск только агрегатора (без Telegram бота)")
        # Запустить сбор новостей один раз
        aggregator.collect_news()
    else:
        # Запустить первый сбор новостей
        logger.info("Первый сбор новостей...")
        aggregator.collect_news()
        
        # Запустить сбор новостей в отдельном потоке
        import threading
        collection_thread = threading.Thread(
    target=aggregator.schedule_collection,
    daemon=True
)
        collection_thread.start()
        
        logger.info("Запуск Telegram Bot...")
        bot = ESGNewsBot(TELEGRAM_BOT_TOKEN, aggregator.db)
        
        try:
            # Запустить бот в основном потоке
            bot.run()
        except KeyboardInterrupt:
            logger.info("Бот остановлен")


def print_help():
    """Вывести справку по командам"""
    help_text = """
ESG News Aggregator Bot - Справка по командам
=============================================

Использование: python main.py [command] [args]

Команды:
  collect                 - Запустить сбор новостей один раз
  search <query> [N]      - Поиск новостей по тексту (N=количество, default=10)
                            можно добавить флаг --ai для поиска по эмбеддингам
  cleanup-old N           - Удалить новости старше N дней (default: 30)
  cleanup-all             - Удалить все новости из БД
  cleanup-db              - Полностью очистить БД (пересоздать все таблицы)
  stats                   - Показать статистику БД
  help                    - Показать эту справку
  (без аргументов)        - Запустить бот в нормальном режиме

Примеры:
  python main.py                  # Запустить бот
  python main.py collect          # Собрать новости
  python main.py search "earthquake"     # Простое текстовое совпадение
  python main.py search "earthquake" 20  # Поиск 20 новостей
  python main.py search "earthquake" --ai # ИИ-расширенный поиск
  python main.py cleanup-old 7    # Удалить новости старше 7 дней
  python main.py stats            # Показать статистику БД
    """
    print(help_text)


if __name__ == '__main__':
    main()
