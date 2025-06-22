from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards.main_menu import main_menu

router = Router()

@router.message(Command("menu"))
async def show_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu)

# Сброс состояния при нажатии на любую кнопку главного меню
@router.message(lambda m: m.text in [
    "➕ Добавить доход", "➖ Добавить расход", "💰 Баланс", "📊 Отчёт", "🎯 Цели", "📈 Инвестиции", "🤖 Агент"
])
async def main_menu_button_pressed(message: types.Message, state: FSMContext):
    await state.clear()
    # Не отправляем меню повторно, просто сбрасываем состояние 