from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def main_menu_kb(is_admin: bool = False, lang: str = 'kz'):
    builder = ReplyKeyboardBuilder()
    if lang == 'kz':
        builder.button(text="🌟 Stars сатып алу")
        builder.button(text="💎 Telegram Premium")
        builder.button(text="🏠 NFT жалдау")
        builder.button(text="👤 Профиль")
        builder.button(text="👥 Реферал")
        builder.button(text="🛠 Қолдау")
        builder.button(text="🎁 Промокод")
        builder.button(text="🌍 Тілді өзгерту")
    else:
        builder.button(text="🌟 Купить Stars")
        builder.button(text="💎 Telegram Premium")
        builder.button(text="🏠 Аренда NFT")
        builder.button(text="👤 Профиль")
        builder.button(text="👥 Реферал")
        builder.button(text="🛠 Поддержка")
        builder.button(text="🎁 Промокод")
        builder.button(text="🌍 Сменить язык")
        
    builder.button(text="🖥 Web App", web_app=types.WebAppInfo(url="https://your-app-url.run.app"))
    if is_admin:
        builder.button(text="📊 Админ панель")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

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

def profile_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Толтыру (₸)", callback_data="topup")
    builder.button(text="📜 Тапсырыстар тарихы", callback_data="history")
    builder.adjust(1)
    return builder.as_markup()
