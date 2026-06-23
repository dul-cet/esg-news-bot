from typing import Tuple, List, Optional, Dict
import re
import logging
import sqlite3
import time

logger = logging.getLogger(__name__)


class ESGClassifier:
    """Классификатор новостей по ESG-категориям на основе keyword matching"""
    
    def __init__(self, use_nlp: bool = True, db_path: Optional[str] = None):
        # Параметр оставлен для обратной совместимости, NLP-модели отключены.
        self.use_nlp = False
        self.nlp_model = None
        self.db_path = db_path
        self._custom_cache: Dict[str, Dict[str, List[str]]] = {}
        self._custom_cache_ts = 0.0

        if use_nlp:
            logger.info("NLP-модели отключены, используется keyword matching.")
        
        # Ключевые слова для fallback классификации
        self.environment_keywords = {
            'ru': [
                'окружающая среда', 'экология', 'климат', 'климатические изменения',
                'выбросы', 'углерод', 'co2', 'возобновляемые источники',
                'энергия', 'вода', 'загрязнение', 'переработка', 'отходы',
                'лес', 'леса', 'биоразнообразие', 'полезные ископаемые',
                'нефть', 'газ', 'уголь', 'зеленая энергия', 'солнечная',
                'ветровая', 'гидро', 'атомная', 'ядерная'
            ],
            'en': [
                'environment', 'ecology', 'climate', 'climate change',
                'emissions', 'carbon', 'co2', 'renewable energy',
                'energy', 'water', 'pollution', 'recycling', 'waste',
                'forest', 'forests', 'biodiversity', 'minerals',
                'oil', 'gas', 'coal', 'green energy', 'solar',
                'wind', 'hydro', 'nuclear', 'zero emission'
            ],
            'kk': [
                'экология', 'қоршаған орта', 'климат', 'климаттың өзгеруі',
                'шығарындылар', 'көміртек', 'энергия', 'жасыл энергия',
                'күн энергетикасы', 'жел энергетикасы', 'су', 'ластану',
                'қалдық', 'қайта өңдеу', 'орман', 'биоалуантүрлілік',
                'мұнай', 'газ', 'көмір', 'гэс', 'су тасқыны', 'ауа сапасы'
            ]
        }
        
        self.social_keywords = {
            'ru': [
                'социальная', 'общество', 'трудовые права', 'занятость',
                'образование', 'здравоохранение', 'здоровье', 'безопасность',
                'условия труда', 'зарплата', 'льготы', 'равенство', 'дискриминация',
                'разнообразие', 'инклюзия', 'благотворительность', 'опасность',
                'несчастные случаи', 'профессиональные болезни', 'социальная ответственность',
                'сообщество', 'местное население', 'коренные народы', 'женщины'
            ],
            'en': [
                'social', 'society', 'labor rights', 'employment',
                'education', 'healthcare', 'health', 'safety',
                'working conditions', 'salary', 'benefits', 'equality', 'discrimination',
                'diversity', 'inclusion', 'charity', 'hazard',
                'accident', 'occupational disease', 'social responsibility',
                'community', 'local population', 'indigenous', 'women'
            ],
            'kk': [
                'әлеуметтік', 'қоғам', 'еңбек', 'еңбек құқығы', 'жұмыспен қамту',
                'білім', 'денсаулық', 'денсаулық сақтау', 'қауіпсіздік',
                'еңбек жағдайы', 'жалақы', 'жеңілдік', 'теңдік', 'кемсіту',
                'инклюзия', 'қайырымдылық', 'қауымдастық', 'халық',
                'әйелдер', 'балалар', 'әлеуметтік жауапкершілік'
            ]
        }
        
        self.governance_keywords = {
            'ru': [
                'управление', 'корпоративное управление', 'совет директоров',
                'этика', 'коррупция', 'взятки', 'прозрачность',
                'отчетность', 'аудит', 'риск', 'безопасность информации',
                'маркетинг', 'реклама', 'потребитель', 'справедливое ведение бизнеса',
                'политика', 'лобби', 'благодарность', 'вознаграждение', 'топ-менеджмент'
            ],
            'en': [
                'governance', 'corporate governance', 'board of directors',
                'ethics', 'corruption', 'bribery', 'transparency',
                'reporting', 'audit', 'risk', 'information security',
                'marketing', 'advertising', 'consumer', 'fair business',
                'politics', 'lobbying', 'compliance', 'executive compensation', 'leadership'
            ],
            'kk': [
                'басқару', 'корпоративтік басқару', 'директорлар кеңесі',
                'этика', 'жемқорлық', 'пара', 'ашықтық', 'есептілік',
                'аудит', 'тәуекел', 'ақпараттық қауіпсіздік', 'саясат',
                'заң', 'қаулы', 'үкімет', 'президент', 'министрлік',
                'комплаенс', 'реттеу', 'бақылау'
            ]
        }
    
    def classify(self, title: str, digest: str, lang: str = 'ru') -> Tuple[str, float]:
        """
        Классифицировать новость по ESG-категории (keyword matching)
        
        Args:
            title: Заголовок новости
            digest: Краткое описание новости
            lang: Язык текста ('ru' или 'en')
        
        Returns:
            Кортеж (категория, уверенность от 0 до 1)
        """
        text = f"{title} {digest}".strip()
        if not text:
            return 'ESG', 0.0
        
        # Классификация по ключевым словам
        return self._classify_by_keywords(text, lang)
    
    def _classify_by_keywords(self, text: str, lang: str = 'ru') -> Tuple[str, float]:
        """Классифицировать по ключевым словам (fallback)"""
        lang = (lang or 'ru').lower()
        base_lang = lang if lang in self.environment_keywords else 'ru'
        
        text_lower = text.lower()

        env_keywords = self._merged_keywords('Environment', base_lang, self.environment_keywords[base_lang])
        soc_keywords = self._merged_keywords('Social', base_lang, self.social_keywords[base_lang])
        gov_keywords = self._merged_keywords('Governance', base_lang, self.governance_keywords[base_lang])
        
        env_score = self._calculate_score(text_lower, env_keywords)
        soc_score = self._calculate_score(text_lower, soc_keywords)
        gov_score = self._calculate_score(text_lower, gov_keywords)
        
        scores = {
            'Environment': env_score,
            'Social': soc_score,
            'Governance': gov_score
        }
        
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]
        
        if confidence == 0:
            best_category = 'ESG'
            confidence = 0.0
        else:
            total = sum(scores.values())
            confidence = confidence / total if total > 0 else 0
        
        return best_category, confidence
    
    def _calculate_score(self, text: str, keywords: List[str]) -> int:
        """Подсчитать количество совпадений ключевых слов"""
        score = 0
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, text))
            score += matches
        return score
    
    def extract_keywords(self, text: str, lang: str = 'ru', limit: int = 5) -> List[str]:
        """Извлечь релевантные ESG-ключевые слова из текста"""
        lang = (lang or 'ru').lower()
        base_lang = lang if lang in self.environment_keywords else 'ru'
        
        text_lower = text.lower()
        all_keywords = (
            self._merged_keywords('Environment', base_lang, self.environment_keywords[base_lang]) +
            self._merged_keywords('Social', base_lang, self.social_keywords[base_lang]) +
            self._merged_keywords('Governance', base_lang, self.governance_keywords[base_lang])
        )
        
        found_keywords = []
        for keyword in all_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        found_keywords = list(set(found_keywords))[:limit]
        
        return found_keywords

    def _merged_keywords(self, category: str, lang: str, base_keywords: List[str]) -> List[str]:
        """Объединить встроенные и кастомные ключевые слова"""
        custom = self._get_custom_keywords(category, lang)
        merged = list(base_keywords)
        for keyword in custom:
            if keyword not in merged:
                merged.append(keyword)
        return merged

    def _get_custom_keywords(self, category: str, lang: str) -> List[str]:
        """Загрузить кастомные ключевые слова из БД (с коротким кэшем)"""
        if not self.db_path:
            return []

        now = time.time()
        if now - self._custom_cache_ts > 60:
            self._custom_cache = self._load_custom_keywords_map()
            self._custom_cache_ts = now

        category_map = self._custom_cache.get(category, {})
        return category_map.get(lang, [])

    def _load_custom_keywords_map(self) -> Dict[str, Dict[str, List[str]]]:
        """Прочитать кастомные ключевые слова из таблицы custom_keywords"""
        result: Dict[str, Dict[str, List[str]]] = {
            'Environment': {},
            'Social': {},
            'Governance': {},
        }
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT category, lang, keyword FROM custom_keywords')
            rows = cursor.fetchall()
            conn.close()

            for category, lang, keyword in rows:
                if category not in result:
                    continue
                lang_map = result[category].setdefault((lang or 'ru').lower(), [])
                lang_map.append((keyword or '').strip().lower())
        except Exception as e:
            logger.warning(f"Не удалось загрузить кастомные ключевые слова: {e}")
        return result
