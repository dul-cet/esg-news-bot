"""
Конфигурация ESG News Bot
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram Bot Token (установите свой токен)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_telegram_bot_token')

# Хранилизще данных и логов
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# База данных
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(DATA_DIR / "news.db")
)

LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

# Парсинг
PARSERS_CONFIG = {
    # RSS-only mode: all news are collected strictly from RSS feeds.
    'rss_esg': {
        'enabled': True,
        'interval_hours': 6,
        'parser': 'Parse_RSSFeeds',
        'lang': 'en',
        'max_items_per_feed': 25,
        'feed_urls': [
            'https://esgnews.com/feed/',
            'https://www.unep.org/rss.xml'
        ]
    },
    # Kazakhstan news feeds (tagged as kk content stream for local users).
    'rss_kz': {
        'enabled': True,
        'interval_hours': 6,
        'parser': 'Parse_RSSFeeds',
        'lang': 'kk',
        'max_items_per_feed': 25,
        'feed_urls': [
            'https://inbusiness.kz/kz/rss',
            'https://kaz.tengrinews.kz/news.rss'
        ]
    },
    # Российские ESG новости (через универсальный парсер сайта)    
    'esgworld': {
    'enabled': True,
    'interval_hours': 6,
    'parser': 'Parse_ESGWorld',
    'lang': 'ru',
    'max_items_per_feed': 25,
    'feed_urls': [
        'https://esgworld.news/rss'
    ]
}
}

# ESG Classifier
CLASSIFIER_CONFIG = {
    'enabled': True,
    'min_confidence': 0.3,
    # Classifier работает по ключевым словам.
    'use_nlp': False,
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your_gemini_api_key')
GEMINI_CONFIG = {
    'enabled': True,
    # Use a currently available default model; can be overridden with GEMINI_MODEL_NAME.
    'model_name': os.getenv('GEMINI_MODEL_NAME', 'gemini-2.0-flash'),
    'temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.3')),
}

# API endpoints
API_ENDPOINTS = {
    'esgnews': 'https://esgnews.com',
    'govkz': 'https://www.gov.kz',
    'inform_kz': 'https://www.inform.kz'
}

# Networking resiliency
NETWORK_CONFIG = {
    'request_timeout_sec': int(os.getenv('REQUEST_TIMEOUT_SEC', '8')),
    'max_retries': int(os.getenv('REQUEST_MAX_RETRIES', '3')),
    'retry_backoff_sec': float(os.getenv('REQUEST_RETRY_BACKOFF_SEC', '0.5')),
}

# Non-functional target controls
PERFORMANCE_CONFIG = {
    'max_response_time_sec': float(os.getenv('MAX_RESPONSE_TIME_SEC', '2.0')),
}
