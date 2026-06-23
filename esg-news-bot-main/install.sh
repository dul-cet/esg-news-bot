#!/bin/bash

# Скрипт установки и запуска ESG News Bot

echo "🚀 ESG News Bot - Скрипт установки"
echo "===================================="

# Проверить наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Пожалуйста, установите Python3."
    exit 1
fi

echo "✓ Python3 найден: $(python3 --version)"

# Создать виртуальное окружение
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активировать окружение
echo "✓ Активирование окружения..."
source venv/bin/activate

# Установить зависимости
echo ""
echo "📥 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Все зависимости установлены!"

# Информация о конфигурации
echo ""
echo "⚙️  Конфигурация"
echo "================="
echo ""
echo "Перед запуском бота выполните:"
echo ""
echo "  1. Установите TELEGRAM_BOT_TOKEN:"
echo "     export TELEGRAM_BOT_TOKEN='ваш_токен_здесь'"
echo ""
echo "  ИЛИ отредактируйте config.py и установите токен вручную"
echo ""
echo "  2. Запустите бот:"
echo "     python main.py"
echo ""
echo "  3. (Опционально) Запустите примеры:"
echo "     python examples.py"
echo ""

echo "✓ Установка завершена!"
