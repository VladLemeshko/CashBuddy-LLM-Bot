from aiogram import Router, F
from aiogram.types import Message, InputFile, FSInputFile
from keyboards import main_menu
from db import DB_PATH
import aiosqlite
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime, timedelta
from keyboards.expense_categories import EXPENSE_CATEGORIES
from keyboards.income_categories import INCOME_CATEGORIES

router = Router()

# show_balance, show_report, plot_balance 

@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        balance = row[0] if row[0] is not None else 0
    await message.answer(f"💰 <b>Ваш текущий баланс:</b> <b>{balance:.2f} ₽</b>\n\nПродолжайте контролировать свои финансы! 🚀", parse_mode="HTML")

@router.message(F.text == "📊 Отчёт")
async def show_report(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT category, SUM(amount) FROM transactions WHERE user_id=? AND type='expense' GROUP BY category ORDER BY SUM(amount) DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
    if not rows:
        await message.answer("📊 Нет данных о расходах. Добавьте расходы, чтобы увидеть отчёт! 🧾")
        return

    total = sum(amt for _, amt in rows)
    max_amt = max(amt for _, amt in rows) if rows else 1
    bar_length = 12  # длина полоски

    text = "<b>📊 Траты по категориям:</b>\n\n"
    colors = ["🟩", "🟦", "🟧", "🟥", "🟪", "🟫", "🟨", "🟧", "🟦", "🟩", "🟫", "🟪"]
    for i, (cat, amt) in enumerate(rows):
        cat_name = EXPENSE_CATEGORIES.get(cat, cat)
        percent = amt / total * 100 if total else 0
        blocks = int(round((amt / max_amt) * bar_length))
        color = colors[i % len(colors)]
        bar = color * blocks
        text += f"{cat_name}: <b>{amt:.2f} ₽</b>\n{bar} {percent:.1f}%\n\n"
    await message.answer(text, parse_mode="HTML")

def plot_balance(dates, balances):
    plt.figure(figsize=(6,3))
    plt.plot(dates, balances, marker='o')
    plt.title('Динамика баланса')
    plt.xlabel('Дата')
    plt.ylabel('Баланс, ₽')
    plt.grid(True)
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.tight_layout()
    plt.savefig(tmpfile.name)
    plt.close()
    return tmpfile.name 