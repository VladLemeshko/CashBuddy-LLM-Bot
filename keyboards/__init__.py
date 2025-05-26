from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить доход"), KeyboardButton(text="➖ Добавить расход")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📊 Отчёт")],
        [KeyboardButton(text="🎯 Цели"), KeyboardButton(text="💡 Совет GPT")],
        [KeyboardButton(text="💬 Вопрос агенту")],
    ],
    resize_keyboard=True
)

transaction_type_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Доход"), KeyboardButton(text="Расход")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True
)

income_categories_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💼 Зарплата"), KeyboardButton(text="💸 Подработка")],
        [KeyboardButton(text="🏦 Проценты/Дивиденды"), KeyboardButton(text="🎁 Подарки")],
        [KeyboardButton(text="🏆 Призы/Бонусы"), KeyboardButton(text="🛒 Продажа вещей")],
        [KeyboardButton(text="📈 Инвестиции"), KeyboardButton(text="Другое")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True
)

expense_categories_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Продукты"), KeyboardButton(text="🏠 Жильё/Коммуналка")],
        [KeyboardButton(text="🚗 Транспорт/Топливо"), KeyboardButton(text="📱 Связь/Интернет")],
        [KeyboardButton(text="🎓 Образование"), KeyboardButton(text="👔 Одежда/Обувь")],
        [KeyboardButton(text="🍽️ Кафе/Рестораны"), KeyboardButton(text="🏥 Здоровье/Лекарства")],
        [KeyboardButton(text="🎉 Развлечения"), KeyboardButton(text="🏖️ Путешествия")],
        [KeyboardButton(text="🐾 Домашние животные"), KeyboardButton(text="🎁 Подарки/Пожертвования")],
        [KeyboardButton(text="🛠️ Техника/Гаджеты"), KeyboardButton(text="Другое")],
        [KeyboardButton(text="Отмена")],
    ],
    resize_keyboard=True
)
