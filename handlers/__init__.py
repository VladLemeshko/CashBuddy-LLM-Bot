from aiogram import Router, F
from aiogram.types import Message, InputFile, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards import main_menu, transaction_type_kb, income_categories_kb, expense_categories_kb
from db import DB_PATH
import aiosqlite
from gpt import ask_agent
import logging
import re
import matplotlib.pyplot as plt
import tempfile
import os
from datetime import datetime, timedelta

router = Router()

class AddTransaction(StatesGroup):
    type = State()
    category = State()
    amount = State()

class GoalStates(StatesGroup):
    name = State()
    amount = State()
    deadline = State()

class AskAgentState(StatesGroup):
    waiting_for_question = State()

@router.message(F.text == "/menu")
@router.message(F.text == "Меню")
async def show_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

@router.message(F.text == "➕ Добавить доход")
async def add_income_start(message: Message, state: FSMContext):
    await state.update_data(type="income")
    await state.set_state(AddTransaction.category)
    await message.answer("Выберите категорию дохода:", reply_markup=income_categories_kb)

@router.message(F.text == "➖ Добавить расход")
async def add_expense_start(message: Message, state: FSMContext):
    await state.update_data(type="expense")
    await state.set_state(AddTransaction.category)
    await message.answer("Выберите категорию расхода:", reply_markup=expense_categories_kb)

@router.message(AddTransaction.category)
async def input_amount(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return
    data = await state.get_data()
    if data.get("type") == "income" and message.text not in [btn.text for row in income_categories_kb.keyboard for btn in row]:
        await message.answer("Пожалуйста, выберите категорию из списка.")
        return
    if data.get("type") == "expense" and message.text not in [btn.text for row in expense_categories_kb.keyboard for btn in row]:
        await message.answer("Пожалуйста, выберите категорию из списка.")
        return
    await state.update_data(category=message.text)
    await state.set_state(AddTransaction.amount)
    await message.answer("Введите сумму:")

@router.message(AddTransaction.amount)
async def save_transaction(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return
    data = await state.get_data()
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, amount, category, type) VALUES (?, ?, ?, ?)",
            (user_id, amount, data["category"], data["type"])
        )
        await db.commit()
    await state.clear()
    await message.answer("Транзакция успешно добавлена!", reply_markup=main_menu)

@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        balance = row[0] if row[0] is not None else 0
    await message.answer(f"Ваш текущий баланс: <b>{balance:.2f} ₽</b>", parse_mode="HTML")

