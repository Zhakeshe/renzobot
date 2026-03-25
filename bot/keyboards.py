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
    builder.button(text="👥 Пайдаланушылар", callback_data="admin_users")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.adjust(1)
    return builder.as_markup()

def stars_items_kb(items: list, lang: str = 'kz'):
    builder = InlineKeyboardBuilder()
    for item in items:
        # item: {id, name, price_rub_with_margin}
        builder.button(text=f"{item['name']}", callback_data=f"buy_stars_item_{item['id']}")
    
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
