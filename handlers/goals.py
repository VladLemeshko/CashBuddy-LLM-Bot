from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards import main_menu, period_kb, confirm_amount_kb
from keyboards.goals import get_goals_inline_keyboard, get_deposit_quick_inline_kb, get_goals_delete_inline_keyboard, get_goals_edit_inline_keyboard, get_confirm_inline_keyboard, format_goal_pretty, get_goals_action_inline_keyboard, get_goal_manage_inline_keyboard, get_goal_edit_field_inline_keyboard, get_goals_list_inline_keyboard
from db import DB_PATH
import aiosqlite
from .states import GoalStates, GoalDepositStates
from datetime import datetime, timedelta

router = Router()

# Клавиатура с кнопкой возврата в главное меню
def get_menu_with_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

@router.message(F.text == "🎯 Цели")
async def show_goals(message: Message, state: FSMContext):
    user_id = message.from_user.id
    print(f"DEBUG: Пользователь {user_id} запросил цели")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name, target_amount, current_amount, deadline, period, strategy_value, priority FROM goals WHERE user_id=?", (user_id,))
        goals = await cursor.fetchall()
        print(f"DEBUG: Найдено целей для пользователя {user_id}: {len(goals)}")
        
        # Подробная информация о каждой цели
        for i, goal in enumerate(goals):
            name, target, current, deadline, period, strategy, priority = goal
            percent = int(min(100, (current / target) * 100)) if target else 0
            print(f"DEBUG: Цель {i+1}: {name} - {current}/{target}₽ ({percent}%)")
        
        # Проверяем все цели в базе
        cursor = await db.execute("SELECT user_id, goal_name, current_amount, target_amount FROM goals")
        all_goals = await cursor.fetchall()
        print(f"DEBUG: Всего целей в базе: {len(all_goals)}")
        for g in all_goals:
            print(f"DEBUG: User {g[0]}, Goal: {g[1]}, Current: {g[2]}, Target: {g[3]}")
    
    kb = get_goals_list_inline_keyboard(goals)
    await message.answer("Выберите цель для управления или добавьте новую:", reply_markup=kb)

@router.message(F.text == "🏠 Вернуться в главное меню")
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Вы вернулись в главное меню", reply_markup=main_menu)

