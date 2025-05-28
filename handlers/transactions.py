from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards import income_categories_kb, expense_categories_kb, main_menu
from keyboards.expense_categories import get_expense_categories_inline_keyboard, EXPENSE_CATEGORIES
from keyboards.income_categories import get_income_categories_inline_keyboard, INCOME_CATEGORIES
from keyboards.goals import get_goals_inline_keyboard, get_deposit_quick_inline_kb
from db import DB_PATH
import aiosqlite
from .states import AddTransaction, GoalDepositStates

router = Router()

@router.message(F.text == "➕ Добавить доход")
async def add_income_start(message: Message, state: FSMContext):
    await state.update_data(type="income")
    kb = get_income_categories_inline_keyboard()
    await state.set_state(AddTransaction.category)
    await message.answer("💰 Выберите категорию дохода:", reply_markup=kb)

@router.message(F.text == "➖ Добавить расход")
async def add_expense_start(message: Message, state: FSMContext):
    await state.update_data(type="expense")
    kb = get_expense_categories_inline_keyboard()
    await state.set_state(AddTransaction.category)
    await message.answer("💸 Выберите категорию расхода:", reply_markup=kb)

@router.message(AddTransaction.amount)
async def save_transaction(message: Message, state: FSMContext):
    if message.text == "Отмена":
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректную сумму.")
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
    await message.answer("✅ Транзакция успешно добавлена!", reply_markup=main_menu)

    # --- Автоматическое предложение пополнить цели ---
    if data["type"] == "income":
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT id, goal_name, target_amount, current_amount, deadline, period, strategy_value FROM goals WHERE user_id=?", (user_id,))
            goals = await cursor.fetchall()
        if not goals:
            return
        from datetime import datetime
        today = datetime.now().date()
        offers = []
        for goal in goals:
            goal_id, name, target, current, deadline, period, strategy_value = goal
            deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
            if current >= target:
                continue
            left = max(0, target - current)
            period_l = (period or '').lower()
            if period_l == "ежедневно":
                days_left = (deadline - today).days
                rec = round(left / days_left, 2) if days_left > 0 else left
            elif period_l == "еженедельно":
                weeks_left = max(1, (deadline - today).days // 7)
                rec = round(left / weeks_left, 2)
            else:  # ежемесячно
                months_left = max(1, (deadline.year - today.year) * 12 + (deadline.month - today.month))
                rec = round(left / months_left, 2)
            if rec > 0:
                offers.append((goal_id, name, rec, left))
        if offers:
            kb = get_goals_inline_keyboard([name for _, name, _, _ in offers])
            text = "🎯 У вас есть цели, которые можно пополнить с этого дохода:\nВыберите цель для пополнения или нажмите 'Отмена'."
            await state.set_state(GoalDepositStates.waiting_for_goal)
            await state.update_data(goal_offers=offers)
            await message.answer(text, reply_markup=kb)

@router.message(GoalDepositStates.waiting_for_goal)
async def choose_goal_to_deposit(message: Message, state: FSMContext):
    if message.text.lower() == "нет":
        await state.clear()
        await message.answer("👌 Хорошо! Если захотите пополнить цель — выберите её в разделе целей.", reply_markup=main_menu)
        return
    offers = (await state.get_data()).get("goal_offers", [])
    goal_names = [name for _, name, _, _ in offers]
    if message.text not in goal_names:
        await message.answer("⚠️ Пожалуйста, введите название цели из списка выше или 'Нет'.")
        return
    await state.update_data(selected_goal=message.text)
    # Найти рекомендованную сумму
    rec = None
    for _, name, rec_val, _ in offers:
        if name == message.text:
            rec = rec_val
            break
    await state.set_state(GoalDepositStates.waiting_for_amount)
    await message.answer(f"💰 Введите сумму для пополнения цели <b>{message.text}</b> (рекомендуем: {rec:.2f}₽):", parse_mode="HTML")

@router.message(GoalDepositStates.waiting_for_amount)
async def deposit_goal_amount(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    try:
        value = float(message.text.replace(",", "."))
        if value <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректную сумму для пополнения.")
        return
    data = await state.get_data()
    user_id = message.from_user.id
    goal_name = data.get("selected_goal")
    # Найти goal_id
    offers = data.get("goal_offers", [])
    goal_id = None
    for gid, name, _, _ in offers:
        if name == goal_name:
            goal_id = gid
            break
    if not goal_id:
        await state.clear()
        await message.answer("⚠️ Не удалось найти цель. Попробуйте ещё раз.", reply_markup=main_menu)
        return
    # Обновить накопленное и записать в историю
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE goals SET current_amount = current_amount + ? WHERE id=?", (value, goal_id))
        await db.execute("INSERT INTO goal_deposits (goal_id, user_id, amount, date, source) VALUES (?, ?, ?, DATE('now'), ?) ", (goal_id, user_id, value, "доход"))
        await db.commit()
        # Получить новое значение
        cursor = await db.execute("SELECT current_amount, target_amount FROM goals WHERE id=?", (goal_id,))
        current, target = await cursor.fetchone()
    await state.clear()
    percent = min(100, round(current / target * 100, 1))
    bar = "▓" * int(percent // 10) + "░" * (10 - int(percent // 10))
    await message.answer(f"🎉 Пополнение цели <b>{goal_name}</b> на {value:.2f}₽ успешно!\n\nПрогресс: {current:.2f}/{target:.2f}₽ ({percent}%)\n{bar}", parse_mode="HTML", reply_markup=main_menu)

@router.callback_query(F.data.startswith("expense_cat:"), AddTransaction.category)
async def choose_expense_category(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":", 1)[1]
    category = EXPENSE_CATEGORIES.get(code, code)
    await state.update_data(category=category, type="expense")
    await state.set_state(AddTransaction.amount)
    await call.message.edit_text(f"Вы выбрали категорию. Введите сумму:")

@router.callback_query(F.data == "expense_cat_cancel", AddTransaction.category)
async def cancel_expense_category(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Операция отменена.", reply_markup=main_menu)

@router.message(F.text == "Добавить доход")
async def ask_income_category(message: Message, state: FSMContext):
    categories = ["Зарплата", "Подарок", "Бизнес", "Другое"]
    kb = get_income_categories_inline_keyboard(categories)
    await state.set_state(AddTransaction.category)
    await message.answer("💰 Выберите категорию дохода:", reply_markup=kb)

@router.callback_query(F.data.startswith("income_cat:"), AddTransaction.category)
async def choose_income_category(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":", 1)[1]
    await state.update_data(category=code, type="income")
    await state.set_state(AddTransaction.amount)
    await call.message.edit_text(f"Вы выбрали категорию. Введите сумму:")

@router.callback_query(F.data == "income_cat_cancel", AddTransaction.category)
async def cancel_income_category(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Операция отменена.", reply_markup=main_menu)

# --- Пополнение цели после дохода ---
@router.callback_query(F.data.startswith("goal_select:"), GoalDepositStates.waiting_for_goal)
async def choose_goal_to_deposit_callback(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    offers = data.get("goal_offers", [])
    goal_name = call.data.split(":", 1)[1]
    rec = None
    for _, name, rec_val, _ in offers:
        if name == goal_name:
            rec = rec_val
            break
    await state.update_data(selected_goal=goal_name)
    await state.set_state(GoalDepositStates.waiting_for_amount)
    kb = get_deposit_quick_inline_kb(rec)
    await call.message.edit_text(f"💰 Введите сумму для пополнения цели <b>{goal_name}</b> или выберите быстрый вариант:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("deposit:"), GoalDepositStates.waiting_for_amount)
async def deposit_goal_quick_amount(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    goal_name = data.get("selected_goal")
    offers = data.get("goal_offers", [])
    goal_id = None
    for gid, name, _, _ in offers:
        if name == goal_name:
            goal_id = gid
            break
    if not goal_id:
        await state.clear()
        await call.message.edit_text("⚠️ Не удалось найти цель. Попробуйте ещё раз.", reply_markup=main_menu)
        return
    value_str = call.data.split(":", 1)[1]
    if value_str == "custom":
        await call.message.edit_text(f"Введите свою сумму для пополнения цели <b>{goal_name}</b>:", parse_mode="HTML")
        return
    try:
        value = float(value_str)
        if value <= 0:
            raise ValueError
    except ValueError:
        await call.message.edit_text("⚠️ Пожалуйста, введите корректную сумму для пополнения.")
        return
    user_id = call.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE goals SET current_amount = current_amount + ? WHERE id=?", (value, goal_id))
        await db.execute("INSERT INTO goal_deposits (goal_id, user_id, amount, date, source) VALUES (?, ?, ?, DATE('now'), ?) ", (goal_id, user_id, value, "доход"))
        await db.commit()
        cursor = await db.execute("SELECT current_amount, target_amount FROM goals WHERE id=?", (goal_id,))
        current, target = await cursor.fetchone()
    await state.clear()
    await call.message.edit_text(f"🎉 Пополнение цели <b>{goal_name}</b> на {value:.2f}₽ успешно!", parse_mode="HTML")

@router.message(GoalDepositStates.waiting_for_amount)
async def deposit_goal_custom_amount(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
        if value <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректную сумму для пополнения.")
        return
    data = await state.get_data()
    goal_name = data.get("selected_goal")
    offers = data.get("goal_offers", [])
    goal_id = None
    for gid, name, _, _ in offers:
        if name == goal_name:
            goal_id = gid
            break
    if not goal_id:
        await state.clear()
        await message.answer("⚠️ Не удалось найти цель. Попробуйте ещё раз.", reply_markup=main_menu)
        return
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE goals SET current_amount = current_amount + ? WHERE id=?", (value, goal_id))
        await db.execute("INSERT INTO goal_deposits (goal_id, user_id, amount, date, source) VALUES (?, ?, ?, DATE('now'), ?) ", (goal_id, user_id, value, "доход"))
        await db.commit()
        cursor = await db.execute("SELECT current_amount, target_amount FROM goals WHERE id=?", (goal_id,))
        current, target = await cursor.fetchone()
    await state.clear()
    await message.answer(f"🎉 Пополнение цели <b>{goal_name}</b> на {value:.2f}₽ успешно!", parse_mode="HTML", reply_markup=main_menu) 