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

load_dotenv(".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я — твой финансовый помощник. Помогу вести учёт доходов и расходов, анализировать траты и достигать финансовых целей!\n\nИспользуй меню для начала работы.",
        reply_markup=main_menu
    )

async def main():
    await init_db()
    for r in routers:
        dp.include_router(r)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