@router.message(F.text == "📊 Отчёт")
async def show_report(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT category, SUM(amount) FROM transactions WHERE user_id=? AND type='expense' GROUP BY category ORDER BY SUM(amount) DESC", (user_id,))
        rows = await cursor.fetchall()
    if not rows:
        await message.answer("Нет данных о расходах.")
        return
    text = "<b>Траты по категориям:</b>\n"
    for cat, amt in rows:
        text += f"{cat}: <b>{amt:.2f} ₽</b>\n"
    await message.answer(text, parse_mode="HTML")

def beautify_answer(text: str) -> str:
    # Удаляем жирный (**текст** -> текст)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    # Заменяем нумерацию на эмодзи (1. -> 🔹, 2. -> 🔸, 3. -> 🔹 ...)
    lines = text.splitlines()
    emoji_cycle = ["🔹", "🔸", "🔷", "🔶", "🟢", "🟣", "🟠", "🔺", "🔻", "🔵"]
    for i, line in enumerate(lines):
        if re.match(r"^\d+\. ", line):
            emoji = emoji_cycle[i % len(emoji_cycle)]
            lines[i] = re.sub(r"^\d+\. ", f"{emoji} ", line)
    return "\n".join(lines)

# --- Агрегация данных ---
async def aggregate_user_data(user_id):
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        # Средний расход по категориям за месяц
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor = await db.execute("""
            SELECT category, AVG(amount) FROM transactions
            WHERE user_id=? AND type='expense' AND date>=?
            GROUP BY category ORDER BY AVG(amount) DESC
        """, (user_id, month_ago))
        avg_expenses = await cursor.fetchall()
        avg_expenses_str = '\n'.join([f"{cat}: {amt:.2f}₽" for cat, amt in avg_expenses]) or 'нет данных'

        # Самые частые траты
        cursor = await db.execute("""
            SELECT category, COUNT(*) as cnt FROM transactions
            WHERE user_id=? AND type='expense'
            GROUP BY category ORDER BY cnt DESC LIMIT 3
        """, (user_id,))
        frequent = await cursor.fetchall()
        frequent_str = ', '.join([f"{cat} ({cnt} раз)" for cat, cnt in frequent]) or 'нет данных'

        # Прогресс по целям
        cursor = await db.execute("SELECT goal_name, target_amount, current_amount FROM goals WHERE user_id=?", (user_id,))
        goals = await cursor.fetchall()
        goals_str = '\n'.join([f"{g[0]}: {g[2]:.2f}/{g[1]:.2f}₽" for g in goals]) or 'нет целей'

        # Динамика баланса (по дням)
        cursor = await db.execute("""
            SELECT date(date), SUM(CASE WHEN type='income' THEN amount ELSE -amount END) FROM transactions
            WHERE user_id=? GROUP BY date(date) ORDER BY date(date)
        """, (user_id,))
        rows = await cursor.fetchall()
        dates, balances = [], []
        total = 0
        for d, change in rows:
            total += change
            dates.append(d)
            balances.append(total)
        return avg_expenses_str, frequent_str, goals_str, dates, balances

# --- Графики ---
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

# --- Используем агрегацию и графики в советах ---
@router.message(F.text == "💡 Совет GPT")
async def gpt_advice(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT type, category, amount, date FROM transactions WHERE user_id=? ORDER BY date DESC LIMIT 20", (user_id,))
        rows = await cursor.fetchall()
    if not rows:
        await message.answer("Недостаточно данных для анализа. Добавьте хотя бы одну транзакцию.")
        return
    history = "\n".join([f"{r[3][:10]}: {r[0]} {r[1]} {r[2]:.2f}₽" for r in rows])
    await message.answer("🤖 Агент анализирует ваши финансы...", reply_markup=main_menu)
    advice = await ask_agent(history, "", "Дай персональный совет по управлению финансами на основе моей истории.")
    advice = beautify_answer(advice)
    await message.answer(f"<b>Совет от финансового агента:</b>\n{advice}", parse_mode="HTML")

@router.message(F.text == "🎯 Цели")
async def show_goals(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name, target_amount, current_amount, deadline FROM goals WHERE user_id=?", (user_id,))
        goals = await cursor.fetchall()
    if not goals:
        await message.answer("У вас пока нет целей. Хотите создать новую? Напишите название цели или отправьте 'Отмена'.")
        await state.set_state(GoalStates.name)
        return
    text = "<b>Ваши финансовые цели:</b>\n"
    for name, target, current, deadline in goals:
        text += f"• {name}: {current:.2f}/{target:.2f} ₽ (до {deadline})\n"
    text += "\nЧтобы добавить новую цель, напишите её название или отправьте 'Отмена'."
    await message.answer(text, parse_mode="HTML")
    await state.set_state(GoalStates.name)

@router.message(GoalStates.name)
async def goal_set_name(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return
    await state.update_data(goal_name=message.text)
    await state.set_state(GoalStates.amount)
    await message.answer("Введите целевую сумму:")

@router.message(GoalStates.amount)
async def goal_set_amount(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
        return
    await state.update_data(target_amount=amount)
    await state.set_state(GoalStates.deadline)
    await message.answer("Введите дедлайн (например, 2024-12-31):")

@router.message(GoalStates.deadline)
async def goal_set_deadline(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return
    data = await state.get_data()
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)",
            (user_id, data["goal_name"], data["target_amount"], message.text)
        )
        await db.commit()
    await state.clear()
    await message.answer("Цель успешно добавлена!", reply_markup=main_menu)

@router.message(F.text == "💬 Вопрос агенту")
async def ask_agent_start(message: Message, state: FSMContext):
    await state.set_state(AskAgentState.waiting_for_question)
    await message.answer("Задайте любой вопрос вашему финансовому агенту. Например: 'Как мне сэкономить?', 'Стоит ли мне увеличить доход?', 'Как быстрее достичь цели?'\n\nДля отмены отправьте 'Отмена'.")

@router.message(AskAgentState.waiting_for_question)
async def process_agent_question(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=main_menu)
        return
    user_id = message.from_user.id
    # Собираем историю транзакций
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT type, category, amount, date FROM transactions WHERE user_id=? ORDER BY date DESC LIMIT 30", (user_id,))
        transactions = await cursor.fetchall()
        cursor = await db.execute("SELECT goal_name, target_amount, current_amount, deadline FROM goals WHERE user_id=?", (user_id,))
        goals = await cursor.fetchall()
    history = "\n".join([f"{r[3][:10]}: {r[0]} {r[1]} {r[2]:.2f}₽" for r in transactions]) if transactions else "нет данных"
    goals_str = "\n".join([f"{g[0]}: {g[2]:.2f}/{g[1]:.2f}₽ до {g[3]}" for g in goals]) if goals else "нет целей"
    logging.info("[AGENT] История пользователя:\n%s", history)
    logging.info("[AGENT] Цели пользователя:\n%s", goals_str)
    await message.answer("🤖 Агент анализирует ваши финансы и формулирует ответ...", reply_markup=main_menu)
    answer = await ask_agent(history, goals_str, message.text)
    answer = beautify_answer(answer)
    await state.clear()
    await message.answer(f"<b>Ответ агента:</b>\n{answer}", parse_mode="HTML")
