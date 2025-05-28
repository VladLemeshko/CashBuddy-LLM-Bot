from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards import main_menu
from db import DB_PATH
import aiosqlite
from gpt import ask_agent
from .states import AskAgentState
from .utils import beautify_answer
from handlers.advice import build_user_context

router = Router()

# ask_agent_start, process_agent_question 

@router.message(F.text == "💬 Вопрос агенту")
async def ask_agent_start(message: Message, state: FSMContext):
    await state.set_state(AskAgentState.waiting_for_question)
    await message.answer("💬 Задайте любой вопрос вашему финансовому агенту! Например: 'Как мне сэкономить?', 'Стоит ли мне увеличить доход?', 'Как быстрее достичь цели?'\n\nДля отмены отправьте 'Отмена'.")

@router.message(AskAgentState.waiting_for_question)
async def process_agent_question(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=main_menu)
        return
    user_id = message.from_user.id
    # Собираем историю транзакций
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT type, category, amount, date FROM transactions WHERE user_id=? ORDER BY date DESC LIMIT 30", (user_id,))
        transactions = await cursor.fetchall()
    history = "\n".join([f"{r[3][:10]}: {r[0]} {r[1]} {r[2]:.2f}₽" for r in transactions]) if transactions else "нет данных"
    user_context = await build_user_context(user_id)
    await message.answer("🤖 Агент анализирует ваши финансы и формулирует ответ... Пожалуйста, подождите! ⏳", reply_markup=main_menu)
    answer = await ask_agent(history, user_context, message.text)
    answer = beautify_answer(answer)
    await state.clear()
    await message.answer(f"<b>Ответ агента:</b>\n{answer}\n\n💡 Если нужен ещё совет — просто напишите!", parse_mode="HTML") 