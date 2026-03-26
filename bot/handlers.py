from aiogram import Router, F
import random
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from api_client import APIClient
from keyboards import main_menu_kb, profile_kb, language_kb, admin_kb, stars_items_kb, main_reply_kb, calculator_kb
import os
from dotenv import load_dotenv

router = Router()
db = Database()

class PromoState(StatesGroup):
    waiting_for_promo = State()

class TopupState(StatesGroup):
    waiting_for_amount = State()

class StarsState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_id = State()

class PremiumState(StatesGroup):
    waiting_for_months = State()
    waiting_for_id = State()

class NFTState(StatesGroup):
    waiting_for_days = State()
    waiting_for_address = State()
    waiting_for_ton_connect = State()

class AdminState(StatesGroup):
    waiting_for_balance = State()
    waiting_for_rate = State()
    waiting_for_broadcast = State()

class SupportState(StatesGroup):
    waiting_for_subject = State()
    waiting_for_message = State()
    waiting_for_reply = State()

class TONState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_address = State()

class SellStarsState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_address = State()

class CalculatorState(StatesGroup):
    waiting_for_stars = State()
    waiting_for_ton = State()

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
KZT_RATE = float(os.getenv("RUB_KZT_RATE", 5.2))
REF_PERCENT = float(os.getenv("REFERRAL_PERCENT", 0.05))
STARS_RATE_KZT = float(os.getenv("STARS_RATE_KZT", 15.0))
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
MARGIN = 1.15

TEXTS = {
    'kz': {
        'start': "Қош келдіңіз! Біздің сервисте сіз Telegram Stars, Telegram Premium сатып ала аласыз және NFT жалдай аласыз. 🍪\n\n⭐ Ағымдағы теңгерім: `{balance:.2f} ₸` .\n\n🧸 Біздің сервис көмегімен:\n┌ Сатып алынған жұлдыздар: `{stars_count}` шт.;\n├ Жалға алынған NFT-сыйлықтар: `{gifts_count}` шт.;\n└ Жалға алынған NFT-username: `{usernames_count}` шт.",
        'profile': "👤 **Профиль**\n\n🆔 ID: `{id}`\n💰 Теңгерім: `{balance:.2f} ₸`",
        'ref': "👥 **Реферал жүйесі**\n\nСілтемеңіз:\n`{link}`\n\n🎁 Әрбір толтырудан сізге `{percent}%` бонус түседі!\n\n📊 Статистика:\n👥 Шақырылғандар: `{count}` адам\n💰 Табылған пайда: `{earned:.2f} ₸`",
        'promo_prompt': "🎁 Промокодты енгізіңіз:",
        'promo_success': "✅ Құттықтаймыз! `{amount} ₸` теңгеріміңізге қосылды.",
        'promo_invalid': "❌ Қате немесе белсенді емес промокод.",
        'promo_already': "❌ Сіз бұл промокодты қолданып қойғансыз.",
        'promo_expired': "❌ Промокодтың мерзімі біткен немесе шектеуі таусылған.",
        'lang_changed': "🌍 Тіл қазақшаға өзгертілді!",
        'broadcast_prompt': "📣 Барлық пайдаланушыларға жіберілетін хабарламаны жазыңыз:",
        'nft_rental_menu': "🖼 **NFT Жалдау**\n\n🎁 **NFT-подарки**\n└ Telegram-ның бірегей сыйлықтарын тәулігіне теңгемен жалға алыңыз.\n\n👤 **NFT-юзернеймдер**\n└ Ең қысқадан ең сирекке дейінгі әдемі және танымал есімдер.\n\n☎️ **NFT-номерлер**\n└ Жалға алуға арналған бірегей Telegram +888 цифрлық нөмірлері — сирек, қымбат.\n\nЖалға алғыңыз келетін нәрсені таңдаңыз 👇",
        'nft_list': "📦 **Қолжетімді тауарлар ({type}):**\n\n{items}\n\nСатып алу үшін таңдаңыз 👇",
        'nft_rent_days': "💎 **{name}**\n\n💰 Жалдау бағасы: `{price:.2f} ₸/күн`\n📦 Ең аз мерзім: `{min_days}` күн\n\nНеше күнге жалдағыңыз келеді? (санын жазыңыз):",
        'nft_rent_success': "✅ **Жалдау сәтті орындалды!**\n\n📦 Тауар: `{name}`\n📅 Мерзімі: `{days} күн`\n💰 Барлығы: `{total:.2f} ₸`\n\nЕнді Fragment-те қолдану үшін TON Connect арқылы қосылуыңыз керек.",
        'nft_connect_prompt': "🔗 Fragment-тен TON Connect сілтемесін (URL) жіберіңіз:",
        'nft_connect_success': "✅ TON Connect сәтті қосылды! Енді Fragment-те қолдана аласыз.",
        'history_title': "📜 **Тапсырыстар тарихы:**",
        'history_menu': "📜 **Тарих мәзірі:**\n\nТөмендегі бөлімдердің бірін таңдаңыз:",
        'payments_history_title': "💳 **Толтырулар тарихы:**",
        'payment_details': "💰 **Толтыру мәліметтері:**\n\n🆔 ID: `{id}`\n💵 Сома: `{amount} ₸`\n🔌 Әдіс: `{method}`\n📝 Код: `{code}`\n📊 Күйі: {status}\n📅 Күні: `{date}`",
        'order_details': "📦 **Тапсырыс мәліметтері #{id}.**\n\n📝 Өнім: `{name}`;\n💰 Бағасы: `{price:.2f} ₸`;\n📊 Статус: {status};\n📅 Күні: `{date}`;\n\n📄 Сипаттама: `{description}`.\n🔗 Fragment: {fragment_status}"
    },
    'ru': {
        'start': "Добро пожаловать! У нас Вы можете приобрести Telegram Stars, Telegram Premium и арендовать NFT. 🍪\n\n⭐ Текущий баланс: `{balance:.2f} ₸` .\n\n🧸 С помощью нашего сервиса:\n┌ Приобретено звёзд: `{stars_count}` шт.;\n├ Арендовано NFT-подарков: `{gifts_count}` шт.;\n└ Арендовано NFT-username: `{usernames_count}` шт.",
        'profile': "👤 **Профиль**\n\n🆔 ID: `{id}`\n💰 Баланс: `{balance:.2f} ₸`",
        'ref': "👥 **Реферальная система**\n\nВаша ссылка:\n`{link}`\n\n🎁 Вы получаете `{percent}%` от каждого пополнения реферала!\n\n📊 Статистика:\n👥 Приглашено: `{count}` человек\n💰 Заработано: `{earned:.2f} ₸`",
        'promo_prompt': "🎁 Введите промокод:",
        'promo_success': "✅ Поздравляем! `{amount} ₸` зачислено на ваш баланс.",
        'promo_invalid': "❌ Неверный или неактивный промокод.",
        'promo_already': "❌ Вы уже использовали этот промокод.",
        'promo_expired': "❌ Срок действия промокода истек или лимит исчерпан.",
        'lang_changed': "🌍 Язык изменен на русский!",
        'broadcast_prompt': "📣 Введите сообщение для рассылки всем пользователям:",
        'nft_rental_menu': "🖼 **Аренда NFT**\n\n🎁 **NFT-подарки**\n└ Уникальные подарки Telegram в аренду за рубли, посуточно.\n\n👤 **NFT-юзернеймы**\n└ Красивые и узнаваемые имена от самых коротких до самых редких.\n\n☎️ **NFT-номера**\n└ Уникальные цифровые номера Telegram +888 для аренды — редкие, дорогие.\n\nВыберите, что хотите арендовать 👇",
        'nft_list': "📦 **Доступные товары ({type}):**\n\n{items}\n\nВыберите для покупки 👇",
        'nft_rent_days': "💎 **{name}**\n\n💰 Цена аренды: `{price:.2f} ₸/день`\n📦 Мин. срок: `{min_days}` дн.\n\nНа сколько дней хотите арендовать? (введите число):",
        'nft_rent_success': "✅ **Аренда успешно оформлена!**\n\n📦 Товар: `{name}`\n📅 Срок: `{days} дн.`\n💰 Итого: `{total:.2f} ₸`\n\nТеперь вам нужно подключиться через TON Connect для использования на Fragment.",
        'nft_connect_prompt': "🔗 Пришлите TON Connect ссылку (URL) из Fragment:",
        'nft_connect_success': "✅ TON Connect успешно подключен! Теперь вы можете использовать его на Fragment.",
        'history_title': "📜 **История покупок:**",
        'history_menu': "📜 **Меню истории:**\n\nВыберите один из разделов ниже:",
        'payments_history_title': "💳 **История пополнений:**",
        'payment_details': "💰 **Детали пополнения:**\n\n🆔 ID: `{id}`\n💵 Сумма: `{amount} ₸`\n🔌 Метод: `{method}`\n📝 Код: `{code}`\n📊 Статус: {status}\n📅 Дата: `{date}`",
        'order_details': "📦 **Детали заказа #{id}.**\n\n📝 Продукт: `{name}`;\n💰 Цена: `{price:.2f} ₸`;\n📊 Статус: {status};\n📅 Дата: `{date}`;\n\n📄 Описание: Аренда `{name}` на `{days}` дней.\n🔗 Fragment: {fragment_status}"
    }
}

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user = await db.get_user(message.from_user.id)
    # Anti-fraud check
    ip = message.from_user.id # Placeholder for real IP if available via proxy
    device = message.from_user.id # Placeholder for device ID
    
    is_fraud = await db.check_fraud(message.from_user.id, str(ip))
    if is_fraud:
        await message.answer("⚠️ Күдікті белсенділік анықталды. / Обнаружена подозрительная активность.")
        # Optional: auto-ban or notify admin
        # await db.ban_user(message.from_user.id)
        # return

    if not user:
        args = command.args
        referred_by = None
        if args and args.isdigit():
            referred_by = int(args)
            if referred_by == message.from_user.id:
                referred_by = None
        
        await db.create_user(message.from_user.id, message.from_user.username, referred_by)
        await db.update_anti_fraud(message.from_user.id, str(ip), str(device))
        user = await db.get_user(message.from_user.id)
        
        if referred_by:
            try:
                await message.bot.send_message(
                    referred_by,
                    f"👤 Сіздің сілтемеңіз арқылы жаңа пайдаланушы тіркелді: `@{message.from_user.username or message.from_user.id}`\n\n"
                    f"🎁 Енді оның әрбір толтыруынан сізге бонус түседі!",
                    parse_mode="Markdown"
                )
            except:
                pass
    
    lang = user[4] if user else 'kz'
    is_admin = message.from_user.id == ADMIN_ID
    
    stars_count, gifts_count, usernames_count = await db.get_global_stats()
    
    await message.answer(
        TEXTS[lang]['start'].format(
            balance=user[1],
            stars_count=stars_count,
            gifts_count=gifts_count,
            usernames_count=usernames_count
        ),
        reply_markup=main_reply_kb(lang),
        parse_mode="Markdown"
    )
    await message.answer(
        "Төмендегі мәзірді қолданыңыз 👇" if lang == 'kz' else "Используйте меню ниже 👇",
        reply_markup=main_menu_kb(is_admin, lang)
    )

