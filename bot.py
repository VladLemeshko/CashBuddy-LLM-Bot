import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from db import init_db
from handlers import routers
from keyboards import main_menu
from tools.fetch_sravni_vklady import fetch_sravni_vklady_html

load_dotenv(".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def update_deposits_periodically():
    while True:
        print("Обновляю данные по вкладам...")
        try:
            fetch_sravni_vklady_html()
        except Exception as e:
            print(f"Ошибка при обновлении вкладов: {e}")
        await asyncio.sleep(60 * 60 * 24)  # 24 часа

async def main():
    await init_db()
    # Сразу обновить при запуске
    fetch_sravni_vklady_html()
    # Запустить задачу в фоне
    asyncio.create_task(update_deposits_periodically())
    for r in routers:
        dp.include_router(r)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
