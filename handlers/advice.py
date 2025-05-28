from aiogram import Router, F
from aiogram.types import Message
from keyboards import main_menu
from db import DB_PATH
import aiosqlite
from gpt import ask_agent
from .utils import beautify_answer
from keyboards.expense_categories import EXPENSE_CATEGORIES

router = Router()

# gpt_advice 

async def build_user_context(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        # Баланс
        cursor = await db.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        balance = row[0] if row and row[0] is not None else 0
        # Цели
        cursor = await db.execute("SELECT goal_name, target_amount, current_amount, deadline, period, strategy_value, priority FROM goals WHERE user_id=?", (user_id,))
        goals = await cursor.fetchall()
        goals_text = ""
        for name, target, current, deadline, period, strategy, prio in goals:
            percent = int(min(100, (current / target) * 100)) if target else 0
            goals_text += f"• {name}: {current:.0f}/{target:.0f}₽ ({percent}%), до {deadline}\n"
        # Траты по категориям
        cursor = await db.execute("SELECT category, SUM(amount) FROM transactions WHERE user_id=? AND type='expense' GROUP BY category ORDER BY SUM(amount) DESC", (user_id,))
        rows = await cursor.fetchall()
        expenses_text = ""
        for cat, amt in rows:
            cat_name = EXPENSE_CATEGORIES.get(cat, cat)
            expenses_text += f"{cat_name}: {amt:.0f}₽\n"
    context = (
        f"Баланс: {balance:.2f}₽\n"
        f"Цели:\n{goals_text or 'Нет целей'}\n"
        f"Траты по категориям:\n{expenses_text or 'Нет трат'}"
    )
    return context

@router.message(F.text == "💡 Совет GPT")
async def gpt_advice(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT type, category, amount, date FROM transactions WHERE user_id=? ORDER BY date DESC LIMIT 20", (user_id,))
        rows = await cursor.fetchall()
    if not rows:
        await message.answer("😕 Недостаточно данных для анализа. Добавьте хотя бы одну транзакцию, чтобы получить совет! 💡")
        return
    history = "\n".join([f"{r[3][:10]}: {r[0]} {r[1]} {r[2]:.2f}₽" for r in rows])
    user_context = await build_user_context(user_id)
    await message.answer("🤖 Агент анализирует ваши финансы... Пожалуйста, подождите пару секунд! ⏳", reply_markup=main_menu)
    advice = await ask_agent(history, user_context, "Дай персональный совет по управлению финансами на основе моей истории и текущего состояния.")
    advice = beautify_answer(advice)
    await message.answer(f"<b>✨ Совет от финансового агента:</b>\n{advice}\n\n🌱 Удачи в достижении ваших целей!", parse_mode="HTML") 