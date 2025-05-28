from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards import main_menu
from gpt import ask_agent
from .utils import beautify_answer
from keyboards.expense_categories import EXPENSE_CATEGORIES
import aiosqlite
from aiogram.fsm.state import StatesGroup, State
from db import DB_PATH
from aiogram.types import CallbackQuery

router = Router()

class AgentDialogState(StatesGroup):
    active = State()

@router.message(F.text == "🤖 Агент")
async def start_agent_dialog(message: Message, state: FSMContext):
    await state.set_state(AgentDialogState.active)
    await message.answer("Вы в диалоге с финансовым агентом! Просто напишите свой вопрос или опишите ситуацию. Для выхода отправьте 'Отмена'.")

@router.message(AgentDialogState.active)
async def agent_dialog(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Диалог с агентом завершён.", reply_markup=main_menu)
        return
    user_id = message.from_user.id
    # Формируем историю транзакций с датами
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT type, category, amount, date FROM transactions WHERE user_id=? ORDER BY date DESC LIMIT 30",
            (user_id,)
        )
        transactions = await cursor.fetchall()
    history = "\n".join([f"{r[3][:10]}: {r[0]} {r[1]} {r[2]:.2f}₽" for r in transactions]) if transactions else "нет данных"
    user_context = await build_user_context(user_id)
    answer = await ask_agent(history, user_context, message.text)
    answer = beautify_answer(answer)
    await message.answer(f"<b>🤖 Агент:</b>\n{answer}", parse_mode="HTML")

@router.callback_query(F.data == "stop_agent_chat", AgentDialogState.active)
async def stop_agent_chat(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Диалог с агентом завершён.", reply_markup=main_menu)

async def build_user_context(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        # Финансовый профиль
        cursor = await db.execute("SELECT income_type, monthly_income, has_deposits, deposit_interest, deposit_amount, has_loans, loans_total, loans_interest, has_investments, investments_amount, investments_profit, financial_mood FROM user_profiles WHERE user_id=?", (user_id,))
        profile = await cursor.fetchone()
        profile_text = ""
        if profile:
            income_type, monthly_income, has_deposits, deposit_interest, deposit_amount, has_loans, loans_total, loans_interest, has_investments, investments_amount, investments_profit, financial_mood = profile
            profile_text = (
                f"<b>Профиль пользователя:</b>\n"
                f"• Источник дохода: {income_type or '—'}\n"
                f"• Доход в месяц: {monthly_income if monthly_income is not None else '—'}₽\n"
                f"• Вклады: {'Да' if has_deposits else 'Нет'}"
            )
            if has_deposits:
                profile_text += f" ({deposit_interest or '—'}% годовых, {deposit_amount or '—'}₽)\n"
            else:
                profile_text += "\n"
            profile_text += f"• Кредиты: {'Да' if has_loans else 'Нет'}"
            if has_loans:
                profile_text += f" ({loans_total or '—'}₽, {loans_interest or '—'}% годовых)\n"
            else:
                profile_text += "\n"
            profile_text += f"• Инвестиции: {'Да' if has_investments else 'Нет'}"
            if has_investments:
                profile_text += f" ({investments_amount or '—'}₽, доходность {investments_profit or '—'}%)\n"
            else:
                profile_text += "\n"
            profile_text += f"• Финансовое настроение: {financial_mood or '—'}\n\n"
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
        (profile_text or "") +
        f"Баланс: {balance:.2f}₽\n"
        f"Цели:\n{goals_text or 'Нет целей'}\n"
        f"Траты по категориям:\n{expenses_text or 'Нет трат'}"
    )
    return context 