"""
ESG News Aggregator Bot
Автоматический сбор и распространение ESG-новостей
"""

__version__ = "1.0.0"
__author__ = "ESG Bot Team"

from esgparser.core import NewsClass, NewsDatabase
from esgparser.parsers import (
    Parse_EsgnewscomRuNews,
    Parse_EsgnewscomEnNews,
    Parse_GovkznewsRu,
    Parse_GovkznewsKz,
    Parse_informkzRuNews
)
from esgparser.classifier import ESGClassifier
from esgparser.bot import ESGNewsBot

__all__ = [
    'NewsClass',
    'NewsDatabase',
    'Parse_EsgnewscomRuNews',
    'Parse_EsgnewscomEnNews',
    'Parse_GovkznewsRu',
    'Parse_GovkznewsKz',
    'Parse_informkzRuNews',
    'ESGClassifier',
    'ESGNewsBot'
]
