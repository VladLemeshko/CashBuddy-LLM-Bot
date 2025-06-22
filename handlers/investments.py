from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.main_menu import main_menu
from tools.crypto_rates import get_crypto_rates
from tools.stock_movers import get_top_us_movers, get_top_ru_movers
from tools.deposit_parser import get_best_deposits

router = Router()

# Клавиатура для инвестиций
investments_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📈 Криптовалюты"), KeyboardButton(text="📊 Акции")],
        [KeyboardButton(text="🏦 Вклады"), KeyboardButton(text="📋 Общий обзор")],
        [KeyboardButton(text="🔙 Главное меню")],
    ],
    resize_keyboard=True
)

@router.message(Command("investments"))
@router.message(lambda message: message.text == "📈 Инвестиции")
async def investments_menu_handler(message: types.Message):
    """Показывает меню инвестиций"""
    await message.answer(
        "📈 <b>Инвестиционный обзор</b>\n\n"
        "Выберите, что хотите посмотреть:",
        reply_markup=investments_menu,
        parse_mode="HTML"
    )

@router.message(lambda message: message.text == "📈 Криптовалюты")
async def crypto_handler(message: types.Message):
    """Показывает курсы криптовалют"""
    try:
        crypto_data = get_crypto_rates()
        response = "📈 <b>Курсы криптовалют</b>\n\n"
        
        for crypto in crypto_data:
            response += f"<b>{crypto['name']}</b>\n"
            response += f"💵 ${crypto['usd']:,.2f}\n"
            response += f"₽ {crypto['rub']:,.2f}\n\n"
        
        await message.answer(response, parse_mode="HTML", reply_markup=investments_menu)
    except Exception as e:
        await message.answer(
            "❌ Ошибка при получении курсов криптовалют. Попробуйте позже.",
            reply_markup=investments_menu
        )

@router.message(lambda message: message.text == "📊 Акции")
async def stocks_handler(message: types.Message):
    """Показывает топ движения акций"""
    try:
        # Получаем данные по американским акциям
        us_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "SBUX"]
        us_movers = get_top_us_movers(us_tickers, 5)
        
        # Получаем данные по российским акциям
        ru_movers = get_top_ru_movers(5)
        
        response = "📊 <b>Топ движения акций</b>\n\n"
        
        response += "<b>🇺🇸 Американские акции:</b>\n"
        for ticker, change in us_movers:
            emoji = "🟢" if change > 0 else "🔴"
            response += f"{emoji} {ticker}: {change:+.2f}%\n"
        
        response += "\n<b>🇷🇺 Российские акции:</b>\n"
        for ticker, change in ru_movers:
            emoji = "🟢" if change > 0 else "🔴"
            response += f"{emoji} {ticker}: {change:+.2f}%\n"
        
        await message.answer(response, parse_mode="HTML", reply_markup=investments_menu)
    except Exception as e:
        await message.answer(
            "❌ Ошибка при получении данных по акциям. Попробуйте позже.",
            reply_markup=investments_menu
        )

@router.message(lambda message: message.text == "🏦 Вклады")
async def deposits_handler(message: types.Message):
    """Показывает лучшие вклады"""
    try:
        deposits = get_best_deposits()
        response = "🏦 <b>Топ-5 вкладов на рынке</b>\n\n"
        
        for i, deposit in enumerate(deposits[:5], 1):
            response += f"<b>{i}. {deposit['Банк']}</b>\n"
            response += f"📈 Доходность: {deposit['Доходность']}\n"
            response += f"⏳ Срок: {deposit['Срок']}\n"
            response += f"💰 Мин. сумма: {deposit['Мин. сумма']}\n\n"
        
        await message.answer(response, parse_mode="HTML", reply_markup=investments_menu)
    except Exception as e:
        await message.answer(
            "❌ Ошибка при получении данных по вкладам. Попробуйте позже.",
            reply_markup=investments_menu
        )

@router.message(lambda message: message.text == "📋 Общий обзор")
async def overview_handler(message: types.Message):
    """Показывает общий инвестиционный обзор"""
    try:
        # Получаем все данные
        crypto_data = get_crypto_rates()
        us_movers = get_top_us_movers(["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"], 3)
        ru_movers = get_top_ru_movers(3)
        deposits = get_best_deposits()
        
        response = "📋 <b>Инвестиционный обзор</b>\n\n"
        
        # Криптовалюты
        response += "📈 <b>Криптовалюты:</b>\n"
        for crypto in crypto_data:
            response += f"• {crypto['name']}: ${crypto['usd']:,.0f} (₽{crypto['rub']:,.0f})\n"
        
        # Топ акции
        response += "\n📊 <b>Топ акции США:</b>\n"
        for ticker, change in us_movers:
            emoji = "🟢" if change > 0 else "🔴"
            response += f"• {emoji} {ticker}: {change:+.1f}%\n"
        
        # Топ вклады
        response += "\n🏦 <b>Лучшие вклады:</b>\n"
        for i, deposit in enumerate(deposits[:3], 1):
            response += f"• {i}. {deposit['Банк']}: {deposit['Доходность']}\n"
        
        response += "\n💡 <i>Используйте кнопки выше для детального просмотра</i>"
        
        await message.answer(response, parse_mode="HTML", reply_markup=investments_menu)
    except Exception as e:
        await message.answer(
            "❌ Ошибка при получении обзора. Попробуйте позже.",
            reply_markup=investments_menu
        )

@router.message(lambda message: message.text == "🔙 Главное меню")
async def back_to_main_menu(message: types.Message):
    """Возврат в главное меню"""
    await message.answer(
        "🔙 Возвращаемся в главное меню",
        reply_markup=main_menu
    ) 