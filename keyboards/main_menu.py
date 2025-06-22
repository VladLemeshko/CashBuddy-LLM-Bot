from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить доход"), KeyboardButton(text="➖ Добавить расход")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📊 Отчёт")],
        [KeyboardButton(text="🎯 Цели"), KeyboardButton(text="📈 Инвестиции")],
        [KeyboardButton(text="💳 Кредиты"), KeyboardButton(text="🤖 Агент")],
    ],
    resize_keyboard=True
) 