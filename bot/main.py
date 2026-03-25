import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from handlers import router
from api_client import APIClient
from database import Database

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
BASE_URL = os.getenv("API_BASE_URL")
MARGIN = float(os.getenv("MARGIN", 1.20))

async def poll_orders(bot: Bot, api: APIClient, db: Database):
    while True:
        orders = await db.get_pending_orders()
        for db_id, user_id, api_id in orders:
            status_data = await api.get_order_status(api_id)
            if status_data.get("success"):
                new_status = status_data["order"]["status"]
                if new_status == "completed":
                    await db.update_order_status(db_id, "completed")
                    await bot.send_message(user_id, "✅ Тапсырысыңыз дайын! / Ваш заказ готов!")
                elif new_status == "failed":
                    await db.update_order_status(db_id, "failed")
                    await bot.send_message(user_id, "❌ Тапсырыс орындалмады. / Ошибка выполнения заказа.")
        await asyncio.sleep(60) # 1 минут сайын тексеру

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    db = Database()
    await db.setup()
    
    api = APIClient(base_url=BASE_URL, token=API_TOKEN, margin=MARGIN)
    
    dp.include_router(router)
    dp["api"] = api
    dp["db"] = db
    
    # Фондық тапсырманы іске қосу
    asyncio.create_task(poll_orders(bot, api, db))
    
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