@router.message(F.text == "🏠 Мәзір / Меню")
async def manual_menu(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    is_admin = message.from_user.id == ADMIN_ID
    stars_count, gifts_count, usernames_count = await db.get_global_stats()
    
    await message.answer(
        TEXTS[lang]['start'].format(
            balance=user[1],
            stars_count=stars_count,
            gifts_count=gifts_count,
            usernames_count=usernames_count
        ),
        reply_markup=main_menu_kb(is_admin, lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "change_lang")
async def change_lang(callback: CallbackQuery):
    await callback.message.answer("Тілді таңдаңыз / Выберите язык:", reply_markup=language_kb())
    await callback.answer()

@router.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = "🛠 **Қолдау орталығы**\n\nСұрақтарыңыз болса тикет ашыңыз немесе бұрынғы тикеттерді көріңіз." if lang == 'kz' else "🛠 **Центр поддержки**\n\nЕсли у вас есть вопросы, откройте тикет или просмотрите предыдущие."
    from keyboards import support_kb
    await callback.message.edit_text(text, reply_markup=support_kb(lang), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "support_new")
async def support_new(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = "📝 Сұрағыңыздың тақырыбын жазыңыз:" if lang == 'kz' else "📝 Введите тему вашего вопроса:"
    await callback.message.answer(text)
    await state.set_state(SupportState.waiting_for_subject)
    await callback.answer()

@router.message(SupportState.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    text = "💬 Енді сұрағыңызды толық жазыңыз:" if lang == 'kz' else "💬 Теперь опишите ваш вопрос подробно:"
    await message.answer(text)
    await state.set_state(SupportState.waiting_for_message)

@router.message(SupportState.waiting_for_message)
async def process_message(message: Message, state: FSMContext):
    data = await state.get_data()
    subject = data['subject']
    text = message.text
    
    ticket_id = await db.create_ticket(message.from_user.id, subject)
    await db.add_ticket_message(ticket_id, message.from_user.id, text)
    
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    success_text = f"✅ Тикет #{ticket_id} сәтті ашылды! Админ жауабын күтіңіз." if lang == 'kz' else f"✅ Тикет #{ticket_id} успешно открыт! Ожидайте ответа админа."
    await message.answer(success_text)
    
    # Notify admin
    try:
        await message.bot.send_message(ADMIN_ID, f"🆕 **Жаңа тикет!**\n\n🆔 #{ticket_id}\n👤 Пайдаланушы: @{message.from_user.username or message.from_user.id}\n📝 Тақырыбы: {subject}\n\nКөру үшін: /ticket_{ticket_id}")
    except: pass
    
    await state.clear()

@router.callback_query(F.data == "support_list")
async def support_list(callback: CallbackQuery):
    tickets = await db.get_user_tickets(callback.from_user.id)
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    if not tickets:
        await callback.message.answer("📭 Сізде әлі тикеттер жоқ." if lang == 'kz' else "📭 У вас еще нет тикетов.")
        return
        
    text = "📂 **Сіздің тикеттеріңіз:**" if lang == 'kz' else "📂 **Ваши тикеты:**"
    from keyboards import tickets_list_kb
    await callback.message.edit_text(text, reply_markup=tickets_list_kb(tickets), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("ticket_view_"))
async def ticket_view(callback: CallbackQuery):
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket(ticket_id)
    messages = await db.get_ticket_messages(ticket_id)
    
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    is_admin = callback.from_user.id == ADMIN_ID
    
    status_text = "Ашық" if ticket[3] == 'open' else "Жауап берілді" if ticket[3] == 'answered' else "Жабық"
    text = f"🎫 **Тикет #{ticket_id}**\n📝 Тақырыбы: {ticket[2]}\n📊 Статусы: {status_text}\n\n💬 **Сөйлесу тарихы:**\n"
    
    for msg in messages:
        sender = "👤 Сіз" if msg[2] == callback.from_user.id else "👨‍💻 Админ"
        if is_admin:
            sender = "👤 Пайдаланушы" if msg[2] != ADMIN_ID else "👨‍💻 Сіз"
        text += f"\n**{sender}:**\n{msg[3]}\n"
    
    from keyboards import ticket_actions_kb
    await callback.message.edit_text(text, reply_markup=ticket_actions_kb(ticket_id, is_admin, ticket[3]), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("ticket_reply_"))
async def ticket_reply(callback: CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split("_")[2])
    await state.update_data(reply_ticket_id=ticket_id)
    
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    await callback.message.answer("💬 Жауабыңызды жазыңыз:" if lang == 'kz' else "💬 Введите ваш ответ:")
    await state.set_state(SupportState.waiting_for_reply)
    await callback.answer()

@router.message(SupportState.waiting_for_reply)
async def process_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_id = data['reply_ticket_id']
    text = message.text
    
    await db.add_ticket_message(ticket_id, message.from_user.id, text)
    
    ticket = await db.get_ticket(ticket_id)
    is_admin = message.from_user.id == ADMIN_ID
    
    if is_admin:
        await db.update_ticket_status(ticket_id, 'answered')
        # Notify user
        try:
            await message.bot.send_message(ticket[1], f"👨‍💻 **Админ тикетке жауап берді!**\n\n🆔 #{ticket_id}\n📝 Тақырыбы: {ticket[2]}\n\nКөру үшін профильге өтіңіз.")
        except: pass
    else:
        await db.update_ticket_status(ticket_id, 'open')
        # Notify admin
        try:
            await message.bot.send_message(ADMIN_ID, f"💬 **Тикетке жаңа жауап!**\n\n🆔 #{ticket_id}\n👤 Пайдаланушы: @{message.from_user.username or message.from_user.id}\n\nКөру үшін: /ticket_{ticket_id}")
        except: pass
        
    await message.answer("✅ Жауап жіберілді!")
    await state.clear()

@router.callback_query(F.data.startswith("ticket_close_"))
async def ticket_close(callback: CallbackQuery):
    ticket_id = int(callback.data.split("_")[2])
    await db.update_ticket_status(ticket_id, 'closed')
    await callback.message.answer(f"✅ Тикет #{ticket_id} жабылды.")
    await callback.answer()

@router.message(F.text.startswith("/ticket_"))
async def admin_ticket_view(message: Message):
    if message.from_user.id != ADMIN_ID: return
    ticket_id = int(message.text.split("_")[1])
    
    ticket = await db.get_ticket(ticket_id)
    if not ticket: return
    
    messages = await db.get_ticket_messages(ticket_id)
    
    status_text = "Ашық" if ticket[3] == 'open' else "Жауап берілді" if ticket[3] == 'answered' else "Жабық"
    text = f"🎫 **Тикет #{ticket_id}**\n👤 Пайдаланушы ID: `{ticket[1]}`\n📝 Тақырыбы: {ticket[2]}\n📊 Статусы: {status_text}\n\n💬 **Сөйлесу тарихы:**\n"
    
    for msg in messages:
        sender = "👤 Пайдаланушы" if msg[2] != ADMIN_ID else "👨‍💻 Сіз"
        text += f"\n**{sender}:**\n{msg[3]}\n"
        
    from keyboards import ticket_actions_kb
    await message.answer(text, reply_markup=ticket_actions_kb(ticket_id, True, ticket[3]), parse_mode="Markdown")

@router.callback_query(F.data == "admin_panel", F.from_user.id == ADMIN_ID)
async def admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📊 **Админ панель**\n\n"
        f"Төмендегі батырмалар арқылы ботты басқара аласыз:",
        reply_markup=admin_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats", F.from_user.id == ADMIN_ID)
async def admin_stats_view(callback: CallbackQuery):
    users, sales = await db.get_stats()
    profit = await db.get_profit_stats()
    new_users, today_sales, today_profit = await db.get_today_stats()
    
    text = (
        f"📊 **Жалпы статистика:**\n\n"
        f"👥 Пайдаланушылар: `{users}`\n"
        f"💰 Жалпы сауда: `{sales:.2f} ₸`\n"
        f"📈 Таза пайда: `{profit:.2f} ₸`\n\n"
        f"📅 **Бүгінгі статистика:**\n\n"
        f"🆕 Жаңа пайдаланушылар: `{new_users}`\n"
        f"💰 Бүгінгі сауда: `{today_sales:.2f} ₸`\n"
        f"📈 Бүгінгі пайда: `{today_profit:.2f} ₸`"
    )
    
    from keyboards import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="‹ Артқа", callback_data="admin_panel")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📢 Барлық пайдаланушыларға жіберілетін хабарламаны жазыңыз:")
    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.answer()

@router.message(AdminState.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def admin_broadcast_process(message: Message, state: FSMContext):
    text = message.text
    users = await db.get_all_users_ids()
    
    await message.answer(f"⏳ Хабарлама `{len(users)}` пайдаланушыға жіберілуде...", parse_mode="Markdown")
    
    count = 0
    for user_id in users:
        try:
            await message.bot.send_message(user_id, text)
            count += 1
            await asyncio.sleep(0.05) # Rate limit-тен сақтану
        except:
            pass
            
    await message.answer(f"✅ Хабарлама `{count}` пайдаланушыға сәтті жіберілді!", reply_markup=admin_kb())
    await state.clear()

@router.callback_query(F.data == "admin_reward_referrals", F.from_user.id == ADMIN_ID)
async def admin_reward_referrals(callback: CallbackQuery):
    top = await db.get_top_referrers(3) # Reward top 3
    rewards = [5000, 3000, 1000] # 1st: 5000, 2nd: 3000, 3rd: 1000
    
    for i, (ref_id, count) in enumerate(top):
        if i < len(rewards):
            reward = rewards[i]
            await db.update_balance(ref_id, reward)
            try:
                await callback.message.bot.send_message(
                    ref_id,
                    f"🏆 **Құттықтаймыз!**\n\nСіз рефералдар саны бойынша `{i+1}`-орын алдыңыз және `{reward} ₸` бонус алдыңыз!",
                    parse_mode="Markdown"
                )
            except:
                pass
                
    await callback.message.answer("✅ Топ рефералдар марапатталды!")
    await callback.answer()

@router.callback_query(F.data == "admin_api_balance", F.from_user.id == ADMIN_ID)
async def admin_api_balance(callback: CallbackQuery, api: APIClient):
    try:
        balance_data = await api.get_balance()
        if balance_data.get("success"):
            nano = balance_data.get("balance_nano", 0)
            rub = api.nano_to_rub(nano)
            await callback.message.answer(f"💳 **API Теңгерім:**\n\n`{rub:.2f} ₽` (`{nano} nano`)")
        else:
            await callback.message.answer(f"❌ Қате: {balance_data.get('error')}")
    except Exception as e:
        await callback.message.answer(f"❌ Қате: {str(e)}")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_users_"), F.from_user.id == ADMIN_ID)
async def admin_users_list(callback: CallbackQuery):
    offset = int(callback.data.split("_")[2])
    users = await db.get_users_paged(10, offset)
    from keyboards import admin_users_kb
    await callback.message.edit_text("👥 **Пайдаланушылар тізімі:**", reply_markup=admin_users_kb(users, offset))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_"), F.from_user.id == ADMIN_ID)
async def admin_user_detail(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Пайдаланушы табылмады.")
        return
    
    # user: (user_id, balance, username, referred_by, lang, ip, device, is_blocked, ref_bal, created_at)
    status = "🚫 Блокталған" if user[7] else "✅ Белсенді"
    text = (
        f"👤 **Пайдаланушы ақпараты**\n\n"
        f"🆔 ID: `{user[0]}`\n"
        f"👤 Username: @{user[2] or 'жоқ'}\n"
        f"💰 Баланс: `{user[1]:.2f} ₸`\n"
        f"👥 Реферал баланс: `{user[8]:.2f} ₸`\n"
        f"🌍 Тіл: {user[4]}\n"
        f"📊 Статус: {status}\n"
        f"📅 Тіркелді: {user[9]}\n"
        f"🌐 IP: `{user[5] or 'белгісіз'}`\n"
        f"📱 Device: `{user[6] or 'белгісіз'}`"
    )
    from keyboards import user_actions_kb
    await callback.message.edit_text(text, reply_markup=user_actions_kb(user_id, user[7]), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_bal_"), F.from_user.id == ADMIN_ID)
async def admin_edit_bal_start(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[3])
    await state.update_data(edit_user_id=user_id)
    await callback.message.answer("💰 Жаңа балансты енгізіңіз (₸):")
    await state.set_state(AdminState.waiting_for_balance)
    await callback.answer()

@router.message(AdminState.waiting_for_balance, F.from_user.id == ADMIN_ID)
async def admin_edit_bal_process(message: Message, state: FSMContext):
    try:
        new_balance = float(message.text)
        data = await state.get_data()
        user_id = data['edit_user_id']
        await db.set_user_balance(user_id, new_balance)
        await message.answer(f"✅ Пайдаланушы `{user_id}` балансы `{new_balance} ₸` болып өзгертілді.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Тек санды енгізіңіз.")

@router.callback_query(F.data.startswith("admin_ban_"), F.from_user.id == ADMIN_ID)
async def admin_ban(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    await db.ban_user(user_id)
    await callback.message.answer(f"🚫 Пайдаланушы `{user_id}` блоктауға жіберілді.")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_unban_"), F.from_user.id == ADMIN_ID)
async def admin_unban(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    await db.unban_user(user_id)
    await callback.message.answer(f"✅ Пайдаланушы `{user_id}` блоктан шығарылды.")
    await callback.answer()

@router.callback_query(F.data == "admin_tickets", F.from_user.id == ADMIN_ID)
async def admin_tickets_list(callback: CallbackQuery):
    tickets = await db.get_all_tickets()
    if not tickets:
        await callback.message.answer("📭 Тикеттер жоқ.")
        return
    from keyboards import tickets_list_kb
    await callback.message.edit_text("🎫 **Барлық тикеттер:**", reply_markup=tickets_list_kb(tickets, True))
    await callback.answer()

@router.callback_query(F.data == "admin_settings", F.from_user.id == ADMIN_ID)
async def admin_settings(callback: CallbackQuery, state: FSMContext):
    global KZT_RATE
    await callback.message.answer(
        f"⚙️ **Баптаулар**\n\n"
        f"📈 Ағымдағы курс (RUB -> KZT): `{KZT_RATE}`\n\n"
        f"Курсты өзгерту үшін жаңа мәнді жіберіңіз (мысалы: 5.5):",
        parse_mode="Markdown"
    )
    await state.set_state(AdminState.waiting_for_rate)
    await callback.answer()

@router.message(AdminState.waiting_for_rate, F.from_user.id == ADMIN_ID)
async def admin_edit_rate_process(message: Message, state: FSMContext):
    global KZT_RATE
    try:
        new_rate = float(message.text)
        KZT_RATE = new_rate
        await message.answer(f"✅ Курс `{new_rate}` болып өзгертілді.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Тек санды енгізіңіз.")

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if user:
        balance = user[1]
        await callback.message.answer(
            f"👤 **Профиль**\n\n"
            f"🆔 ID: `{callback.from_user.id}`\n"
            f"💰 Теңгерім: `{balance:.2f} ₸`",
            reply_markup=profile_kb(),
            parse_mode="Markdown"
        )
    await callback.answer()

@router.callback_query(F.data == "buy_stars")
async def buy_stars_info(callback: CallbackQuery, state: FSMContext, api: APIClient):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    try:
        # Егер тауарлар жоқ болса, мөлшерді қолмен енгізу (rate)
        rate_data = await api.get_stars_rate()
        if rate_data.get("success"):
            price_rub = rate_data["price_per_star_rub_with_margin"]
            price_kzt = price_rub * KZT_RATE
            
            text = {
                'kz': f"🌟 **Telegram Stars сатып алу**\n\n💵 Бағасы (1 дана): `{price_kzt:.2f} ₸` (~{price_rub} ₽)\n📦 Ең аз мөлшер: {rate_data['min_quantity']}\n\nСатып алғыңыз келетін Stars мөлшерін енгізіңіз:",
                'ru': f"🌟 **Покупка Telegram Stars**\n\n💵 Цена (1 шт): `{price_kzt:.2f} ₸` (~{price_rub} ₽)\n📦 Мин. количество: {rate_data['min_quantity']}\n\nВведите количество Stars, которое хотите купить:"
            }[lang]
            
            await callback.message.answer(text, parse_mode="Markdown")
            await state.set_state(StarsState.waiting_for_amount)
        else:
            await callback.message.answer("❌ Қызмет уақытша қолжетімсіз." if lang == 'kz' else "❌ Сервис временно недоступен.")
    except Exception as e:
        await callback.message.answer("❌ Қате орын алды." if lang == 'kz' else "❌ Произошла ошибка.")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_stars_item_"))
async def buy_stars_item(callback: CallbackQuery, state: FSMContext, api: APIClient):
    item_id = int(callback.data.split("_")[3])
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    items_data = await api.get_stars_items()
    item = next((i for i in items_data.get("items", []) if i['id'] == item_id), None)
    
    if not item:
        await callback.message.answer("❌ Тауар табылмады." if lang == 'kz' else "❌ Товар не найден.")
        return
    
    price_kzt = item["price_rub_with_margin"] * KZT_RATE
    if user[1] < price_kzt:
        await callback.message.answer(
            f"❌ Қаражат жеткіліксіз!\n💰 Қажет: `{price_kzt:.2f} ₸`\n💳 Сізде: `{user[1]:.2f} ₸`" if lang == 'kz' else 
            f"❌ Недостаточно средств!\n💰 Нужно: `{price_kzt:.2f} ₸`\n💳 У вас: `{user[1]:.2f} ₸`",
            parse_mode="Markdown"
        )
        return

    await state.update_data(item_id=item_id, amount=item['name'], total_kzt=price_kzt)
    await callback.message.answer(
        "👤 Stars жіберілетін пайдаланушының ID-ін немесе Юзернеймін жазыңыз:" if lang == 'kz' else
        "👤 Введите ID или Юзернейм пользователя, которому нужно отправить Stars:"
    )
    await state.set_state(StarsState.waiting_for_id)
    await callback.answer()

@router.message(StarsState.waiting_for_amount)
async def process_stars_amount(message: Message, state: FSMContext, api: APIClient):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз." if lang == 'kz' else "❌ Введите только цифры.")
        return
    
    amount = int(message.text)
    rate_data = await api.get_stars_rate()
    
    if amount < rate_data.get('min_quantity', 50):
        await message.answer(f"❌ Ең аз мөлшер: {rate_data.get('min_quantity', 50)}" if lang == 'kz' else f"❌ Мин. количество: {rate_data.get('min_quantity', 50)}")
        return
    
    price_rub = rate_data["price_per_star_rub_with_margin"]
    total_kzt = amount * price_rub * KZT_RATE
    
    if user[1] < total_kzt:
        await message.answer(
            f"❌ Қаражат жеткіліксіз!\n💰 Қажет: `{total_kzt:.2f} ₸`\n💳 Сізде: `{user[1]:.2f} ₸`" if lang == 'kz' else 
            f"❌ Недостаточно средств!\n💰 Нужно: `{total_kzt:.2f} ₸`\n💳 У вас: `{user[1]:.2f} ₸`",
            parse_mode="Markdown"
        )
        await state.clear()
        return

    await state.update_data(amount=amount, total_kzt=total_kzt)
    await message.answer(
        "👤 Stars жіберілетін пайдаланушының ID-ін немесе Юзернеймін жазыңыз:" if lang == 'kz' else
        "👤 Введите ID или Юзернейм пользователя, которому нужно отправить Stars:"
    )
    await state.set_state(StarsState.waiting_for_id)

@router.message(StarsState.waiting_for_id)
async def process_stars_id(message: Message, state: FSMContext, api: APIClient):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    target = message.text.strip().replace("@", "")
    data = await state.get_data()
    
    # API-ге тапсырыс жіберу
    order_res = await api.place_stars_order(target, data['amount'])
    
    if order_res.get("success"):
        await db.update_balance(message.from_user.id, -data['total_kzt'])
        
        # Сауданы базаға жазу
        await db.create_order(
            user_id=message.from_user.id,
            order_id_api=order_res.get("order_id", 0),
            product_type="stars",
            product_name=f"{data['amount']} Stars",
            description=f"Telegram Stars @{target}",
            amount_kzt=data['total_kzt'],
            profit_kzt=data['total_kzt'] * 0.1, # 10% пайда
            status='completed'
        )
        
        await message.answer(
            f"✅ Тапсырыс қабылданды!\n📦 Мөлшер: `{data['amount']} Stars`\n👤 Алушы: `@{target}`\n💰 Бағасы: `{data['total_kzt']:.2f} ₸`" if lang == 'kz' else
            f"✅ Заказ принят!\n📦 Количество: `{data['amount']} Stars`\n👤 Получатель: `@{target}`\n💰 Цена: `{data['total_kzt']:.2f} ₸`",
            parse_mode="Markdown"
        )
    else:
        error = order_res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}" if lang == 'kz' else f"❌ Ошибка: {error}")
        
    await state.clear()

@router.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[2]
    await db.set_language(callback.from_user.id, lang)
    await callback.message.edit_text(TEXTS[lang]['lang_changed'])
    await callback.message.answer(TEXTS[lang]['start'].format(name=callback.from_user.full_name), reply_markup=main_menu_kb(callback.from_user.id == ADMIN_ID, lang))
    await callback.answer()

@router.callback_query(F.data == "topup")
async def start_topup(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    from keyboards import payment_methods_kb
    await callback.message.edit_text(
        "💳 Төлем әдісін таңдаңыз / Выберите способ оплаты:" if lang == 'kz' else "💳 Выберите способ оплаты:",
        reply_markup=payment_methods_kb(lang)
    )
    await callback.answer()

@router.callback_query(F.data == "topup_kaspi")
async def topup_kaspi(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = "💳 **Kaspi арқылы толтыру**\n\nТолтыру сомасын енгізіңіз (₸):" if lang == 'kz' else "💳 **Пополнение через Kaspi**\n\nВведите сумму пополнения (₸):"
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(TopupState.waiting_for_amount)
    await state.update_data(method="kaspi")
    await callback.answer()

@router.callback_query(F.data == "topup_cryptobot")
async def topup_cryptobot(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = (
        "🎩 **CryptoBot арқылы толтыру**\n\n"
        "Алу сомасы төлем жүйелерінің комиссиясына байланысты төлем сомасынан өзгеше болуы мүмкін.\n\n"
        "Барлық толтырулар автоматты түрде рубльге айырбасталады.\n\n"
        "✏️ Толтыру сомасын рубльмен енгізіңіз:"
        if lang == 'kz' else
        "🎩 **Пополнение через CryptoBot**\n\n"
        "Сумма к получению может отличаться от суммы к оплате из-за комиссии платёжных систем.\n\n"
        "Все пополнения автоматически конвертируются в рубли.\n\n"
        "✏️ Введите сумму пополнения в рублях:"
    )
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(TopupState.waiting_for_amount)
    await state.update_data(method="cryptobot")
    await callback.answer()

@router.message(TopupState.waiting_for_amount, F.text)
async def process_amount_for_payment(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    
    amount = float(message.text)
    data = await state.get_data()
    method = data.get("method")
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    if method == "kaspi":
        # Generate random code
        random_code = random.randint(1000000000, 9999999999)
        comment_code = f"{random_code}_{message.from_user.id}"
        
        req_id = await db.create_payment_request(message.from_user.id, amount, "kaspi", comment_code=comment_code)
        
        from keyboards import payment_paid_kb
        text = (
            f"💳 **Kaspi арқылы аударым**\n\n"
            f"1. `+7 700 123 45 67` нөміріне (Аты-жөні: РЕНЗО) аударыңыз.\n"
            f"2. Сома: `{amount} ₸`\n"
            f"3. **МАҢЫЗДЫ:** Түсініктемеге (комментарий) мына кодты жазыңыз: `{comment_code}`\n\n"
            f"⚠️ Кодсыз төлем қабылданбайды! Төлеген соң төмендегі батырманы басыңыз."
            if lang == 'kz' else
            f"💳 **Перевод через Kaspi**\n\n"
            f"1. Переведите на номер `+7 700 123 45 67` (Имя: РЕНЗО).\n"
            f"2. Сумма: `{amount} ₸`\n"
            f"3. **ВАЖНО:** В комментарии обязательно укажите код: `{comment_code}`\n\n"
            f"⚠️ Без кода оплата не принимается! После оплаты нажмите кнопку ниже."
        )
        await message.answer(text, reply_markup=payment_paid_kb(req_id, lang), parse_mode="Markdown")
        await state.clear()

    elif method == "cryptobot":
        # Generate random code for CryptoBot too
        random_code = random.randint(1000000000, 9999999999)
        comment_code = f"{random_code}_{message.from_user.id}"
        
        # amount here is in RUB as per user request
        req_id = await db.create_payment_request(message.from_user.id, amount, "cryptobot", comment_code=comment_code)
        
        from keyboards import payment_paid_kb
        text = (
            f"🎩 **CryptoBot арқылы аударым**\n\n"
            f"1. CryptoBot-тағы әмияныңызға өтіңіз.\n"
            f"2. Сома: `{amount} RUB`\n"
            f"3. **МАҢЫЗДЫ:** Түсініктемеге (комментарий) мына кодты жазыңыз: `{comment_code}`\n\n"
            f"⚠️ Важно: Обязательно укажите комментарий `{comment_code}` при переводе!\n\n"
            f"Төлеген соң төмендегі батырманы басыңыз."
            if lang == 'kz' else
            f"🎩 **Перевод через CryptoBot**\n\n"
            f"1. Перейдите в свой кошелек в CryptoBot.\n"
            f"2. Сумма: `{amount} RUB`\n"
            f"3. **ВАЖНО:** В комментарии обязательно укажите код: `{comment_code}`\n\n"
            f"⚠️ Важно: Обязательно укажите комментарий `{comment_code}` при переводе!\n\n"
            f"После оплаты нажмите кнопку ниже."
        )
        await message.answer(text, reply_markup=payment_paid_kb(req_id, lang), parse_mode="Markdown")
        await state.clear()

    elif method == "stars":
        prices = [LabeledPrice(label="Telegram Stars", amount=int(amount))]
        await message.bot.send_invoice(
            message.chat.id,
            title="Теңгерімді толтыру (Stars)" if lang == 'kz' else "Пополнение баланса (Stars)",
            description=f"Бот теңгерімін {amount} Stars арқылы толтыру" if lang == 'kz' else f"Пополнение баланса бота через {amount} Stars",
            provider_token="", # Empty for Stars
            currency="XTR",
            prices=prices,
            payload=f"topup_stars_{message.from_user.id}_{amount}"
        )
        await state.clear()

@router.callback_query(F.data.startswith("pay_confirm_"))
async def user_confirm_payment(callback: CallbackQuery):
    req_id = int(callback.data.split("_")[2])
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    req = await db.get_payment_request(req_id)
    if not req:
        await callback.answer("❌ Сұраныс табылмады.")
        return

    await callback.message.edit_text(
        "⏳ **Тексерілуде...**\n\nАдмин төлемді тексеріп жатыр. Расталған соң сізге хабарлама келеді." if lang == 'kz' else
        "⏳ **Проверяется...**\n\nАдмин проверяет ваш платеж. После подтверждения вам придет уведомление.",
        parse_mode="Markdown"
    )
    
    # Notify admin
    try:
        from keyboards import admin_payment_request_kb
        await callback.bot.send_message(
            ADMIN_ID,
            f"💳 **Жаңа төлем сұранысы (Кодпен)!**\n\n"
            f"👤 Пайдаланушы: @{callback.from_user.username or callback.from_user.id}\n"
            f"💰 Сома: `{req[2]} ₸`\n"
            f"🔑 Код: `{req[5]}`\n"
            f"Сұраныс ID: `#{req_id}`\n\n"
            f"Төлемді тексеріп, растаңыз.",
            reply_markup=admin_payment_request_kb(req_id),
            parse_mode="Markdown"
        )
    except: pass
    await callback.answer()

@router.callback_query(F.data.startswith("adm_pay_approve_"), F.from_user.id == ADMIN_ID)
async def admin_approve_payment(callback: CallbackQuery, state: FSMContext):
    req_id = int(callback.data.split("_")[3])
    req = await db.get_payment_request(req_id)
    
    if req and req[6] == 'pending':
        await db.update_payment_request_status(req_id, 'approved')
        user_id = req[1]
        amount = req[2]
        
        if amount > 0:
            # If amount was already specified in request
            await db.update_balance(user_id, amount)
            await db.update_payment_request_status(req_id, 'completed')
            await callback.message.answer(f"✅ Пайдаланушыға {amount} ₸ қосылды!")
            try:
                await callback.bot.send_message(user_id, f"✅ Сіздің төлеміңіз расталды! Теңгеріміңізге `{amount} ₸` қосылды.", parse_mode="Markdown")
            except: pass
        else:
            # Ask for amount if it was 0 (old flow)
            await callback.message.answer(f"💰 Сұраныс #{req_id} үшін соманы енгізіңіз (₸):")
            await state.update_data(approve_req_id=req_id, approve_user_id=req[1])
            await state.set_state(AdminState.waiting_for_balance)
    
    await callback.answer()

@router.callback_query(F.data.startswith("adm_pay_reject_"), F.from_user.id == ADMIN_ID)
async def admin_reject_payment(callback: CallbackQuery):
    req_id = int(callback.data.split("_")[3])
    req = await db.get_payment_request(req_id)
    if req:
        await db.update_payment_request_status(req_id, 'rejected')
        await callback.message.edit_text(f"❌ Сұраныс #{req_id} қабылданбады.")
        try:
            await callback.bot.send_message(req[1], "❌ Сіздің төлеміңіз қабылданбады. Қолдау қызметіне хабарласыңыз.")
        except: pass
    await callback.answer()

@router.message(AdminState.waiting_for_balance, F.from_user.id == ADMIN_ID)
async def admin_process_approve_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    req_id = data.get("approve_req_id")
    user_id = data.get("approve_user_id")
    
    try:
        amount = float(message.text)
        await db.update_balance(user_id, amount)
        await db.update_payment_request_status(req_id, 'completed')
        
        await message.answer(f"✅ Пайдаланушыға {amount} ₸ қосылды!")
        await message.bot.send_message(user_id, f"✅ Сіздің төлеміңіз расталды! Теңгеріміңізге `{amount} ₸` қосылды.", parse_mode="Markdown")
    except:
        await message.answer("❌ Қате сома.")
        
    await state.clear()

@router.callback_query(F.data == "top_clients")
async def show_top_clients(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    top = await db.get_top_referrers()
    text = "🏆 **Топ рефералдар:**\n\n" if lang == 'kz' else "🏆 **Топ рефералов:**\n\n"
    
    for i, (ref_id, count) in enumerate(top, 1):
        ref_user = await db.get_user_by_id(ref_id)
        username = ref_user[2] if ref_user else ref_id
        text += f"{i}. `@{username}` — {count} адам\n"
        
    await callback.message.edit_text(text, reply_markup=top_referrers_kb(lang), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    count, earned = await db.get_referral_stats(callback.from_user.id)
    link = f"https://t.me/renzonftbot?start={callback.from_user.id}"
    await callback.message.answer(TEXTS[lang]['ref'].format(link=link, count=count, earned=earned, percent=int(REF_PERCENT*100)), parse_mode="Markdown")
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("topup_stars_"):
        _, _, user_id, stars_amount = payload.split("_")
        user_id = int(user_id)
        stars_amount = float(stars_amount)
        kzt_amount = stars_amount * STARS_RATE_KZT
        await db.update_balance(user_id, kzt_amount)
        await message.answer(f"✅ Теңгеріміңіз `{kzt_amount:.2f} ₸` сомасына сәтті толтырылды! (Stars: {stars_amount})", parse_mode="Markdown")
    elif payload.startswith("sell_stars_"):
        _, _, user_id, amount, address = payload.split("_")
        user_id = int(user_id)
        amount = int(amount)
        
        # Notify admin
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f"💰 **Stars Сату сұранысы (Төленді)!**\n\n"
                f"👤 Пайдаланушы: @{message.from_user.username or user_id}\n"
                f"🌟 Сома: `{amount} Stars`\n"
                f"📬 TON Адрес: `{address}`\n\n"
                f"Пайдаланушы Stars жіберді. Енді оған TON немесе ₸ жіберіңіз.",
                parse_mode="Markdown"
            )
        except: pass
        await message.answer("✅ Төлем қабылданды! Админ жақын арада сізбен хабарласады немесе көрсетілген адрес бойынша төлем жасайды.")
    elif payload.startswith("topup_"):
        _, user_id, amount = payload.split("_")
        user_id = int(user_id)
        amount = float(amount)
        await db.update_balance(user_id, amount)
        await message.answer(f"✅ Теңгеріміңіз `{amount} ₸`-ге сәтті толтырылды!", parse_mode="Markdown")

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    await callback.message.answer("🛠 Қолдау қызметі: @renzo_support")
    await callback.answer()

@router.callback_query(F.data == "promocode")
async def show_promocode(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    await callback.message.answer(TEXTS[lang]['promo_prompt'])
    await state.set_state(PromoState.waiting_for_promo)
    await callback.answer()

@router.message(PromoState.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    code = message.text.strip()
    
    amount, status = await db.check_promocode(code, message.from_user.id)
    
    if status == "ok":
        await db.use_promocode(message.from_user.id, code, amount)
        await message.answer(TEXTS[lang]['promo_success'].format(amount=amount), parse_mode="Markdown")
    elif status == "already_used":
        await message.answer(TEXTS[lang]['promo_already'])
    elif status == "expired":
        await message.answer(TEXTS[lang]['promo_expired'])
    else:
        await message.answer(TEXTS[lang]['promo_invalid'])
    
    await state.clear()

@router.callback_query(F.data == "buy_ton")
async def start_buy_ton(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    await callback.message.edit_text(
        "💎 **TON сатып алу**\n\nҚанша TON сатып алғыңыз келеді?" if lang == 'kz' else
        "💎 **Покупка TON**\n\nСколько TON вы хотите купить?",
        parse_mode="Markdown"
    )
    await state.set_state(TONState.waiting_for_amount)
    await callback.answer()

@router.message(TONState.waiting_for_amount)
async def process_ton_amount(message: Message, state: FSMContext):
    if not message.text.replace(".", "").isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    amount = float(message.text)
    await state.update_data(amount=amount)
    await message.answer("📬 TON әмияныңыздың мекен-жайын (address) жіберіңіз:")
    await state.set_state(TONState.waiting_for_address)

@router.message(TONState.waiting_for_address)
async def process_ton_address(message: Message, state: FSMContext, api: APIClient):
    data = await state.get_data()
    address = message.text.strip()
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    # Calculate price
    ton_amount = data['amount']
    ton_rate = 2500 * MARGIN # Base rate
    total_price = ton_amount * ton_rate
    
    if user[1] < total_price:
        await message.answer(f"❌ Қаражат жеткіліксіз. Қажет: `{total_price:.2f} ₸`", parse_mode="Markdown")
        await state.clear()
        return

    # Deduct balance
    await db.update_balance(user_id, -total_price)
    
    # Notify admin
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"💎 **TON Сатып алу сұранысы!**\n\n"
            f"👤 Пайдаланушы: @{message.from_user.username or user_id}\n"
            f"💰 Сома: `{ton_amount} TON`\n"
            f"💵 Төленді: `{total_price:.2f} ₸`\n"
            f"📬 Адрес: `{address}`\n\n"
            f"Өтінеміз, TON жіберіңіз.",
            parse_mode="Markdown"
        )
    except: pass
    
    await message.answer(f"✅ Тапсырыс қабылданды! Админ жақын арада `{ton_amount} TON` жібереді.", parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "sell_stars")
async def start_sell_stars(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    await callback.message.edit_text(
        "💰 **Stars сату**\n\nҚанша Stars сатқыңыз келеді?" if lang == 'kz' else
        "💰 **Продажа Stars**\n\nСколько Stars вы хотите продать?",
        parse_mode="Markdown"
    )
    await state.set_state(SellStarsState.waiting_for_amount)
    await callback.answer()

@router.message(SellStarsState.waiting_for_amount)
async def process_sell_stars_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    amount = int(message.text)
    await state.update_data(amount=amount)
    await message.answer("📬 Төлемді алатын TON әмияныңыздың мекен-жайын жіберіңіз:")
    await state.set_state(SellStarsState.waiting_for_address)

@router.message(SellStarsState.waiting_for_address)
async def process_sell_stars_address(message: Message, state: FSMContext):
    data = await state.get_data()
    address = message.text.strip()
    amount = data['amount']
    user_id = message.from_user.id
    
    await state.update_data(address=address)
    
    # Send invoice for Stars
    from aiogram.types import LabeledPrice
    prices = [LabeledPrice(label="Sell Stars", amount=amount)]
    await message.bot.send_invoice(
        message.chat.id,
        title="Stars сату",
        description=f"{amount} Stars сату үшін төлем жасаңыз. Админ сізге TON жібереді.",
        provider_token="",
        currency="XTR",
        prices=prices,
        payload=f"sell_stars_{user_id}_{amount}_{address}"
    )
    await message.answer("⏳ Төлемді күтудеміз... Төлеген соң админге хабарлама барады.")
    await state.clear()

@router.callback_query(F.data == "buy_premium")
async def buy_premium_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="3 ай / мес", callback_data="premium_3")
    builder.button(text="6 ай / мес", callback_data="premium_6")
    builder.button(text="12 ай / мес", callback_data="premium_12")
    builder.button(text="‹ Мәзірге / В меню", callback_data="back_to_main")
    builder.adjust(1)
    
    text = "💎 Telegram Premium мерзімін таңдаңыз:" if lang == 'kz' else "💎 Выберите срок Telegram Premium:"
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("premium_"))
async def select_premium(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[1])
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    # Бағаларды API-ден алу керек немесе қолмен қою (API-де Premium бағасын алу жоқ сияқты)
    # Мысалы: 3 ай - 5000, 6 ай - 8000, 12 ай - 14000
    prices = {3: 5000, 6: 8000, 12: 14000}
    price = prices[months]
    
    if user[1] < price:
        await callback.message.answer(f"❌ Қаражат жеткіліксіз! Бағасы: {price} ₸" if lang == 'kz' else f"❌ Недостаточно средств! Цена: {price} ₸")
        return

    await state.update_data(months=months, price=price)
    await callback.message.answer("👤 Premium жіберілетін пайдаланушының Юзернеймін жазыңыз (мысалы: `durov`):", parse_mode="Markdown")
    await state.set_state(PremiumState.waiting_for_id)
    await callback.answer()

@router.message(PremiumState.waiting_for_id)
async def process_premium_id(message: Message, state: FSMContext, api: APIClient):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    target = message.text.strip().replace("@", "")
    data = await state.get_data()
    
    order_res = await api.place_premium_order(target, data['months'])
    
    if order_res.get("success"):
        await db.update_balance(message.from_user.id, -data['price'])
        
        # Сауданы базаға жазу
        await db.create_order(
            user_id=message.from_user.id,
            order_id_api=order_res.get("order_id", 0),
            product_type="premium",
            product_name=f"Premium {data['months']} ай",
            description=f"Telegram Premium @{target}",
            amount_kzt=data['price'],
            profit_kzt=data['price'] * 0.2, # 20% пайда
            status='completed'
        )
        
        await message.answer(
            f"✅ Premium тапсырысы қабылданды!\n📦 Мерзімі: `{data['months']} ай`\n👤 Алушы: `@{target}`" if lang == 'kz' else
            f"✅ Заказ на Premium принят!\n📦 Срок: `{data['months']} мес`\n👤 Получатель: `@{target}`",
            parse_mode="Markdown"
        )
    else:
        error = order_res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}" if lang == 'kz' else f"❌ Ошибка: {error}")
        
    await state.clear()

def get_nft_link(name: str) -> str:
    # Rare Bird #9797 -> RareBird-9797
    # +888 1234 5678 -> 88812345678
    # username -> username
    clean_name = name.replace(" ", "").replace("#", "-").replace("+", "")
    return f"https://t.me/nft/{clean_name}"

@router.callback_query(F.data == "rent_nft")
async def show_nft_rental_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    if lang == 'kz':
        builder.button(text="🎁 NFT-подарки", callback_data="nft_cat_gifts")
        builder.button(text="👤 NFT-юзернеймдер", callback_data="nft_cat_usernames")
        builder.button(text="☎️ NFT-номерлер", callback_data="nft_cat_numbers")
        builder.button(text="‹ Мәзірге", callback_data="back_to_main")
    else:
        builder.button(text="🎁 NFT-подарки", callback_data="nft_cat_gifts")
        builder.button(text="👤 NFT-юзернеймы", callback_data="nft_cat_usernames")
        builder.button(text="☎️ NFT-номера", callback_data="nft_cat_numbers")
        builder.button(text="‹ В меню", callback_data="back_to_main")
        
    builder.adjust(1)
    
    await callback.message.edit_text(
        TEXTS[lang]['nft_rental_menu'],
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "calculator")
async def show_calculator(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = "🧮 **Калькулятор**\n\nАйырбастау бағасын есептеңіз:" if lang == 'kz' else "🧮 **Калькулятор**\n\nРассчитайте стоимость обмена:"
    await callback.message.edit_text(text, reply_markup=calculator_kb(lang), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "calc_stars_kzt")
async def calc_stars(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    await callback.message.edit_text("🌟 Stars санын енгізіңіз:" if lang == 'kz' else "Введите количество Stars:")
    await state.set_state(CalculatorState.waiting_for_stars)
    await callback.answer()

@router.message(CalculatorState.waiting_for_stars)
async def process_calc_stars(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    stars = int(message.text)
    kzt = stars * STARS_RATE_KZT
    await message.answer(f"🌟 {stars} Stars = `{kzt:.2f} ₸`", parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "calc_ton_kzt")
async def calc_ton(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    await callback.message.edit_text("💎 TON санын енгізіңіз:" if lang == 'kz' else "Введите количество TON:")
    await state.set_state(CalculatorState.waiting_for_ton)
    await callback.answer()

@router.message(CalculatorState.waiting_for_ton)
async def process_calc_ton(message: Message, state: FSMContext, api: APIClient):
    if not message.text.replace(".", "").isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    ton = float(message.text)
    # Get TON rate (placeholder or from API if available)
    # For now, let's assume 1 TON = 2500 KZT as a base
    ton_rate = 2500 * MARGIN
    kzt = ton * ton_rate
    await message.answer(f"💎 {ton} TON ≈ `{kzt:.2f} ₸`", parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    is_admin = callback.from_user.id == ADMIN_ID
    
    stars_count, gifts_count, usernames_count = await db.get_global_stats()
    
    await callback.message.edit_text(
        TEXTS[lang]['start'].format(
            balance=user[1],
            stars_count=stars_count,
            gifts_count=gifts_count,
            usernames_count=usernames_count
        ),
        reply_markup=main_menu_kb(is_admin, lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("nft_cat_"))
async def show_nft_category(callback: CallbackQuery, api: APIClient, state: FSMContext):
    category = callback.data.split("_")[2]
    await state.update_data(category=category)
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    try:
        collections_res = await api.get_nft_collections()
        if not collections_res.get("success"):
            await callback.answer("❌ Қате орын алды.")
            return
            
        collections = collections_res.get("collections", [])
        
        if category == "gifts":
            # Show collections that are NOT usernames or numbers
            gift_collections = [c for c in collections if "username" not in c['name'].lower() and "number" not in c['name'].lower()]
            
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            for col in gift_collections[:10]: # Limit to 10
                col_name = col['name']
                col_address = col.get('address') or col.get('nft_address')
                if not col_address:
                    continue
                if len(col_name) > 15:
                    col_name = col_name[:12] + "..."
                builder.button(text=f"🖼 {col_name}", callback_data=f"nc_{col_address}")
            
            builder.button(text="‹ Артқа / Назад", callback_data="rent_nft")
            builder.adjust(1)
            
            await callback.message.edit_text(
                "🎁 **NFT-подарки**\n\nКоллекцияны таңдаңыз:" if lang == 'kz' else "🎁 **NFT-подарки**\n\nВыберите коллекцию:",
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        elif category == "usernames":
            col = next((c for c in collections if "username" in c['name'].lower()), None)
            if col:
                col_address = col.get('address') or col.get('nft_address')
                if col_address:
                    await show_nft_items_internal(callback, col_address, api, state)
                else:
                    await callback.answer("❌ Коллекция адресі табылмады." if lang == 'kz' else "❌ Адрес коллекции не найден.")
            else:
                await callback.answer("❌ Табылмады." if lang == 'kz' else "❌ Не найдено.")
        elif category == "numbers":
            col = next((c for c in collections if "number" in c['name'].lower()), None)
            if col:
                col_address = col.get('address') or col.get('nft_address')
                if col_address:
                    await show_nft_items_internal(callback, col_address, api, state)
                else:
                    await callback.answer("❌ Коллекция адресі табылмады." if lang == 'kz' else "❌ Адрес коллекции не найден.")
            else:
                await callback.answer("❌ Табылмады." if lang == 'kz' else "❌ Не найдено.")
                
    except Exception as e:
        await callback.message.answer(f"❌ Қате: {str(e)}")
    
    await callback.answer()

async def show_nft_items_internal(callback: CallbackQuery, collection_address: str, api: APIClient, state: FSMContext, cursor: str = None):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    try:
        data = await api.get_nft_list(collection_address, cursor)
        if data.get("success"):
            items = data.get("items", [])
            if items:
                MAX_ITEMS_PER_PAGE = 3
                current_items = items[:MAX_ITEMS_PER_PAGE]
                
                await state.update_data(
                    current_collection=collection_address,
                    current_items=items,
                    current_cursor=data.get("cursor")
                )
                
                items_text = ""
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                builder = InlineKeyboardBuilder()
                
                for idx, item in enumerate(current_items):
                    price_kzt = item["price_per_day_rub_with_margin"] * KZT_RATE
                    link = get_nft_link(item['name'])
                    day_text = "күн" if lang == 'kz' else "день"
                    items_text += f"🔹 [{item['name']}]({link}) — `{price_kzt:.2f} ₸/{day_text}`\n"
                    builder.button(text=f"🛒 {item['name'][:15]}", callback_data=f"ri_{idx}")
                
                next_cursor = data.get("cursor")
                if next_cursor:
                    builder.button(text="➡️ Келесі / Далее", callback_data="nft_next")
                
                builder.button(text="‹ Артқа / Назад", callback_data="rent_nft")
                builder.adjust(1)
                
                await callback.message.edit_text(
                    f"📦 **Қолжетімді тауарлар:**\n\n{items_text}\n\nСатып алу үшін таңдаңыз 👇" if lang == 'kz' else
                    f"📦 **Доступные товары:**\n\n{items_text}\n\nВыберите для покупки 👇",
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                await callback.message.answer("❌ Қазіргі уақытта тауарлар жоқ." if lang == 'kz' else "❌ В данный момент товаров нет.")
        else:
            error_msg = data.get("error", "Unknown error")
            await callback.message.answer(f"❌ Қате: {error_msg}")
    except Exception as e:
        await callback.message.answer(f"❌ Қате: {str(e)}")

@router.callback_query(F.data.startswith("nc_"))
async def show_nft_items(callback: CallbackQuery, state: FSMContext, api: APIClient):
    parts = callback.data.split("_")
    collection_address = parts[1]
    cursor = parts[2] if len(parts) > 2 else None
    await show_nft_items_internal(callback, collection_address, api, state, cursor)
    await callback.answer()

@router.callback_query(F.data == "nft_next")
async def next_nft_page(callback: CallbackQuery, state: FSMContext, api: APIClient):
    state_data = await state.get_data()
    collection_address = state_data.get("current_collection")
    cursor = state_data.get("current_cursor")
    
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    if not collection_address or not cursor:
        await callback.answer("❌ Сессия аяқталды." if lang == 'kz' else "❌ Сессия истекла.")
        return
    
    try:
        data = await api.get_nft_list(collection_address, cursor)
        if data.get("success"):
            items = data.get("items", [])
            if items:
                MAX_ITEMS_PER_PAGE = 3
                current_items = items[:MAX_ITEMS_PER_PAGE]
                
                await state.update_data(
                    current_items=items,
                    current_cursor=data.get("cursor")
                )
                
                items_text = ""
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                builder = InlineKeyboardBuilder()
                
                for idx, item in enumerate(current_items):
                    price_kzt = item["price_per_day_rub_with_margin"] * KZT_RATE
                    link = get_nft_link(item['name'])
                    day_text = "күн" if lang == 'kz' else "день"
                    items_text += f"🔹 [{item['name']}]({link}) — `{price_kzt:.2f} ₸/{day_text}`\n"
                    builder.button(text=f"🛒 {item['name'][:15]}", callback_data=f"ri_{idx}")
                
                if data.get("cursor"):
                    builder.button(text="➡️ Келесі / Далее", callback_data="nft_next")
                
                builder.button(text="‹ Артқа / Назад", callback_data="rent_nft")
                builder.adjust(1)
                
                await callback.message.edit_text(
                    f"📦 **Қолжетімді тауарлар:**\n\n{items_text}\n\nСатып алу үшін таңдаңыз 👇" if lang == 'kz' else
                    f"📦 **Доступные товары:**\n\n{items_text}\n\nВыберите для покупки 👇",
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
    except Exception as e:
        print(f"Error in next_nft_page: {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("ri_"))
async def start_nft_rent(callback: CallbackQuery, state: FSMContext, api: APIClient):
    try:
        idx = int(callback.data.split("_")[1])
        state_data = await state.get_data()
        items = state_data.get("current_items", [])
        
        user = await db.get_user(callback.from_user.id)
        lang = user[4] if user else 'kz'
        
        if idx >= len(items):
            await callback.answer("❌ Тауар табылмады." if lang == 'kz' else "❌ Товар не найден.")
            return
            
        item = items[idx]
        nft_address = item.get("address") or item.get("nft_address")
        
        if not nft_address:
            await callback.answer("❌ Тауар адресі табылмады." if lang == 'kz' else "❌ Адрес товара не найден.")
            return
        
        # Use data from item to avoid rate limit on get_nft_rate
        price_kzt = item.get("price_per_day_rub_with_margin", 0) * KZT_RATE
        nft_name = item.get("name", "NFT")
        min_days = item.get('min_days', 1)
        
        # If price is 0, try to get it from API once, but catch errors
        if price_kzt == 0:
            try:
                rate_res = await api.get_nft_rate(nft_address)
                if rate_res.get("success"):
                    price_kzt = rate_res["price_per_day_rub_with_margin"] * KZT_RATE
                    nft_name = rate_res.get("nft_name", nft_name)
                    min_days = rate_res.get('min_days', min_days)
            except Exception as e:
                print(f"Error fetching rate: {e}")
        
        if price_kzt == 0:
            await callback.answer("❌ Тауар бағасын алу мүмкін болмады." if lang == 'kz' else "❌ Не удалось получить цену товара.")
            return

        await state.update_data(nft_address=nft_address, price_per_day=price_kzt, name=nft_name, min_days=min_days)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="‹ Артқа / Назад", callback_data="rent_nft")
        
        await callback.message.edit_text(
            TEXTS[lang]['nft_rent_days'].format(
                name=nft_name,
                price=price_kzt,
                min_days=min_days
            ),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state(NFTState.waiting_for_days)
        await callback.answer()
    except Exception as e:
        print(f"Error in start_nft_rent: {e}")
        await callback.message.answer(f"❌ Қате: {str(e)}")
        await callback.answer()

@router.message(NFTState.waiting_for_days)
async def process_nft_days(message: Message, state: FSMContext, api: APIClient):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз." if lang == 'kz' else "❌ Введите только числа.")
        return
        
    days = int(message.text)
    data = await state.get_data()
    min_days = data.get('min_days', 1)
    
    if days < min_days:
        await message.answer(
            f"❌ Ең аз жалдау мерзімі: {min_days} күн." if lang == 'kz' else
            f"❌ Минимальный срок аренды: {min_days} дн."
        )
        return
        
    total_price = data['price_per_day'] * days
    
    if user[1] < total_price:
        await message.answer(
            f"❌ Қаражат жеткіліксіз! Қажет: {total_price:.2f} ₸" if lang == 'kz' else
            f"❌ Недостаточно средств! Нужно: {total_price:.2f} ₸"
        )
        await state.clear()
        return
        
    # Жалдау тапсырысын жіберу
    rent_res = await api.place_nft_rent_order(data['nft_address'], days)
    
    if rent_res.get("success"):
        await db.update_balance(message.from_user.id, -total_price)
        
        # Get transaction_id or order_id from response
        transaction_id = rent_res.get("transaction_id") or rent_res.get("order_id") or rent_res.get("id")
        
        # Log order to DB
        # product_type should be determined from category
        state_data = await state.get_data()
        category = state_data.get("category", "nft")
        description = f"Аренда {data['name']} на {days} дней."
        
        await db.create_order(
            user_id=message.from_user.id,
            order_id_api=transaction_id,
            product_type=category,
            product_name=data['name'],
            description=description,
            amount_kzt=total_price,
            profit_kzt=total_price * 0.15, # Example profit
            status='completed'
        )
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        if transaction_id:
            builder.button(text="🔗 TON Connect қосу / Подключить", callback_data=f"cn_{transaction_id}")
        
        await message.answer(
            TEXTS[lang]['nft_rent_success'].format(
                name=data['name'],
                days=days,
                total=total_price
            ),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    else:
        error = rent_res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}" if lang == 'kz' else f"❌ Ошибка: {error}")
        
    await state.clear()

@router.callback_query(F.data.startswith("cn_"))
async def start_connect_nft(callback: CallbackQuery, state: FSMContext):
    transaction_id = callback.data.split("_")[1]
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Бас тарту / Отмена", callback_data="back_to_main")
    
    await state.update_data(transaction_id=transaction_id)
    await callback.message.edit_text(
        TEXTS[lang]['nft_connect_prompt'],
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(NFTState.waiting_for_ton_connect)
    await callback.answer()

@router.message(NFTState.waiting_for_ton_connect)
async def process_ton_connect(message: Message, state: FSMContext, api: APIClient):
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    url = message.text.strip()
    if not url.startswith("tc://") and not url.startswith("https://"):
        await message.answer("❌ Қате сілтеме. Қайтадан жіберіңіз." if lang == 'kz' else "❌ Неверная ссылка. Отправьте еще раз.")
        return
        
    data = await state.get_data()
    
    # Use transaction_id instead of nft_address
    res = await api.connect_nft_rent(data['transaction_id'], url)
    
    if res.get("success"):
        await message.answer(TEXTS[lang]['nft_connect_success'])
    else:
        error = res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}" if lang == 'kz' else f"❌ Ошибка: {error}")
        
    await state.clear()

@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    from keyboards import history_menu_kb
    await callback.message.edit_text(
        TEXTS[lang]['history_menu'],
        reply_markup=history_menu_kb(lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "history_orders")
async def show_orders_history(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    orders = await db.get_user_orders(callback.from_user.id)
    from keyboards import history_kb
    await callback.message.edit_text(
        TEXTS[lang]['history_title'],
        reply_markup=history_kb(orders, lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "history_payments")
async def show_payments_history(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    payments = await db.get_user_payments(callback.from_user.id)
    from keyboards import payments_history_kb
    await callback.message.edit_text(
        TEXTS[lang]['payments_history_title'],
        reply_markup=payments_history_kb(payments, lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pay_view_"))
async def view_payment(callback: CallbackQuery):
    req_id = int(callback.data.split("_")[2])
    pay = await db.get_payment_request(req_id)
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    if not pay:
        await callback.answer("❌ Төлем табылмады." if lang == 'kz' else "❌ Пополнение не найдено.")
        return
        
    # pay: (id, user_id, amount, method, receipt_file_id, comment_code, status, created_at)
    status_text = "✅ Расталды / Одобрено" if pay[6] == 'approved' else "⏳ Күтілуде / Ожидание" if pay[6] == 'pending' else "❌ Бас тартылды / Отклонено"
    
    from keyboards import payment_details_kb
    await callback.message.edit_text(
        TEXTS[lang]['payment_details'].format(
            id=pay[0],
            amount=pay[2],
            method=pay[3],
            code=pay[5] or "—",
            status=status_text,
            date=pay[7]
        ),
        reply_markup=payment_details_kb(lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("order_view_"))
async def view_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    order = await db.get_order(order_id)
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    if not order:
        await callback.answer("❌ Тапсырыс табылмады." if lang == 'kz' else "❌ Заказ не найден.")
        return
        
    # order: (id, user_id, order_id_api, status, product_type, product_name, description, amount_kzt, profit_kzt, tx_hash, is_notified, created_at)
    status_text = "✅ Выполнен" if order[3] == 'completed' else "⏳ В обработке" if order[3] in ['pending', 'processing'] else "❌ Отменен"
    fragment_status = "Привязан" if order[9] else "Не привязан" # Using tx_hash as proxy for connection status for now
    
    from keyboards import order_details_kb
    await callback.message.edit_text(
        TEXTS[lang]['order_details'].format(
            id=order[0],
            name=order[5],
            price=order[7],
            status=status_text,
            date=order[11],
            description=order[6],
            fragment_status=fragment_status
        ),
        reply_markup=order_details_kb(order[0], lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "calculator")
async def show_calculator(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    from keyboards import calculator_kb
    text = "🧮 **Калькулятор**\n\nАйырбастау бағытын таңдаңыз:" if lang == 'kz' else "🧮 **Калькулятор**\n\nВыберите направление обмена:"
    await callback.message.edit_text(text, reply_markup=calculator_kb(lang), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "calc_stars_kzt")
async def calc_stars(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = "🌟 **Stars ➔ ₸**\n\nStars мөлшерін енгізіңіз:" if lang == 'kz' else "🌟 **Stars ➔ ₸**\n\nВведите количество Stars:"
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(CalculatorState.waiting_for_stars)
    await callback.answer()

@router.message(CalculatorState.waiting_for_stars, F.text)
async def process_calc_stars(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    
    stars = int(message.text)
    kzt = stars * STARS_RATE_KZT
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    text = f"🧮 **Нәтиже:**\n\n`{stars} Stars` = `{kzt:.2f} ₸`" if lang == 'kz' else f"🧮 **Результат:**\n\n`{stars} Stars` = `{kzt:.2f} ₸`"
    from keyboards import calculator_kb
    await message.answer(text, reply_markup=calculator_kb(lang), parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "calc_ton_kzt")
async def calc_ton(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    text = "💎 **TON ➔ ₸**\n\nTON мөлшерін енгізіңіз:" if lang == 'kz' else "💎 **TON ➔ ₸**\n\nВведите количество TON:"
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(CalculatorState.waiting_for_ton)
    await callback.answer()

@router.message(CalculatorState.waiting_for_ton, F.text)
async def process_calc_ton(message: Message, state: FSMContext):
    try:
        ton = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("❌ Қате формат.")
        return
    
    # Placeholder TON rate: 1 TON = 2500 KZT
    ton_rate = 2500.0 
    kzt = ton * ton_rate
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    text = f"🧮 **Нәтиже:**\n\n`{ton} TON` = `{kzt:.2f} ₸`" if lang == 'kz' else f"🧮 **Результат:**\n\n`{ton} TON` = `{kzt:.2f} ₸`"
    from keyboards import calculator_kb
    await message.answer(text, reply_markup=calculator_kb(lang), parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    from keyboards import main_menu_kb
    await callback.message.edit_text(
        TEXTS[lang]['start'].format(name=callback.from_user.full_name),
        reply_markup=main_menu_kb(callback.from_user.id == ADMIN_ID, lang)
    )
    await callback.answer()
