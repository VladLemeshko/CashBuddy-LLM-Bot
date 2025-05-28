from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить доход"), KeyboardButton(text="➖ Добавить расход")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📊 Отчёт")],
        [KeyboardButton(text="🎯 Цели"), KeyboardButton(text="💡 Совет GPT")],
        [KeyboardButton(text="💬 Вопрос агенту"), KeyboardButton(text="Меню")],
    ],
    resize_keyboard=True
) 