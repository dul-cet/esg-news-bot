from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime


class NewsClass(ABC):
    """Базовый класс для всех новостей"""
    
    def __init__(self):
        self.title: str = ""
        self.url: str = ""
        self.date: datetime = None
        self.digest: str = ""
        self.image_url: Optional[str] = None
        self.site_url: str = ""
        self.lang: str = ""
        self.esg_category: Optional[str] = None
        self.esg_score: Optional[float] = None
        self.keywords: list = []
        self.processing_status: str = "collected"
    
    @abstractmethod
    def getExtra(self, session):
        """Получить дополнительную информацию (изображение, полный текст)"""
        pass
    
    def to_dict(self) -> dict:
        """Преобразовать объект в словарь"""
        return {
            'title': self.title,
            'url': self.url,
            'date': self.date.isoformat() if self.date else None,
            'digest': self.digest,
            'image_url': self.image_url,
            'site_url': self.site_url,
            'lang': self.lang,
            'esg_category': self.esg_category,
            'esg_score': self.esg_score,
            'keywords': self.keywords,
            'processing_status': self.processing_status,
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.title[:50]}...>"
