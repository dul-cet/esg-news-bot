#!/usr/bin/env python3
"""
Быстрый старт ESG News Bot
Запустите этот файл чтобы пройти интерактивную установку
"""
import os
import sys
import subprocess


def print_header():
    """Вывести заголовок"""
    print("\n")
    print("╔" + "="*48 + "╗")
    print("║" + " "*8 + "🌍 ESG NEWS BOT - QUICK START" + " "*10 + "║")
    print("╚" + "="*48 + "╝")
    print()


def check_python():
    """Проверить версию Python"""
    print("🔍 Проверка Python...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Требуется Python 3.8+, у вас {version.major}.{version.minor}")
        return False
    
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
    return True


def check_venv():
    """Проверить виртуальное окружение"""
    print("\n🔍 Проверка виртуального окружения...")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Виртуальное окружение активно")
        return True
    else:
        print("⚠️  Виртуальное окружение не активно")
        response = input("Хотите его создать? (y/n): ")
        
        if response.lower() == 'y':
            subprocess.run([sys.executable, '-m', 'venv', 'venv'])
            print("✓ Окружение создано")
            print("\n  Активируйте его:")
            print("  macOS/Linux: source venv/bin/activate")
            print("  Windows: venv\\Scripts\\activate")
            return False
        return False


def install_dependencies():
    """Установить зависимости"""
    print("\n📥 Установка зависимостей...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Зависимости установлены")
        return True
    except Exception as e:
        print(f"❌ Ошибка при установке: {e}")
        return False


def setup_token():
    """Настроить Telegram токен"""
    print("\n🤖 Настройка Telegram Bot Token")
    print("-" * 50)
    print("Как получить токен:")
    print("1. Напишите @BotFather в Telegram")
    print("2. Отправьте команду /newbot")
    print("3. Следуйте инструкциям")
    print()
    
    response = input("У вас уже есть токен? (y/n): ")
    
    if response.lower() == 'y':
        token = input("Введите ваш токен: ").strip()
        
        # Сохранить в config.py или .env
        response = input("Сохранить локально? (y/n): ")
        
        if response.lower() == 'y':
            # Обновить config.py
            with open('config.py', 'r') as f:
                content = f.read()
            
            content = content.replace(
                "TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')",
                f"TELEGRAM_BOT_TOKEN = '{token}'"
            )
            
            with open('config.py', 'w') as f:
                f.write(content)
            
            print(f"✓ Токен сохранен в config.py")
        else:
            print("\n✓ Установите переменную окружения:")
            print(f"  export TELEGRAM_BOT_TOKEN='{token}'")
    else:
        print("\n✓ Вы можете установить токен позже")
        print("  export TELEGRAM_BOT_TOKEN='ваш_токен'")


def run_tests():
    """Запустить тесты"""
    print("\n🧪 Запуск тестов...")
    response = input("Хотите запустить тесты? (y/n): ")
    
    if response.lower() == 'y':
        subprocess.run([sys.executable, 'test.py'])
    else:
        print("⏭️  Пропущены тесты")


def show_next_steps():
    """Показать следующие шаги"""
    print("\n" + "="*50)
    print("✓ ГОТОВО К ЗАПУСКУ!")
    print("="*50)
    print()
    print("Следующие шаги:")
    print()
    print("1️⃣  Запустить бот:")
    print("   python main.py")
    print()
    print("2️⃣  Или запустить примеры:")
    print("   python examples.py")
    print()
    print("3️⃣  Или с помощью утилит:")
    print("   python utils.py")
    print()
    print("📖 Документация: README.md")
    print()


def main():
    """Главная функция"""
    print_header()
    
    if not check_python():
        print("\n❌ Ошибка: требуется Python 3.8+")
        sys.exit(1)
    
    if not check_venv():
        print("\n⚠️  Пожалуйста, активируйте виртуальное окружение и запустите снова")
        sys.exit(1)
    
    if not install_dependencies():
        print("\n❌ Не удалось установить зависимости")
        sys.exit(1)
    
    setup_token()
    run_tests()
    show_next_steps()
    
    print("\n🚀 Удачи с вашим ESG News Bot!\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Установка отменена")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        sys.exit(1)
