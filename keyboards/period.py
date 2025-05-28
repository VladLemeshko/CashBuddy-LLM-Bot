from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

period_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ежедневно")],
        [KeyboardButton(text="Еженедельно")],
        [KeyboardButton(text="Ежемесячно")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

confirm_amount_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
) 