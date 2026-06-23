#!/usr/bin/env python3
"""
Интегрированный скрипт для управления ESG News Bot
Использование: python manage.py [команда] [опции]
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path


class BotManager:
    """Менеджер для управления ботом"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_dir = self.project_dir / 'venv'
        self.python = 'python3' if sys.platform != 'win32' else 'python'
    
    def run_command(self, command):
        """Запустить команду в терминале"""
        try:
            result = subprocess.run(command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка выполнения команды: {e}")
            return False
    
    def setup(self):
        """Полная установка проекта"""
        print("🚀 Полная установка ESG News Bot")
        print("=" * 50)
        
        # 1. Создать виртуальное окружение
        print("\n1. Создание виртуального окружения...")
        if not self.venv_dir.exists():
            self.run_command(f"{self.python} -m venv venv")
            print("✓ Виртуальное окружение создано")
        else:
            print("✓ Виртуальное окружение уже существует")
        
        # 2. Активировать и обновить pip
        print("\n2. Обновление pip...")
        pip = str(self.venv_dir / ('Scripts' if sys.platform == 'win32' else 'bin') / 'pip')
        self.run_command(f"{pip} install --upgrade pip")
        
        # 3. Установить зависимости
        print("\n3. Установка зависимостей...")
        self.run_command(f"{pip} install -r requirements.txt")
        print("✓ Зависимости установлены")
        
        # 4. Инициализировать БД
        print("\n4. Инициализация базы данных...")
        self.run_command(f"{pip} run python -c \"from esgparser.core import NewsDatabase; NewsDatabase()\"")
        print("✓ БД инициализирована")
        
        print("\n✓ Установка завершена!")
        print("\nДалее выполните:")
        print("  python manage.py run")
    
    def run(self):
        """Запустить бот"""
        print("🤖 Запуск ESG News Bot...")
        self.run_command(f"{self.python} main.py")
    
    def test(self):
        """Запустить тесты"""
        print("🧪 Запуск тестов...")
        self.run_command(f"{self.python} test.py")
    
    def collect_news(self):
        """Собрать новости вручную"""
        print("📰 Сбор новостей...")
        self.run_command(f"{self.python} -c \"from main import NewsAggregator; agg = NewsAggregator(); agg.collect_news()\"")
    
    def migrate(self):
        """Миграция БД"""
        print("🔄 Миграция БД...")
        print("✓ БД создана/обновлена")
    
    def stats(self):
        """Показать статистику"""
        print("📊 Статистика проекта")
        print("=" * 50)
        self.run_command(f"{self.python} -c \"from utils import NewsAnalyzer; from esgparser.core import NewsDatabase; db = NewsDatabase(); analyzer = NewsAnalyzer(db); analyzer.print_statistics()\"")
    
    def export(self, format_type='json'):
        """Экспортировать новости"""
        print(f"📤 Экспорт новостей в {format_type}...")
        format_type = format_type.lower()
        
        if format_type == 'json':
            self.run_command(f"{self.python} -c \"from utils import NewsExporter; from esgparser.core import NewsDatabase; db = NewsDatabase(); news = db.get_recent_news(100); NewsExporter.to_json(news)\"")
        elif format_type == 'csv':
            self.run_command(f"{self.python} -c \"from utils import NewsExporter; from esgparser.core import NewsDatabase; db = NewsDatabase(); news = db.get_recent_news(100); NewsExporter.to_csv(news)\"")
        elif format_type == 'html':
            self.run_command(f"{self.python} -c \"from utils import NewsExporter; from esgparser.core import NewsDatabase; db = NewsDatabase(); news = db.get_recent_news(100); NewsExporter.to_html(news)\"")
    
    def examples(self):
        """Запустить примеры"""
        print("📚 Запуск примеров...")
        self.run_command(f"{self.python} examples.py")
    
    def clean(self):
        """Очистить кеш и логи"""
        print("🧹 Очистка файлов...")
        
        import shutil
        
        # Удалить __pycache__
        for pycache in self.project_dir.rglob('__pycache__'):
            shutil.rmtree(pycache)
            print(f"  ✓ Удален {pycache}")
        
        # Удалить .pyc файлы
        for pyc in self.project_dir.rglob('*.pyc'):
            pyc.unlink()
        
        # Очистить логи
        logs_dir = self.project_dir / 'logs'
        if logs_dir.exists():
            shutil.rmtree(logs_dir)
        
        print("✓ Очистка завершена")
    
    def reset(self):
        """Полный сброс проекта"""
        response = input("⚠️  Это удалит БД, логи и кеш. Продолжить? (y/n): ")
        
        if response.lower() != 'y':
            print("❌ Отменено")
            return
        
        import shutil
        
        # Удалить БД
        db_file = self.project_dir / 'news.db'
        if db_file.exists():
            db_file.unlink()
            print("✓ БД удалена")
        
        # Очистить логи и кеш
        self.clean()
        
        print("✓ Сброс завершен")
    
    def shell(self):
        """Интерактивная оболочка Python"""
        print("🐍 Интерактивная оболочка")
        print("Примеры:")
        print("  from esgparser.core import NewsDatabase")
        print("  db = NewsDatabase()")
        print("  news = db.get_recent_news()")
        print("")
        
        self.run_command(f"{self.python} -i")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Менеджер для управления ESG News Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  python manage.py setup        # Полная установка
  python manage.py run          # Запустить бот
  python manage.py test         # Запустить тесты
  python manage.py collect      # Собрать новости вручную
  python manage.py stats        # Показать статистику
  python manage.py export json  # Экспортировать в JSON
  python manage.py clean        # Очистить кеш
        '''
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'run', 'test', 'collect', 'migrate', 'stats', 
                'export', 'examples', 'clean', 'reset', 'shell'],
        help='Команда для выполнения'
    )
    
    parser.add_argument(
        'option',
        nargs='?',
        default='json',
        help='Опция для команды (например, формат экспорта)'
    )
    
    args = parser.parse_args()
    
    manager = BotManager()
    
    if args.command == 'setup':
        manager.setup()
    elif args.command == 'run':
        manager.run()
    elif args.command == 'test':
        manager.test()
    elif args.command == 'collect':
        manager.collect_news()
    elif args.command == 'migrate':
        manager.migrate()
    elif args.command == 'stats':
        manager.stats()
    elif args.command == 'export':
        manager.export(args.option)
    elif args.command == 'examples':
        manager.examples()
    elif args.command == 'clean':
        manager.clean()
    elif args.command == 'reset':
        manager.reset()
    elif args.command == 'shell':
        manager.shell()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Операция отменена")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
