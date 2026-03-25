from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from api_client import APIClient
from keyboards import main_menu_kb, profile_kb, language_kb, admin_kb, stars_items_kb
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
        await message.answer(
            f"✅ Premium тапсырысы қабылданды!\n📦 Мерзімі: `{data['months']} ай`\n👤 Алушы: `@{target}`" if lang == 'kz' else
            f"✅ Заказ на Premium принят!\n📦 Срок: `{data['months']} мес`\n👤 Получатель: `@{target}`",
            parse_mode="Markdown"
        )
    else:
        error = order_res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}" if lang == 'kz' else f"❌ Ошибка: {error}")
        
    await state.clear()

@router.callback_query(F.data == "rent_nft")
async def show_nft_rental_menu(callback: CallbackQuery, api: APIClient):
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    try:
        collections_res = await api.get_nft_collections()
        if collections_res.get("success"):
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            
            for col in collections_res.get("collections", []):
                builder.button(text=f"🖼 {col['name']}", callback_data=f"nft_col_{col['address']}")
            
            builder.button(text="‹ Мәзірге / В меню", callback_data="back_to_main")
            builder.adjust(1)
            
            await callback.message.edit_text(
                TEXTS[lang]['nft_rental_menu'],
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        else:
            error = collections_res.get("error", "Unknown error")
            await callback.message.answer(f"❌ Қате: {error}")
    except Exception as e:
        await callback.message.answer(f"❌ Қате: {str(e)}")
    
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

@router.callback_query(F.data.startswith("nft_col_"))
async def show_nft_items(callback: CallbackQuery, api: APIClient):
    collection_address = callback.data.split("_")[2]
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    try:
        # Тауарлар тізімін алу
        data = await api.get_nft_list(collection_address)
        if data.get("success"):
            if data.get("items"):
                items_text = ""
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                builder = InlineKeyboardBuilder()
                
                for item in data["items"]:
                    price_kzt = item["price_per_day_rub_with_margin"] * KZT_RATE
                    items_text += f"🔹 `{item['name']}` — `{price_kzt:.2f} ₸/күн` (ID: `{item['id']}`)\n"
                    builder.button(text=f"Жалға алу: {item['name']}", callback_data=f"rent_item_{item['address']}")
                
                builder.button(text="‹ Артқа / Назад", callback_data="rent_nft")
                builder.adjust(1)
                
                await callback.message.edit_text(
                    f"📦 **Қолжетімді тауарлар:**\n\n{items_text}\n\nСатып алу үшін таңдаңыз 👇" if lang == 'kz' else
                    f"📦 **Доступные товары:**\n\n{items_text}\n\nВыберите для покупки 👇",
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
            else:
                await callback.message.answer("❌ Қазіргі уақытта тауарлар жоқ." if lang == 'kz' else "❌ В данный момент товаров нет.")
        else:
            error_msg = data.get("error", "Unknown error")
            await callback.message.answer(f"❌ Қате: {error_msg}" if lang == 'kz' else f"❌ Ошибка: {error_msg}")
    except Exception as e:
        await callback.message.answer(f"❌ Қате: {str(e)}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("rent_item_"))
async def start_nft_rent(callback: CallbackQuery, state: FSMContext, api: APIClient):
    nft_address = callback.data.split("_")[2]
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    rate_res = await api.get_nft_rate(nft_address)
    if not rate_res.get("success"):
        await callback.message.answer("❌ Тауар туралы ақпарат алу мүмкін болмады." if lang == 'kz' else "❌ Не удалось получить информацию о товаре.")
        return
        
    price_kzt = rate_res["price_per_day_rub_with_margin"] * KZT_RATE
    await state.update_data(nft_address=nft_address, price_per_day=price_kzt, name=rate_res.get("nft_name", "NFT"))
    
    await callback.message.answer(
        f"💎 **{rate_res.get('nft_name', 'NFT')}**\n\n"
        f"💰 Жалдау бағасы: `{price_kzt:.2f} ₸/күн`\n"
        f"📦 Ең аз мерзім: {rate_res.get('min_days', 1)} күн\n\n"
        "Неше күнге жалдағыңыз келеді? (санын жазыңыз):",
        parse_mode="Markdown"
    )
    await state.set_state(NFTState.waiting_for_days)
    await callback.answer()

@router.message(NFTState.waiting_for_days)
async def process_nft_days(message: Message, state: FSMContext, api: APIClient):
    if not message.text.isdigit():
        await message.answer("❌ Тек сандарды енгізіңіз.")
        return
        
    days = int(message.text)
    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    total_price = data['price_per_day'] * days
    
    if user[1] < total_price:
        await message.answer(f"❌ Қаражат жеткіліксіз! Қажет: {total_price:.2f} ₸")
        await state.clear()
        return
        
    # Жалдау тапсырысын жіберу
    rent_res = await api.place_nft_rent_order(data['nft_address'], days)
    
    if rent_res.get("success"):
        await db.update_balance(message.from_user.id, -total_price)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔗 TON Connect қосу / Подключить", callback_data=f"connect_nft_{data['nft_address']}")
        
        await message.answer(
            f"✅ **Жалдау сәтті орындалды!**\n\n"
            f"📦 Тауар: `{data['name']}`\n"
            f"📅 Мерзімі: `{days} күн`\n"
            f"💰 Барлығы: `{total_price:.2f} ₸`\n\n"
            "Енді Fragment-те қолдану үшін TON Connect арқылы қосылуыңыз керек.",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    else:
        error = rent_res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}")
        
    await state.clear()

@router.callback_query(F.data.startswith("connect_nft_"))
async def start_connect_nft(callback: CallbackQuery, state: FSMContext):
    nft_address = callback.data.split("_")[2]
    user = await db.get_user(callback.from_user.id)
    lang = user[4] if user else 'kz'
    
    await state.update_data(nft_address=nft_address)
    await callback.message.answer(
        "🔗 Fragment-тен TON Connect сілтемесін (URL) жіберіңіз:" if lang == 'kz' else
        "🔗 Пришлите TON Connect ссылку (URL) из Fragment:"
    )
    await state.set_state(NFTState.waiting_for_ton_connect)
    await callback.answer()

@router.message(NFTState.waiting_for_ton_connect)
async def process_ton_connect(message: Message, state: FSMContext, api: APIClient):
    url = message.text.strip()
    if not url.startswith("tc://") and not url.startswith("https://"):
        await message.answer("❌ Қате сілтеме. Қайтадан жіберіңіз.")
        return
        
    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    lang = user[4] if user else 'kz'
    
    res = await api.connect_nft_rent(data['nft_address'], url)
    
    if res.get("success"):
        await message.answer("✅ TON Connect сәтті қосылды! Енді Fragment-те қолдана аласыз." if lang == 'kz' else "✅ TON Connect успешно подключен! Теперь вы можете использовать его на Fragment.")
    else:
        error = res.get("error", "Unknown error")
        await message.answer(f"❌ Қате: {error}")
        
    await state.clear()
