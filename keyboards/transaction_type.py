from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

transaction_type_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить доход"), KeyboardButton(text="➖ Добавить расход")],
        [KeyboardButton(text="Меню")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
) 