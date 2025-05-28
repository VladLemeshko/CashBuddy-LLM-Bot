from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

EXPENSE_CATEGORIES = {
    "products": "🛒 Продукты",
    "housing": "🏠 Жильё/Коммуналка",
    "transport": "🚗 Транспорт/Топливо",
    "internet": "📱 Связь/Интернет",
    "education": "🎓 Образование",
    "clothes": "👔 Одежда/Обувь",
    "cafe": "🍽️ Кафе/Рестораны",
    "health": "🏥 Здоровье/Лекарства",
    "entertainment": "🎉 Развлечения",
    "travel": "🏖️ Путешествия",
    "pets": "🐾 Домашние животные",
    "gifts": "🎁 Подарки/Пожертвования",
    "gadgets": "🛠️ Техника/Гаджеты",
    "other": "Другое"
}

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

def get_expense_categories_inline_keyboard():
    categories = [
        ("🛒 Продукты", "products"),
        ("🏠 Жильё/Коммуналка", "housing"),
        ("🚗 Транспорт/Топливо", "transport"),
        ("📱 Связь/Интернет", "internet"),
        ("🎓 Образование", "education"),
        ("👔 Одежда/Обувь", "clothes"),
        ("🍽️ Кафе/Рестораны", "cafe"),
        ("🏥 Здоровье/Лекарства", "health"),
        ("🎉 Развлечения", "entertainment"),
        ("🏖️ Путешествия", "travel"),
        ("🐾 Домашние животные", "pets"),
        ("🎁 Подарки/Пожертвования", "gifts"),
        ("🛠️ Техника/Гаджеты", "gadgets"),
        ("Другое", "other")
    ]
    keyboard = [
        [InlineKeyboardButton(text=cat, callback_data=f"expense_cat:{cb}") for cat, cb in zip([categories[i][0] for i in range(j, min(j+2, len(categories)))], [categories[i][1] for i in range(j, min(j+2, len(categories)))])]
        for j in range(0, len(categories), 2)
    ]
    keyboard.append([InlineKeyboardButton(text="Отмена", callback_data="expense_cat_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 