from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

INCOME_CATEGORIES = {
    "salary": "💼 Зарплата",
    "sidejob": "💸 Подработка",
    "dividends": "🏦 Проценты/Дивиденды",
    "gift": "🎁 Подарки",
    "bonus": "🏆 Призы/Бонусы",
    "sale": "🛒 Продажа вещей",
    "invest": "📈 Инвестиции",
    "other": "Другое"
}

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

def get_income_categories_inline_keyboard():
    categories = [
        ("💼 Зарплата", "salary"),
        ("💸 Подработка", "sidejob"),
        ("🏦 Проценты/Дивиденды", "dividends"),
        ("🎁 Подарки", "gift"),
        ("🏆 Призы/Бонусы", "bonus"),
        ("🛒 Продажа вещей", "sale"),
        ("📈 Инвестиции", "invest"),
        ("Другое", "other")
    ]
    keyboard = [
        [InlineKeyboardButton(text=cat, callback_data=f"income_cat:{cb}") for cat, cb in zip([categories[i][0] for i in range(j, min(j+2, len(categories)))], [categories[i][1] for i in range(j, min(j+2, len(categories)))])]
        for j in range(0, len(categories), 2)
    ]
    keyboard.append([InlineKeyboardButton(text="Отмена", callback_data="income_cat_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 