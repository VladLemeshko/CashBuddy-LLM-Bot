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
from tools.deposit_parser import get_best_deposits

router = Router()

class AgentDialogState(StatesGroup):
    active = State()

@router.message(F.text == "🤖 Агент")
async def start_agent_dialog(message: Message, state: FSMContext):
    await state.set_state(AgentDialogState.active)
    await message.answer("Вы в диалоге с финансовым агентом! Просто напишите свой вопрос или опишите ситуацию. Для выхода отправьте 'Отмена' или нажмите любую кнопку главного меню.")

@router.message(AgentDialogState.active)
async def agent_dialog(message: Message, state: FSMContext):
    if (message.text.lower() == "отмена" or 
        message.text == "➕ Добавить доход" or
        message.text == "➖ Добавить расход" or
        message.text == "💰 Баланс" or
        message.text == "📊 Отчёт" or
        message.text == "🎯 Цели" or
        message.text == "📈 Инвестиции" or
        message.text == "💳 Кредиты"):
        await state.clear()
        await message.answer("❌ Диалог с агентом завершён.", reply_markup=main_menu)
        
        # Вызываем соответствующие обработчики
        if message.text == "➕ Добавить доход":
            from .transactions import add_income_start
            await add_income_start(message, state)
        elif message.text == "➖ Добавить расход":
            from .transactions import add_expense_start
            await add_expense_start(message, state)
        elif message.text == "💰 Баланс":
            from .report import show_balance
            await show_balance(message)
        elif message.text == "📊 Отчёт":
            from .report import show_report
            await show_report(message)
        elif message.text == "🎯 Цели":
            from .goals import show_goals
            await show_goals(message, state)
        elif message.text == "📈 Инвестиции":
            from .investments import investments_menu_handler
            await investments_menu_handler(message)
        elif message.text == "💳 Кредиты":
            from .credits import credits_menu
            await credits_menu(message, state)
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
    import sys
    sys.path.append("./tools")
    from tools.crypto_rates import get_crypto_rates
    from tools.stock_movers import get_top_us_movers, get_top_ru_movers
    from tools.deposit_parser import get_best_deposits
    import asyncio
    import concurrent.futures
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Финансовый профиль
        cursor = await db.execute("SELECT income_type, monthly_income, has_deposits, deposit_bank, deposit_interest, deposit_amount, deposit_term, deposit_date, has_loans, loans_total, loans_interest, has_investments, investments_amount, investments_profit, financial_mood, has_regular_payments, regular_payments_list FROM user_profiles WHERE user_id=?", (user_id,))
        profile = await cursor.fetchone()
        profile_text = ""
        deposit_analysis = ""
        if profile:
            (
                income_type, monthly_income, has_deposits, deposit_bank, deposit_interest, deposit_amount, deposit_term, deposit_date,
                has_loans, loans_total, loans_interest, has_investments, investments_amount, investments_profit, financial_mood,
                has_regular_payments, regular_payments_list
            ) = profile
            profile_text = (
                f"<b>Профиль пользователя:</b>\n"
                f"• Источник дохода: {income_type or '—'}\n"
                f"• Доход в месяц: {monthly_income if monthly_income is not None else '—'}₽\n"
                f"• Вклады: {'Да' if has_deposits else 'Нет'}"
            )
            if has_deposits:
                profile_text += f"\n  Банк: {deposit_bank or '—'}\n  Ставка: {deposit_interest or '—'}%\n  Сумма: {deposit_amount or '—'}₽\n  Срок: {deposit_term or '—'}\n  Дата открытия: {deposit_date or '—'}\n"
                # Сравнение с топ-5 рыночными вкладами
                try:
                    best_deposits = get_best_deposits()
                    best = sorted(best_deposits, key=lambda d: float(str(d['Доходность']).replace('%','').replace(',','.')), reverse=True)[:5]
                    deposits_block = "<b>Топ-5 вкладов на рынке:</b>\n"
                    for i, d in enumerate(best, 1):
                        deposits_block += f"{i}. {d['Банк']} — {d['Доходность']}, {d['Срок']}, мин. {d['Мин. сумма']}\n"
                    deposit_analysis = (f"\n{deposits_block}\n"
                        "Сравни мой вклад с этими предложениями и дай совет: где условия лучше, стоит ли менять вклад, на что обратить внимание.\n")
                except Exception as e:
                    deposit_analysis = ""
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
        
        # Кредитные заявки
        cursor = await db.execute("SELECT age, marital_status, housing, loan, job_category, education, duration, campaign, credit_probability, created_at FROM credit_applications WHERE user_id=? ORDER BY created_at DESC LIMIT 3", (user_id,))
        credit_applications = await cursor.fetchall()
        credit_text = ""
        if credit_applications:
            credit_text = "\n<b>Кредитные заявки:</b>\n"
            for i, app in enumerate(credit_applications, 1):
                age, marital, housing, loan, job, education, amount, term, prob, date = app
                marital_text = "Женат/замужем" if marital else "Холост/не замужем"
                housing_text = "Да" if housing else "Нет"
                loan_text = "Да" if loan else "Нет"
                credit_text += f"{i}. {date[:10]}: {prob}% одобрения\n"
                credit_text += f"   Возраст: {age}, {marital_text}, Жилье: {housing_text}\n"
                credit_text += f"   Профессия: {job}, Образование: {education}\n"
                credit_text += f"   Сумма: {amount:,}₽, Срок: {term} мес.\n\n"
    # --- ДОБАВЛЯЕМ АКТУАЛЬНЫЕ ДАННЫЕ РЫНКА ---
    def get_market_data_sync():
        crypto = get_crypto_rates()
        us = get_top_us_movers(["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"], 3)
        ru = get_top_ru_movers(3)
        deposits = get_best_deposits()
        return crypto, us, ru, deposits
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        crypto, us, ru, deposits = await loop.run_in_executor(pool, get_market_data_sync)
    # Формируем текст для LLM
    market_text = "\n<b>Актуальные данные рынка:</b>\n"
    market_text += "\n<b>Курсы криптовалют:</b>\n"
    for c in crypto:
        market_text += f"• {c['name']}: ${c['usd']} (₽{c['rub']})\n"
    market_text += "\n<b>Топ-3 акции США:</b>\n"
    for ticker, change in us:
        emoji = "🟢" if change > 0 else "🔴"
        market_text += f"• {emoji} {ticker}: {change:+.2f}%\n"
    market_text += "\n<b>Топ-3 акции РФ:</b>\n"
    for ticker, change in ru:
        emoji = "🟢" if change > 0 else "🔴"
        market_text += f"• {emoji} {ticker}: {change:+.2f}%\n"
    market_text += "\n<b>Лучшие вклады:</b>\n"
    for d in deposits[:3]:
        market_text += f"• {d['Банк']}: {d['Доходность']}, {d['Срок']}, мин. {d['Мин. сумма']}\n"
    # ---
    context = (
        (profile_text or "") +
        (deposit_analysis or "") +
        f"Баланс: {balance:.2f}₽\n"
        f"Цели:\n{goals_text or 'Нет целей'}\n"
        f"Траты по категориям:\n{expenses_text or 'Нет трат'}\n"
        + credit_text
        + market_text
    )
    return context 