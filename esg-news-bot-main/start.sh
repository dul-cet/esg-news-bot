#!/bin/bash
# Быстрый старт для ESG News Bot

echo "🚀 Быстрый старт ESG News Bot"
echo "=============================="
echo ""

# Проверка Python
echo "✅ Проверяю Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Пожалуйста, установите Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION найден"
echo ""

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi
echo "✅ Зависимости установлены"
echo ""

# Диагностика
echo "🔍 Диагностика..."
python3 diagnose.py
echo ""

# Меню
echo "=============================="
echo "📋 Выберите что делать:"
echo "=============================="
echo "1) Запустить бота (main.py)"
echo "2) Смотреть БД (view_database.py)"
echo "3) Примеры (examples.py)"
echo "4) Тесты (test.py)"
echo "5) Выход"
echo ""
read -p "Введите номер (1-5): " CHOICE

case $CHOICE in
    1)
        echo "🤖 Запуск бота..."
        echo "⏳ При первом запуске загрузка моделей займет 5-15 минут..."
        echo ""
        python3 main.py
        ;;
    2)
        echo "📊 Просмотр БД..."
        python3 view_database.py
        ;;
    3)
        echo "📚 Примеры..."
        python3 examples.py
        ;;
    4)
        echo "🧪 Тесты..."
        python3 test.py
        ;;
    5)
        echo "👋 До свидания!"
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac