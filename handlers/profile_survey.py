from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from db import DB_PATH
import aiosqlite
from keyboards.main_menu import main_menu

router = Router()

class ProfileSurvey(StatesGroup):
    waiting_for_income_type = State()
    waiting_for_monthly_income = State()
    waiting_for_has_deposits = State()
    waiting_for_deposit_bank = State()
    waiting_for_deposit_interest = State()
    waiting_for_deposit_amount = State()
    waiting_for_deposit_term = State()
    waiting_for_deposit_date = State()
    waiting_for_has_loans = State()
    waiting_for_loans_details = State()
    waiting_for_has_investments = State()
    waiting_for_investments_details = State()
    waiting_for_financial_mood = State()
    waiting_for_regular_payments = State()
    waiting_for_regular_payments_details = State()

# Клавиатура с кнопкой возврата в главное меню
def get_menu_with_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

@router.message(F.text == "🏠 Вернуться в главное меню")
async def return_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Вы вернулись в главное меню", reply_markup=main_menu)

# Клавиатуры
start_survey_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Начать")], [KeyboardButton(text="Пропустить")]],
    resize_keyboard=True
)
income_type_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Постоянная зарплата")],
        [KeyboardButton(text="Нерегулярный доход")],
        [KeyboardButton(text="Доход от бизнеса")],
        [KeyboardButton(text="Нет постоянного дохода")],
        [KeyboardButton(text="🏠 Вернуться в главное меню")]
    ],
    resize_keyboard=True
)
has_deposits_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да")], 
        [KeyboardButton(text="Нет")],
        [KeyboardButton(text="🏠 Вернуться в главное меню")]
    ],
    resize_keyboard=True
)
has_loans_kb = has_deposits_kb
has_investments_kb = has_deposits_kb
financial_mood_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Всё отлично, всё под контролем!")],
        [KeyboardButton(text="Могло бы быть лучше, хочу больше порядка")],
        [KeyboardButton(text="Есть сложности, хочу разобраться")],
        [KeyboardButton(text="🏠 Вернуться в главное меню")]
    ],
    resize_keyboard=True
)

# Приветствие и объяснение
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_name = message.from_user.first_name or "друг"
    text = (
        f"👋 Привет, {user_name}! Я — твой персональный финансовый помощник.\n\n"
        "Чтобы давать тебе действительно полезные и персонализированные советы, мне нужно немного узнать о твоей финансовой ситуации.\n\n"
        "✨ Чем больше я знаю о твоих доходах, накоплениях, кредитах и инвестициях, тем точнее и полезнее будут мои рекомендации. Я помогу тебе экономить, находить лучшие решения и поддерживать твои цели!\n\n"
        "🔒 Не переживай, это абсолютно безопасно: все твои ответы хранятся только у тебя в профиле и не передаются третьим лицам.\n\n"
        "Готов(а) пройти короткий опрос? Это займёт не больше минуты! 🚀"
    )
    await message.answer(text, reply_markup=start_survey_kb)
    await state.clear()

# Обработка выбора начать/пропустить
@router.message(F.text.in_(["Начать", "Пропустить"]))
async def survey_entry(message: types.Message, state: FSMContext):
    if message.text == "Начать":
        await message.answer("1️⃣ Какой у тебя основной источник дохода?\n(Выбери вариант ниже 👇)", reply_markup=income_type_kb)
        await state.set_state(ProfileSurvey.waiting_for_income_type)
    else:
        await message.answer("Опрос пропущен. Ты всегда можешь заполнить профиль позже в настройках.", reply_markup=ReplyKeyboardRemove())
        await state.clear()

# 1. Тип дохода
@router.message(ProfileSurvey.waiting_for_income_type)
async def income_type_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    await state.update_data(income_type=message.text)
    await message.answer("2️⃣ Какой у тебя средний доход в месяц?\n(Напиши сумму в рублях, например: 50000)", reply_markup=get_menu_with_back_keyboard())
    await state.set_state(ProfileSurvey.waiting_for_monthly_income)

# 2. Доход
@router.message(ProfileSurvey.waiting_for_monthly_income)
async def monthly_income_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    try:
        income = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Пожалуйста, введи сумму числом, например: 50000")
        return
    await state.update_data(monthly_income=income)
    await message.answer("3️⃣ Есть ли у тебя банковские вклады или накопления?\n(Это поможет мне анализировать твои сбережения 💰)", reply_markup=has_deposits_kb)
    await state.set_state(ProfileSurvey.waiting_for_has_deposits)

# 3. Вклады/накопления
@router.message(ProfileSurvey.waiting_for_has_deposits)
async def has_deposits_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    has_deposits = 1 if message.text == "Да" else 0
    await state.update_data(has_deposits=has_deposits)
    if has_deposits:
        await message.answer("🏦 В каком банке у тебя открыт вклад?", reply_markup=get_menu_with_back_keyboard())
        await state.set_state(ProfileSurvey.waiting_for_deposit_bank)
    else:
        await state.update_data(
            deposit_bank=None,
            deposit_interest=None,
            deposit_amount=None,
            deposit_term=None,
            deposit_date=None
        )
        await message.answer("4️⃣ Есть ли у тебя кредиты, рассрочки или долги?\n(Это поможет мне оценить твою кредитную нагрузку 🏦)", reply_markup=has_loans_kb)
        await state.set_state(ProfileSurvey.waiting_for_has_loans)

@router.message(ProfileSurvey.waiting_for_deposit_bank)
async def deposit_bank_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    await state.update_data(deposit_bank=message.text)
    await message.answer("📈 Какой процент по вкладу?", reply_markup=get_menu_with_back_keyboard())
    await state.set_state(ProfileSurvey.waiting_for_deposit_interest)

@router.message(ProfileSurvey.waiting_for_deposit_interest)
async def deposit_interest_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    try:
        percent = float(message.text.replace(',', '.'))
        await state.update_data(deposit_interest=percent)
        await message.answer("💵 Какая сумма на вкладе?", reply_markup=get_menu_with_back_keyboard())
        await state.set_state(ProfileSurvey.waiting_for_deposit_amount)
    except ValueError:
        await message.answer("Пожалуйста, введи процент числом, например: 7.5")

@router.message(ProfileSurvey.waiting_for_deposit_amount)
async def deposit_amount_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(deposit_amount=amount)
        await message.answer("⏳ На какой срок открыт вклад? (например, 6 месяцев, 1 год)", reply_markup=get_menu_with_back_keyboard())
        await state.set_state(ProfileSurvey.waiting_for_deposit_term)
    except ValueError:
        await message.answer("Пожалуйста, введи сумму числом, например: 100000")

@router.message(ProfileSurvey.waiting_for_deposit_term)
async def deposit_term_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    await state.update_data(deposit_term=message.text)
    await message.answer("📅 Когда ты открыл вклад? (или когда он заканчивается)", reply_markup=get_menu_with_back_keyboard())
    await state.set_state(ProfileSurvey.waiting_for_deposit_date)

@router.message(ProfileSurvey.waiting_for_deposit_date)
async def deposit_date_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    await state.update_data(deposit_date=message.text)
    await message.answer("4️⃣ Есть ли у тебя кредиты, рассрочки или долги?\n(Это поможет мне оценить твою кредитную нагрузку 🏦)", reply_markup=has_loans_kb)
    await state.set_state(ProfileSurvey.waiting_for_has_loans)

# 4. Кредиты/долги
@router.message(ProfileSurvey.waiting_for_has_loans)
async def has_loans_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    has_loans = 1 if message.text == "Да" else 0
    await state.update_data(has_loans=has_loans)
    if has_loans:
        await message.answer("💳 Какой общий остаток по кредитам/долгам?\n(В рублях, например: 150000)", reply_markup=get_menu_with_back_keyboard())
        await state.set_state(ProfileSurvey.waiting_for_loans_details)
    else:
        await state.update_data(loans_total=None, loans_interest=None)
        await message.answer("5️⃣ Инвестируешь ли ты во что-то?\n(Акции, облигации, крипта и т.д. 📊)", reply_markup=has_investments_kb)
        await state.set_state(ProfileSurvey.waiting_for_has_investments)

@router.message(ProfileSurvey.waiting_for_loans_details)
async def loans_details_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    data = await state.get_data()
    if data.get('loans_total') is None:
        try:
            total = float(message.text.replace(',', '.'))
            await state.update_data(loans_total=total)
            await message.answer("📈 Какой средний процент по кредитам?\n(Напиши число, например: 12.5)", reply_markup=get_menu_with_back_keyboard())
        except ValueError:
            await message.answer("Пожалуйста, введи сумму числом, например: 150000")
            return
    else:
        try:
            percent = float(message.text.replace(',', '.'))
            await state.update_data(loans_interest=percent)
            await message.answer("5️⃣ Инвестируешь ли ты во что-то?\n(Акции, облигации, крипта и т.д. 📊)", reply_markup=has_investments_kb)
            await state.set_state(ProfileSurvey.waiting_for_has_investments)
        except ValueError:
            await message.answer("Пожалуйста, введи процент числом, например: 12.5")

# 5. Инвестиции
@router.message(ProfileSurvey.waiting_for_has_investments)
async def has_investments_q(message: types.Message, state: FSMContext):
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    has_investments = 1 if message.text == "Да" else 0
    await state.update_data(has_investments=has_investments)
    if has_investments:
        await message.answer("💹 Какой примерный объём твоих инвестиций?\n(В рублях, например: 50000)", reply_markup=get_menu_with_back_keyboard())
        await state.set_state(ProfileSurvey.waiting_for_investments_details)
    else:
        await state.update_data(investments_amount=None, investments_profit=None)
        await message.answer("6️⃣ Как ты оцениваешь своё финансовое состояние сейчас?\n(Выбери вариант ниже 👇)", reply_markup=financial_mood_kb)
        await state.set_state(ProfileSurvey.waiting_for_financial_mood)

@router.message(ProfileSurvey.waiting_for_investments_details)
async def investments_details_q(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get('investments_amount') is None:
        try:
            amount = float(message.text.replace(',', '.'))
            await state.update_data(investments_amount=amount)
            await message.answer("📈 Какой средний годовой доход/убыток по инвестициям за последний год (в процентах)?\n(Напиши число, например: 8.5)")
        except ValueError:
            await message.answer("Пожалуйста, введи сумму числом, например: 50000")
            return
    else:
        try:
            percent = float(message.text.replace(',', '.'))
            await state.update_data(investments_profit=percent)
            await message.answer("6️⃣ Как ты оцениваешь своё финансовое состояние сейчас?\n(Выбери вариант ниже 👇)", reply_markup=financial_mood_kb)
            await state.set_state(ProfileSurvey.waiting_for_financial_mood)
        except ValueError:
            await message.answer("Пожалуйста, введи процент числом, например: 8.5")

# 6. Финансовое настроение
@router.message(ProfileSurvey.waiting_for_financial_mood)
async def financial_mood_q(message: types.Message, state: FSMContext):
    await state.update_data(financial_mood=message.text)
    await message.answer("Есть ли у тебя регулярные платежи (ЖКХ, интернет, кредиты и т.д.)?", reply_markup=has_deposits_kb)
    await state.set_state(ProfileSurvey.waiting_for_regular_payments)

@router.message(ProfileSurvey.waiting_for_regular_payments)
async def has_regular_payments_q(message: types.Message, state: FSMContext):
    has_payments = 1 if message.text == "Да" else 0
    await state.update_data(has_regular_payments=has_payments)
    if has_payments:
        await message.answer("Перечисли, пожалуйста, свои регулярные платежи через запятую (например: ЖКХ, интернет, кредит, аренда)")
        await state.set_state(ProfileSurvey.waiting_for_regular_payments_details)
    else:
        await state.update_data(regular_payments_list=None)
        await finish_profile_survey(message, state)

@router.message(ProfileSurvey.waiting_for_regular_payments_details)
async def regular_payments_details_q(message: types.Message, state: FSMContext):
    await state.update_data(regular_payments_list=message.text)
    await finish_profile_survey(message, state)

async def finish_profile_survey(message, state):
    data = await state.get_data()
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO user_profiles (
                user_id, income_type, monthly_income, has_deposits, deposit_bank, deposit_interest, deposit_amount,
                deposit_term, deposit_date, has_loans, loans_total, loans_interest, has_investments, investments_amount, investments_profit,
                financial_mood, has_regular_payments, regular_payments_list
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('income_type'),
            data.get('monthly_income'),
            data.get('has_deposits'),
            data.get('deposit_bank'),
            data.get('deposit_interest'),
            data.get('deposit_amount'),
            data.get('deposit_term'),
            data.get('deposit_date'),
            data.get('has_loans'),
            data.get('loans_total'),
            data.get('loans_interest'),
            data.get('has_investments'),
            data.get('investments_amount'),
            data.get('investments_profit'),
            data.get('financial_mood'),
            data.get('has_regular_payments'),
            data.get('regular_payments_list')
        ))
        await db.commit()
    await message.answer("🎉 Спасибо! Профиль заполнен. Теперь я смогу давать тебе более точные и полезные советы! 😊\n\nЧтобы начать пользоваться ботом, нажми /menu", reply_markup=ReplyKeyboardRemove())
    await state.clear() 