@router.callback_query(F.data == "goal_add_new")
async def goal_add_new(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите название новой цели:")
    
    await state.set_state(GoalStates.name)

@router.callback_query(F.data.startswith("goal_action:"))
async def goal_action_select(call: CallbackQuery, state: FSMContext):
    goal_name = call.data.split(":", 1)[1].strip()
    await state.update_data(selected_goal=goal_name)
    kb = get_goal_manage_inline_keyboard(goal_name)
    await call.message.edit_text(f"Что вы хотите сделать с целью <b>{goal_name}</b>?", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("goal_manage:deposit:"))
async def goal_manage_deposit(call: CallbackQuery, state: FSMContext):
    goal_name = call.data.split(":", 2)[2].strip()
    await state.update_data(selected_goal=goal_name)
    await call.message.edit_text(f"💰 Введите сумму для пополнения цели <b>{goal_name}</b>:", parse_mode="HTML")
    await state.set_state(GoalDepositStates.waiting_for_amount)

@router.callback_query(F.data.startswith("goal_manage:edit:"))
async def goal_manage_edit(call: CallbackQuery, state: FSMContext):
    goal_name = call.data.split(":", 2)[2]
    await state.update_data(selected_goal=goal_name)
    kb = get_goal_edit_field_inline_keyboard(goal_name)
    await call.message.edit_text(f"Что вы хотите изменить в цели <b>{goal_name}</b>?", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_goal_field:"))
async def edit_goal_field(call: CallbackQuery, state: FSMContext):
    field = call.data.split(":", 1)[1]
    await state.update_data(edit_field=field)
    prompts = {"name": "Введите новое название:", "deadline": "Введите новый дедлайн (ГГГГ-ММ-ДД):", "amount": "Введите новую целевую сумму:"}
    await call.message.edit_text(prompts[field])
    await state.set_state(GoalStates.edit_confirm_amount)

@router.message(GoalStates.edit_confirm_amount)
async def save_edited_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    goal_name = data.get("selected_goal")
    field = data.get("edit_field")
    user_id = message.from_user.id
    value = message.text.strip()
    async with aiosqlite.connect(DB_PATH) as db:
        if field == "name":
            await db.execute("UPDATE goals SET goal_name=? WHERE user_id=? AND goal_name=?", (value, user_id, goal_name))
        elif field == "deadline":
            await db.execute("UPDATE goals SET deadline=? WHERE user_id=? AND goal_name=?", (value, user_id, goal_name))
        elif field == "amount":
            try:
                value = float(value.replace(",", "."))
            except ValueError:
                await message.answer("⚠️ Пожалуйста, введите корректную сумму.")
                return
            await db.execute("UPDATE goals SET target_amount=? WHERE user_id=? AND goal_name=?", (value, user_id, goal_name))
        await db.commit()
    await state.clear()
    await message.answer("✅ Цель успешно обновлена!", reply_markup=main_menu)

@router.callback_query(F.data.startswith("goal_manage:delete:"))
async def goal_manage_delete(call: CallbackQuery, state: FSMContext):
    goal_name = call.data.split(":", 2)[2]
    user_id = call.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM goals WHERE user_id=? AND goal_name=?", (user_id, goal_name))
        await db.commit()
    await state.clear()
    await call.message.edit_text(f"🗑️ Цель <b>{goal_name}</b> удалена!", parse_mode="HTML")

@router.callback_query(F.data == "goal_manage:back")
async def goal_manage_back(call: CallbackQuery, state: FSMContext):
    # Возврат к списку целей
    await show_goals(call.message, state)

@router.message(GoalStates.name)
async def goal_set_name(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    await state.update_data(goal_name=message.text)
    await state.set_state(GoalStates.amount)
    await message.answer("💰 Введите целевую сумму:", reply_markup=get_menu_with_back_keyboard())

@router.message(GoalStates.amount)
async def goal_set_amount(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректную сумму.")
        return
    await state.update_data(target_amount=amount)
    await state.set_state(GoalStates.deadline)
    today = datetime.now().strftime("%Y-%m-%d")
    await message.answer(f"📅 Введите дедлайн (например, {today}):", reply_markup=get_menu_with_back_keyboard())

@router.message(GoalStates.deadline)
async def goal_set_deadline(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    await state.update_data(deadline=message.text)
    await state.set_state(GoalStates.period)
    await message.answer(
        "🔄 Какой способ накопления вам удобнее?",
        reply_markup=period_kb
    )

@router.message(GoalStates.period)
async def goal_set_period(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    period = message.text.strip().lower()
    if period not in ["ежедневно", "еженедельно", "ежемесячно"]:
        await message.answer("⚠️ Пожалуйста, выберите: ежедневно, еженедельно или ежемесячно.")
        return
    data = await state.get_data()
    # Расчёт количества периодов до дедлайна
    try:
        deadline = datetime.strptime(data["deadline"], "%Y-%m-%d")
    except Exception:
        await message.answer("⚠️ Некорректный формат даты. Введите дедлайн (например, 2024-12-31):")
        await state.set_state(GoalStates.deadline)
        return
    today = datetime.now()
    if deadline <= today:
        await message.answer("⚠️ Дедлайн должен быть в будущем. Введите корректную дату:")
        await state.set_state(GoalStates.deadline)
        return
    total = float(data["target_amount"])
    if period == "ежедневно":
        periods = (deadline - today).days
    elif period == "еженедельно":
        periods = max(1, (deadline - today).days // 7)
    else:
        periods = max(1, (deadline.year - today.year) * 12 + (deadline.month - today.month))
    if periods < 1:
        periods = 1
    amount_per_period = round(total / periods, 2)
    await state.update_data(period=period)
    await state.update_data(calc_amount=amount_per_period)
    await state.set_state(GoalStates.confirm_amount)
    await message.answer(
        f"📈 Чтобы достичь цели к {data['deadline']}, нужно откладывать по <b>{amount_per_period:.2f}₽</b> {period}. Оставить это значение?",
        reply_markup=confirm_amount_kb,
        parse_mode="HTML"
    )

@router.message(GoalStates.confirm_amount)
async def goal_confirm_amount(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    data = await state.get_data()
    recommended = data["calc_amount"]
    period = data["period"]
    deadline_str = data["deadline"]
    total = float(data["target_amount"])
    from datetime import datetime, timedelta
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
    except Exception:
        await message.answer("⚠️ Некорректный формат даты. Введите дедлайн (например, 2024-12-31):")
        await state.set_state(GoalStates.deadline)
        return
    today = datetime.now()
    # Пользователь подтверждает рекомендованную сумму
    if message.text.lower() in ["да", "ок", "yes"]:
        await state.update_data(strategy_value=recommended)
        await state.set_state(GoalStates.priority)
        await message.answer("🎯 Выберите приоритет цели (1-5, где 1 - самый высокий):", reply_markup=get_menu_with_back_keyboard())
    else:
        try:
            custom_amount = float(message.text.replace(",", "."))
            await state.update_data(strategy_value=custom_amount)
            await state.set_state(GoalStates.priority)
            await message.answer("🎯 Выберите приоритет цели (1-5, где 1 - самый высокий):", reply_markup=get_menu_with_back_keyboard())
        except ValueError:
            await message.answer("⚠️ Пожалуйста, введите корректную сумму или 'Да' для подтверждения.")

@router.message(GoalStates.priority)
async def goal_set_priority(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    try:
        priority = int(message.text)
        if priority < 1 or priority > 5:
            await message.answer("⚠️ Приоритет должен быть от 1 до 5.")
            return
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число от 1 до 5.")
        return
    data = await state.get_data()
    user_id = message.from_user.id
    print(f"DEBUG: Создание цели для пользователя {user_id}")
    print(f"DEBUG: Данные цели: {data}")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем, есть ли пользователь
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        user_exists = await cursor.fetchone()
        if not user_exists:
            print(f"DEBUG: Создаем пользователя {user_id}")
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()
        
        await db.execute(
            "INSERT INTO goals (user_id, goal_name, target_amount, deadline, period, strategy_value, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, data["goal_name"], data["target_amount"], data["deadline"], data["period"], data["strategy_value"], priority)
        )
        await db.commit()
        print(f"DEBUG: Цель успешно создана для пользователя {user_id}")
    await state.clear()
    await message.answer("✅ Цель успешно создана!", reply_markup=main_menu)

@router.message(F.text == "Пополнить цель")
async def ask_goal_to_deposit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name FROM goals WHERE user_id=?", (user_id,))
        goals = [row[0] for row in await cursor.fetchall()]
    if not goals:
        await message.answer("У вас нет целей для пополнения.", reply_markup=main_menu)
        return
    kb = get_goals_inline_keyboard(goals)
    await state.set_state(GoalDepositStates.waiting_for_goal)
    await message.answer("💡 Выберите цель для пополнения:", reply_markup=kb)

@router.callback_query(F.data.startswith("goal_select:"), GoalDepositStates.waiting_for_goal)
async def choose_goal_to_deposit_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    goal_name = call.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, goal_name, target_amount, current_amount, deadline, period, strategy_value FROM goals WHERE user_id=? AND goal_name=?", (user_id, goal_name))
        goal = await cursor.fetchone()
    if not goal:
        await call.message.edit_text("⚠️ Цель не найдена. Выберите из списка.")
        return
    goal_id, name, target, current, deadline, period, strategy_value = goal
    from datetime import datetime
    today = datetime.now().date()
    left = max(0, target - current)
    period_l = (period or '').lower()
    if period_l == "ежедневно":
        days_left = (datetime.strptime(deadline, "%Y-%m-%d").date() - today).days
        rec = round(left / days_left, 2) if days_left > 0 else left
    elif period_l == "еженедельно":
        weeks_left = max(1, (datetime.strptime(deadline, "%Y-%m-%d").date() - today).days // 7)
        rec = round(left / weeks_left, 2)
    else:
        months_left = max(1, (datetime.strptime(deadline, "%Y-%m-%d").date().year - today.year) * 12 + (datetime.strptime(deadline, "%Y-%m-%d").date().month - today.month))
        rec = round(left / months_left, 2)
    await state.set_state(GoalDepositStates.waiting_for_amount)
    await state.update_data(selected_goal=goal_name, goal_id=goal_id, target=target, current=current)
    kb = get_deposit_quick_inline_kb(rec)
    await call.message.edit_text(f"💰 Введите сумму для пополнения цели <b>{goal_name}</b> или выберите быстрый вариант:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("goal_cancel"), GoalDepositStates.waiting_for_goal)
async def cancel_goal_deposit(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Операция отменена.", reply_markup=main_menu)

@router.message(F.text == "История цели")
async def ask_goal_for_history(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name FROM goals WHERE user_id=?", (user_id,))
        goals = [row[0] for row in await cursor.fetchall()]
    if not goals:
        await message.answer("У вас нет целей.", reply_markup=main_menu)
        return
    kb = get_goals_inline_keyboard(goals)
    await state.set_state(GoalDepositStates.waiting_for_goal)
    await message.answer("📖 Выберите цель для просмотра истории:", reply_markup=kb)

@router.callback_query(F.data.startswith("goal_history:"), GoalDepositStates.waiting_for_goal)
async def show_goal_history(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    goal_name = call.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM goals WHERE user_id=? AND goal_name=?", (user_id, goal_name))
        row = await cursor.fetchone()
        if not row:
            await call.message.edit_text("⚠️ Цель не найдена.")
            return
        goal_id = row[0]
        cursor = await db.execute("SELECT amount, date, source FROM goal_deposits WHERE goal_id=? ORDER BY date DESC", (goal_id,))
        deposits = await cursor.fetchall()
    if not deposits:
        await call.message.edit_text("ℹ️ Для этой цели ещё не было пополнений.")
        return
    text = f"<b>История пополнений для цели {goal_name}:</b>\n"
    for amount, date, source in deposits:
        text += f"{date}: +{amount:.2f}₽ ({source})\n"
    await call.message.edit_text(text, parse_mode="HTML")

@router.message(F.text == "Удалить цель")
async def ask_goal_to_delete(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name FROM goals WHERE user_id=?", (user_id,))
        goals = [row[0] for row in await cursor.fetchall()]
    if not goals:
        await message.answer("У вас нет целей для удаления.", reply_markup=main_menu)
        return
    kb = get_goals_delete_inline_keyboard(goals)
    await state.set_state(GoalDepositStates.waiting_for_goal)
    await message.answer("🗑️ Выберите цель для удаления:", reply_markup=kb)

@router.callback_query(F.data.startswith("goal_delete:"), GoalDepositStates.waiting_for_goal)
async def confirm_goal_delete(call: CallbackQuery, state: FSMContext):
    goal_name = call.data.split(":", 1)[1]
    await state.update_data(goal_to_delete=goal_name)
    kb = get_confirm_inline_keyboard()
    await call.message.edit_text(f"Вы уверены, что хотите удалить цель <b>{goal_name}</b>?", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "confirm_yes", GoalDepositStates.waiting_for_goal)
async def do_goal_delete(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    goal_name = data.get("goal_to_delete")
    user_id = call.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM goals WHERE user_id=? AND goal_name=?", (user_id, goal_name))
        await db.commit()
    await state.clear()
    await call.message.edit_text(f"✅ Цель <b>{goal_name}</b> удалена!", reply_markup=main_menu, parse_mode="HTML")

@router.callback_query(F.data == "confirm_no", GoalDepositStates.waiting_for_goal)
async def cancel_goal_delete(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Удаление отменено.", reply_markup=main_menu)

@router.message(F.text == "Редактировать цель")
async def ask_goal_to_edit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name FROM goals WHERE user_id=?", (user_id,))
        goals = [row[0] for row in await cursor.fetchall()]
    if not goals:
        await message.answer("У вас нет целей для редактирования.", reply_markup=main_menu)
        return
    kb = get_goals_edit_inline_keyboard(goals)
    await state.set_state(GoalDepositStates.waiting_for_goal)
    await message.answer("✏️ Выберите цель для редактирования:", reply_markup=kb)

@router.message(GoalDepositStates.waiting_for_amount)
async def deposit_goal_custom_amount(message: Message, state: FSMContext):
    if message.text.lower() in ["отмена", "🏠 вернуться в главное меню"]:
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректную сумму.")
        return
    data = await state.get_data()
    goal_name = data.get("selected_goal")
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем goal_id
        cursor = await db.execute("SELECT id, current_amount FROM goals WHERE user_id=? AND goal_name=?", (user_id, goal_name))
        goal_data = await cursor.fetchone()
        if goal_data:
            goal_id, current_amount = goal_data
            new_amount = current_amount + amount
            # Обновляем текущую сумму цели
            await db.execute("UPDATE goals SET current_amount=? WHERE id=?", (new_amount, goal_id))
            # Записываем пополнение
            await db.execute("INSERT INTO goal_deposits (goal_id, user_id, amount, date, source) VALUES (?, ?, ?, ?, ?)", 
                           (goal_id, user_id, amount, datetime.now().strftime("%Y-%m-%d"), "manual"))
            await db.commit()
            await state.clear()
            await message.answer(f"✅ Цель <b>{goal_name}</b> пополнена на {amount:.2f}₽! Текущая сумма: {new_amount:.2f}₽", 
                               parse_mode="HTML", reply_markup=main_menu)
        else:
            await message.answer("❌ Цель не найдена.", reply_markup=main_menu)
            await state.clear()

# Красивый вывод целей
async def pretty_goals_list(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT goal_name, current_amount, target_amount, deadline, period, strategy_value, priority FROM goals WHERE user_id=?", (user_id,))
        goals = await cursor.fetchall()
    if not goals:
        return "У вас пока нет целей. Добавьте первую!"
    text = "🎯 Ваши цели:\n"
    for name, current, target, deadline, period, strategy_value, priority in goals:
        text += format_goal_pretty(name, current, target, deadline, period, strategy_value, priority) + "\n\n"
    return text 