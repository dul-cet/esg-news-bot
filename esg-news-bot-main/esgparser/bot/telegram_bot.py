import logging
import asyncio
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
)
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from esgparser.core.database import NewsDatabase
from esgparser.classifier.esg_classifier import ESGClassifier
from config import (
    CLASSIFIER_CONFIG,
    GEMINI_API_KEY,
    GEMINI_CONFIG,
    NETWORK_CONFIG,
    PERFORMANCE_CONFIG,
)
from esgparser.bot.i18n import t, detect_lang

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ESGNewsBot:
    """Telegram бот для распространения ESG новостей с интегрированным ИИ и Push-рассылкой"""

    ADMIN_IDS = [1025932126]

    def __init__(self, token: str, db: NewsDatabase):
        self.token = token
        self.db = db
        self.classifier = ESGClassifier(
            use_nlp=CLASSIFIER_CONFIG.get('use_nlp', False),
            db_path=self.db.db_path,
        )
        self.gemini_model = None
        self.gemini_client = None
        self._gemini_load_error = None
        self._gemini_retry_after_ts = 0.0
        self._gemini_soft_disabled_reason = None
        self._gemini_fallback_models = [
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash',
        ]
        self.max_response_time = PERFORMANCE_CONFIG.get('max_response_time_sec', 2.0)
        self.send_retries = max(1, NETWORK_CONFIG.get('max_retries', 3))

        if GEMINI_CONFIG.get('enabled'):
            self._load_gemini_model()

        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.scheduler = self._setup_scheduler()
        # Start scheduler only after the event loop is running
        self.application.post_init = self._post_init

    async def _post_init(self, application):
        """Запускается после старта event loop — безопасное место для scheduler.start()"""
        self.scheduler.start()
        logger.info("📅 Планировщик Push-рассылки запущен")
        user_commands = [
            BotCommand("news",           "📰 Последние ESG новости"),
            BotCommand("digest",         "📅 Получить дайджест"),
            BotCommand("awareness",      "📈 Моя ESG-осведомлённость"),
            BotCommand("settings",       "⚙️ Настройки"),
            BotCommand("manage_subs",    "📬 Управление подписками"),
            BotCommand("suggest_source", "💡 Предложить источник"),
            BotCommand("help",           "❓ Помощь"),
        ]
        try:
            await application.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
            admin_commands = user_commands + [BotCommand("admin", "🛠 Админ-панель")]
            for admin_id in self.ADMIN_IDS:
                await application.bot.set_my_commands(
                    admin_commands,
                    scope=BotCommandScopeChat(chat_id=admin_id),
                )
            logger.info("✅ Команды бота установлены для пользователей и администратора")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось установить команды меню: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # Scheduler / Push-рассылка
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_scheduler(self) -> AsyncIOScheduler:
        """Настроить планировщик задач для Push-рассылки"""
        scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

        # Ежедневный дайджест в 09:00 для всех пользователей без персональных настроек
        scheduler.add_job(
            self._send_daily_digest,
            CronTrigger(hour=9, minute=0),
            id='daily_digest',
            name='Ежедневный ESG-дайджест',
            replace_existing=True,
        )

        scheduler.add_job(
            self._ensure_scheduler_health,
            CronTrigger(minute='*/5'),
            id='scheduler_watchdog',
            name='Проверка здоровья планировщика',
            replace_existing=True,
        )

        logger.info("📅 Планировщик настроен: дайджест каждый день в 09:00 (Алматы)")
        return scheduler

    def _ensure_scheduler_health(self):
        """Простая самопроверка для повышения доступности расписаний."""
        try:
            if not self.scheduler.get_job('daily_digest'):
                self.scheduler.add_job(
                    self._send_daily_digest,
                    CronTrigger(hour=9, minute=0),
                    id='daily_digest',
                    name='Ежедневный ESG-дайджест',
                    replace_existing=True,
                )
                logger.warning("⚠️ Восстановлена задача daily_digest")
        except Exception as e:
            logger.error(f"❌ Ошибка watchdog планировщика: {e}")

    async def _send_with_retry(self, chat_id: int, text: str, **kwargs):
        """Отправка сообщения с retry/timeout для устойчивости сервиса."""
        last_error = None
        for attempt in range(1, self.send_retries + 1):
            try:
                await asyncio.wait_for(
                    self.application.bot.send_message(chat_id=chat_id, text=text, **kwargs),
                    timeout=self.max_response_time,
                )
                return True
            except Exception as e:
                last_error = e
                if attempt < self.send_retries:
                    await asyncio.sleep(0.4 * attempt)
        raise last_error

    def _warn_if_slow(self, started_at: float, label: str):
        elapsed = asyncio.get_running_loop().time() - started_at
        if elapsed > self.max_response_time:
            logger.warning(
                f"SLA warning: '{label}' took {elapsed:.2f}s (> {self.max_response_time:.2f}s)"
            )

    async def _send_daily_digest(self):
        """Push-рассылка: отправить дайджест всем подписанным пользователям"""
        logger.info("🔔 Запуск ежедневной Push-рассылки дайджеста...")

        users = self.db.get_all_users()
        if not users:
            logger.info("Нет пользователей для рассылки.")
            return

        sent_count = 0
        failed_count = 0

        for user in users:
            user_id = user['user_id']

            # Пропускаем пользователей без подписок
            subs = self.db.get_user_subscriptions(user_id)
            if not subs:
                continue

            # Пропускаем пользователей с персональным временем (у них отдельная задача)
            if self.scheduler.get_job(f'digest_{user_id}'):
                continue

            news = self.db.get_digest_news(user_id)
            if not news:
                continue
            news_ids = [item.get('id') for item in news if item.get('id') is not None]

            try:
                msg = self._build_digest_message(news, is_push=True, lang=user.get('language', 'ru'))
                await self._send_with_retry(
                    chat_id=user_id,
                    text=msg,
                    parse_mode='HTML',
                    disable_web_page_preview=True,
                )
                self._log_delivery_result(user_id, news_ids, status='sent', digest_type='push')
                self._track_event(user_id, 'digest_push_sent', payload={'items': len(news_ids)})
                sent_count += 1
                logger.info(f"✅ Дайджест отправлен пользователю {user_id}")
            except Exception as e:
                self._log_delivery_result(
                    user_id,
                    news_ids,
                    status='failed',
                    digest_type='push',
                    error_message=str(e),
                )
                self._track_event(user_id, 'digest_push_failed')
                failed_count += 1
                logger.warning(f"❌ Не удалось отправить дайджест пользователю {user_id}: {e}")

        logger.info(f"📊 Рассылка завершена: отправлено {sent_count}, ошибок {failed_count}")

    async def _send_digest_to_user(self, user_id: int):
        """Отправить дайджест конкретному пользователю (персональное расписание)"""
        news = self.db.get_digest_news(user_id)
        if not news:
            return
        news_ids = [item.get('id') for item in news if item.get('id') is not None]
        try:
            lang = self.db.get_user_language(user_id)
            msg = self._build_digest_message(news, is_push=True, lang=lang)
            await self._send_with_retry(
                chat_id=user_id,
                text=msg,
                parse_mode='HTML',
                disable_web_page_preview=True,
            )
            self._log_delivery_result(user_id, news_ids, status='sent', digest_type='push')
            self._track_event(user_id, 'digest_push_sent', payload={'items': len(news_ids)})
            logger.info(f"✅ Персональный дайджест отправлен пользователю {user_id}")
        except Exception as e:
            self._log_delivery_result(
                user_id,
                news_ids,
                status='failed',
                digest_type='push',
                error_message=str(e),
            )
            self._track_event(user_id, 'digest_push_failed')
            logger.warning(f"❌ Ошибка отправки пользователю {user_id}: {e}")

    def _log_delivery_result(
        self,
        user_id: int,
        news_ids: list,
        status: str,
        digest_type: str,
        error_message: str = None,
    ):
        """Сохранить результат рассылки в историю отправок"""
        try:
            self.db.add_delivery_history_batch(
                user_id=user_id,
                news_ids=news_ids,
                status=status,
                channel='telegram',
                digest_type=digest_type,
                error_message=error_message,
            )
        except Exception as e:
            logger.warning(f"Не удалось сохранить историю рассылки для пользователя {user_id}: {e}")

    def _build_digest_message(self, news: list, is_push: bool = False, lang: str = 'ru') -> str:
        """Сформировать текст дайджеста, сгруппированный по категориям E/S/G"""
        emoji_map = {
            'Environment': '🌱',
            'Social':      '👥',
            'Governance':  '⚖️',
        }

        # Группируем новости по категориям
        grouped: dict = {}
        for n in news:
            cat = n.get('esg_category') or 'Прочее'
            grouped.setdefault(cat, []).append(n)

        header = t(lang, 'digest_push_header') if is_push else t(lang, 'digest_manual_header')
        read_label = t(lang, 'digest_read_article')
        msg = header + "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

        for cat, items in grouped.items():
            emoji = emoji_map.get(cat, '📰')
            msg += f"{emoji} <b>{cat}</b>\n\n"
            for n in items:
                title = n.get('title', '').replace('<', '').replace('>', '')
                digest_text = (n.get('digest') or '')[:150]
                url = n.get('url', '')
                msg += f"🔹 <b>{title}</b>\n"
                if digest_text:
                    msg += f"📝 {digest_text}...\n"
                msg += f"🔗 <a href='{url}'>{read_label}</a>\n\n"

        return msg

    # ──────────────────────────────────────────────────────────────────────────
    # Gemini
    # ──────────────────────────────────────────────────────────────────────────

    def _load_gemini_model(self):
        """Инициализировать Gemini API клиент"""
        if not GEMINI_API_KEY:
            self._gemini_load_error = "GEMINI_API_KEY не задан"
            logger.warning("⚠️ Gemini API ключ не задан")
            return
        try:
            from google import genai

            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            model_name = GEMINI_CONFIG.get('model_name', 'gemini-1.5-flash')
            self.gemini_model = model_name
            logger.info(f"✅ Gemini модель инициализирована: {model_name}")
        except Exception as e:
            # Backward-compatible fallback for old SDK installations.
            try:
                import google.generativeai as genai

                genai.configure(api_key=GEMINI_API_KEY)
                model_name = GEMINI_CONFIG.get('model_name', 'gemini-1.5-flash')
                self.gemini_model = genai.GenerativeModel(model_name)
                self.gemini_client = None
                logger.info(f"✅ Gemini модель инициализирована (legacy SDK): {model_name}")
            except Exception as fallback_error:
                self._gemini_load_error = f"new_sdk: {e}; legacy_sdk: {fallback_error}"
                logger.error(f"❌ Не удалось инициализировать Gemini: {self._gemini_load_error}")

    def _generate_with_gemini(self, prompt: str) -> str:
        """Сгенерировать ответ через Gemini"""
        if not self.gemini_model:
            raise RuntimeError("Gemini модель недоступна")

        now = time.time()
        if now < self._gemini_retry_after_ts:
            wait_for = int(max(1, self._gemini_retry_after_ts - now))
            raise RuntimeError(f"Gemini quota cooldown active. Retry in {wait_for}s.")

        if self.gemini_client is not None:
            try:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                )
                text = getattr(response, 'text', None)
                return (text or '').strip()
            except Exception as e:
                err = str(e).lower()
                if 'not found' in err or 'is not supported' in err or '404' in err:
                    fallback_candidates = [m for m in self._gemini_fallback_models if m != self.gemini_model]
                    for candidate in fallback_candidates:
                        try:
                            response = self.gemini_client.models.generate_content(
                                model=candidate,
                                contents=prompt,
                            )
                            self.gemini_model = candidate
                            logger.warning(f"⚠️ Gemini model switched to fallback: {candidate}")
                            text = getattr(response, 'text', None)
                            return (text or '').strip()
                        except Exception:
                            continue
                self._handle_gemini_quota_error(e)
                raise

        response = self.gemini_model.generate_content(
            prompt,
            generation_config={
                'temperature': GEMINI_CONFIG.get('temperature', 0.3),
                'max_output_tokens': 512,
            },
        )
        text = getattr(response, 'text', None)
        return (text or '').strip()

    def _handle_gemini_quota_error(self, error: Exception):
        """Set local cooldown when Gemini API reports quota/rate limiting."""
        message = str(error)
        lower = message.lower()
        if 'resource_exhausted' not in lower and 'quota exceeded' not in lower and '429' not in lower:
            return

        # Try to parse retry hints like "retry in 29.5s".
        wait_seconds = 30
        match = re.search(r'retry in\s+([0-9]+(?:\.[0-9]+)?)s', lower)
        if match:
            try:
                wait_seconds = max(5, int(float(match.group(1))))
            except Exception:
                wait_seconds = 30

        # Soft-disable AI mode when provider reports zero available quota.
        # This prevents repeated failed requests and keeps bot responsive.
        if 'limit: 0' in lower or 'perday' in lower:
            wait_seconds = max(wait_seconds, 3600)
            self._gemini_soft_disabled_reason = 'quota_zero'

        self._gemini_retry_after_ts = time.time() + wait_seconds

    def _gemini_is_available(self) -> bool:
        """Return whether AI requests can be made right now."""
        if not self.gemini_model:
            return False
        return time.time() >= self._gemini_retry_after_ts

    def _friendly_ai_error_text(self, user_id: int, error: Exception) -> str:
        """Return safe, short error text for users instead of raw provider payload."""
        msg = str(error).lower()
        if 'resource_exhausted' in msg or 'quota exceeded' in msg or '429' in msg:
            wait_for = int(max(1, self._gemini_retry_after_ts - time.time()))
            if self._gemini_soft_disabled_reason == 'quota_zero':
                return (
                    "Gemini API лимит исчерпан для текущего тарифа (limit: 0).\n"
                    "Проверьте billing/quota в Google AI Studio и повторите позже."
                )
            return (
                "Gemini API уақытша шектелді / Gemini API временно недоступен по квоте.\n"
                f"Попробуйте снова через ~{wait_for} сек. или проверьте billing/quota в Google AI Studio."
            )
        return self._t(user_id, 'ai_unavailable')

    # ──────────────────────────────────────────────────────────────────────────
    # i18n helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_lang(self, user_id: int) -> str:
        """Retrieve the stored interface language for a user."""
        return self.db.get_user_language(user_id)

    def _t(self, user_id: int, key: str, **kwargs) -> str:
        """Shortcut: translate a key into the user's stored language."""
        return t(self._get_lang(user_id), key, **kwargs)

    def _is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.ADMIN_IDS

    def _command_specs(self):
        """Return supported slash commands and whether they are admin-only."""
        return [
            ('start', self.start_command, False),
            ('help', self.help_command, False),
            ('news', self.news_command, False),
            ('environment', self.environment_command, False),
            ('social', self.social_command, False),
            ('governance', self.governance_command, False),
            ('subscribe', self.subscribe_command, False),
            ('subscriptions', self.subscriptions_command, False),
            ('unsubscribe', self.unsubscribe_command, False),
            ('digest', self.digest_command, False),
            ('set_digest_time', self.set_digest_time_command, False),
            ('set_news_limit', self.set_news_limit_command, False),
            ('awareness', self.awareness_command, False),
            ('admin', self.admin_command, True),
            ('health', self.health_command, True),
            ('language', self.language_command, False),
            ('suggest_source', self.suggest_source_command, False),
            ('add_source', self.add_source_command, True),
            ('sources', self.sources_command, True),
            ('moderate_sources', self.moderate_sources_command, True),
            ('delete_source', self.delete_source_command, True),
            ('add_keyword', self.add_keyword_command, True),
            ('remove_keyword', self.remove_keyword_command, True),
            ('keywords', self.keywords_command, True),
            ('admin_news', self.admin_news_command, True),
            ('delete_news', self.delete_news_command, True),
            ('hide_news', self.hide_news_command, True),
            ('unhide_news', self.unhide_news_command, True),
            ('edit_category', self.edit_category_command, True),
            ('settings', self.settings_command, False),
            ('manage_subs', self.manage_subs_command, False),
        ]

    def _extract_manual_command(self, text: str, bot_username: str = None):
        """Parse malformed command text like '@bot /sources' into command + args."""
        if not text:
            return None, []

        stripped = text.strip()
        # Be tolerant to extra spaces/newlines and parse the first command-like line.
        first_line = next((line.strip() for line in stripped.splitlines() if line.strip()), "")
        candidate = first_line or stripped
        match = re.match(
            r'^(?:@(?P<prefix>[A-Za-z0-9_]+)\s+)?/(?P<command>[A-Za-z0-9_]+)(?:@(?P<suffix>[A-Za-z0-9_]+))?(?:\s+(?P<args>.*))?$',
            candidate,
            flags=re.IGNORECASE,
        )
        if not match:
            return None, []

        normalized_username = (bot_username or '').lstrip('@').lower()
        mentioned_names = [name.lower() for name in (match.group('prefix'), match.group('suffix')) if name]
        if normalized_username and any(name != normalized_username for name in mentioned_names):
            return None, []

        args_text = (match.group('args') or '').strip()
        return match.group('command').lower(), args_text.split() if args_text else []

    async def _dispatch_manual_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, args: list) -> bool:
        """Dispatch a parsed text command through the same handlers as slash commands."""
        command_map = {
            name: (handler, admin_only)
            for name, handler, admin_only in self._command_specs()
        }
        handler_entry = command_map.get(command)
        if not handler_entry:
            return False

        handler, admin_only = handler_entry
        user_id = update.effective_user.id
        if admin_only and not self._is_admin(user_id):
            await update.message.reply_text(self._t(user_id, 'command_admin_only'))
            return True

        original_args = getattr(context, 'args', [])
        context.args = args
        try:
            await handler(update, context)
        finally:
            context.args = original_args
        return True

    def setup_handlers(self):
        app = self.application
        for command_name, handler, _admin_only in self._command_specs():
            app.add_handler(CommandHandler(command_name, handler))
        app.add_handler(CallbackQueryHandler(self.button_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.free_text_handler))
        app.add_error_handler(self.error_handler)

    # ──────────────────────────────────────────────────────────────────────────
    # Commands
    # ──────────────────────────────────────────────────────────────────────────

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show language selection keyboard."""
        started_at = asyncio.get_running_loop().time()
        keyboard = [[
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
            InlineKeyboardButton("🇰🇿 Қазақша", callback_data='lang_kk'),
        ]]
        await update.message.reply_text(
            t('ru', 'language_select'),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        self._warn_if_slow(started_at, 'language_command')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        started_at = asyncio.get_running_loop().time()
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"
        # Detect Telegram language and save as default on first visit
        tg_lang = getattr(update.effective_user, 'language_code', None)
        detected = detect_lang(tg_lang)
        self.db.add_user(user_id, username, language=detected)
        # Show language picker so user can confirm or change
        keyboard = [[
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
            InlineKeyboardButton("🇰🇿 Қазақша", callback_data='lang_kk'),
        ]]
        await update.message.reply_text(
            t('ru', 'language_select'),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        self._track_event(user_id, 'start')
        self._warn_if_slow(started_at, 'start_command')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        started_at = asyncio.get_running_loop().time()
        uid = update.effective_user.id
        key = 'help_admin' if self._is_admin(uid) else 'help'
        await update.message.reply_text(self._t(uid, key), parse_mode='HTML')
        self._warn_if_slow(started_at, 'help_command')

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show a compact admin control panel."""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            await update.message.reply_text(self._t(uid, 'command_admin_only'))
            return
        await update.message.reply_text(
            self._t(uid, 'admin_menu_title'),
            parse_mode='HTML',
            reply_markup=self._build_admin_keyboard(uid),
        )

    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        keyboard = [[
            InlineKeyboardButton("📰 " + self._t(uid, 'news_btn_all'),      callback_data='news_cat_all'),
            InlineKeyboardButton("🌱 E",                                    callback_data='news_cat_Environment'),
            InlineKeyboardButton("👥 S",                                    callback_data='news_cat_Social'),
            InlineKeyboardButton("🏛 G",                                    callback_data='news_cat_Governance'),
        ]]
        await update.message.reply_text(
            self._t(uid, 'news_category_pick'),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        self._track_event(uid, 'news_open')

    def _format_news_date(self, raw_date) -> str:
        """Преобразовать дату новости к формату DD.MM.YYYY."""
        if not raw_date:
            return '-'

        if isinstance(raw_date, datetime):
            return raw_date.strftime('%d.%m.%Y')

        text = str(raw_date).strip()
        if not text:
            return '-'

        # Most stored values are ISO-like strings.
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y')
        except Exception:
            pass

        if len(text) >= 10 and text[4] == '-' and text[7] == '-':
            yyyy, mm, dd = text[:10].split('-')
            return f"{dd}.{mm}.{yyyy}"

        return text[:10]

    def _clean_text(self, raw_value: str) -> str:
        """Convert possible HTML fragments to plain text for Telegram output."""
        if not raw_value:
            return ""
        text = BeautifulSoup(str(raw_value), 'lxml').get_text(' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler for telegram update processing."""
        logger.exception("Unhandled exception while processing update", exc_info=context.error)

    async def environment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._show_category_news(update, 'Environment')

    async def social_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._show_category_news(update, 'Social')

    async def governance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._show_category_news(update, 'Governance')
        

    async def _show_category_news(self, update: Update, category: str):
        started_at = asyncio.get_running_loop().time()
        uid = update.effective_user.id
        user_lang = self._get_lang(uid)
        
        news_list = self.db.get_news_by_category(category, limit=5, lang=user_lang)
        used_fallback = False
        
        if not news_list and user_lang != 'kk':
            news_list = self.db.get_news_by_category(category, limit=5)
            used_fallback = bool(news_list)
            
        if not news_list:
            if user_lang == 'kk':
                await update.message.reply_text(
                    self._t(uid, 'category_empty_selected_lang', category=category, selected_lang=user_lang)
                )
            else:
                await update.message.reply_text(self._t(uid, 'category_empty', category=category))
            return

        emoji = {'Environment': '🌱', 'Social': '👥', 'Governance': '⚖️'}.get(category, '📰')
        title = self._t(uid, 'category_news_title', category=category)
        read_label = self._t(uid, 'news_read_source')
        
        shown_label = self._t(uid, 'news_shown_count') 
        
        message = f"{emoji} <b>{title}</b>\n"
        message += f"📌 {shown_label}: <b>{len(news_list)}</b>\n\n"
        # -------------------------------

        for i, news in enumerate(news_list, 1):
            raw_title = self._clean_text(news.get('title') or '')
            raw_digest = self._clean_text(news.get('digest') or '')
            digest_short = raw_digest if len(raw_digest) <= 140 else raw_digest[:137] + '...'

            date_str = self._format_news_date(news.get('date'))
            message += f"<b>{i}) {raw_title}</b>\n"
            if digest_short:
                message += f"📝 {digest_short}\n"
            message += f"📅 {date_str}\n"
            message += f"🔗 <a href='{news.get('url', '')}'>{read_label}</a>\n\n"
            
        if used_fallback:
            message += self._t(uid, 'lang_fallback_notice', selected_lang=user_lang)
            
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
        self._track_event(uid, 'category_view', category=category, payload={'items': len(news_list)})
        self._warn_if_slow(started_at, f'category_{category.lower()}')

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        keyboard = [
            [InlineKeyboardButton("🌱 Environment", callback_data='sub_Environment'),
             InlineKeyboardButton("👥 Social",       callback_data='sub_Social')],
            [InlineKeyboardButton("⚖️ Governance",   callback_data='sub_Governance')],
        ]
        await update.message.reply_text(
            self._t(uid, 'subscribe_prompt'),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        self._track_event(uid, 'subscribe_open')

    async def subscriptions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        started_at = asyncio.get_running_loop().time()
        uid = update.effective_user.id
        subs = self.db.get_user_subscriptions(uid)
        if not subs:
            await update.message.reply_text(self._t(uid, 'subscriptions_empty'))
            self._warn_if_slow(started_at, 'subscriptions_command')
            return
        
        # Создаём кнопки отписки
        keyboard = []
        for sub in subs:
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {sub}",
                    callback_data=f'unsub_{sub}'
                )
            ])
        
        await update.message.reply_text(
            self._t(uid, 'subscriptions_title') + "\n".join(f"✓ {s}" for s in subs) +
            self._t(uid, 'subscriptions_manage'),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        self._warn_if_slow(started_at, 'subscriptions_command')

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отписка от категории - показать кнопки для выбора"""
        started_at = asyncio.get_running_loop().time()
        uid = update.effective_user.id
        subs = self.db.get_user_subscriptions(uid)
        if not subs:
            await update.message.reply_text(self._t(uid, 'unsubscribe_no_subs'))
            self._warn_if_slow(started_at, 'unsubscribe_command')
            return
        
        keyboard = []
        for sub in subs:
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {sub}",
                    callback_data=f'unsub_{sub}'
                )
            ])
        
        await update.message.reply_text(
            self._t(uid, 'unsubscribe_prompt'),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        self._warn_if_slow(started_at, 'unsubscribe_command')

    async def digest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Дайджест по запросу пользователя"""
        started_at = asyncio.get_running_loop().time()
        user_id = update.effective_user.id
        subs = self.db.get_user_subscriptions(user_id)
        if not subs:
            await update.message.reply_text(self._t(user_id, 'digest_no_subs'))
            self._track_event(user_id, 'digest_no_subs')
            self._warn_if_slow(started_at, 'digest_command')
            return

        news = self.db.get_digest_news(user_id)
        if not news:
            await update.message.reply_text(self._t(user_id, 'digest_no_news'))
            self._track_event(user_id, 'digest_no_news')
            self._warn_if_slow(started_at, 'digest_command')
            return

        news_ids = [item.get('id') for item in news if item.get('id') is not None]
        try:
            msg = self._build_digest_message(news, is_push=False, lang=self._get_lang(user_id))
            await self._send_with_retry(
                chat_id=user_id,
                text=msg,
                parse_mode='HTML',
                disable_web_page_preview=True,
            )
            self._log_delivery_result(user_id, news_ids, status='sent', digest_type='manual')
            self._track_event(user_id, 'digest_manual_sent', payload={'items': len(news_ids)})
        except Exception as e:
            self._log_delivery_result(
                user_id,
                news_ids,
                status='failed',
                digest_type='manual',
                error_message=str(e),
            )
            logger.warning(f"❌ Ошибка ручной отправки дайджеста пользователю {user_id}: {e}")
            await update.message.reply_text("Ошибка при отправке дайджеста. Попробуйте позже.")
            self._track_event(user_id, 'digest_manual_failed')
        self._warn_if_slow(started_at, 'digest_command')

    async def awareness_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать ESG-осведомленность пользователя и персональные рекомендации."""
        uid = update.effective_user.id
        stats = self.db.get_user_engagement_stats(uid, days=30)
        by_category = stats.get('by_category', {})
        event_count = stats.get('total_events', 0)

        categories = ['Environment', 'Social', 'Governance']
        weakest = min(categories, key=lambda c: by_category.get(c, 0))
        tips = {
            'Environment': self._t(uid, 'awareness_tip_environment'),
            'Social': self._t(uid, 'awareness_tip_social'),
            'Governance': self._t(uid, 'awareness_tip_governance'),
        }

        text = self._t(
            uid,
            'awareness_report',
            days=stats.get('period_days', 30),
            total=event_count,
            env=by_category.get('Environment', 0),
            soc=by_category.get('Social', 0),
            gov=by_category.get('Governance', 0),
            weakest=weakest,
            tip=tips.get(weakest, ''),
        )
        await self._send_with_retry(chat_id=uid, text=text, parse_mode='HTML', disable_web_page_preview=True)
        self._track_event(uid, 'awareness_report_view')

    async def set_digest_time_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Изменить время получения Push-дайджеста"""
        uid = update.effective_user.id
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                self._t(uid, 'set_time_prompt'),
                parse_mode='HTML'
            )
            return

        hour = int(context.args[0])
        if not 0 <= hour <= 23:
            await update.message.reply_text(self._t(uid, 'set_time_invalid'))
            return

        user_id = update.effective_user.id

        # Сохраняем персональное время в БД
        self.db.update_user_settings(user_id, digest_hour=hour)

        # Создаём или обновляем персональную задачу в планировщике
        job_id = f'digest_{user_id}'
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            self._send_digest_to_user,
            CronTrigger(hour=hour, minute=0, timezone="Asia/Almaty"),
            id=job_id,
            args=[user_id],
            replace_existing=True,
        )

        await update.message.reply_text(
            self._t(uid, 'set_time_done', hour=f"{hour:02d}"),
            parse_mode='HTML'
        )

    async def set_news_limit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установить количество новостей в дайджесте"""
        uid = update.effective_user.id
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                self._t(uid, 'set_news_limit_prompt'),
                parse_mode='HTML'
            )
            return

        limit = int(context.args[0])
        if not 1 <= limit <= 50:
            await update.message.reply_text(self._t(uid, 'set_news_limit_invalid'))
            return

        # Сохраняем настройку в БД
        self.db.update_user_settings(uid, news_limit=limit)

        await update.message.reply_text(
            self._t(uid, 'set_news_limit_done', limit=limit),
            parse_mode='HTML'
        )

    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка доступности ключевых компонентов сервиса."""
        started_at = asyncio.get_running_loop().time()
        uid = update.effective_user.id
        if not self._is_admin(uid):
            await update.message.reply_text(self._t(uid, 'command_admin_only'))
            return
        text = self._build_health_report(uid)
        await self._send_with_retry(chat_id=uid, text=text, parse_mode='HTML')
        self._track_event(uid, 'health_check')
        self._warn_if_slow(started_at, 'health_command')

    def _track_event(
        self,
        user_id: int,
        event_type: str,
        category: str = None,
        payload: dict = None,
    ):
        """Безопасный трекинг пользовательских ESG-событий."""
        try:
            self.db.log_user_engagement(user_id, event_type, category=category, payload=payload)
        except Exception as e:
            logger.warning(f"Не удалось сохранить событие вовлеченности {event_type} для {user_id}: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # UI helpers — settings & subscriptions keyboards
    # ──────────────────────────────────────────────────────────────────────────

    def _build_settings_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Build the main settings inline keyboard."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(self._t(user_id, 'settings_btn_lang'),  callback_data='settings_lang'),
                InlineKeyboardButton(self._t(user_id, 'settings_btn_subs'),  callback_data='settings_subs'),
            ],
            [
                InlineKeyboardButton(self._t(user_id, 'settings_btn_time'),  callback_data='settings_time'),
                InlineKeyboardButton(self._t(user_id, 'settings_btn_limit'), callback_data='settings_limit'),
            ],
        ])

    def _build_admin_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Build the admin dashboard keyboard."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(self._t(user_id, 'admin_btn_sources'), callback_data='admin_panel_sources'),
                InlineKeyboardButton(self._t(user_id, 'admin_btn_keywords'), callback_data='admin_panel_keywords'),
            ],
            [
                InlineKeyboardButton(self._t(user_id, 'admin_btn_news'), callback_data='admin_panel_news'),
                InlineKeyboardButton(self._t(user_id, 'admin_btn_system'), callback_data='admin_panel_system'),
            ],
        ])

    def _build_admin_back_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(self._t(user_id, 'admin_back_btn'), callback_data='admin_back')]
        ])

    def _build_health_report(self, user_id: int) -> str:
        """Collect a short health summary for admin checks."""
        db_ok = False
        try:
            _ = self.db.get_database_stats()
            db_ok = True
        except Exception:
            db_ok = False

        scheduler_ok = self.scheduler.running if self.scheduler else False
        digest_job_ok = bool(self.scheduler.get_job('daily_digest')) if self.scheduler else False
        return (
            f"{self._t(user_id, 'health_title')}\n\n"
            f"DB: {'✅' if db_ok else '❌'}\n"
            f"Scheduler: {'✅' if scheduler_ok else '❌'}\n"
            f"Daily job: {'✅' if digest_job_ok else '❌'}\n"
            f"SLA target: ≤ {self.max_response_time:.1f}s"
        )

    async def _send_admin_news_list(self, bot, chat_id: int, user_id: int, limit: int = 10):
        """Send recent news to admin with moderation buttons."""
        news_list = self.db.get_recent_news(limit=limit, include_hidden=True)
        if not news_list:
            await bot.send_message(chat_id=chat_id, text=self._t(user_id, 'admin_news_empty'))
            return

        await bot.send_message(
            chat_id=chat_id,
            text=self._t(user_id, 'admin_news_title'),
            parse_mode='HTML',
        )
        for row in news_list:
            hidden = int(row.get('is_hidden', 0)) == 1
            hidden_mark = '🚫 ' if hidden else ''
            body = (
                f"#{row['id']} {hidden_mark}<b>{(row.get('title') or '')[:55]}</b>\n"
                f"📁 {row.get('esg_category') or 'ESG'} | 🌐 {row.get('lang') or '-'}\n"
                f"🔗 <a href='{row.get('url', '')}'>{self._t(user_id, 'news_read')}</a>"
            )
            actions = [
                [
                    InlineKeyboardButton('🌱 E', callback_data=f"admin_setcat_{row['id']}_Environment"),
                    InlineKeyboardButton('👥 S', callback_data=f"admin_setcat_{row['id']}_Social"),
                    InlineKeyboardButton('🏛 G', callback_data=f"admin_setcat_{row['id']}_Governance"),
                ],
                [
                    InlineKeyboardButton(
                        self._t(user_id, 'admin_btn_unhide_news') if hidden else self._t(user_id, 'admin_btn_hide_news'),
                        callback_data=f"admin_{'unhide' if hidden else 'hide'}_{row['id']}",
                    ),
                    InlineKeyboardButton(
                        self._t(user_id, 'admin_btn_delete_news'),
                        callback_data=f"admin_delete_{row['id']}",
                    ),
                ],
            ]
            await bot.send_message(
                chat_id=chat_id,
                text=body,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(actions),
            )

    def _build_subs_keyboard(self, user_id: int, subs: set, from_settings: bool = True) -> InlineKeyboardMarkup:
        """Build the subscription toggle keyboard."""
        callback_prefix = 'manage_toggle_' if from_settings else 'subs_toggle_'
        categories = [('Environment', '🌱'), ('Social', '👥'), ('Governance', '🏛')]
        keyboard = []
        for cat, emoji in categories:
            check = '🔔' if cat in subs else '🔕'
            keyboard.append([InlineKeyboardButton(f"{check} {emoji} {cat}", callback_data=f'{callback_prefix}{cat}')])
        if from_settings:
            keyboard.append([InlineKeyboardButton(self._t(user_id, 'settings_back_btn'), callback_data='settings_back')])
        return InlineKeyboardMarkup(keyboard)

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unified settings menu with inline buttons."""
        uid = update.effective_user.id
        await update.message.reply_text(
            self._t(uid, 'settings_main'),
            parse_mode='HTML',
            reply_markup=self._build_settings_keyboard(uid),
        )

    async def manage_subs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle ESG category subscriptions via inline buttons."""
        uid = update.effective_user.id
        subs = set(self.db.get_user_subscriptions(uid))
        await update.message.reply_text(
            self._t(uid, 'manage_subs_title'),
            parse_mode='HTML',
            reply_markup=self._build_subs_keyboard(uid, subs, from_settings=False),
        )

    async def _send_all_news_to(self, bot, chat_id: int, user_id: int):
        """Send all recent ESG news to the given chat."""
        user_lang = self._get_lang(user_id)
        news_list = self.db.get_news_by_language(user_lang, limit=10)
        used_fallback = False
        if not news_list and user_lang != 'kk':
            news_list = self.db.get_recent_news(limit=10)
            used_fallback = bool(news_list)
        if not news_list:
            text = (
                self._t(user_id, 'news_empty_selected_lang', selected_lang=user_lang)
                if user_lang == 'kk' else self._t(user_id, 'news_empty')
            )
            await bot.send_message(chat_id=chat_id, text=text)
            self._track_event(user_id, 'news_view_empty')
            return
        read_label = self._t(user_id, 'news_read_source')
        message = self._t(user_id, 'news_esg_title')
        emoji_by_category = {'Environment': '🌱', 'Social': '👥', 'Governance': '🏛'}
        for news in news_list:
            category = news.get('esg_category') or 'ESG'
            emoji = emoji_by_category.get(category, '📰')
            date_str = self._format_news_date(news.get('date'))
            title = self._clean_text(news.get('title') or '')
            message += (
                f"<b>{title}</b>\n"
                f"{emoji} {category} | 📅 {date_str}\n"
                f"🔗 <a href='{news.get('url', '')}'>{read_label}</a>\n\n"
            )
        if used_fallback:
            message += self._t(user_id, 'lang_fallback_notice', selected_lang=user_lang)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', disable_web_page_preview=True)
        self._track_event(user_id, 'news_view', payload={'items': len(news_list)})

    async def _send_category_news_to(self, bot, chat_id: int, user_id: int, category: str):
        """Send ESG category news to the given chat."""
        user_lang = self._get_lang(user_id)
        news_list = self.db.get_news_by_category(category, limit=5, lang=user_lang)
        used_fallback = False
        if not news_list and user_lang != 'kk':
            news_list = self.db.get_news_by_category(category, limit=5)
            used_fallback = bool(news_list)
        if not news_list:
            text = (
                self._t(user_id, 'category_empty_selected_lang', category=category, selected_lang=user_lang)
                if user_lang == 'kk' else self._t(user_id, 'category_empty', category=category)
            )
            await bot.send_message(chat_id=chat_id, text=text)
            return
        emoji = {'Environment': '🌱', 'Social': '👥', 'Governance': '⚖️'}.get(category, '📰')
        title_label = self._t(user_id, 'category_news_title', category=category)
        read_label = self._t(user_id, 'news_read_source')
        shown_label = self._t(user_id, 'news_shown_count')
        message = f"{emoji} <b>{title_label}</b>\n📌 {shown_label}: <b>{len(news_list)}</b>\n\n"
        for i, news in enumerate(news_list, 1):
            raw_title = self._clean_text(news.get('title') or '')
            raw_digest = self._clean_text(news.get('digest') or '')
            digest_short = raw_digest if len(raw_digest) <= 140 else raw_digest[:137] + '...'
            date_str = self._format_news_date(news.get('date'))
            message += f"<b>{i}) {raw_title}</b>\n"
            if digest_short:
                message += f"📝 {digest_short}\n"
            message += f"📅 {date_str}\n🔗 <a href='{news.get('url', '')}'>{read_label}</a>\n\n"
        if used_fallback:
            message += self._t(user_id, 'lang_fallback_notice', selected_lang=user_lang)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', disable_web_page_preview=True)
        self._track_event(user_id, 'category_view', category=category, payload={'items': len(news_list)})

    # ──────────────────────────────────────────────────────────────────────────
    # Callbacks
    # ──────────────────────────────────────────────────────────────────────────

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data

        if data.startswith('admin_') and not self._is_admin(user_id):
            await query.edit_message_text(self._t(user_id, 'command_admin_only'))
            return

        if data.startswith('lang_'):
            lang_code = data.replace('lang_', '')
            self.db.update_user_settings(user_id, language=lang_code)
            # Send language-set confirmation, then welcome
            await query.edit_message_text(
                t(lang_code, 'language_set'),
                parse_mode='HTML'
            )
            await self.application.bot.send_message(
                chat_id=user_id,
                text=t(lang_code, 'welcome'),
                parse_mode='HTML'
            )
        elif data.startswith('sub_'):
            category = data.replace('sub_', '')
            self.db.subscribe_user_to_category(user_id, category)
            await query.edit_message_text(
                t(self._get_lang(user_id), 'subscribe_done', category=category),
                parse_mode='HTML'
            )
            self._track_event(user_id, 'subscribe_done', category=category)
        elif data.startswith('unsub_'):
            category = data.replace('unsub_', '')
            self.db.unsubscribe_user_from_category(user_id, category)
            await query.edit_message_text(
                t(self._get_lang(user_id), 'unsubscribe_done', category=category),
                parse_mode='HTML'
            )
            self._track_event(user_id, 'unsubscribe_done', category=category)
        elif data.startswith('approve_'):
            source_id = int(data.replace('approve_', ''))
            if self.db.promote_suggested_source(source_id):
                await query.edit_message_text(t(self._get_lang(user_id), 'source_approved'))
        elif data.startswith('reject_'):
            source_id = int(data.replace('reject_', ''))
            if self.db.update_source_status(source_id, 'rejected'):
                await query.edit_message_text(t(self._get_lang(user_id), 'source_rejected'))

        # ── Admin panel ─────────────────────────────────────────────────────
        elif data == 'admin_back':
            await query.edit_message_text(
                self._t(user_id, 'admin_menu_title'),
                parse_mode='HTML',
                reply_markup=self._build_admin_keyboard(user_id),
            )
        elif data == 'admin_panel_sources':
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_sources'), switch_inline_query_current_chat='/sources'),
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_moderate'), switch_inline_query_current_chat='/moderate_sources'),
                ],
                [
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_add_source'), switch_inline_query_current_chat='/add_source '),
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_delete_source'), switch_inline_query_current_chat='/delete_source '),
                ],
                [InlineKeyboardButton(self._t(user_id, 'admin_back_btn'), callback_data='admin_back')],
            ])
            await query.edit_message_text(
                self._t(user_id, 'admin_panel_sources'),
                parse_mode='HTML',
                reply_markup=keyboard,
            )
        elif data == 'admin_panel_keywords':
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_keywords'), switch_inline_query_current_chat='/keywords'),
                ],
                [
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_add_keyword'), switch_inline_query_current_chat='/add_keyword '),
                    InlineKeyboardButton(self._t(user_id, 'admin_quick_remove_keyword'), switch_inline_query_current_chat='/remove_keyword '),
                ],
                [InlineKeyboardButton(self._t(user_id, 'admin_back_btn'), callback_data='admin_back')],
            ])
            await query.edit_message_text(
                self._t(user_id, 'admin_panel_keywords'),
                parse_mode='HTML',
                reply_markup=keyboard,
            )
        elif data == 'admin_panel_news':
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(self._t(user_id, 'admin_quick_recent_news'), callback_data='admin_recent_news')],
                [InlineKeyboardButton(self._t(user_id, 'admin_back_btn'), callback_data='admin_back')],
            ])
            await query.edit_message_text(
                self._t(user_id, 'admin_panel_news'),
                parse_mode='HTML',
                reply_markup=keyboard,
            )
        elif data == 'admin_panel_system':
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(self._t(user_id, 'admin_quick_health'), callback_data='admin_run_health')],
                [InlineKeyboardButton(self._t(user_id, 'admin_back_btn'), callback_data='admin_back')],
            ])
            await query.edit_message_text(
                self._t(user_id, 'admin_panel_system'),
                parse_mode='HTML',
                reply_markup=keyboard,
            )
        elif data == 'admin_recent_news':
            await self._send_admin_news_list(context.bot, query.message.chat_id, user_id, limit=10)
        elif data == 'admin_run_health':
            await query.edit_message_text(
                self._build_health_report(user_id),
                parse_mode='HTML',
                reply_markup=self._build_admin_back_keyboard(user_id),
            )
        elif data.startswith('admin_hide_'):
            news_id = int(data.replace('admin_hide_', ''))
            if self.db.set_news_hidden(news_id, hidden=True):
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=self._t(user_id, 'hide_news_done', news_id=news_id),
                    parse_mode='HTML',
                )
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton('🌱 E', callback_data=f'admin_setcat_{news_id}_Environment'),
                            InlineKeyboardButton('👥 S', callback_data=f'admin_setcat_{news_id}_Social'),
                            InlineKeyboardButton('🏛 G', callback_data=f'admin_setcat_{news_id}_Governance'),
                        ],
                        [
                            InlineKeyboardButton(self._t(user_id, 'admin_btn_unhide_news'), callback_data=f'admin_unhide_{news_id}'),
                            InlineKeyboardButton(self._t(user_id, 'admin_btn_delete_news'), callback_data=f'admin_delete_{news_id}'),
                        ],
                    ])
                )
        elif data.startswith('admin_unhide_'):
            news_id = int(data.replace('admin_unhide_', ''))
            if self.db.set_news_hidden(news_id, hidden=False):
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=self._t(user_id, 'unhide_news_done', news_id=news_id),
                    parse_mode='HTML',
                )
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton('🌱 E', callback_data=f'admin_setcat_{news_id}_Environment'),
                            InlineKeyboardButton('👥 S', callback_data=f'admin_setcat_{news_id}_Social'),
                            InlineKeyboardButton('🏛 G', callback_data=f'admin_setcat_{news_id}_Governance'),
                        ],
                        [
                            InlineKeyboardButton(self._t(user_id, 'admin_btn_hide_news'), callback_data=f'admin_hide_{news_id}'),
                            InlineKeyboardButton(self._t(user_id, 'admin_btn_delete_news'), callback_data=f'admin_delete_{news_id}'),
                        ],
                    ])
                )
        elif data.startswith('admin_delete_'):
            news_id = int(data.replace('admin_delete_', ''))
            if self.db.delete_news(news_id):
                await query.edit_message_text(
                    self._t(user_id, 'delete_news_done', news_id=news_id),
                    parse_mode='HTML',
                )
        elif data.startswith('admin_setcat_'):
            _, _, news_id_text, category = data.split('_', 3)
            news_id = int(news_id_text)
            self.db.update_news_category(news_id, category, score=1.0)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=self._t(user_id, 'edit_category_done', news_id=news_id, category=category),
                parse_mode='HTML',
            )

        # ── Settings ────────────────────────────────────────────────────────
        elif data == 'settings_back':
            await query.edit_message_text(
                self._t(user_id, 'settings_main'),
                parse_mode='HTML',
                reply_markup=self._build_settings_keyboard(user_id),
            )
        elif data == 'settings_lang':
            keyboard = [[
                InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
                InlineKeyboardButton("🇬🇧 English",  callback_data='lang_en'),
                InlineKeyboardButton("🇰🇿 Қазақша",  callback_data='lang_kk'),
            ], [
                InlineKeyboardButton(self._t(user_id, 'settings_back_btn'), callback_data='settings_back'),
            ]]
            await query.edit_message_text(
                t('ru', 'language_select'),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        elif data == 'settings_subs':
            subs = set(self.db.get_user_subscriptions(user_id))
            await query.edit_message_text(
                self._t(user_id, 'manage_subs_title'),
                parse_mode='HTML',
                reply_markup=self._build_subs_keyboard(user_id, subs, from_settings=True),
            )
        elif data == 'settings_time':
            rows = []
            for start in range(0, 24, 6):
                rows.append([
                    InlineKeyboardButton(f"{h:02d}:00", callback_data=f'stime_{h}')
                    for h in range(start, start + 6)
                ])
            rows.append([InlineKeyboardButton(self._t(user_id, 'settings_back_btn'), callback_data='settings_back')])
            await query.edit_message_text(
                self._t(user_id, 'settings_time_pick'),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(rows),
            )
        elif data == 'settings_limit':
            keyboard = [
                [InlineKeyboardButton("5",  callback_data='slimit_5'),
                 InlineKeyboardButton("10", callback_data='slimit_10'),
                 InlineKeyboardButton("15", callback_data='slimit_15'),
                 InlineKeyboardButton("20", callback_data='slimit_20')],
                [InlineKeyboardButton("30", callback_data='slimit_30'),
                 InlineKeyboardButton("50", callback_data='slimit_50')],
                [InlineKeyboardButton(self._t(user_id, 'settings_back_btn'), callback_data='settings_back')],
            ]
            await query.edit_message_text(
                self._t(user_id, 'settings_limit_pick'),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        elif data.startswith('stime_'):
            hour = int(data.replace('stime_', ''))
            self.db.update_user_settings(user_id, digest_hour=hour)
            job_id = f'digest_{user_id}'
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            self.scheduler.add_job(
                self._send_digest_to_user,
                CronTrigger(hour=hour, minute=0, timezone="Asia/Almaty"),
                id=job_id,
                args=[user_id],
                replace_existing=True,
            )
            await query.edit_message_text(
                self._t(user_id, 'set_time_done', hour=f"{hour:02d}"),
                parse_mode='HTML',
            )
        elif data.startswith('slimit_'):
            limit = int(data.replace('slimit_', ''))
            self.db.update_user_settings(user_id, news_limit=limit)
            await query.edit_message_text(
                self._t(user_id, 'set_news_limit_done', limit=limit),
                parse_mode='HTML',
            )

        # ── Subscription toggles ─────────────────────────────────────────────
        elif data.startswith('manage_toggle_'):
            category = data.replace('manage_toggle_', '')
            subs = set(self.db.get_user_subscriptions(user_id))
            if category in subs:
                self.db.unsubscribe_user_from_category(user_id, category)
                self._track_event(user_id, 'unsubscribe_done', category=category)
            else:
                self.db.subscribe_user_to_category(user_id, category)
                self._track_event(user_id, 'subscribe_done', category=category)
            subs = set(self.db.get_user_subscriptions(user_id))
            await query.edit_message_reply_markup(
                reply_markup=self._build_subs_keyboard(user_id, subs, from_settings=True)
            )
        elif data.startswith('subs_toggle_'):
            category = data.replace('subs_toggle_', '')
            subs = set(self.db.get_user_subscriptions(user_id))
            if category in subs:
                self.db.unsubscribe_user_from_category(user_id, category)
                self._track_event(user_id, 'unsubscribe_done', category=category)
            else:
                self.db.subscribe_user_to_category(user_id, category)
                self._track_event(user_id, 'subscribe_done', category=category)
            subs = set(self.db.get_user_subscriptions(user_id))
            await query.edit_message_reply_markup(
                reply_markup=self._build_subs_keyboard(user_id, subs, from_settings=False)
            )

        # ── News category picker ─────────────────────────────────────────────
        elif data.startswith('news_cat_'):
            cat = data.replace('news_cat_', '')
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
            if cat == 'all':
                await self._send_all_news_to(context.bot, query.message.chat_id, user_id)
            else:
                await self._send_category_news_to(context.bot, query.message.chat_id, user_id, cat)

    # ──────────────────────────────────────────────────────────────────────────
    # Admin
    # ──────────────────────────────────────────────────────────────────────────

    async def suggest_source_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(self._t(uid, 'suggest_source_format'))
            return
        source_name, source_url = context.args[0], context.args[1]
        description = ' '.join(context.args[2:]) if len(context.args) > 2 else ""
        if self.db.add_suggested_source(uid, source_name, source_url, description):
            await update.message.reply_text(self._t(uid, 'suggest_source_sent', name=source_name))

    async def delete_source_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить источник (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return
        
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(self._t(uid, 'delete_source_prompt'))
            return
        
        source_id = int(context.args[0])
        
        if self.db.delete_managed_source(source_id):
            await update.message.reply_text(
                self._t(uid, 'delete_source_done', source_id=source_id),
                parse_mode='HTML'
            )
            logger.info(f"Admin {uid} deleted source {source_id}")
        else:
            await update.message.reply_text(
                self._t(uid, 'delete_source_error', source_id=source_id),
                parse_mode='HTML'
            )

    async def add_source_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавить активный источник (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if len(context.args) < 3:
            await update.message.reply_text(self._t(uid, 'add_source_prompt'), parse_mode='HTML')
            return

        source_url = context.args[0].strip()
        lang = context.args[1].strip().lower()
        source_name = ' '.join(context.args[2:]).strip()

        if not source_url.startswith(('http://', 'https://')) or lang not in ('ru', 'en', 'kk') or not source_name:
            await update.message.reply_text(self._t(uid, 'add_source_prompt'), parse_mode='HTML')
            return

        if self.db.add_managed_source(source_name, source_url, lang=lang, created_by=uid):
            await update.message.reply_text(self._t(uid, 'add_source_done', name=source_name), parse_mode='HTML')
        else:
            await update.message.reply_text(self._t(uid, 'add_source_error'), parse_mode='HTML')

    async def sources_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать активные источники (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        sources = self.db.get_managed_sources(enabled_only=False)
        if not sources:
            await update.message.reply_text(self._t(uid, 'sources_empty'))
            return

        lines = [self._t(uid, 'sources_title')]
        for s in sources[:50]:
            status = '✅' if int(s.get('enabled', 0)) == 1 else '⛔'
            lines.append(f"{status} #{s['id']} [{s.get('lang','en')}] {s['source_name']}\n{s['source_url']}")
        await update.message.reply_text('\n\n'.join(lines), disable_web_page_preview=True)
    async def moderate_sources_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return
        pending = self.db.get_pending_sources()
        if not pending:
            await update.message.reply_text(self._t(uid, 'moderate_no_pending'))
            return
        for s in pending:
            keyboard = [[
                InlineKeyboardButton(self._t(uid, 'moderate_approve_btn'), callback_data=f"approve_{s['id']}"),
                InlineKeyboardButton(self._t(uid, 'moderate_reject_btn'),  callback_data=f"reject_{s['id']}")
            ]]
            await update.message.reply_text(
                f"🔹 <b>{s['source_name']}</b>\n{s['source_url']}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def edit_category_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to manually correct ESG category of a news item"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(self._t(uid, 'edit_category_prompt'))
            return

        try:
            news_id = int(context.args[0])
            new_category = context.args[1].capitalize()

            if new_category not in ['Environment', 'Social', 'Governance']:
                await update.message.reply_text(
                    self._t(uid, 'edit_category_prompt'), parse_mode='HTML'
                )
                return

            # Check if news exists
            news = self.db.get_news_by_id(news_id)
            if not news:
                await update.message.reply_text(
                    self._t(uid, 'edit_category_error', news_id=news_id),
                    parse_mode='HTML'
                )
                return

            # Update category
            self.db.update_news_category(news_id, new_category, score=1.0)
            await update.message.reply_text(
                self._t(uid, 'edit_category_done', news_id=news_id, category=new_category),
                parse_mode='HTML'
            )
            logger.info(f"Admin {uid} changed news {news_id} category to {new_category}")

        except (ValueError, IndexError):
            await update.message.reply_text(self._t(uid, 'edit_category_prompt'))

    async def add_keyword_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавить кастомное ключевое слово ESG (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if len(context.args) < 3:
            await update.message.reply_text(self._t(uid, 'add_keyword_prompt'), parse_mode='HTML')
            return

        category = context.args[0].capitalize()
        lang = context.args[1].lower()
        keyword = ' '.join(context.args[2:]).strip()

        if category not in ('Environment', 'Social', 'Governance') or lang not in ('ru', 'en', 'kk') or not keyword:
            await update.message.reply_text(self._t(uid, 'add_keyword_prompt'), parse_mode='HTML')
            return

        if self.db.add_custom_keyword(category, lang, keyword, created_by=uid):
            await update.message.reply_text(
                self._t(uid, 'add_keyword_done', category=category, lang=lang, keyword=keyword),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(self._t(uid, 'add_keyword_error'), parse_mode='HTML')

    async def remove_keyword_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить кастомное ключевое слово ESG (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if len(context.args) < 3:
            await update.message.reply_text(self._t(uid, 'remove_keyword_prompt'), parse_mode='HTML')
            return

        category = context.args[0].capitalize()
        lang = context.args[1].lower()
        keyword = ' '.join(context.args[2:]).strip()

        if category not in ('Environment', 'Social', 'Governance') or lang not in ('ru', 'en', 'kk') or not keyword:
            await update.message.reply_text(self._t(uid, 'remove_keyword_prompt'), parse_mode='HTML')
            return

        if self.db.remove_custom_keyword(category, lang, keyword):
            await update.message.reply_text(
                self._t(uid, 'remove_keyword_done', category=category, lang=lang, keyword=keyword),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(self._t(uid, 'remove_keyword_error'), parse_mode='HTML')

    async def keywords_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать кастомные ESG-ключевые слова (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        category = None
        lang = None
        if len(context.args) >= 1:
            category = context.args[0].capitalize()
            if category not in ('Environment', 'Social', 'Governance'):
                category = None
        if len(context.args) >= 2:
            lang = context.args[1].lower()
            if lang not in ('ru', 'en', 'kk'):
                lang = None

        keywords = self.db.get_custom_keywords(category=category, lang=lang)
        if not keywords:
            await update.message.reply_text(self._t(uid, 'keywords_empty'))
            return

        lines = [self._t(uid, 'keywords_title')]
        for row in keywords[:200]:
            lines.append(f"• {row['category']} [{row['lang']}] — {row['keyword']}")
        await update.message.reply_text('\n'.join(lines))

    async def admin_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр собранных новостей для админа"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            await update.message.reply_text(self._t(uid, 'command_admin_only'))
            return

        limit = 15
        if context.args and context.args[0].isdigit():
            limit = max(1, min(50, int(context.args[0])))
        await self._send_admin_news_list(context.bot, update.effective_chat.id, uid, limit=limit)

    async def delete_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить новость (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(self._t(uid, 'delete_news_prompt'), parse_mode='HTML')
            return

        news_id = int(context.args[0])
        if self.db.delete_news(news_id):
            await update.message.reply_text(self._t(uid, 'delete_news_done', news_id=news_id), parse_mode='HTML')
        else:
            await update.message.reply_text(self._t(uid, 'delete_news_error', news_id=news_id), parse_mode='HTML')

    async def hide_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Скрыть новость (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(self._t(uid, 'hide_news_prompt'), parse_mode='HTML')
            return

        news_id = int(context.args[0])
        if self.db.set_news_hidden(news_id, hidden=True):
            await update.message.reply_text(self._t(uid, 'hide_news_done', news_id=news_id), parse_mode='HTML')
        else:
            await update.message.reply_text(self._t(uid, 'hide_news_error', news_id=news_id), parse_mode='HTML')

    async def unhide_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Вернуть скрытую новость (админ)"""
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(self._t(uid, 'unhide_news_prompt'), parse_mode='HTML')
            return

        news_id = int(context.args[0])
        if self.db.set_news_hidden(news_id, hidden=False):
            await update.message.reply_text(self._t(uid, 'unhide_news_done', news_id=news_id), parse_mode='HTML')
        else:
            await update.message.reply_text(self._t(uid, 'unhide_news_error', news_id=news_id), parse_mode='HTML')

    # ──────────────────────────────────────────────────────────────────────────
    # Free text
    # ──────────────────────────────────────────────────────────────────────────

    async def free_text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text.strip()
        if not query:
            return

        command_name, command_args = self._extract_manual_command(
            query,
            bot_username=getattr(context.bot, 'username', None),
        )
        if command_name and await self._dispatch_manual_command(update, context, command_name, command_args):
            return

        await update.message.chat.send_action("typing")

        uid = update.effective_user.id
        try:
            results = self._search_news(query, use_ai=True, top_k=5)
            if results:
                read_label = self._t(uid, 'news_read')
                message = self._t(uid, 'found_news_title')
                for i, news in enumerate(results, 1):
                    message += (
                        f"{i}. <b>{news.get('title','')[:60]}...</b>\n"
                        f"   🔗 <a href='{news.get('url','')}'>{ read_label}</a>\n\n"
                    )
                await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
                return
        except Exception as e:
            logger.warning(f"Ошибка поиска: {e}")

        if not self._gemini_is_available():
            await update.message.reply_text(self._t(uid, 'ai_unavailable'))
            return

        try:
            prompt = (
                "Ты ESG-ассистент. Отвечай кратко и по делу. "
                f"Вопрос пользователя: {query}"
            )
            ai_response = self._generate_with_gemini(prompt)
            await update.message.reply_text(
                self._t(uid, 'ai_answer', text=ai_response[:4000]), parse_mode='HTML'
            )
        except Exception as e:
            # Avoid noisy error logs for known quota throttling in soft mode.
            msg = str(e).lower()
            if 'quota' in msg or '429' in msg or 'resource_exhausted' in msg:
                self._handle_gemini_quota_error(e)
                wait_for = int(max(1, self._gemini_retry_after_ts - time.time()))
                reason = self._gemini_soft_disabled_reason or 'rate_limit'
                logger.warning(
                    f"Gemini временно недоступен (quota). cooldown={wait_for}s, reason={reason}"
                )
            else:
                logger.error(f"Генерация: {e}")
            await update.message.reply_text(self._friendly_ai_error_text(uid, e))

    # ──────────────────────────────────────────────────────────────────────────
    # Search helper
    # ──────────────────────────────────────────────────────────────────────────

    def _search_news(self, query: str, use_ai: bool = False, top_k: int = 10):
        return self.db.search_news(query, limit=top_k)

    # ──────────────────────────────────────────────────────────────────────────
    # Run
    # ──────────────────────────────────────────────────────────────────────────

    def run(self):
        logger.info("🚀 Запуск ESG News Bot...")
        self.application.run_polling()