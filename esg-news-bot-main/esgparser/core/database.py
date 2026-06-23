import sqlite3
from datetime import datetime
from typing import List, Optional
import json
import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


class NewsDatabase:
    """Класс для работы с БД новостей"""

    def __init__(self, db_path: str = "news.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализировать БД и выполнить миграции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # SQLite tuning for better concurrent reads/writes and latency
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA busy_timeout=5000')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                url_hash TEXT UNIQUE,
                date DATETIME,
                digest TEXT,
                image_url TEXT,
                site_url TEXT,
                lang TEXT,
                esg_category TEXT,
                esg_score REAL,
                keywords TEXT,
                processing_status TEXT DEFAULT 'processed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                news_id INTEGER,
                channel TEXT DEFAULT 'telegram',
                digest_type TEXT DEFAULT 'push',
                status TEXT NOT NULL,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (news_id) REFERENCES news(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                language TEXT DEFAULT 'ru',
                news_limit INTEGER DEFAULT 5,
                digest_hour INTEGER DEFAULT 9,
                preferences TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                esg_category TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, esg_category),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggested_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                source_name TEXT,
                source_url TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                admin_comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS managed_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                source_url TEXT UNIQUE NOT NULL,
                source_type TEXT DEFAULT 'rss',
                lang TEXT DEFAULT 'en',
                enabled INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                lang TEXT NOT NULL,
                keyword TEXT NOT NULL,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, lang, keyword),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                category TEXT,
                payload TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # ── Migrations: add columns that may be missing in existing DBs ───────
        migrations = [
            "ALTER TABLE users ADD COLUMN news_limit INTEGER DEFAULT 5",
            "ALTER TABLE users ADD COLUMN digest_hour INTEGER DEFAULT 9",
            "ALTER TABLE news ADD COLUMN is_hidden INTEGER DEFAULT 0",
            "ALTER TABLE news ADD COLUMN processing_status TEXT DEFAULT 'processed'",
            "ALTER TABLE news ADD COLUMN url_hash TEXT",
        ]
        for sql in migrations:
            try:
                cursor.execute(sql)
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists — safe to ignore

        # Performance indexes for frequently used queries
        # Clean legacy duplicates before enforcing uniqueness.
        cursor.execute('''
            DELETE FROM user_subscriptions
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM user_subscriptions
                GROUP BY user_id, esg_category
            )
        ''')

        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_news_date ON news(date DESC)",
            "CREATE INDEX IF NOT EXISTS idx_news_category_lang_hidden ON news(esg_category, lang, is_hidden, processing_status)",
            "CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON user_subscriptions(user_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_user_category_unique ON user_subscriptions(user_id, esg_category)",
            "CREATE INDEX IF NOT EXISTS idx_delivery_history_user_date ON delivery_history(user_id, created_at DESC)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_news_url_hash_unique ON news(url_hash)",
            "CREATE INDEX IF NOT EXISTS idx_user_engagement_user_date ON user_engagement(user_id, created_at DESC)",
        ]
        for sql in index_statements:
            cursor.execute(sql)

        # Backfill hash for existing records where possible
        cursor.execute('SELECT id, url FROM news WHERE url_hash IS NULL')
        for news_id, url in cursor.fetchall():
            url_hash = self._hash_url(url)
            if url_hash:
                try:
                    cursor.execute('UPDATE news SET url_hash = ? WHERE id = ?', (url_hash, news_id))
                except sqlite3.IntegrityError:
                    # Duplicate normalized URL already exists; keep older record hash
                    pass

        # Backfill language labels for legacy rows that were hard-tagged as 'kk'
        # even when actual text is Russian.
        cursor.execute("SELECT id, title, digest FROM news WHERE lang = 'kk'")
        for news_id, title, digest in cursor.fetchall():
            merged = f"{title or ''} {digest or ''}"
            if not self._looks_kazakh_text(merged):
                cursor.execute("UPDATE news SET lang = 'ru' WHERE id = ?", (news_id,))
        # ─────────────────────────────────────────────────────────────────────

        conn.commit()
        conn.close()

    @staticmethod
    def _normalize_url(url: Optional[str]) -> str:
        """Нормализовать URL для более надежной дедупликации"""
        if not url:
            return ""
        parsed = urlparse(url.strip())
        path = parsed.path.rstrip('/')
        query_pairs = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False) if not k.startswith('utm_')]
        query_pairs.sort(key=lambda item: item[0])
        normalized_query = urlencode(query_pairs)
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, '', normalized_query, ''))

    def _hash_url(self, url: Optional[str]) -> Optional[str]:
        normalized = self._normalize_url(url)
        if not normalized:
            return None
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def _looks_kazakh_text(text: str) -> bool:
        """Basic check that text likely contains Kazakh content."""
        if not text:
            return False
        kazakh_chars = set("әіңғүұқөһӘІҢҒҮҰҚӨҺ")
        if any(ch in kazakh_chars for ch in text):
            return True
        lowered = text.lower()
        hint_words = (
            " қазақстан", " және ", " туралы ", " бойынша ",
            " жаңалық", " министр", " бүгін", " жылы ", " жылына ",
        )
        return any(token in lowered for token in hint_words)

    # ──────────────────────────────────────────────────────────────────────────
    # News
    # ──────────────────────────────────────────────────────────────────────────

    def add_news(self, news_dict: dict) -> bool:
        """Добавить новость в БД"""
        for attempt in range(3):
            conn = None
            try:
                conn = sqlite3.connect(self.db_path, timeout=15)
                cursor = conn.cursor()
                cursor.execute('PRAGMA busy_timeout=5000')

                cursor.execute('''
                    INSERT INTO news
                    (title, url, url_hash, date, digest, image_url, site_url, lang, esg_category, esg_score, keywords, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news_dict.get('title'),
                    news_dict.get('url'),
                    self._hash_url(news_dict.get('url')),
                    news_dict.get('date'),
                    news_dict.get('digest'),
                    news_dict.get('image_url'),
                    news_dict.get('site_url'),
                    news_dict.get('lang'),
                    news_dict.get('esg_category'),
                    news_dict.get('esg_score'),
                    json.dumps(news_dict.get('keywords', [])),
                    news_dict.get('processing_status', 'processed')
                ))

                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Duplicate URL/hash is normal during repeated collections.
                return False
            except sqlite3.OperationalError as e:
                if 'locked' in str(e).lower() and attempt < 2:
                    continue
                print(f"Error adding news: {e}")
                return False
            except Exception as e:
                print(f"Error adding news: {e}")
                return False
            finally:
                if conn is not None:
                    conn.close()
        return False

    def update_news_processing_status(self, news_id: int, processing_status: str) -> bool:
        """Обновить статус обработки новости"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE news SET processing_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (processing_status, news_id)
            )
            updated = cursor.rowcount
            conn.commit()
            conn.close()
            return updated > 0
        except Exception as e:
            print(f"Error updating processing status: {e}")
            return False

    def get_news_by_category(self, category: str, limit: int = 10, lang: Optional[str] = None) -> List[dict]:
        """Получить новости по категории (опционально с фильтром по языку)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if lang:
            sql_limit = limit * 5 if lang == 'kk' else limit
            cursor.execute('''
                SELECT * FROM news
                WHERE esg_category = ?
                  AND lang = ?
                  AND is_hidden = 0
                  AND processing_status = 'processed'
                ORDER BY date DESC
                LIMIT ?
            ''', (category, lang, sql_limit))
        else:
            cursor.execute('''
                SELECT * FROM news
                WHERE esg_category = ?
                  AND is_hidden = 0
                  AND processing_status = 'processed'
                ORDER BY date DESC
                LIMIT ?
            ''', (category, limit))
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        items = [dict(zip(columns, row)) for row in rows]
        if lang == 'kk':
            items = [
                row for row in items
                if self._looks_kazakh_text(f"{row.get('title') or ''} {row.get('digest') or ''}")
            ]
            return items[:limit]
        return items

    def get_news_by_language(self, lang: str, limit: int = 20) -> List[dict]:
        """Получить новости по языку"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        sql_limit = limit * 5 if lang == 'kk' else limit
        cursor.execute('''
            SELECT * FROM news
            WHERE lang = ?
              AND is_hidden = 0
                            AND processing_status = 'processed'
            ORDER BY date DESC
            LIMIT ?
        ''', (lang, sql_limit))
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        items = [dict(zip(columns, row)) for row in rows]
        if lang == 'kk':
            items = [
                row for row in items
                if self._looks_kazakh_text(f"{row.get('title') or ''} {row.get('digest') or ''}")
            ]
            return items[:limit]
        return items

    def get_recent_news(self, limit: int = 20, include_hidden: bool = False) -> List[dict]:
        """Получить последние новости"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if include_hidden:
            cursor.execute('''
                SELECT * FROM news
                ORDER BY date DESC
                LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT * FROM news
                WHERE is_hidden = 0
                ORDER BY date DESC
                LIMIT ?
            ''', (limit,))
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_all_news(self, include_hidden: bool = False) -> List[dict]:
        """Получить все новости из БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if include_hidden:
            cursor.execute('SELECT * FROM news ORDER BY date DESC')
        else:
            cursor.execute('SELECT * FROM news WHERE is_hidden = 0 ORDER BY date DESC')
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def search_news(self, query: str, limit: int = 20, include_hidden: bool = False) -> List[dict]:
        """Поиск новостей по тексту заголовка или описания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        pattern = f"%{query}%"
        if include_hidden:
            cursor.execute('''
                SELECT * FROM news
                WHERE title LIKE ? OR digest LIKE ?
                ORDER BY date DESC
                LIMIT ?
            ''', (pattern, pattern, limit))
        else:
            cursor.execute('''
                SELECT * FROM news
                WHERE (title LIKE ? OR digest LIKE ?)
                  AND is_hidden = 0
                ORDER BY date DESC
                LIMIT ?
            ''', (pattern, pattern, limit))
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def count_news(self, include_hidden: bool = False) -> int:
        """Получить количество новостей в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if include_hidden:
            cursor.execute('SELECT COUNT(*) FROM news')
        else:
            cursor.execute('SELECT COUNT(*) FROM news WHERE is_hidden = 0')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def update_news_category(self, news_id: int, new_category: str, score: float = None) -> bool:
        """Обновить категорию ESG новости (для админ корректировки)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if score is not None:
                cursor.execute(
                    'UPDATE news SET esg_category = ?, esg_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (new_category, score, news_id)
                )
            else:
                cursor.execute(
                    'UPDATE news SET esg_category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (new_category, news_id)
                )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating news category: {e}")
            return False

    def get_news_by_id(self, news_id: int) -> Optional[dict]:
        """Получить новость по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM news WHERE id = ?', (news_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            columns = [d[0] for d in cursor.description]
            return dict(zip(columns, row))
        return None

    def delete_news(self, news_id: int) -> bool:
        """Удалить новость по ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted > 0
        except Exception as e:
            print(f"Error deleting news: {e}")
            return False

    def set_news_hidden(self, news_id: int, hidden: bool = True) -> bool:
        """Скрыть или показать новость"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE news SET is_hidden = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (1 if hidden else 0, news_id)
            )
            updated = cursor.rowcount
            conn.commit()
            conn.close()
            return updated > 0
        except Exception as e:
            print(f"Error setting hidden flag: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Users
    # ──────────────────────────────────────────────────────────────────────────

    def add_user(self, user_id: int, username: str, language: str = 'ru'):
        """Добавить пользователя (или проигнорировать, если уже есть)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, language)
                VALUES (?, ?, ?)
            ''', (user_id, username, language))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def get_user_language(self, user_id: int) -> str:
        """Получить язык интерфейса пользователя (ru / en / kk)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row and row[0] else 'ru'
        except Exception:
            return 'ru'

    def get_all_users(self) -> List[dict]:
        """Получить всех пользователей (для Push-рассылки)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, language, news_limit, digest_hour FROM users')
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def update_user_settings(
        self,
        user_id: int,
        language: str = None,
        news_limit: int = None,
        digest_hour: int = None,
    ):
        """Обновить настройки пользователя (язык, лимит новостей, час рассылки)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if language is not None:
                cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
            if news_limit is not None:
                cursor.execute('UPDATE users SET news_limit = ? WHERE user_id = ?', (news_limit, user_id))
            if digest_hour is not None:
                cursor.execute('UPDATE users SET digest_hour = ? WHERE user_id = ?', (digest_hour, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Subscriptions
    # ──────────────────────────────────────────────────────────────────────────

    def subscribe_user_to_category(self, user_id: int, esg_category: str):
        """Подписать пользователя на категорию (без дублей)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO user_subscriptions (user_id, esg_category)
                VALUES (?, ?)
            ''', (user_id, esg_category))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error subscribing user: {e}")
            return False

    def unsubscribe_user_from_category(self, user_id: int, esg_category: str):
        """Удалить подписку пользователя на категорию"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM user_subscriptions
                WHERE user_id = ? AND esg_category = ?
            ''', (user_id, esg_category))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error unsubscribing: {e}")
            return False

    def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Получить список категорий подписок пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT esg_category FROM user_subscriptions
            WHERE user_id = ?
            ORDER BY esg_category
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    # ──────────────────────────────────────────────────────────────────────────
    # Digest
    # ──────────────────────────────────────────────────────────────────────────

    def get_digest_news(self, user_id: int) -> List[dict]:
        """Получить новости по подпискам пользователя с учётом его лимита и языка"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Настройки пользователя
        cursor.execute(
            'SELECT language, news_limit FROM users WHERE user_id = ?',
            (user_id,)
        )
        pref  = cursor.fetchone()
        lang  = pref[0] if pref and pref[0] else 'ru'
        limit = pref[1] if pref and pref[1] else 5

        # 2. Категории подписок
        cursor.execute(
            'SELECT esg_category FROM user_subscriptions WHERE user_id = ?',
            (user_id,)
        )
        categories = [row[0] for row in cursor.fetchall()]

        if not categories:
            conn.close()
            return []

        # 3. Новости по категориям (lang IS NULL тоже включаем)
        placeholders = ', '.join(['?'] * len(categories))
        query = f'''
            SELECT * FROM news
            WHERE esg_category IN ({placeholders})
              AND (lang = ? OR lang IS NULL)
                            AND is_hidden = 0
                            AND processing_status = 'processed'
            ORDER BY date DESC
            LIMIT ?
        '''
        cursor.execute(query, (*categories, lang, limit))
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def add_delivery_history(
        self,
        user_id: int,
        news_id: Optional[int],
        status: str,
        channel: str = 'telegram',
        digest_type: str = 'push',
        error_message: Optional[str] = None,
    ) -> bool:
        """Добавить запись в историю рассылок"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO delivery_history (user_id, news_id, channel, digest_type, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (user_id, news_id, channel, digest_type, status, error_message)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding delivery history: {e}")
            return False

    def add_delivery_history_batch(
        self,
        user_id: int,
        news_ids: List[int],
        status: str,
        channel: str = 'telegram',
        digest_type: str = 'push',
        error_message: Optional[str] = None,
    ) -> bool:
        """Добавить пакет записей в историю рассылок"""
        if not news_ids:
            return self.add_delivery_history(
                user_id=user_id,
                news_id=None,
                status=status,
                channel=channel,
                digest_type=digest_type,
                error_message=error_message,
            )
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany(
                '''
                INSERT INTO delivery_history (user_id, news_id, channel, digest_type, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                [
                    (user_id, news_id, channel, digest_type, status, error_message)
                    for news_id in news_ids
                ]
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding delivery history batch: {e}")
            return False

    def get_delivery_history(self, user_id: Optional[int] = None, limit: int = 100) -> List[dict]:
        """Получить историю рассылок"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if user_id is None:
            cursor.execute(
                '''
                SELECT * FROM delivery_history
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (limit,)
            )
        else:
            cursor.execute(
                '''
                SELECT * FROM delivery_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def log_user_engagement(
        self,
        user_id: int,
        event_type: str,
        category: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> bool:
        """Сохранить событие вовлеченности пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO user_engagement (user_id, event_type, category, payload)
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, event_type, category, json.dumps(payload) if payload else None)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error logging user engagement: {e}")
            return False

    def get_user_engagement_stats(self, user_id: int, days: int = 30) -> dict:
        """Получить агрегированную статистику ESG-вовлеченности пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT COUNT(*)
            FROM user_engagement
            WHERE user_id = ?
              AND created_at >= datetime('now', '-' || ? || ' days')
            ''',
            (user_id, days)
        )
        total_events = cursor.fetchone()[0]

        cursor.execute(
            '''
            SELECT event_type, COUNT(*)
            FROM user_engagement
            WHERE user_id = ?
              AND created_at >= datetime('now', '-' || ? || ' days')
            GROUP BY event_type
            ''',
            (user_id, days)
        )
        by_event = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute(
            '''
            SELECT category, COUNT(*)
            FROM user_engagement
            WHERE user_id = ?
              AND category IS NOT NULL
              AND created_at >= datetime('now', '-' || ? || ' days')
            GROUP BY category
            ''',
            (user_id, days)
        )
        by_category = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()
        return {
            'period_days': days,
            'total_events': total_events,
            'by_event': by_event,
            'by_category': by_category,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Suggested Sources
    # ──────────────────────────────────────────────────────────────────────────

    def add_managed_source(
        self,
        source_name: str,
        source_url: str,
        lang: str = 'en',
        source_type: str = 'rss',
        created_by: Optional[int] = None,
    ) -> bool:
        """Добавить активный источник для парсинга"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO managed_sources (source_name, source_url, source_type, lang, enabled, created_by)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (source_name, source_url, source_type, lang, created_by))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding managed source: {e}")
            return False

    def get_managed_sources(self, enabled_only: bool = False) -> List[dict]:
        """Получить список управляемых источников"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if enabled_only:
            cursor.execute('SELECT * FROM managed_sources WHERE enabled = 1 ORDER BY created_at DESC')
        else:
            cursor.execute('SELECT * FROM managed_sources ORDER BY created_at DESC')
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_active_rss_source_urls(self) -> List[dict]:
        """Получить активные RSS-источники (url + lang)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT source_url, lang FROM managed_sources
            WHERE enabled = 1 AND source_type = 'rss'
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [{'url': row[0], 'lang': row[1] or 'en'} for row in rows]

    def delete_managed_source(self, source_id: int) -> bool:
        """Удалить управляемый источник"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM managed_sources WHERE id = ?', (source_id,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted > 0
        except Exception as e:
            print(f"Error deleting managed source: {e}")
            return False

    def promote_suggested_source(self, source_id: int, admin_comment: str = "", default_lang: str = 'en') -> bool:
        """Одобрить предложенный источник и добавить в активные"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT source_name, source_url FROM suggested_sources
                WHERE id = ?
            ''', (source_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            source_name, source_url = row

            cursor.execute('''
                UPDATE suggested_sources
                SET status = 'approved', admin_comment = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (admin_comment, source_id))

            cursor.execute('''
                INSERT OR IGNORE INTO managed_sources (source_name, source_url, source_type, lang, enabled)
                VALUES (?, ?, 'rss', ?, 1)
            ''', (source_name, source_url, default_lang))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error promoting source: {e}")
            return False

    def add_suggested_source(self, user_id: int, source_name: str, source_url: str, description: str = "") -> bool:
        """Добавить предложенный источник"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO suggested_sources (user_id, source_name, source_url, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, source_name, source_url, description))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding suggested source: {e}")
            return False

    def get_pending_sources(self) -> List[dict]:
        """Получить ожидающие модерации источники"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ss.*, u.username FROM suggested_sources ss
                LEFT JOIN users u ON ss.user_id = u.user_id
                WHERE ss.status = 'pending'
                ORDER BY ss.created_at DESC
            ''')
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    'id': row[0], 'user_id': row[1], 'source_name': row[2],
                    'source_url': row[3], 'description': row[4], 'status': row[5],
                    'admin_comment': row[6], 'created_at': row[7],
                    'reviewed_at': row[8], 'username': row[9]
                })
            conn.close()
            return sources
        except Exception as e:
            print(f"Error getting pending sources: {e}")
            return []

    def update_source_status(self, source_id: int, status: str, admin_comment: str = "") -> bool:
        """Обновить статус предложенного источника"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE suggested_sources
                SET status = ?, admin_comment = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, admin_comment, source_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating source status: {e}")
            return False

    def delete_source(self, source_id: int) -> bool:
        """Совместимый метод удаления: сначала из managed_sources, затем из suggested_sources"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM managed_sources WHERE id = ?', (source_id,))
            deleted = cursor.rowcount
            if deleted == 0:
                cursor.execute('DELETE FROM suggested_sources WHERE id = ?', (source_id,))
                deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted > 0
        except Exception as e:
            print(f"Error deleting source: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Custom Keywords
    # ──────────────────────────────────────────────────────────────────────────

    def add_custom_keyword(self, category: str, lang: str, keyword: str, created_by: Optional[int] = None) -> bool:
        """Добавить кастомное ключевое слово для ESG категории"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO custom_keywords (category, lang, keyword, created_by)
                VALUES (?, ?, ?, ?)
            ''', (category, lang, keyword.strip().lower(), created_by))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding custom keyword: {e}")
            return False

    def remove_custom_keyword(self, category: str, lang: str, keyword: str) -> bool:
        """Удалить кастомное ключевое слово"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM custom_keywords WHERE category = ? AND lang = ? AND keyword = ?',
                (category, lang, keyword.strip().lower())
            )
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted > 0
        except Exception as e:
            print(f"Error removing custom keyword: {e}")
            return False

    def get_custom_keywords(self, category: str = None, lang: str = None) -> List[dict]:
        """Получить кастомные ключевые слова"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category and lang:
            cursor.execute(
                'SELECT category, lang, keyword FROM custom_keywords WHERE category = ? AND lang = ? ORDER BY keyword',
                (category, lang)
            )
        elif category:
            cursor.execute(
                'SELECT category, lang, keyword FROM custom_keywords WHERE category = ? ORDER BY lang, keyword',
                (category,)
            )
        elif lang:
            cursor.execute(
                'SELECT category, lang, keyword FROM custom_keywords WHERE lang = ? ORDER BY category, keyword',
                (lang,)
            )
        else:
            cursor.execute('SELECT category, lang, keyword FROM custom_keywords ORDER BY category, lang, keyword')

        rows = cursor.fetchall()
        conn.close()
        return [{'category': row[0], 'lang': row[1], 'keyword': row[2]} for row in rows]
    # ──────────────────────────────────────────────────────────────────────────
    # Cleanup / Stats
    # ──────────────────────────────────────────────────────────────────────────

    def clear_old_news(self, days: int = 30) -> int:
        """Удалить новости старше чем N дней"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM news
                WHERE date < datetime('now', '-' || ? || ' days')
            ''', (days,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"Error clearing old news: {e}")
            return 0

    def clear_all_news(self) -> int:
        """Удалить все новости из БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM news')
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            print(f"Error clearing all news: {e}")
            return 0

    def clear_all_data(self) -> bool:
        """Полностью очистить БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS user_subscriptions')
            cursor.execute('DROP TABLE IF EXISTS users')
            cursor.execute('DROP TABLE IF EXISTS news')
            cursor.execute('DROP TABLE IF EXISTS suggested_sources')
            cursor.execute('DROP TABLE IF EXISTS managed_sources')
            cursor.execute('DROP TABLE IF EXISTS custom_keywords')
            cursor.execute('DROP TABLE IF EXISTS delivery_history')
            cursor.execute('DROP TABLE IF EXISTS user_engagement')
            conn.commit()
            conn.close()
            self.init_database()
            return True
        except Exception as e:
            print(f"Error clearing all data: {e}")
            return False

    def get_database_stats(self) -> dict:
        """Получить статистику БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM news')
            news_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM users')
            users_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM user_subscriptions')
            subscriptions_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM managed_sources')
            managed_sources_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM custom_keywords')
            custom_keywords_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM delivery_history')
            delivery_history_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM user_engagement')
            user_engagement_count = cursor.fetchone()[0]
            conn.close()
            return {
                'news_count': news_count,
                'users_count': users_count,
                'subscriptions_count': subscriptions_count,
                'managed_sources_count': managed_sources_count,
                'custom_keywords_count': custom_keywords_count,
                'delivery_history_count': delivery_history_count,
                'user_engagement_count': user_engagement_count,
            }
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}