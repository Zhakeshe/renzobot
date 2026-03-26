from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def top_referrers_kb(lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    back_text = "‹ Артқа" if lang == 'kz' else "‹ Назад"
    builder.button(text=back_text, callback_data="referral")
    return builder.as_markup()

def payment_methods_kb(lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    if lang == 'kz':
        builder.button(text="💳 Kaspi (Аударма)", callback_data="topup_kaspi")
        builder.button(text="🤖 CryptoBot", callback_data="topup_cryptobot")
        builder.button(text="🌟 Telegram Stars", callback_data="topup_stars")
        builder.button(text="‹ Артқа", callback_data="profile")
    else:
        builder.button(text="💳 Kaspi (Перевод)", callback_data="topup_kaspi")
        builder.button(text="🤖 CryptoBot", callback_data="topup_cryptobot")
        builder.button(text="🌟 Telegram Stars", callback_data="topup_stars")
        builder.button(text="‹ Назад", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()

def admin_payment_request_kb(req_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Растау", callback_data=f"adm_pay_approve_{req_id}")
    builder.button(text="❌ Бас тарту", callback_data=f"adm_pay_reject_{req_id}")
    builder.adjust(2)
    return builder.as_markup()

def main_menu_kb(is_admin: bool = False, lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    if lang == 'kz':
        builder.button(text="🌟 Stars сатып алу", callback_data="buy_stars")
        builder.button(text="💰 Stars сату", callback_data="sell_stars")
        builder.button(text="🏠 NFT жалдау", callback_data="rent_nft")
        builder.button(text="📦 NFT сатып алу", callback_data="buy_nft")
        builder.button(text="🎁 Кәдімгі сыйлық", callback_data="buy_gift")
        builder.button(text="💎 TON сатып алу", callback_data="buy_ton")
        builder.button(text="✨ Премиум", callback_data="buy_premium")
        builder.button(text="💳 Толтыру", callback_data="topup")
        builder.button(text="👤 Профиль", callback_data="profile")
        builder.button(text="🛠 Қолдау", callback_data="support")
        builder.button(text="🧮 Калькулятор", callback_data="calculator")
        builder.button(text="ℹ️ Ақпарат", callback_data="info")
        builder.button(text="👥 Реферал жүйесі", callback_data="referral")
        builder.button(text="🏆 Топ клиенттер", callback_data="top_clients")
        builder.button(text="💕 Пікірлер", url="https://t.me/reviews")
        builder.button(text="🎁 Нұсқаулық", url="https://t.me/instruction")
        builder.button(text="💸 Жарнама", url="https://t.me/ads")
    else:
        builder.button(text="🌟 Купить звёзды", callback_data="buy_stars")
        builder.button(text="💰 Продать звёзды", callback_data="sell_stars")
        builder.button(text="🏠 Аренда NFT", callback_data="rent_nft")
        builder.button(text="📦 Купить NFT.", callback_data="buy_nft")
        builder.button(text="🎁 Купить обычный подарок.", callback_data="buy_gift")
        builder.button(text="💎 Купить TON", callback_data="buy_ton")
        builder.button(text="✨ Премиум", callback_data="buy_premium")
        builder.button(text="💳 Пополнение", callback_data="topup")
        builder.button(text="👤 Профиль", callback_data="profile")
        builder.button(text="🛠 Поддержка", callback_data="support")
        builder.button(text="🧮 Калькулятор", callback_data="calculator")
        builder.button(text="ℹ️ Информация", callback_data="info")
        builder.button(text="👥 Реферальная система", callback_data="referral")
        builder.button(text="🏆 Топ клиентов", callback_data="top_clients")
        builder.button(text="💕 Отзывы", url="https://t.me/reviews")
        builder.button(text="🎁 Инструкция", url="https://t.me/instruction")
        builder.button(text="💸 Купить рекламу в боте.", url="https://t.me/ads")
        
    if is_admin:
        builder.button(text="📊 Админ панель", callback_data="admin_panel")
    
    builder.adjust(2, 2, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1)
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
    builder.button(text="📢 Жарнама (Рассылка)", callback_data="admin_broadcast")
    builder.button(text="🏆 Рефералдарды марапаттау", callback_data="admin_reward_referrals")
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
    builder.button(text="🌍 Тілді өзгерту / Сменить язык", callback_data="change_lang")
    builder.button(text="‹ Артқа / Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def history_kb(orders: list, lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    for order in orders:
        # order: (id, user_id, order_id_api, status, product_type, product_name, description, amount_kzt, profit_kzt, tx_hash, is_notified, created_at)
        status_emoji = "✅" if order[3] == 'completed' else "⏳" if order[3] in ['pending', 'processing'] else "❌"
        builder.button(text=f"🔹 {order[5]} | {order[7]:.1f}₸ {status_emoji}", callback_data=f"order_view_{order[0]}")
    
    back_text = "‹ Профильге қайту" if lang == 'kz' else "‹ Назад к профилю"
    builder.button(text=back_text, callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()

def order_details_kb(order_id: int, lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    if lang == 'kz':
        builder.button(text="🔄 Fragment қайта қосу", callback_data=f"cn_{order_id}")
        builder.button(text="✍️ Пікір қалдыру", callback_data=f"review_{order_id}")
        builder.button(text="‹ Тарихқа қайту", callback_data="history")
    else:
        builder.button(text="🔄 Перевязать Fragment", callback_data=f"cn_{order_id}")
        builder.button(text="✍️ Оставить отзыв", callback_data=f"review_{order_id}")
        builder.button(text="‹ Назад к истории", callback_data="history")
    builder.adjust(1)
    return builder.as_markup()
