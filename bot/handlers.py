from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from bot.database import Database
from bot.api_client import APIClient
from bot.keyboards import main_menu_kb, profile_kb
import os

router = Router()
db = Database()
# In a real app, these would come from env
KZT_RATE = 5.2 

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
KZT_RATE = float(os.getenv("RUB_KZT_RATE", 5.2))
REF_PERCENT = float(os.getenv("REFERRAL_PERCENT", 0.05))

TEXTS = {
    'kz': {
        'start': "Сәлем, {name}! 👋\nЦифрлық тауарлар дүкеніне қош келдіңіз.",
        'profile': "👤 **Профиль**\n\n🆔 ID: `{id}`\n💰 Теңгерім: `{balance:.2f} ₸`",
        'ref': "👥 **Реферал жүйесі**\n\nСілтемеңіз:\n`{link}`",
        'promo_prompt': "🎁 Промокодты енгізіңіз:",
        'lang_changed': "🌍 Тіл қазақшаға өзгертілді!",
        'broadcast_prompt': "📣 Барлық пайдаланушыларға жіберілетін хабарламаны жазыңыз:"
    },
    'ru': {
        'start': "Привет, {name}! 👋\nДобро пожаловать в магазин цифровых товаров.",
        'profile': "👤 **Профиль**\n\n🆔 ID: `{id}`\n💰 Баланс: `{balance:.2f} ₸`",
        'ref': "👥 **Реферальная система**\n\nВаша ссылка:\n`{link}`",
        'promo_prompt': "🎁 Введите промокод:",
        'lang_changed': "🌍 Язык изменен на русский!",
        'broadcast_prompt': "📣 Введите сообщение для рассылки всем пользователям:"
    }
}

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)
    
    lang = user[4] if user else 'kz'
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer(
        TEXTS[lang]['start'].format(name=message.from_user.full_name),
        reply_markup=main_menu_kb(is_admin, lang)
    )

@router.message(F.text.in_(["🌍 Тілді өзгерту", "🌍 Сменить язык"]))
async def change_lang(message: Message):
    await message.answer("Тілді таңдаңыз / Выберите язык:", reply_markup=language_kb())

@router.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[2]
    await db.set_language(callback.from_user.id, lang)
    await callback.message.edit_text(TEXTS[lang]['lang_changed'])
    await callback.message.answer(TEXTS[lang]['start'].format(name=callback.from_user.full_name), reply_markup=main_menu_kb(callback.from_user.id == ADMIN_ID, lang))

@router.message(F.text == "📊 Админ панель", F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message):
    users, sales = await db.get_stats()
    profit = await db.get_profit_stats()
    await message.answer(
        f"📊 **Админ панель**\n\n"
        f"👥 Пайдаланушылар: {users}\n"
        f"💰 Жалпы сауда: {sales:.2f} ₸\n"
        f"📈 Таза пайда: {profit:.2f} ₸",
        reply_markup=admin_kb()
    )

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def start_broadcast(callback: CallbackQuery):
    await callback.message.answer(TEXTS['kz']['broadcast_prompt'])
    # Мұнда күту режимін (FSM) қосу керек, бірақ мысал үшін жай ғана көрсетілді

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if user:
        balance = user[1]
        await message.answer(
            f"👤 **Профиль**\n\n"
            f"🆔 ID: `{message.from_user.id}`\n"
            f"💰 Теңгерім: `{balance:.2f} ₸`",
            reply_markup=profile_kb(),
            parse_mode="Markdown"
        )

@router.message(F.text == "🌟 Stars сатып алу")
async def buy_stars_info(message: Message, api: APIClient):
    rate_data = await api.get_stars_rate()
    if rate_data.get("success"):
        # api_client ішінде MARGIN автоматты түрде қосылған
        price_rub = rate_data["price_per_star_rub_with_margin"]
        price_kzt = price_rub * KZT_RATE
        
        await message.answer(
            f"🌟 **Telegram Stars сатып алу**\n\n"
            f"💵 Бағасы (1 дана): `{price_kzt:.2f} ₸` (~{price_rub} ₽)\n"
            f"📦 Ең аз мөлшер: {rate_data['min_quantity']}\n\n"
            "Сатып алғыңыз келетін Stars мөлшерін енгізіңіз:",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Курсты алу мүмкін болмады. Кейінірек қайталаңыз.")
