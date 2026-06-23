# 🌱 ESG News Bot

> Telegram-бот для сбора, классификации и персональной доставки ESG-новостей.  
> Поддерживает русский, казахский и английский языки (RU / EN / KK).  
> Запускается независимо, не создаёт конфликтов с другими сервисами.

---

## 📋 Содержание

- [Краткое описание](#краткое-описание)
- [Технический стек](#технический-стек)
- [Порт и healthcheck](#порт-и-healthcheck)
- [Переменные окружения](#переменные-окружения)
- [Быстрый старт](#быстрый-старт)
- [Установка](#установка)
- [Команды бота](#команды-бота)
- [Архитектура](#архитектура)
- [База данных](#база-данных)
- [Технические требования](#технические-требования)
- [Оценка нагрузки](#оценка-нагрузки)
- [Логи](#логи)
- [Деплой](#деплой)
- [Перезапуск](#перезапуск)
- [Резервная копия](#резервная-копия)

---

## Краткое описание

ESG News Bot — это автономный Telegram-бот, который:

- 🔍 **Собирает** ESG-новости из 10+ источников (RSS, API, казахстанские сайты) каждые 6 часов
- 🏷️ **Классифицирует** каждую новость по категориям: **Environment / Social / Governance**
- 📬 **Рассылает** персональные дайджесты подписчикам по расписанию (по умолчанию 09:00 Алматы)
- 🤖 **Отвечает** на свободные ESG-вопросы через Google Gemini AI
- 🛠️ **Предоставляет** полноценную админ-панель для модерации источников и новостей

---

## Содержание

- [Функции](#функции)
- [Технический стек](#технический-стек)
- [Быстрый старт](#быстрый-старт)
- [Установка](#установка)
- [Переменные окружения](#переменные-окружения)
- [Команды бота](#команды-бота)
- [Архитектура](#архитектура)
- [База данных](#база-данных)
- [Деплой](#деплой)
- [Диагностика и healthcheck](#диагностика-и-healthcheck)
- [Резервная копия](#резервная-копия)

---

---

## Технический стек

| Слой | Библиотека | Назначение |
|------|-----------|-----------|
| Бот | `python-telegram-bot` | Приём команд, кнопки, рассылка |
| Планировщик | `APScheduler` | Cron-задачи дайджестов |
| Парсинг RSS | `feedparser` | Чтение RSS-каналов |
| HTTP-запросы | `requests`, `aiohttp` | Загрузка страниц источников |
| HTML-парсинг | `beautifulsoup4`, `lxml` | Извлечение текста из HTML |
| AI | `google-generativeai` | Ответы и классификация через Gemini |
| БД | `SQLite` (встроенная) | Хранение новостей, пользователей |
| Даты/таймзоны | `pytz` | Корректная обработка времени |
| Язык | Python 3.9+ | Основной язык проекта |

> **Внешние зависимости:** Redis — не требуется. PostgreSQL — не требуется.  
> Бот полностью автономен: для работы нужны только Python, pip и SQLite (встроен в Python).

---

## Порт и healthcheck

| Параметр | Значение |
|----------|----------|
| **HTTP-порт** | Не используется (работает через Telegram Polling, не webhook) |
| **Протокол** | Outbound HTTPS (api.telegram.org, ai.google.dev) |
| **Healthcheck** | Проверка файла БД + SQL integrity check |

```bash
# Проверка базы данных
sqlite3 news.db "PRAGMA integrity_check;"
# Ожидаемый ответ: ok

# Проверка Telegram API
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" | python3 -m json.tool

# Количество новостей в базе
sqlite3 news.db "SELECT COUNT(*) FROM news;"
```

> ℹ️ Бот не занимает ни один входящий порт — не создаёт конфликтов при деплое рядом с другими сервисами.

---

## Быстрый старт

> 5 минут до запуска

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен.
2. Получите API-ключ Gemini на [ai.google.dev](https://ai.google.dev).
3. Выполните:

```bash
cd NewsBotESG
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполните токены
python main.py
```

4. Откройте Telegram и отправьте боту `/start`.

---

## Установка

### macOS / Linux

```bash
cd NewsBotESG
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Windows (PowerShell)

```powershell
cd NewsBotESG
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python main.py
```

### Docker

```bash
cp .env.example .env
docker-compose up -d
docker-compose logs -f bot
```

### Проверка после установки

```bash
python diagnose.py
sqlite3 news.db "SELECT COUNT(*) FROM news;"
```

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните обязательные поля:

```bash
cp .env.example .env
```

| Переменная | Обязательно | Описание | Пример |
|-----------|:-----------:|---------|--------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен бота от @BotFather | `8620496467:AAE...` |
| `GEMINI_API_KEY` | ✅ | API-ключ Google Gemini (ai.google.dev) | `AIzaSy...` |
| `DATABASE_PATH` | ✅ | Путь к SQLite-файлу (уникален для проекта) | `./data/news.db` |
| `LOG_LEVEL` | — | Уровень логирования | `INFO` |
| `ENVIRONMENT` | — | Среда запуска | `production` |
| `TIMEZONE` | — | Таймзона планировщика | `Asia/Almaty` |
| `GEMINI_MODEL_NAME` | — | Модель Gemini | `gemini-2.0-flash` |
| `GEMINI_TEMPERATURE` | — | Творческость AI (0.0–1.0) | `0.3` |
| `REQUEST_TIMEOUT_SEC` | — | Таймаут HTTP-запросов (сек) | `8` |
| `REQUEST_MAX_RETRIES` | — | Количество retry при ошибках | `3` |
| `MAX_RESPONSE_TIME_SEC` | — | SLA-цель ответа бота (сек) | `2.0` |
| `CLASSIFIER_MIN_CONFIDENCE` | — | Минимальная уверенность классификатора (0–1) | `0.3` |
| `PUSH_DIGEST_HOUR` | — | Час рассылки дайджеста по умолчанию | `9` |
| `LOG_DIR` | — | Директория для файлов логов | `./logs` |

> ⚠️ Каждый экземпляр бота должен использовать **уникальные** `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY` и `DATABASE_PATH`, чтобы не создавать конфликтов.

---

## Команды бота

### Пользовательские

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация и выбор языка |
| `/help` | Справка |
| `/news` | Последние ESG-новости |
| `/environment` | Новости по категории E (Environment) |
| `/social` | Новости по категории S (Social) |
| `/governance` | Новости по категории G (Governance) |
| `/digest` | Получить дайджест вручную |
| `/awareness` | Статистика вашей ESG-активности |
| `/settings` | Настройки (язык, подписки, время) |
| `/manage_subs` | Управление подписками |
| `/suggest_source` | Предложить новый источник |
| `/language` | Сменить язык интерфейса |
| `/set_digest_time` | Установить время получения дайджеста |
| `/set_news_limit` | Количество новостей в дайджесте |

### Административные

| Команда | Описание |
|---------|----------|
| `/admin` | Открыть панель управления |
| `/health` | Состояние системы |
| `/sources` | Список активных источников |
| `/add_source` | Добавить источник |
| `/delete_source` | Удалить источник |
| `/moderate_sources` | Модерировать предложения пользователей |
| `/add_keyword` | Добавить ключевое слово для классификатора |
| `/remove_keyword` | Удалить ключевое слово |
| `/keywords` | Список кастомных ключевых слов |
| `/admin_news` | Список новостей с кнопками модерации |
| `/hide_news` | Скрыть новость |
| `/unhide_news` | Показать скрытую новость |
| `/delete_news` | Удалить новость |
| `/edit_category` | Изменить ESG-категорию новости |

---

## Архитектура

### Как работает система

```
Парсеры (RSS / API / сайты)
        ↓
  ESG-классификатор
        ↓
    SQLite (news.db)
        ↓
Telegram Bot + Планировщик дайджестов
        ↓
     Пользователи
```

### Структура кода

```
main.py                          ← точка входа, запуск агрегатора и бота
config.py                        ← конфигурация и переменные окружения
esgparser/
  parsers/                       ← источники новостей
    rssfeeds.py                  ← универсальный RSS-парсер
    newsapi.py                   ← NewsAPI.org
    esgnews.py                   ← esgnews.com (RU/EN)
    tengrinews.py                ← tengrinews.kz
    govkz.py                     ← gov.kz
    informkz.py                  ← inform.kz
    generic_site.py              ← универсальный HTTP-парсер
  classifier/
    esg_classifier.py            ← keyword-based ESG-классификатор
  core/
    database.py                  ← работа с SQLite
    net.py                       ← HTTP с retry/timeout
    ParsClasses.py               ← базовый класс новости
  bot/
    telegram_bot.py              ← Telegram-бот, команды, scheduler
    i18n.py                      ← переводы (ru/en/kk)
```

### Как запускаются два потока

При старте `main.py`:
1. Агрегатор собирает новости в фоновом потоке (каждые N часов по конфигу).
2. Telegram-бот работает в главном потоке через polling.
3. APScheduler внутри бота отправляет дайджесты по cron.

### Классификатор

Работает по ключевым словам на трёх языках. Алгоритм:
- Считает совпадения с базой слов по каждой из категорий E/S/G.
- Выбирает категорию с наибольшим числом совпадений.
- Отбрасывает новости с уверенностью ниже `min_confidence`.
- Кастомные ключевые слова из БД подгружаются автоматически (с кешем 60 сек).

### Как запускаются два потока

При старте `main.py`:
1. Агрегатор собирает новости в **фоновом потоке** (каждые N часов по конфигу).
2. Telegram-бот работает в **главном потоке** через polling.
3. APScheduler внутри бота отправляет дайджесты по cron.

### Классификатор

Работает по ключевым словам на трёх языках. Алгоритм:
- Считает совпадения с базой слов по каждой из категорий E/S/G.
- Выбирает категорию с наибольшим числом совпадений.
- Отбрасывает новости с уверенностью ниже `min_confidence`.
- Кастомные ключевые слова из БД подгружаются автоматически (с кешем 60 сек).

---

## Технические требования

### Ресурсы

| Ресурс | Минимум | Рекомендовано | Комментарий |
|--------|---------|---------------|-------------|
| **CPU** | 1 core | 2 cores | Парсинг + polling |
| **RAM** | 256 MB | 512 MB | +100 MB на каждые 1000 пользователей |
| **Disk** | 500 MB | 10 GB+ | SQLite растёт ~1 MB/день при активном парсинге |
| **Python** | 3.9+ | 3.11+ | Проверено на 3.9, 3.11 |
| **ОС** | Linux/macOS | Ubuntu 22.04 | Windows поддерживается частично |

### Зависимости

| Зависимость | Требуется | Версия | Комментарий |
|-------------|:---------:|--------|-------------|
| Python | ✅ | 3.9+ | Основной рантайм |
| SQLite | ✅ | встроен | Отдельная установка не нужна |
| Redis | ❌ | — | Не используется |
| PostgreSQL | ❌ | — | Не используется |
| Docker | — | 20.10+ | Рекомендуется для деплоя |

> 🔒 **Изоляция:** Бот полностью изолирован. Не использует общие БД, не требует Redis/Postgres, не занимает входящие порты. Можно запускать рядом с любыми другими сервисами без конфликтов.

---

## Оценка нагрузки

| Метрика | Значение |
|---------|----------|
| Пользователей | до 500 (протестировано) |
| Средний RPS | 1–3 запроса/сек |
| Пиковый RPS (момент рассылки) | до 10–15 запросов/сек |
| Целевое время ответа бота | ≤ 2 сек |
| Парсинг новостей | каждые 6 часов, ~5–10 сек на источник |
| Объём БД (1 год) | ~50–200 MB при активном парсинге |

---

## База данных

SQLite-файл `news.db`. Основные таблицы:

| Таблица | Содержимое |
|---------|-----------|
| `news` | Все новости с ESG-категорией, языком, статусом |
| `users` | Зарегистрированные пользователи, язык, настройки |
| `user_subscriptions` | Подписки пользователей на категории |
| `delivery_history` | История отправок дайджестов |
| `suggested_sources` | Предложенные источники (ожидают модерации) |
| `managed_sources` | Активные RSS-источники, добавленные админом |
| `custom_keywords` | Кастомные ключевые слова для классификатора |
| `user_engagement` | События активности пользователей |

---

## Логи

Логи пишутся в `./logs/` и в stdout.

```bash
# Последние строки
tail -f logs/*.log

# Только ошибки
grep -i "error\|critical" logs/*.log

# Docker
docker-compose logs -f bot

# systemd
sudo journalctl -u newsbot -n 100 -f
```

Формат строки лога:
```
2026-03-31 09:00:01,234 - esgparser.bot.telegram_bot - INFO - 🔔 Запуск рассылки...
```

---

## Деплой

### ✅ Чеклист перед деплоем

- [ ] Заполнен `.env` (скопирован из `.env.example`)
- [ ] `TELEGRAM_BOT_TOKEN` уникален для этого бота
- [ ] `DATABASE_PATH` указывает на уникальный файл (не используется другим сервисом)
- [ ] Успешен локальный запуск `python main.py`
- [ ] Папки `data/` и `logs/` существуют и доступны для записи
- [ ] Настроен автоперезапуск при падении
- [ ] Настроен backup БД

- [ ] Заполнен `.env`
- [ ] Успешен локальный запуск `python main.py`
- [ ] Настроены логи
- [ ] Настроен backup БД
- [ ] Настроен автоперезапуск

### Вариант 1: systemd (Linux VPS)

```bash
sudo mkdir -p /opt/newsbot
cd /opt/newsbot
git clone <repo_url> .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Создайте файл `/etc/systemd/system/newsbot.service`:

```ini
[Unit]
Description=ESG News Bot
After=network.target

[Service]
Type=simple
User=newsbot
WorkingDirectory=/opt/newsbot
Environment="PATH=/opt/newsbot/venv/bin"
ExecStart=/opt/newsbot/venv/bin/python /opt/newsbot/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable newsbot
sudo systemctl start newsbot
sudo systemctl status newsbot
```

### Вариант 2: Docker

```bash
cp .env.example .env
docker-compose up -d
docker-compose ps
docker-compose logs -f bot
```

### Перезапуск

```bash
# systemd
sudo systemctl restart newsbot

# docker
docker-compose restart bot
```

---

## Диагностика и healthcheck

### Проверка процесса

```bash
# systemd
sudo systemctl status newsbot
sudo journalctl -u newsbot -n 100

# docker
docker-compose ps
docker-compose logs --tail=100 bot
```

### Проверка базы данных

```bash
sqlite3 news.db "PRAGMA integrity_check;"   # ожидаемый результат: ok
sqlite3 news.db "SELECT COUNT(*) FROM news;"
```

### Проверка Telegram API

```bash
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
```

### Логи

```bash
tail -f logs/*.log
grep -i "error\|critical" logs/*.log
```

### Диагностический скрипт

```bash
python diagnose.py
```

### Типовые проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| `database is locked` | Параллельные задачи | Включите WAL: `PRAGMA journal_mode=WAL` |
| Бот не отвечает | Неверный токен | Проверьте `TELEGRAM_BOT_TOKEN` |
| Ошибки Gemini 429 | Квота исчерпана | Проверьте billing в Google AI Studio |
| Нет новостей в боте | Парсеры не запустились | Проверьте логи и `python main.py collect` |

---

## Перезапуск

```bash
# systemd
sudo systemctl restart newsbot
sudo systemctl status newsbot

# Docker
docker-compose restart bot
docker-compose ps
```

---

## Резервная копия

```bash
mkdir -p backups
sqlite3 news.db ".backup backups/news_$(date +%Y%m%d_%H%M%S).db"
```

Рекомендуется поставить в cron (ежедневно в 03:00):

```bash
0 3 * * * sqlite3 /opt/newsbot/news.db ".backup /opt/newsbot/backups/news_$(date +\%Y\%m\%d).db"
```

---

> Проект запускается независимо от других сервисов. Не использует общие порты, Redis или PostgreSQL. Изоляция обеспечивается Docker или venv + уникальным `DATABASE_PATH`.

