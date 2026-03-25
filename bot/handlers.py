from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from api_client import APIClient
from keyboards import main_menu_kb, profile_kb, language_kb, admin_kb, nft_rental_kb
import os
from dotenv import load_dotenv

router = Router()
db = Database()

class PromoState(StatesGroup):
    waiting_for_promo = State()

class TopupState(StatesGroup):
    waiting_for_amount = State()

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
KZT_RATE = float(os.getenv("RUB_KZT_RATE", 5.2))
REF_PERCENT = float(os.getenv("REFERRAL_PERCENT", 0.05))

TEXTS = {
    'kz': {
        'start': "Сәлем, {name}! 👋\nЦифрлық тауарлар дүкеніне қош келдіңіз.",
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
        'nft_list': "📦 **Қолжетімді тауарлар ({type}):**\n\n{items}\n\nСатып алу үшін тауардың ID-ін жазыңыз немесе таңдаңыз:"
    },
    'ru': {
        'start': "Привет, {name}! 👋\nДобро пожаловать в магазин цифровых товаров.",
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
        'nft_list': "📦 **Доступные товары ({type}):**\n\n{items}\n\nДля покупки введите ID товара или выберите:"
    }
}

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user = await db.get_user(message.from_user.id)
    if not user:
        args = command.args
        referred_by = None
        if args and args.isdigit():
            referred_by = int(args)
            if referred_by == message.from_user.id:
                referred_by = None
        
        await db.create_user(message.from_user.id, message.from_user.username, referred_by)
        user = await db.get_user(message.from_user.id)
    
    lang = user[4] if user else 'kz'
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer(
        TEXTS[lang]['start'].format(name=message.from_user.full_name),
        reply_markup=main_menu_kb(is_admin, lang)
    )

@router.callback_query(F.data == "change_lang")
async def change_lang(callback: CallbackQuery):
    await callback.message.answer("Тілді таңдаңыз / Выберите язык:", reply_markup=language_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_panel", F.from_user.id == ADMIN_ID)
async def admin_panel(callback: CallbackQuery):
    users, sales = await db.get_stats()
    profit = await db.get_profit_stats()
    await callback.message.answer(
        f"📊 **Админ панель**\n\n"
        f"👥 Пайдаланушылар: {users}\n"
        f"💰 Жалпы сауда: {sales:.2f} ₸\n"
        f"📈 Таза пайда: {profit:.2f} ₸",
        reply_markup=admin_kb()
    )
    await callback.answer()

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
async def buy_stars_info(callback: CallbackQuery, api: APIClient):
    try:
        rate_data = await api.get_stars_rate()
        if rate_data.get("success"):
            price_rub = rate_data["price_per_star_rub_with_margin"]
            price_kzt = price_rub * KZT_RATE
            
            await callback.message.answer(
                f"🌟 **Telegram Stars сатып алу**\n\n"
                f"💵 Бағасы (1 дана): `{price_kzt:.2f} ₸` (~{price_rub} ₽)\n"
                f"📦 Ең аз мөлшер: {rate_data['min_quantity']}\n\n"
                "Сатып алғыңыз келетін Stars мөлшерін енгізіңіз:",
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer("❌ Курсты алу мүмкін болмады. Кейінірек қайталаңыз.")
    except Exception as e:
        await callback.message.answer("❌ Қате орын алды. Кейінірек қайталаңыз.")
    await callback.answer()

@router.callback_query(F.data.startswith("set_lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[2]
    await db.set_language(callback.from_user.id, lang)
    await callback.message.edit_text(TEXTS[lang]['lang_changed'])
    await callback.message.answer(TEXTS[lang]['start'].format(name=callback.from_user.full_name), reply_markup=main_menu_kb(callback.from_user.id == ADMIN_ID, lang))
    await callback.answer()

@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    count, earned = await db.get_referral_stats(callback.from_user.id)
    link = f"https://t.me/renzonftbot?start={callback.from_user.id}"
    await callback.message.answer(TEXTS[lang]['ref'].format(link=link, count=count, earned=earned, percent=int(REF_PERCENT*100)), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    await callback.message.answer("🛠 Қолдау қызметі: @renzo_support")
    await callback.answer()

@router.callback_query(F.data == "topup")
async def start_topup(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💰 Толтырғыңыз келетін соманы енгізіңіз (₸):")
    await state.set_state(TopupState.waiting_for_amount)
    await callback.answer()

@router.message(TopupState.waiting_for_amount)
async def process_topup(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
    
    amount = float(message.text)
    if amount < 100:
        await message.answer("❌ Ең аз толтыру сомасы - 100 ₸")
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    # Балансты толтыру
    await db.update_balance(user_id, amount)
    await message.answer(f"✅ Теңгеріміңіз `{amount:.2f} ₸`-ге толтырылды!", parse_mode="Markdown")
    
    # Реферал бонусы
    if user and user[3]: # referred_by
        referrer_id = user[3]
        bonus = amount * REF_PERCENT
        await db.add_referral_earning(referrer_id, bonus)
        
        try:
            await message.bot.send_message(
                referrer_id, 
                f"💰 Рефералыңыз теңгерімін толтырды! Сізге `{bonus:.2f} ₸` бонус түсті.",
                parse_mode="Markdown"
            )
        except:
            pass # Реферер ботты блоктаған болуы мүмкін

    await state.clear()

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

@router.callback_query(F.data == "buy_premium")
async def buy_premium(callback: CallbackQuery):
    await callback.message.answer("💎 Telegram Premium сатып алу жақын арада қосылады!")
    await callback.answer()

@router.callback_query(F.data == "rent_nft")
async def show_nft_rental_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    await callback.message.edit_text(
        TEXTS[lang]['nft_rental_menu'],
        reply_markup=nft_rental_kb(lang),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    is_admin = callback.from_user.id == ADMIN_ID
    await callback.message.edit_text(
        TEXTS[lang]['start'].format(name=callback.from_user.full_name),
        reply_markup=main_menu_kb(is_admin, lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("nft_"))
async def show_nft_items(callback: CallbackQuery, api: APIClient):
    nft_type = callback.data.split("_")[1] # gifts, usernames, numbers
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    try:
        data = await api.get_nft_items(nft_type)
        if data.get("success") and data.get("items"):
            items_text = ""
            for item in data["items"]:
                price_kzt = item["price_rub_with_margin"] * KZT_RATE
                items_text += f"🔹 `{item['name']}` — `{price_kzt:.2f} ₸` (ID: `{item['id']}`)\n"
            
            type_label = {
                "gifts": "Подарки",
                "usernames": "Юзернеймдер" if lang == 'kz' else "Юзернеймы",
                "numbers": "Номерлер" if lang == 'kz' else "Номера"
            }[nft_type]
            
            await callback.message.answer(
                TEXTS[lang]['nft_list'].format(type=type_label, items=items_text),
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer("❌ Қазіргі уақытта тауарлар жоқ." if lang == 'kz' else "❌ В данный момент товаров нет.")
    except Exception as e:
        await callback.message.answer(f"❌ Қате: {str(e)}")
    
    await callback.answer()

@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery):
    await callback.message.answer("📜 Тапсырыстар тарихы бос.")
    await callback.answer()
