from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

def get_goals_inline_keyboard(goals):
    keyboard = [
        [InlineKeyboardButton(text=goal, callback_data=f"goal_select:{goal}")]
        for goal in goals
    ]
    keyboard.append([InlineKeyboardButton(text="Отмена", callback_data="goal_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_deposit_quick_inline_kb(rec):
    keyboard = [
        [InlineKeyboardButton(text=f"{rec:.2f}", callback_data=f"deposit:{rec:.2f}")],
        [
            InlineKeyboardButton(text=f"{rec/2:.2f}", callback_data=f"deposit:{rec/2:.2f}"),
            InlineKeyboardButton(text="Своя сумма", callback_data="deposit:custom")
        ],
        [InlineKeyboardButton(text="Отмена", callback_data="deposit:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_progress_bar(percent, length=20):
    filled = round(percent / 100 * length)
    return "▓" * filled + "░" * (length - filled)

def get_goals_delete_inline_keyboard(goals):
    keyboard = [
        [InlineKeyboardButton(text=f"🗑 {goal}", callback_data=f"goal_delete:{goal}")]
        for goal in goals
    ]
    keyboard.append([InlineKeyboardButton(text="Отмена", callback_data="goal_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_goals_edit_inline_keyboard(goals):
    keyboard = [
        [InlineKeyboardButton(text=f"✏️ {goal}", callback_data=f"goal_edit:{goal}")]
        for goal in goals
    ]
    keyboard.append([InlineKeyboardButton(text="Отмена", callback_data="goal_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")]
    ])

def format_goal_pretty(name, current, target, deadline, period, strategy_value, priority=None, idx=None):
    left = target - current
    prio_emoji = {1: '🌟', 2: '⭐️', 3: '🏆'}.get(priority, '')
    period_emoji = {'ежедневно': '🗓️/день', 'еженедельно': '🗓️/нед', 'ежемесячно': '🗓️/мес'}
    period_str = period_emoji.get(period.lower(), period)
    num = f"{idx}. " if idx is not None else ""
    # Считаем сколько дней осталось до дедлайна
    try:
        days_left = (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days
        if days_left < 0:
            deadline_str = "⏳ завершено"
        else:
            deadline_str = f"⏳ {days_left} дн."
    except Exception:
        deadline_str = deadline
    text = f"{num}<b>{name}</b> {prio_emoji}\n"
    text += f"   └ Осталось: <b>{left:,.0f}₽</b> из <b>{target:,.0f}₽</b>\n"
    text += f"   └ {deadline_str} | 💸 <b>{strategy_value:,.0f}₽</b> {period_str}"
    return text

def get_goals_action_inline_keyboard(goals):
    keyboard = [
        [InlineKeyboardButton(text=f"{goal}", callback_data=f"goal_action:{goal}")]
        for goal in goals
    ]
    keyboard.append([InlineKeyboardButton(text="Отмена", callback_data="goal_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_goal_manage_inline_keyboard(goal_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Пополнить", callback_data=f"goal_manage:deposit:{goal_name}"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data=f"goal_manage:edit:{goal_name}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"goal_manage:delete:{goal_name}")
        ],
        [InlineKeyboardButton(text="Назад", callback_data="goal_manage:back")]
    ])

def get_goal_edit_field_inline_keyboard(goal_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Название", callback_data="edit_goal_field:name"),
            InlineKeyboardButton(text="Дедлайн", callback_data="edit_goal_field:deadline"),
            InlineKeyboardButton(text="Сумма", callback_data="edit_goal_field:amount")
        ],
        [InlineKeyboardButton(text="Назад", callback_data=f"goal_action:{goal_name}")]
    ])

def get_goals_list_inline_keyboard(goals):
    keyboard = []
    for goal in goals:
        name, target_amount, current_amount, deadline, period, strategy_value, priority = goal
        try:
            days_left = (datetime.strptime(deadline, "%Y-%m-%d") - datetime.now()).days
            if days_left < 0:
                days_str = "⏳ завершено"
            else:
                days_str = f"⏳ {days_left} дн."
        except Exception:
            days_str = deadline
        percent = int(min(100, (current_amount / target_amount) * 100)) if target_amount else 0
        btn_text = f"{name} | {days_str} | {percent}%"
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"goal_action:{name}")])
    keyboard.append([InlineKeyboardButton(text="➕ Добавить новую цель", callback_data="goal_add_new")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 