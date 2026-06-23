"""
Multilingual support for ESG News Bot.
Supported languages: ru (Russian), en (English), kk (Kazakh)
"""

TRANSLATIONS: dict = {
    'ru': {
        'language_select': "🌐 <b>Выберите язык / Choose language / Тілді таңдаңыз:</b>",
        'language_set': "✅ Язык изменен на <b>Русский</b>.",

        'welcome': (
            "🌍 <b>Добро пожаловать в ESG News Bot!</b>\n\n"
            "Бот доставляет последние новости по ESG (Environmental, Social, Governance).\n\n"
            "🔔 <b>Push-рассылка:</b> каждый день в <b>09:00</b> вы будете получать "
            "автоматический дайджест по вашим подпискам.\n\n"
            "Используйте /settings для настройки языка, подписок и времени рассылки.\n"
            "Используйте /news для просмотра последних новостей."
        ),

        'help': (
            "📚 <b>Команды:</b>\n\n"
            "/news — Последние ESG новости\n"
            "/digest — Получить дайджест прямо сейчас\n"
            "/awareness — Моя ESG-осведомлённость\n"
            "/settings — Настройки (язык, подписки, время)\n"
            "/suggest_source — Предложить источник\n\n"
            "🔔 <b>Push-рассылка</b> дайджеста приходит автоматически каждый день в 09:00."
        ),
        'help_admin': (
            "📚 <b>Режим администратора</b>\n\n"
            "Пользовательские команды остаются прежними.\n"
            "Для управления системой используйте /admin.\n\n"
            "Внутри /admin доступны блоки: источники, keywords, новости и система."
        ),

        'news_empty': "❌ Новостей не найдено.",
        'news_title': "📰 <b>Последние новости:</b>\n\n",
        'news_read': "Читать",
        'news_esg_title': "📰 <b>Последние ESG новости:</b>\n\n",
        'news_read_source': "Читать источник",
        'lang_fallback_notice': "⚠️ На языке <b>{selected_lang}</b> новостей пока нет, показаны материалы на других языках.\n",
        'news_empty_selected_lang': "❌ На языке <b>{selected_lang}</b> новостей пока нет.",
        'category_empty': "❌ Новости «{category}» не найдены.",
        'category_empty_selected_lang': "❌ В категории «{category}» нет новостей на языке <b>{selected_lang}</b>.",
        'category_news_title': "Новости: {category}",
        'news_shown_count': "Показано",

        'digest_push_header': "🔔 <b>Ежедневный ESG-дайджест</b>\n",
        'digest_manual_header': "📅 <b>Ваш персональный ESG-дайджест</b>\n",
        'digest_read_article': "Читать статью",
        'digest_no_subs': "📭 У вас нет подписок.\nИспользуйте /subscribe чтобы подписаться на категории.",
        'digest_no_news': "📭 Новостей по вашим категориям пока нет.\nПопробуйте позже или проверьте другие категории через /subscribe.",

        'subscribe_prompt': "Выберите категорию для подписки.\nПосле подписки вы будете получать <b>автоматический дайджест каждый день в 09:00</b>.",
        'subscribe_done': "✅ Вы подписались на <b>{category}</b>!\n\n🔔 Дайджест будет приходить автоматически в <b>09:00</b> каждый день.",
        'subscriptions_empty': "У вас нет активных подписок.\nИспользуйте /subscribe для настройки.",
        'subscriptions_title': "📬 <b>Ваши подписки:</b>\n\n",
        'subscriptions_time': "\n\n🔔 Дайджест приходит автоматически в <b>09:00</b> каждый день.",
        'subscriptions_manage': "\n\n❌ Нажмите кнопку ниже чтобы отписаться от категории.",

        'unsubscribe_prompt': "🔕 <b>Выберите категорию для отписки:</b>",
        'unsubscribe_done': "✅ Вы отписались от <b>{category}</b>!\n\nВы больше не будете получать новости этой категории.",
        'unsubscribe_no_subs': "📭 У вас нет активных подписок.\nНечего отписывать.",

        'set_time_prompt': "⏰ Укажите час (0–23):\nПример: <code>/set_digest_time 8</code>",
        'set_time_invalid': "❌ Укажите число от 0 до 23.",
        'set_time_done': "✅ Готово! Теперь ваш дайджест будет приходить каждый день в <b>{hour}:00</b>.",

        'set_news_limit_prompt': "📊 Укажите количество новостей (1–50):\nПример: <code>/set_news_limit 10</code>",
        'set_news_limit_invalid': "❌ Укажите число от 1 до 50.",
        'set_news_limit_done': "✅ Готово! Теперь вы будете получать до <b>{limit}</b> новостей в каждом дайджесте.",
        'awareness_report': (
            "📈 <b>Ваш ESG-прогресс за {days} дней</b>\n\n"
            "• Всего ESG-взаимодействий: <b>{total}</b>\n"
            "• Environment: <b>{env}</b>\n"
            "• Social: <b>{soc}</b>\n"
            "• Governance: <b>{gov}</b>\n\n"
            "🎯 Зона роста: <b>{weakest}</b>\n"
            "💡 Рекомендация: {tip}\n\n"
            "📣 Вы подключены к централизованному ESG-каналу и получаете регулярные обновления."
        ),
        'awareness_tip_environment': "Проверьте новости о декарбонизации, энергоэффективности и управлении отходами.",
        'awareness_tip_social': "Изучите темы условий труда, инклюзии и влияния бизнеса на сообщества.",
        'awareness_tip_governance': "Сфокусируйтесь на темах прозрачности, этики и корпоративного управления.",

        'suggest_source_format': "Формат: /suggest_source Название URL [Описание]",
        'suggest_source_sent': "✅ Источник «{name}» отправлен на проверку.",
        'moderate_no_pending': "📋 Нет заявок на модерацию.",
        'moderate_approve_btn': "✅ Одобрить",
        'moderate_reject_btn': "❌ Отклонить",
        'source_approved': "✅ Источник одобрен и активирован.",
        'source_rejected': "❌ Источник отклонен.",

        'add_source_prompt': "🧩 Использование: <code>/add_source &lt;url&gt; &lt;lang&gt; &lt;name&gt;</code>\nПример: <code>/add_source https://example.com/rss.xml en Example RSS</code>",
        'add_source_done': "✅ Источник <b>{name}</b> добавлен в активные.",
        'add_source_error': "❌ Не удалось добавить источник (возможно, уже существует).",
        'sources_title': "📡 <b>Управляемые источники:</b>",
        'sources_empty': "📭 Активных источников пока нет.",

        'delete_source_prompt': "🗑️ Укажите ID источника для удаления:\nПример: <code>/delete_source 5</code>",
        'delete_source_done': "✅ Источник #{source_id} удален.",
        'delete_source_error': "❌ Ошибка: источник #{source_id} не найден.",

        'add_keyword_prompt': (
            "🏷️ <b>Как добавить keyword</b>\n"
            "Формат: <code>/add_keyword &lt;Category&gt; &lt;lang&gt; &lt;keyword&gt;</code>\n\n"
            "Category: <code>Environment</code> | <code>Social</code> | <code>Governance</code>\n"
            "lang: <code>ru</code> | <code>en</code> | <code>kk</code>\n\n"
            "Примеры:\n"
            "• <code>/add_keyword Environment ru углеродный след</code>\n"
            "• <code>/add_keyword Social en labor safety</code>"
        ),
        'add_keyword_done': "✅ Добавлено: <b>{category}</b> [{lang}] — {keyword}",
        'add_keyword_error': "❌ Не удалось добавить keyword (возможно, он уже существует).",
        'remove_keyword_prompt': (
            "🧹 <b>Как удалить keyword</b>\n"
            "Формат: <code>/remove_keyword &lt;Category&gt; &lt;lang&gt; &lt;keyword&gt;</code>\n\n"
            "Category: <code>Environment</code> | <code>Social</code> | <code>Governance</code>\n"
            "lang: <code>ru</code> | <code>en</code> | <code>kk</code>\n\n"
            "Примеры:\n"
            "• <code>/remove_keyword Environment ru углеродный след</code>\n"
            "• <code>/remove_keyword Social en labor safety</code>"
        ),
        'remove_keyword_done': "✅ Удалено: <b>{category}</b> [{lang}] — {keyword}",
        'remove_keyword_error': "❌ Keyword не найден.",
        'keywords_title': "🗂️ <b>Кастомные ключевые слова:</b>",
        'keywords_empty': "📭 Кастомных ключевых слов нет.",

        'admin_news_title': "🛠️ <b>Админ-просмотр новостей:</b>",
        'admin_news_empty': "📭 Новостей нет.",
        'delete_news_prompt': "🗑️ Использование: <code>/delete_news &lt;news_id&gt;</code>",
        'delete_news_done': "✅ Новость #{news_id} удалена.",
        'delete_news_error': "❌ Новость #{news_id} не найдена.",
        'hide_news_prompt': "🙈 Использование: <code>/hide_news &lt;news_id&gt;</code>",
        'hide_news_done': "✅ Новость #{news_id} скрыта.",
        'hide_news_error': "❌ Не удалось скрыть новость #{news_id}.",
        'unhide_news_prompt': "👁️ Использование: <code>/unhide_news &lt;news_id&gt;</code>",
        'unhide_news_done': "✅ Новость #{news_id} снова видна пользователям.",
        'unhide_news_error': "❌ Не удалось вернуть новость #{news_id}.",

        'ai_answer': "🤖 <b>Ответ:</b>\n\n{text}",
        'ai_unavailable': "❌ ИИ недоступен. Попробуйте позже.",
        'found_news_title': "🔍 <b>Найденные новости:</b>\n\n",
        'edit_category_prompt': "📝 Укажите: /edit_category &lt;новость_id&gt; &lt;категория&gt;\nКатегории: Environment, Social, Governance",
        'edit_category_done': "✅ Категория новости #{news_id} изменена на <b>{category}</b>",
        'edit_category_error': "❌ Ошибка: новость #{news_id} не найдена",
        'settings_main': "⚙️ <b>Настройки</b>\n\nВыберите, что хотите изменить:",
        'settings_btn_lang': "🌐 Язык",
        'settings_btn_subs': "📬 Подписки",
        'settings_btn_time': "⏰ Время рассылки",
        'settings_btn_limit': "📊 Лимит новостей",
        'settings_time_pick': "⏰ <b>Выберите час получения дайджеста</b> (время Алматы):",
        'settings_limit_pick': "📊 <b>Сколько новостей присылать в дайджесте?</b>",
        'settings_back_btn': "⬅️ Назад",
        'manage_subs_title': "📬 <b>Управление подписками</b>\n\n🔔 — подписан  🔕 — не подписан\nНажмите на категорию, чтобы переключить:",
        'news_category_pick': "📰 <b>Выберите категорию новостей:</b>",
        'news_btn_all': "Все",
        'command_admin_only': "⛔ Эта команда доступна только администратору.",
        'admin_menu_title': "🛠️ <b>Админ-панель</b>\n\nВыберите блок управления:",
        'admin_btn_sources': "📡 Источники",
        'admin_btn_keywords': "🏷️ Keywords",
        'admin_btn_news': "📰 Новости",
        'admin_btn_system': "🏥 Система",
        'admin_back_btn': "⬅️ Назад",
        'admin_panel_sources': "📡 <b>Источники</b>\n\nОткройте список, модерацию или вставьте шаблон команды в строку ввода.",
        'admin_panel_keywords': "🏷️ <b>Keywords</b>\n\nБыстрый доступ к списку и шаблонам команд для управления ключевыми словами.",
        'admin_panel_news': "📰 <b>Новости</b>\n\nОткройте последние новости с ID и кнопками модерации.",
        'admin_panel_system': "🏥 <b>Система</b>\n\nПроверьте состояние сервиса.",
        'admin_quick_sources': "Список",
        'admin_quick_moderate': "Модерация",
        'admin_quick_add_source': "Добавить",
        'admin_quick_delete_source': "Удалить",
        'admin_quick_keywords': "Список keywords",
        'admin_quick_add_keyword': "Добавить keyword",
        'admin_quick_remove_keyword': "Удалить keyword",
        'admin_quick_recent_news': "Последние новости",
        'admin_quick_health': "Health check",
        'admin_btn_hide_news': "🙈 Скрыть",
        'admin_btn_unhide_news': "👁️ Вернуть",
        'admin_btn_delete_news': "🗑️ Удалить",
        'health_title': "🏥 <b>Health check</b>",
    },

    'en': {
        'language_select': "🌐 <b>Выберите язык / Choose language / Тілді таңдаңыз:</b>",
        'language_set': "✅ Language changed to <b>English</b>.",

        'welcome': (
            "🌍 <b>Welcome to ESG News Bot!</b>\n\n"
            "The bot delivers the latest ESG (Environmental, Social, Governance) news.\n\n"
            "🔔 <b>Push digest:</b> every day at <b>09:00</b> you will automatically receive "
            "a digest based on your subscriptions.\n\n"
            "Use /settings to configure language, subscriptions, and digest time.\n"
            "Use /news to see the latest news."
        ),

        'help': (
            "📚 <b>Commands:</b>\n\n"
            "/news \u2014 Latest ESG news\n"
            "/digest \u2014 Get digest now\n"
            "/awareness \u2014 My ESG awareness\n"
            "/settings \u2014 Settings (language, subscriptions, time)\n"
            "/suggest_source \u2014 Suggest a source\n\n"
            "🔔 <b>Push digest</b> arrives automatically every day at 09:00."
        ),
        'help_admin': (
            "📚 <b>Admin mode</b>\n\n"
            "User commands stay minimal.\n"
            "Use /admin to manage the system.\n\n"
            "Inside /admin you will find sources, keywords, news, and system sections."
        ),

        'news_empty': "❌ No news found.",
        'news_title': "📰 <b>Latest news:</b>\n\n",
        'news_read': "Read",
        'news_esg_title': "📰 <b>Latest ESG news:</b>\n\n",
        'news_read_source': "Read source",
        'lang_fallback_notice': "⚠️ No news found in <b>{selected_lang}</b>, showing items from other languages.\n",
        'news_empty_selected_lang': "❌ No news is currently available in <b>{selected_lang}</b>.",
        'category_empty': "❌ No news found for «{category}».",
        'category_empty_selected_lang': "❌ No <b>{selected_lang}</b> news found for «{category}».",
        'category_news_title': "News: {category}",
        'news_shown_count': "Shown",

        'digest_push_header': "🔔 <b>Daily ESG Digest</b>\n",
        'digest_manual_header': "📅 <b>Your Personal ESG Digest</b>\n",
        'digest_read_article': "Read article",
        'digest_no_subs': "📭 You have no subscriptions.\nUse /subscribe to subscribe to categories.",
        'digest_no_news': "📭 No news for your categories yet.",

        'subscribe_prompt': "Choose a category to subscribe to.",
        'subscribe_done': "✅ You subscribed to <b>{category}</b>.",
        'subscriptions_empty': "You have no active subscriptions.",
        'subscriptions_title': "📬 <b>Your subscriptions:</b>\n\n",
        'subscriptions_time': "",
        'subscriptions_manage': "\n\n❌ Click a button below to unsubscribe.",
        'unsubscribe_prompt': "🔕 <b>Choose category to unsubscribe from:</b>",
        'unsubscribe_done': "✅ You unsubscribed from <b>{category}</b>.",
        'unsubscribe_no_subs': "📭 You have no active subscriptions.",

        'set_time_prompt': "⏰ Enter hour (0–23): <code>/set_digest_time 8</code>",
        'set_time_invalid': "❌ Enter a number between 0 and 23.",
        'set_time_done': "✅ Done! Digest will arrive at <b>{hour}:00</b>.",

        'set_news_limit_prompt': "📊 Enter number of news items (1–50): <code>/set_news_limit 10</code>",
        'set_news_limit_invalid': "❌ Enter a number between 1 and 50.",
        'set_news_limit_done': "✅ Done! You will receive up to <b>{limit}</b> items.",
        'awareness_report': (
            "📈 <b>Your ESG progress for {days} days</b>\n\n"
            "• Total ESG interactions: <b>{total}</b>\n"
            "• Environment: <b>{env}</b>\n"
            "• Social: <b>{soc}</b>\n"
            "• Governance: <b>{gov}</b>\n\n"
            "🎯 Growth area: <b>{weakest}</b>\n"
            "💡 Recommendation: {tip}\n\n"
            "📣 You are connected to a centralized ESG information channel with regular updates."
        ),
        'awareness_tip_environment': "Review stories on decarbonization, energy efficiency, and waste management.",
        'awareness_tip_social': "Focus on labor practices, inclusion, and business impact on communities.",
        'awareness_tip_governance': "Track transparency, ethics, and corporate governance developments.",

        'suggest_source_format': "Format: /suggest_source Name URL [Description]",
        'suggest_source_sent': "✅ Source «{name}» submitted for review.",
        'moderate_no_pending': "📋 No pending requests.",
        'moderate_approve_btn': "✅ Approve",
        'moderate_reject_btn': "❌ Reject",
        'source_approved': "✅ Source approved and activated.",
        'source_rejected': "❌ Source rejected.",

        'add_source_prompt': "🧩 Usage: <code>/add_source &lt;url&gt; &lt;lang&gt; &lt;name&gt;</code>",
        'add_source_done': "✅ Source <b>{name}</b> added.",
        'add_source_error': "❌ Could not add source.",
        'sources_title': "📡 <b>Managed sources:</b>",
        'sources_empty': "📭 No managed sources.",

        'delete_source_prompt': "🗑️ Specify source ID: <code>/delete_source 5</code>",
        'delete_source_done': "✅ Source #{source_id} deleted.",
        'delete_source_error': "❌ Source #{source_id} not found.",

        'add_keyword_prompt': (
            "🏷️ <b>How to add a keyword</b>\n"
            "Format: <code>/add_keyword &lt;Category&gt; &lt;lang&gt; &lt;keyword&gt;</code>\n\n"
            "Category: <code>Environment</code> | <code>Social</code> | <code>Governance</code>\n"
            "lang: <code>ru</code> | <code>en</code> | <code>kk</code>\n\n"
            "Examples:\n"
            "• <code>/add_keyword Environment en carbon footprint</code>\n"
            "• <code>/add_keyword Governance ru корпоративная этика</code>"
        ),
        'add_keyword_done': "✅ Added: <b>{category}</b> [{lang}] — {keyword}",
        'add_keyword_error': "❌ Could not add keyword.",
        'remove_keyword_prompt': (
            "🧹 <b>How to remove a keyword</b>\n"
            "Format: <code>/remove_keyword &lt;Category&gt; &lt;lang&gt; &lt;keyword&gt;</code>\n\n"
            "Category: <code>Environment</code> | <code>Social</code> | <code>Governance</code>\n"
            "lang: <code>ru</code> | <code>en</code> | <code>kk</code>\n\n"
            "Examples:\n"
            "• <code>/remove_keyword Environment en carbon footprint</code>\n"
            "• <code>/remove_keyword Governance ru корпоративная этика</code>"
        ),
        'remove_keyword_done': "✅ Removed: <b>{category}</b> [{lang}] — {keyword}",
        'remove_keyword_error': "❌ Keyword not found.",
        'keywords_title': "🗂️ <b>Custom keywords:</b>",
        'keywords_empty': "📭 No custom keywords.",

        'admin_news_title': "🛠️ <b>Admin news view:</b>",
        'admin_news_empty': "📭 No news found.",
        'delete_news_prompt': "🗑️ Usage: <code>/delete_news &lt;news_id&gt;</code>",
        'delete_news_done': "✅ News #{news_id} deleted.",
        'delete_news_error': "❌ News #{news_id} not found.",
        'hide_news_prompt': "🙈 Usage: <code>/hide_news &lt;news_id&gt;</code>",
        'hide_news_done': "✅ News #{news_id} hidden.",
        'hide_news_error': "❌ Could not hide news #{news_id}.",
        'unhide_news_prompt': "👁️ Usage: <code>/unhide_news &lt;news_id&gt;</code>",
        'unhide_news_done': "✅ News #{news_id} visible again.",
        'unhide_news_error': "❌ Could not unhide news #{news_id}.",

        'ai_answer': "🤖 <b>Answer:</b>\n\n{text}",
        'ai_unavailable': "❌ AI unavailable. Please try again later.",
        'found_news_title': "🔍 <b>Found news:</b>\n\n",
        'edit_category_prompt': "📝 Usage: /edit_category &lt;news_id&gt; &lt;category&gt;",
        'edit_category_done': "✅ News #{news_id} category changed to <b>{category}</b>",
        'edit_category_error': "❌ Error: news #{news_id} not found",
        'settings_main': "\u2699\ufe0f <b>Settings</b>\n\nChoose what you'd like to change:",
        'settings_btn_lang': "🌐 Language",
        'settings_btn_subs': "📬 Subscriptions",
        'settings_btn_time': "⏰ Digest time",
        'settings_btn_limit': "📊 News limit",
        'settings_time_pick': "⏰ <b>Choose the hour for your digest</b> (Almaty time):",
        'settings_limit_pick': "📊 <b>How many news items in the digest?</b>",
        'settings_back_btn': "⬅️ Back",
        'manage_subs_title': "📬 <b>Manage subscriptions</b>\n\n🔔 — subscribed  🔕 — not subscribed\nTap a category to toggle:",
        'news_category_pick': "📰 <b>Choose news category:</b>",
        'news_btn_all': "All",
        'command_admin_only': "\u26d4 This command is for administrators only.",
        'admin_menu_title': "🛠️ <b>Admin panel</b>\n\nChoose a control block:",
        'admin_btn_sources': "📡 Sources",
        'admin_btn_keywords': "🏷️ Keywords",
        'admin_btn_news': "📰 News",
        'admin_btn_system': "🏥 System",
        'admin_back_btn': "⬅️ Back",
        'admin_panel_sources': "📡 <b>Sources</b>\n\nOpen the list, moderation queue, or insert a command template into the input field.",
        'admin_panel_keywords': "🏷️ <b>Keywords</b>\n\nQuick access to the list and command templates for keyword management.",
        'admin_panel_news': "📰 <b>News</b>\n\nOpen recent items with IDs and moderation buttons.",
        'admin_panel_system': "🏥 <b>System</b>\n\nCheck current service health.",
        'admin_quick_sources': "List",
        'admin_quick_moderate': "Moderate",
        'admin_quick_add_source': "Add",
        'admin_quick_delete_source': "Delete",
        'admin_quick_keywords': "List keywords",
        'admin_quick_add_keyword': "Add keyword",
        'admin_quick_remove_keyword': "Remove keyword",
        'admin_quick_recent_news': "Recent news",
        'admin_quick_health': "Health check",
        'admin_btn_hide_news': "🙈 Hide",
        'admin_btn_unhide_news': "👁️ Restore",
        'admin_btn_delete_news': "🗑️ Delete",
        'health_title': "🏥 <b>Health check</b>",
    },

    'kk': {
        'language_select': "🌐 <b>Выберите язык / Choose language / Тілді таңдаңыз:</b>",
        'language_set': "✅ Тіл <b>Қазақша</b> тіліне өзгертілді.",
        'welcome': (
            "🌍 <b>ESG News Bot-қа қош келдіңіз!</b>\n\n"
            "ESG (қоршаған орта, әлеуметтік, басқару) бойынша соңғы жаңалықтарды алыңыз.\n\n"
            "🔔 Күн сайын сағат <b>09:00</b>-де автоматты дайджест келеді.\n\n"
            "Тіл, жазылымдар мен уақытты реттеу үшін /settings пәрменін қолданыңыз.\n"
            "Соңғы жаңалықтарды көру үшін /news қолданыңыз."
        ),
        'help': (
            "📚 <b>Пәрмендер:</b>\n\n"
            "/news \u2014 Соңғы ESG жаңалықтар\n"
            "/digest \u2014 Дайджест алу\n"
            "/awareness \u2014 Менің ESG белсенділігім\n"
            "/settings \u2014 Баптаулар (тіл, жазылымдар, уақыт)\n"
            "/suggest_source \u2014 Дереккөз ұсыну\n\n"
            "🔔 <b>Push дайджест</b> күн сайын сағат 09:00-де автоматты жіберіледі."
        ),
        'help_admin': (
            "📚 <b>Admin режимі</b>\n\n"
            "Пайдаланушы пәрмендері ықшам күйінде қалады.\n"
            "Жүйені басқару үшін /admin қолданыңыз.\n\n"
            "Ішінде дереккөздер, keywords, жаңалықтар және жүйе блоктары бар."
        ),
        'news_empty': "❌ Жаңалықтар табылмады.",
        'news_title': "📰 <b>Соңғы жаңалықтар:</b>\n\n",
        'news_read': "Оқу",
        'news_esg_title': "📰 <b>Соңғы ESG жаңалықтары:</b>\n\n",
        'news_read_source': "Дереккөзді оқу",
        'lang_fallback_notice': "⚠️ <b>{selected_lang}</b> тілінде жаңалық жоқ, басқа тілдердегі материалдар көрсетілді.\n",
        'news_empty_selected_lang': "❌ <b>{selected_lang}</b> тілінде жаңалық әзірге жоқ.",
        'category_empty': "❌ «{category}» бойынша жаңалықтар табылмады.",
        'category_empty_selected_lang': "❌ «{category}» санаты бойынша <b>{selected_lang}</b> тілінде жаңалық табылмады.",
        'category_news_title': "Жаңалықтар: {category}",
        'news_shown_count': "Көрсетілді",
        'digest_push_header': "🔔 <b>Күнделікті ESG дайджест</b>\n",
        'digest_manual_header': "📅 <b>Жеке ESG дайджестіңіз</b>\n",
        'digest_read_article': "Мақаланы оқу",
        'digest_no_subs': "📭 Жазылымдар жоқ.",
        'digest_no_news': "📭 Жаңалықтар табылмады.",
        'subscribe_prompt': "Жазылу үшін санатты таңдаңыз.",
        'subscribe_done': "✅ <b>{category}</b> санатына жазылдыңыз.",
        'subscriptions_empty': "Белсенді жазылымдар жоқ.",
        'subscriptions_title': "📬 <b>Сіздің жазылымдарыңыз:</b>\n\n",
        'subscriptions_time': "",
        'subscriptions_manage': "\n\n❌ Төмендегі батырмамен жазылымнан бас тартыңыз.",
        'unsubscribe_prompt': "🔕 <b>Жазылымнан бас тарту санатын таңдаңыз:</b>",
        'unsubscribe_done': "✅ <b>{category}</b> санатынан бас тартылды.",
        'unsubscribe_no_subs': "📭 Белсенді жазылымдар жоқ.",
        'set_time_prompt': "⏰ Сағатты енгізіңіз (0–23): <code>/set_digest_time 8</code>",
        'set_time_invalid': "❌ 0-23 аралығындағы санды енгізіңіз.",
        'set_time_done': "✅ Дайын! Дайджест уақыты: <b>{hour}:00</b>.",
        'set_news_limit_prompt': "📊 Жаңалық саны (1–50): <code>/set_news_limit 10</code>",
        'set_news_limit_invalid': "❌ 1-50 аралығындағы санды енгізіңіз.",
        'set_news_limit_done': "✅ Енді дайджестте <b>{limit}</b> жаңалыққа дейін келеді.",
        'awareness_report': (
            "📈 <b>Соңғы {days} күндегі ESG белсенділігіңіз</b>\n\n"
            "• ESG әрекеттері: <b>{total}</b>\n"
            "• Environment: <b>{env}</b>\n"
            "• Social: <b>{soc}</b>\n"
            "• Governance: <b>{gov}</b>\n\n"
            "🎯 Көбірек көңіл бөлу аймағы: <b>{weakest}</b>\n"
            "💡 Ұсыныс: {tip}\n\n"
            "📣 Сіз орталықтандырылған ESG ақпарат арнасына қосылғансыз."
        ),
        'awareness_tip_environment': "Көміртекті азайту, энергия тиімділігі және қалдықтарды басқару тақырыптарын қараңыз.",
        'awareness_tip_social': "Еңбек жағдайы, инклюзия және қоғамға әсер тақырыптарын оқыңыз.",
        'awareness_tip_governance': "Ашықтық, этика және корпоративтік басқару жаңалықтарын бақылаңыз.",
        'suggest_source_format': "Формат: /suggest_source Атауы URL [Сипаттама]",
        'suggest_source_sent': "✅ «{name}» дереккөзі тексеруге жіберілді.",
        'moderate_no_pending': "📋 Модерацияға сұраныстар жоқ.",
        'moderate_approve_btn': "✅ Мақұлдау",
        'moderate_reject_btn': "❌ Қабылдамау",
        'source_approved': "✅ Дереккөз мақұлданды және қосылды.",
        'source_rejected': "❌ Дереккөз қабылданбады.",
        'add_source_prompt': "🧩 Пайдалану: <code>/add_source &lt;url&gt; &lt;lang&gt; &lt;name&gt;</code>",
        'add_source_done': "✅ <b>{name}</b> дереккөзі қосылды.",
        'add_source_error': "❌ Дереккөзді қосу мүмкін болмады.",
        'sources_title': "📡 <b>Басқарылатын дереккөздер:</b>",
        'sources_empty': "📭 Дереккөздер жоқ.",
        'delete_source_prompt': "🗑️ Дереккөз ID енгізіңіз: <code>/delete_source 5</code>",
        'delete_source_done': "✅ #{source_id} дереккөзі жойылды.",
        'delete_source_error': "❌ #{source_id} дереккөзі табылмады.",
        'add_keyword_prompt': (
            "🏷️ <b>Keyword қосу нұсқаулығы</b>\n"
            "Формат: <code>/add_keyword &lt;Category&gt; &lt;lang&gt; &lt;keyword&gt;</code>\n\n"
            "Category: <code>Environment</code> | <code>Social</code> | <code>Governance</code>\n"
            "lang: <code>ru</code> | <code>en</code> | <code>kk</code>\n\n"
            "Мысалдар:\n"
            "• <code>/add_keyword Environment kk көміртек ізі</code>\n"
            "• <code>/add_keyword Social ru охрана труда</code>"
        ),
        'add_keyword_done': "✅ Қосылды: <b>{category}</b> [{lang}] — {keyword}",
        'add_keyword_error': "❌ Keyword қосылмады.",
        'remove_keyword_prompt': (
            "🧹 <b>Keyword өшіру нұсқаулығы</b>\n"
            "Формат: <code>/remove_keyword &lt;Category&gt; &lt;lang&gt; &lt;keyword&gt;</code>\n\n"
            "Category: <code>Environment</code> | <code>Social</code> | <code>Governance</code>\n"
            "lang: <code>ru</code> | <code>en</code> | <code>kk</code>\n\n"
            "Мысалдар:\n"
            "• <code>/remove_keyword Environment kk көміртек ізі</code>\n"
            "• <code>/remove_keyword Social ru охрана труда</code>"
        ),
        'remove_keyword_done': "✅ Өшірілді: <b>{category}</b> [{lang}] — {keyword}",
        'remove_keyword_error': "❌ Keyword табылмады.",
        'keywords_title': "🗂️ <b>Кастом keyword тізімі:</b>",
        'keywords_empty': "📭 Кастом keyword жоқ.",
        'admin_news_title': "🛠️ <b>Админ жаңалықтар көрінісі:</b>",
        'admin_news_empty': "📭 Жаңалық жоқ.",
        'delete_news_prompt': "🗑️ Пайдалану: <code>/delete_news &lt;news_id&gt;</code>",
        'delete_news_done': "✅ #{news_id} жаңалығы жойылды.",
        'delete_news_error': "❌ #{news_id} жаңалығы табылмады.",
        'hide_news_prompt': "🙈 Пайдалану: <code>/hide_news &lt;news_id&gt;</code>",
        'hide_news_done': "✅ #{news_id} жаңалығы жасырылды.",
        'hide_news_error': "❌ #{news_id} жаңалығын жасыру мүмкін болмады.",
        'unhide_news_prompt': "👁️ Пайдалану: <code>/unhide_news &lt;news_id&gt;</code>",
        'unhide_news_done': "✅ #{news_id} жаңалығы қайта көрсетіледі.",
        'unhide_news_error': "❌ #{news_id} жаңалығын қайта қосу мүмкін болмады.",
        'ai_answer': "🤖 <b>Жауап:</b>\n\n{text}",
        'ai_unavailable': "❌ ЖИ қолжетімсіз. Кейінірек қайталап көріңіз.",
        'found_news_title': "🔍 <b>Табылған жаңалықтар:</b>\n\n",
        'edit_category_prompt': "📝 Пайдалану: /edit_category &lt;news_id&gt; &lt;category&gt;",
        'edit_category_done': "✅ #{news_id} жаңалығының санаты <b>{category}</b> болып өзгертілді",
        'edit_category_error': "❌ Қате: #{news_id} жаңалығы табылмады",
        'settings_main': "⚙️ <b>Баптаулар</b>\n\nНені өзгерткіңіз келеді?",
        'settings_btn_lang': "🌐 Тіл",
        'settings_btn_subs': "📬 Жазылымдар",
        'settings_btn_time': "⏰ Жіберу уақыты",
        'settings_btn_limit': "📊 Жаңалық саны",
        'settings_time_pick': "⏰ <b>Дайджест алу сағатын таңдаңыз</b> (Алматы уақыты):",
        'settings_limit_pick': "📊 <b>Дайджестте қанша жаңалық болсын?</b>",
        'settings_back_btn': "⬅️ Артқа",
        'manage_subs_title': "📬 <b>Жазылымдарды басқару</b>\n\n🔔 — жазылдым  🔕 — жазылмадым\nАуыстыру үшін басыңыз:",
        'news_category_pick': "📰 <b>Жаңалықтар санатын таңдаңыз:</b>",
        'news_btn_all': "Барлығы",
        'command_admin_only': "⛔ Бұл пәрмен тек әкімшіге қол жетімді.",
        'admin_menu_title': "🛠️ <b>Admin панелі</b>\n\nБасқару блогын таңдаңыз:",
        'admin_btn_sources': "📡 Дереккөздер",
        'admin_btn_keywords': "🏷️ Keywords",
        'admin_btn_news': "📰 Жаңалықтар",
        'admin_btn_system': "🏥 Жүйе",
        'admin_back_btn': "⬅️ Артқа",
        'admin_panel_sources': "📡 <b>Дереккөздер</b>\n\nТізімді, модерацияны ашыңыз немесе пәрмен үлгісін енгізу жолағына қойыңыз.",
        'admin_panel_keywords': "🏷️ <b>Keywords</b>\n\nКілт сөздер тізімі мен басқару үлгілеріне жылдам қолжетімділік.",
        'admin_panel_news': "📰 <b>Жаңалықтар</b>\n\nID және модерация батырмалары бар соңғы жазбаларды ашыңыз.",
        'admin_panel_system': "🏥 <b>Жүйе</b>\n\nҚызмет күйін тексеріңіз.",
        'admin_quick_sources': "Тізім",
        'admin_quick_moderate': "Модерация",
        'admin_quick_add_source': "Қосу",
        'admin_quick_delete_source': "Өшіру",
        'admin_quick_keywords': "Keywords тізімі",
        'admin_quick_add_keyword': "Keyword қосу",
        'admin_quick_remove_keyword': "Keyword өшіру",
        'admin_quick_recent_news': "Соңғы жаңалықтар",
        'admin_quick_health': "Health check",
        'admin_btn_hide_news': "🙈 Жасыру",
        'admin_btn_unhide_news': "👁️ Қайтару",
        'admin_btn_delete_news': "🗑️ Өшіру",
        'health_title': "🏥 <b>Health check</b>",
    },
}

_TELEGRAM_LANG_MAP = {
    'ru': 'ru',
    'kk': 'kk',
    'en': 'en',
}
SUPPORTED_LANGS = ('ru', 'en', 'kk')
DEFAULT_LANG = 'ru'


def t(lang: str, key: str, **kwargs) -> str:
    """Return a translated string for the given language and key."""
    strings = TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT_LANG]
    text = strings.get(key) or TRANSLATIONS[DEFAULT_LANG].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def detect_lang(telegram_lang_code: str | None) -> str:
    """Map a Telegram language_code to a supported bot language."""
    if telegram_lang_code:
        code = telegram_lang_code.split('-')[0].lower()
        return _TELEGRAM_LANG_MAP.get(code, DEFAULT_LANG)
    return DEFAULT_LANG
