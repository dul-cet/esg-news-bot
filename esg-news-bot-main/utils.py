"""
Утилиты для ESG News Bot
"""
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from esgparser.core import NewsDatabase


logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """Анализ собранных новостей"""
    
    def __init__(self, db: NewsDatabase):
        self.db = db
    
    def get_statistics(self) -> Dict:
        """Получить статистику по новостям"""
        all_news = self.db.get_recent_news(limit=1000)
        
        if not all_news:
            return {
                'total': 0,
                'by_category': {},
                'by_language': {},
                'by_source': {}
            }
        
        stats = {
            'total': len(all_news),
            'by_category': {},
            'by_language': {},
            'by_source': {}
        }
        
        for news in all_news:
            # По категориям
            cat = news.get('esg_category', 'Unknown')
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            
            # По языкам
            lang = news.get('lang', 'unknown')
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1
            
            # По источникам
            source = news.get('site_url', 'unknown')
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        return stats
    
    def print_statistics(self):
        """Вывести статистику"""
        stats = self.get_statistics()
        
        print("\n📊 Статистика собранных новостей")
        print("="*50)
        print(f"Всего новостей: {stats['total']}")
        
        if stats['by_category']:
            print("\nПо категориям ESG:")
            for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
        
        if stats['by_language']:
            print("\nПо языкам:")
            for lang, count in sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {lang}: {count}")
        
        if stats['by_source']:
            print("\nПо источникам:")
            for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {source}: {count}")
        print("="*50 + "\n")


class NewsFormatter:
    """Форматирование новостей для вывода"""
    
    @staticmethod
    def format_for_telegram(news: Dict) -> str:
        """Форматировать новость для Telegram"""
        text = (
            f"<b>{news.get('title', 'Без заголовка')}</b>\n\n"
            f"{news.get('digest', '')}\n\n"
        )
        
        if news.get('esg_category'):
            text += f"<i>ESG: {news['esg_category']}</i>\n"
        
        text += f"<a href=\"{news.get('url', '#')}\">Читать полностью</a>"
        
        return text
    
    @staticmethod
    def format_for_email(news: Dict) -> str:
        """Форматировать новость для Email"""
        text = f"Title: {news.get('title', 'Без заголовка')}\n"
        text += f"URL: {news.get('url', 'N/A')}\n"
        text += f"Date: {news.get('date', 'N/A')}\n"
        text += f"Category: {news.get('esg_category', 'Unknown')}\n"
        text += f"Language: {news.get('lang', 'unknown')}\n\n"
        text += f"Digest:\n{news.get('digest', '')}\n"
        
        return text
    
    @staticmethod
    def format_digest(news_list: List[Dict]) -> str:
        """Форматировать дайджест из нескольких новостей"""
        text = "<b>ESG News Digest</b>\n\n"
        
        for i, news in enumerate(news_list, 1):
            text += (
                f"{i}. <b>{news['title'][:60]}...</b>\n"
                f"   Category: {news.get('esg_category', 'Unknown')}\n"
                f"   <a href=\"{news['url']}\">Read</a>\n\n"
            )
        
        return text


class NewsValidator:
    """Валидация новостей"""
    
    @staticmethod
    def is_valid_news(news_dict: Dict) -> bool:
        """Проверить, является ли новость валидной"""
        required_fields = ['title', 'url', 'date', 'lang']
        
        for field in required_fields:
            if not news_dict.get(field):
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Проверить длину заголовка
        if len(news_dict.get('title', '')) < 5:
            logger.warning("Title is too short")
            return False
        
        # Проверить URL
        if not news_dict.get('url', '').startswith('http'):
            logger.warning("Invalid URL format")
            return False
        
        return True
    
    @staticmethod
    def validate_batch(news_list: List[Dict]) -> tuple[List[Dict], List[str]]:
        """Валидировать пакет новостей"""
        valid = []
        errors = []
        
        for i, news in enumerate(news_list):
            if NewsValidator.is_valid_news(news):
                valid.append(news)
            else:
                errors.append(f"News {i}: Invalid")
        
        return valid, errors


class NewsExporter:
    """Экспорт новостей в различные форматы"""
    
    @staticmethod
    def to_csv(news_list: List[Dict], filename: str = 'news_export.csv'):
        """Экспортировать в CSV"""
        import csv
        
        if not news_list:
            logger.warning("No news to export")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=news_list[0].keys())
                writer.writeheader()
                writer.writerows(news_list)
            
            logger.info(f"Exported {len(news_list)} news to {filename}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    @staticmethod
    def to_json(news_list: List[Dict], filename: str = 'news_export.json'):
        """Экспортировать в JSON"""
        import json
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Exported {len(news_list)} news to {filename}")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
    
    @staticmethod
    def to_html(news_list: List[Dict], filename: str = 'news_export.html'):
        """Экспортировать в HTML"""
        if not news_list:
            logger.warning("No news to export")
            return
        
        html = """<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .news { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .title { font-size: 18px; font-weight: bold; color: #333; }
        .category { color: #666; font-style: italic; }
        .url { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <h1>ESG News Export</h1>
"""
        
        for news in news_list:
            html += f"""    <div class="news">
        <div class="title">{news.get('title', 'N/A')}</div>
        <div class="category">Category: {news.get('esg_category', 'Unknown')}</div>
        <div>{news.get('digest', '')[:200]}...</div>
        <a href="{news.get('url', '#')}" class="url">Read</a>
        <small>Date: {news.get('date', 'N/A')}</small>
    </div>
"""
        
        html += """</body>
</html>"""
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Exported {len(news_list)} news to {filename}")
        except Exception as e:
            logger.error(f"Error exporting to HTML: {e}")
