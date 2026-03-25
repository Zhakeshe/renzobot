from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def main_menu_kb(is_admin: bool = False, lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    if lang == 'kz':
        builder.button(text="🌟 Stars сатып алу", callback_data="buy_stars")
        builder.button(text="💎 Telegram Premium", callback_data="buy_premium")
        builder.button(text="🏠 NFT жалдау", callback_data="rent_nft")
        builder.button(text="👤 Профиль", callback_data="profile")
        builder.button(text="👥 Реферал", callback_data="referral")
        builder.button(text="🛠 Қолдау", callback_data="support")
        builder.button(text="🎁 Промокод", callback_data="promocode")
        builder.button(text="🌍 Тілді өзгерту", callback_data="change_lang")
    else:
        builder.button(text="🌟 Купить Stars", callback_data="buy_stars")
        builder.button(text="💎 Telegram Premium", callback_data="buy_premium")
        builder.button(text="🏠 Аренда NFT", callback_data="rent_nft")
        builder.button(text="👤 Профиль", callback_data="profile")
        builder.button(text="👥 Реферал", callback_data="referral")
        builder.button(text="🛠 Поддержка", callback_data="support")
        builder.button(text="🎁 Промокод", callback_data="promocode")
        builder.button(text="🌍 Сменить язык", callback_data="change_lang")
        
    builder.button(text="🖥 Web App", web_app=types.WebAppInfo(url="https://ais-dev-rtojpzn754reldc7yedx5e-747018559939.run.app"))
    if is_admin:
        builder.button(text="📊 Админ панель", callback_data="admin_panel")
    builder.adjust(2)
    return builder.as_markup()

def language_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇰🇿 Қазақша", callback_data="set_lang_kz")
    builder.button(text="🇷🇺 Русский", callback_data="set_lang_ru")
    builder.adjust(2)
    return builder.as_markup()

def admin_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Курс/Комиссия", callback_data="admin_settings")
    builder.button(text="👥 Пайдаланушылар", callback_data="admin_users_0")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="💳 API Теңгерім", callback_data="admin_api_balance")
    builder.button(text="🎫 Тикеттер", callback_data="admin_tickets")
    builder.adjust(1)
    return builder.as_markup()

def admin_users_kb(users: list, offset: int):
    builder = InlineKeyboardBuilder()
    for user in users:
        # user: (user_id, balance, username, ...)
        username = user[2] or user[0]
        builder.button(text=f"👤 {username}", callback_data=f"admin_user_{user[0]}")
    
    # Пагинация
    nav_btns = []
    if offset > 0:
        nav_btns.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"admin_users_{max(0, offset-10)}"))
    nav_btns.append(types.InlineKeyboardButton(text="➡️", callback_data=f"admin_users_{offset+10}"))
    builder.row(*nav_btns)
    
    builder.button(text="‹ Артқа", callback_data="admin_panel")
    builder.adjust(1)
    return builder.as_markup()

def user_actions_kb(user_id: int, is_blocked: bool):
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Баланс өзгерту", callback_data=f"admin_edit_bal_{user_id}")
    if is_blocked:
        builder.button(text="✅ Блоктан шығару", callback_data=f"admin_unban_{user_id}")
    else:
        builder.button(text="🚫 Блоктау", callback_data=f"admin_ban_{user_id}")
    builder.button(text="‹ Тізімге", callback_data="admin_users_0")
    builder.adjust(1)
    return builder.as_markup()

def support_kb(lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    if lang == 'kz':
        builder.button(text="🆕 Жаңа тикет ашу", callback_data="support_new")
        builder.button(text="📂 Менің тикеттерім", callback_data="support_list")
        builder.button(text="‹ Мәзірге", callback_data="back_to_main")
    else:
        builder.button(text="🆕 Открыть новый тикет", callback_data="support_new")
        builder.button(text="📂 Мои тикеты", callback_data="support_list")
        builder.button(text="‹ В меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def tickets_list_kb(tickets: list, is_admin: bool = False):
    builder = InlineKeyboardBuilder()
    for t in tickets:
        # t: (id, user_id, subject, status, created_at)
        status_emoji = "🟢" if t[3] == 'open' else "🟡" if t[3] == 'answered' else "🔴"
        builder.button(text=f"{status_emoji} #{t[0]} - {t[2][:20]}", callback_data=f"ticket_view_{t[0]}")
    
    if is_admin:
        builder.button(text="‹ Админ панель", callback_data="admin_panel")
    else:
        builder.button(text="‹ Қолдау", callback_data="support")
    builder.adjust(1)
    return builder.as_markup()

def ticket_actions_kb(ticket_id: int, is_admin: bool = False, status: str = 'open'):
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Жауап жазу", callback_data=f"ticket_reply_{ticket_id}")
    if status != 'closed':
        builder.button(text="🔒 Жабу", callback_data=f"ticket_close_{ticket_id}")
    
    if is_admin:
        builder.button(text="‹ Тізімге", callback_data="admin_tickets")
    else:
        builder.button(text="‹ Тізімге", callback_data="support_list")
    builder.adjust(1)
    return builder.as_markup()

def stars_items_kb(items: list, lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    # Тек алғашқы 5 тауарды көрсетеміз
    for item in items[:5]:
        # item: {id, name, price_rub_with_margin}
        cb_data = f"buy_stars_item_{item['id']}"
        if len(cb_data.encode('utf-8')) <= 64:
            builder.button(text=f"{item['name']}", callback_data=cb_data)
    
    if lang == 'kz':
        builder.button(text="‹ Мәзірге", callback_data="back_to_main")
    else:
        builder.button(text="‹ В меню", callback_data="back_to_main")
    builder.adjust(2)
    return builder.as_markup()

def profile_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Толтыру (₸)", callback_data="topup")
    builder.button(text="📜 Тапсырыстар тарихы", callback_data="history")
    builder.adjust(1)
    return builder.as_markup()
