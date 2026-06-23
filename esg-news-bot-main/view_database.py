"""
Утилита для просмотра содержимого базы данных
"""
import sqlite3
import json
from tabulate import tabulate
from datetime import datetime
from config import DATABASE_PATH


class DatabaseViewer:
    """Просмотр содержимого БД"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
    
    def show_structure(self):
        """Показать структуру БД (все таблицы и колонки)"""
        print("\n" + "="*80)
        print("СТРУКТУРА БАЗЫ ДАННЫХ")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получить все таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Таблица: {table_name}")
            print("-" * 80)
            
            # Получить информацию о колонках
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Форматировать информацию о колонках
            header = ["№", "Колонка", "Тип", "Обязательное", "Default", "Primary Key"]
            col_data = []
            for col in columns:
                col_data.append([
                    col[0],
                    col[1],
                    col[2],
                    "Да" if col[3] else "Нет",
                    col[4] if col[4] else "-",
                    "Да" if col[5] else "Нет"
                ])
            
            print(tabulate(col_data, headers=header, tablefmt="grid"))
            
            # Показать количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 Количество записей: {count}")
        
        conn.close()
    
    def show_news(self, limit: int = 10):
        """Показать новости из таблицы news"""
        print("\n" + "="*80)
        print(f"НОВОСТИ (последние {limit})")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT id, title, url, date, esg_category, esg_score, created_at
            FROM news
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ Новостей нет")
        else:
            # Сокращенный вывод для удобства
            display_data = []
            for row in rows:
                display_data.append([
                    row[0],                              # id
                    row[1][:50] + "..." if len(row[1]) > 50 else row[1],  # title
                    row[2][:40] + "..." if len(row[2]) > 40 else row[2],  # url
                    row[3][:10] if row[3] else "-",     # date
                    row[4] if row[4] else "-",           # category
                    f"{row[5]:.2f}" if row[5] else "-"   # score
                ])
            
            headers = ["ID", "Заголовок", "URL", "Дата", "Категория", "Оценка"]
            print(tabulate(display_data, headers=headers, tablefmt="grid"))
        
        conn.close()
    
    def show_news_full(self, limit: int = 5):
        """Показать полную информацию о новостях"""
        print("\n" + "="*80)
        print(f"ПОЛНАЯ ИНФОРМАЦИЯ О НОВОСТЯХ (последние {limit})")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT * FROM news
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ Новостей нет")
        else:
            for idx, row in enumerate(rows, 1):
                print(f"\n📰 Новость #{idx} (ID: {row[0]})")
                print("-" * 80)
                print(f"  Заголовок:     {row[1]}")
                print(f"  URL:           {row[2]}")
                print(f"  Дата новости:  {row[3]}")
                print(f"  Краткое описание: {row[4][:100] if row[4] else 'N/A'}...")
                print(f"  Изображение:   {row[5] if row[5] else 'Нет'}")
                print(f"  Сайт:          {row[6] if row[6] else 'Нет'}")
                print(f"  Язык:          {row[7]}")
                print(f"  ESG категория: {row[8] if row[8] else '-'}")
                print(f"  ESG оценка:    {f'{row[9]:.3f}' if row[9] else '-'}")
                if row[10]:
                    try:
                        keywords = json.loads(row[10])
                        print(f"  Ключевые слова: {', '.join(keywords)}")
                    except:
                        print(f"  Ключевые слова: {row[10]}")
                print(f"  Создано:       {row[11]}")
                print(f"  Обновлено:     {row[12]}")
        
        conn.close()
    
    def show_users(self):
        """Показать пользователей"""
        print("\n" + "="*80)
        print("ПОЛЬЗОВАТЕЛИ")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, user_id, username, language, created_at FROM users')
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ Пользователей нет")
        else:
            headers = ["ID", "User ID", "Username", "Язык", "Дата регистрации"]
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        conn.close()
    
    def show_subscriptions(self):
        """Показать подписки пользователей"""
        print("\n" + "="*80)
        print("ПОДПИСКИ ПОЛЬЗОВАТЕЛЕЙ")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT us.id, u.username, us.esg_category, us.created_at
            FROM user_subscriptions us
            LEFT JOIN users u ON us.user_id = u.user_id
        ''')
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ Подписок нет")
        else:
            headers = ["ID", "Username", "ESG Категория", "Дата подписки"]
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        conn.close()
    
    def show_stats(self):
        """Показать статистику БД"""
        print("\n" + "="*80)
        print("СТАТИСТИКА БАЗЫ ДАННЫХ")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Статистика по новостям
        cursor.execute('SELECT COUNT(*) FROM news')
        news_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT lang) FROM news')
        langs_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT esg_category) FROM news')
        categories_count = cursor.fetchone()[0]
        
        # Статистика по категориям
        cursor.execute('''
            SELECT esg_category, COUNT(*) as count
            FROM news
            WHERE esg_category IS NOT NULL
            GROUP BY esg_category
            ORDER BY count DESC
        ''')
        categories = cursor.fetchall()
        
        # Статистика по языкам
        cursor.execute('''
            SELECT lang, COUNT(*) as count
            FROM news
            GROUP BY lang
            ORDER BY count DESC
        ''')
        langs = cursor.fetchall()
        
        # Статистика по пользователям
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_subscriptions')
        subs_count = cursor.fetchone()[0]
        
        print(f"\n📰 НОВОСТИ:")
        print(f"  • Всего новостей: {news_count}")
        print(f"  • Языков: {langs_count}")
        print(f"  • ESG категорий: {categories_count}")
        
        if categories:
            print(f"\n  Распределение по ESG категориям:")
            for cat, count in categories:
                print(f"    - {cat}: {count}")
        
        if langs:
            print(f"\n  Распределение по языкам:")
            for lang, count in langs:
                print(f"    - {lang}: {count}")
        
        print(f"\n👥 ПОЛЬЗОВАТЕЛИ:")
        print(f"  • Всего пользователей: {users_count}")
        print(f"  • Подписок: {subs_count}")
        
        conn.close()
    
    def show_all(self):
        """Показать всю информацию"""
        self.show_structure()
        self.show_stats()
        self.show_news()
        self.show_users()
        self.show_subscriptions()


def main():
    """Главная функция"""
    import sys
    
    viewer = DatabaseViewer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'structure':
            viewer.show_structure()
        elif command == 'news':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            viewer.show_news(limit)
        elif command == 'news-full':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            viewer.show_news_full(limit)
        elif command == 'users':
            viewer.show_users()
        elif command == 'subscriptions':
            viewer.show_subscriptions()
        elif command == 'stats':
            viewer.show_stats()
        elif command == 'all':
            viewer.show_all()
        elif command == 'help':
            print_help()
        else:
            print(f"Неизвестная команда: {command}")
            print_help()
    else:
        # По умолчанию показать все
        viewer.show_all()


def print_help():
    """Вывести справку"""
    help_text = """
Database Viewer - Просмотр базы данных
=======================================

Использование: python view_database.py [command]

Команды:
  structure     - Показать структуру БД (таблицы и колонки)
  stats         - Показать статистику БД
  news [N]      - Показать последние N новостей (default: 10)
  news-full [N] - Показать полную информацию о N новостях (default: 5)
  users         - Показать всех пользователей
  subscriptions - Показать подписки пользователей
  all           - Показать всю информацию (default)
  help          - Показать эту справку

Примеры:
  python view_database.py              # Показать все (default)
  python view_database.py stats        # Статистика БД
  python view_database.py news 20      # Показать 20 последних новостей
  python view_database.py news-full 10 # Полная информация о 10 новостях
    """
    print(help_text)


if __name__ == '__main__':
    main()
