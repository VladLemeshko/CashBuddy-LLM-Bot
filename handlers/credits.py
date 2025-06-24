import logging
import numpy as np
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from .states import CreditStates
from db import save_credit_application, get_user_credit_history

router = Router()
logger = logging.getLogger(__name__)

def get_menu_with_back_keyboard():
    """Клавиатура с кнопкой возврата в главное меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )

@router.message(F.text == "🏠 Вернуться в главное меню")
async def return_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню из любого состояния"""
    from keyboards.main_menu import main_menu
    await state.clear()
    await message.answer("🏠 Вы вернулись в главное меню", reply_markup=main_menu)

def calculate_credit_probability(inputs):
    """Расчет вероятности одобрения кредита по модели"""
    logit = -0.596662 + \
            0.004 * inputs['age'] + \
            -0.06 * inputs['marital'] + \
            -0.01 * inputs['housing'] + \
            -0.05 * inputs['loan'] + \
            -1.26 * inputs.get('_manual_labor', 0) + \
            -0.72 * inputs.get('_office_workers', 0) + \
            0.50 * inputs.get('_other', 0) + \
            -1.26 * inputs.get('_service_sector', 0) + \
            -0.98 * inputs.get('_tech_related', 0) + \
            0.12 * inputs.get('_higher', 0) + \
            -0.30 * inputs.get('_secondary', 0) + \
            0.001 * inputs['duration'] + \
            -0.07 * inputs['campaign']
    
    probability = 1 / (1 + np.exp(-logit))
    return round(probability * 100, 2)

def get_selected_job(inputs):
    """Получает выбранную профессию"""
    if inputs.get('_manual_labor'):
        return 'Физический труд'
    elif inputs.get('_office_workers'):
        return 'Офисный работник'
    elif inputs.get('_other'):
        return 'Другое'
    elif inputs.get('_service_sector'):
        return 'Сфера услуг'
    elif inputs.get('_tech_related'):
        return 'IT/Технологии'
    return 'Не указано'

def get_selected_education(inputs):
    """Получает выбранное образование"""
    if inputs.get('_higher'):
        return 'Высшее'
    elif inputs.get('_secondary'):
        return 'Среднее'
    return 'Не указано'

@router.message(F.text == "💳 Кредиты")
async def credits_menu(message: types.Message, state: FSMContext):
    """Показывает меню кредитов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Новая заявка")],
            [KeyboardButton(text="📊 История заявок")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "💳 Кредитный калькулятор\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@router.message(F.text == "📝 Новая заявка")
async def start_credit_survey(message: types.Message, state: FSMContext):
    """Начинает опрос для кредитной заявки"""
    await state.set_state(CreditStates.age)
    await message.answer(
        "📝 Новая кредитная заявка\n\n"
        "Введите ваш возраст:",
        reply_markup=get_menu_with_back_keyboard()
    )

@router.message(F.text == "📊 История заявок")
async def show_credit_history(message: types.Message, state: FSMContext):
    """Показывает историю кредитных заявок"""
    history = await get_user_credit_history(message.from_user.id)
    
    if not history:
        await message.answer("У вас пока нет кредитных заявок.")
        return
    
    response = "📊 История ваших кредитных заявок:\n\n"
    for i, record in enumerate(history[:5], 1):  # Показываем последние 5 заявок
        response += f"{i}. Дата: {record[12]}\n"
        response += f"   Вероятность одобрения: {record[11]}%\n"
        response += f"   Возраст: {record[2]}, Профессия: {record[6]}\n"
        if len(record) > 10 and record[10]:  # loan_amount
            response += f"   Сумма: {record[10]:,.0f}₽, Срок: {record[8]} мес.\n"
            response += f"   Первый кредит в жизни: {'Да' if record[9] == 0 else 'Нет'}\n"
        response += "\n"
    
    await message.answer(response)

@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    from keyboards.main_menu import main_menu
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu)

@router.message(CreditStates.age)
async def process_age(message: types.Message, state: FSMContext):
    """Обрабатывает возраст"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    try:
        age = int(message.text)
        if age < 18 or age > 100:
            await message.answer('Пожалуйста, введите реальный возраст (18-100)')
            return
        
        await state.update_data(age=age)
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Женат/замужем"), KeyboardButton(text="Холост/не замужем")],
                [KeyboardButton(text="🏠 Вернуться в главное меню")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            'Ваше семейное положение:',
            reply_markup=keyboard
        )
        await state.set_state(CreditStates.marital)
    except ValueError:
        await message.answer('Пожалуйста, введите число')

@router.message(CreditStates.marital)
async def process_marital(message: types.Message, state: FSMContext):
    """Обрабатывает семейное положение"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    marital = 1 if message.text == "Женат/замужем" else 0
    await state.update_data(marital=marital)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        'Есть ли у вас жилье в собственности?',
        reply_markup=keyboard
    )
    await state.set_state(CreditStates.housing)

@router.message(CreditStates.housing)
async def process_housing(message: types.Message, state: FSMContext):
    """Обрабатывает наличие жилья"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    housing = 1 if message.text == "Да" else 0
    await state.update_data(housing=housing)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        'Есть ли у вас сейчас действующие кредиты (например, ипотека, автокредит, кредитная карта и т.д.)?\n(Если все кредиты уже погашены — отвечайте "Нет")',
        reply_markup=keyboard
    )
    await state.set_state(CreditStates.loan)

@router.message(CreditStates.loan)
async def process_loan(message: types.Message, state: FSMContext):
    """Обрабатывает наличие других кредитов"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    loan = 1 if message.text == "Да" else 0
    await state.update_data(loan=loan)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Физический труд")],
            [KeyboardButton(text="Офисный работник")],
            [KeyboardButton(text="IT/Технологии")],
            [KeyboardButton(text="Сфера услуг")],
            [KeyboardButton(text="Другое")],
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        'Ваша профессия:',
        reply_markup=keyboard
    )
    await state.set_state(CreditStates.job)

@router.message(CreditStates.job)
async def process_job(message: types.Message, state: FSMContext):
    """Обрабатывает профессию"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    job_type = message.text
    
    # Сбрасываем все категории профессий
    job_data = {
        '_manual_labor': 0,
        '_office_workers': 0,
        '_other': 0,
        '_service_sector': 0,
        '_tech_related': 0
    }
    
    if job_type == 'Физический труд':
        job_data['_manual_labor'] = 1
    elif job_type == 'Офисный работник':
        job_data['_office_workers'] = 1
    elif job_type == 'IT/Технологии':
        job_data['_tech_related'] = 1
    elif job_type == 'Сфера услуг':
        job_data['_service_sector'] = 1
    else:
        job_data['_other'] = 1
    
    await state.update_data(**job_data, job_category=job_type)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Высшее")],
            [KeyboardButton(text="Среднее")],
            [KeyboardButton(text="🏠 Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        'Ваше образование:',
        reply_markup=keyboard
    )
    await state.set_state(CreditStates.education)

@router.message(CreditStates.education)
async def process_education(message: types.Message, state: FSMContext):
    """Обрабатывает образование"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    education = message.text
    
    # Сбрасываем все категории образования
    education_data = {
        '_higher': 0,
        '_secondary': 0,
        '_low': 0
    }
    
    if education == 'Высшее':
        education_data['_higher'] = 1
    elif education == 'Среднее':
        education_data['_secondary'] = 1
    else:
        education_data['_low'] = 1
    
    await state.update_data(**education_data, education=education)
    
    await message.answer(
        'Введите срок кредита в месяцах:',
        reply_markup=get_menu_with_back_keyboard()
    )
    await state.set_state(CreditStates.duration)

@router.message(CreditStates.duration)
async def process_duration(message: types.Message, state: FSMContext):
    """Обрабатывает срок кредита"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    try:
        duration = int(message.text)
        if duration <= 0 or duration > 120:
            await message.answer('Пожалуйста, введите срок от 1 до 120 месяцев')
            return
        
        await state.update_data(duration=duration)
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
                [KeyboardButton(text="🏠 Вернуться в главное меню")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            'Это ваш первый кредит в жизни?\n(Если вы когда-либо брали кредит, даже если сейчас у вас нет кредитов — отвечайте "Нет")',
            reply_markup=keyboard
        )
        await state.set_state(CreditStates.campaign)
    except ValueError:
        await message.answer('Пожалуйста, введите число')

@router.message(CreditStates.campaign)
async def process_campaign(message: types.Message, state: FSMContext):
    """Обрабатывает первый ли кредит"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    # campaign = 0 если первый кредит (Да), 1 если не первый (Нет)
    campaign = 0 if message.text == "Да" else 1
    await state.update_data(campaign=campaign)
    
    await message.answer(
        'Введите желаемую сумму кредита (в рублях):',
        reply_markup=get_menu_with_back_keyboard()
    )
    await state.set_state(CreditStates.loan_amount)

@router.message(CreditStates.loan_amount)
async def process_loan_amount(message: types.Message, state: FSMContext):
    """Обрабатывает сумму кредита и завершает опрос"""
    if message.text == "🏠 Вернуться в главное меню":
        await return_to_main_menu(message, state)
        return
    
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer('Пожалуйста, введите положительную сумму')
            return
        
        await state.update_data(loan_amount=amount)
        
        # Получаем все данные
        data = await state.get_data()
        
        # Расчет вероятности
        probability = calculate_credit_probability(data)
        
        # Сохраняем в базу данных
        await save_credit_application(message.from_user.id, data, probability)
        
        # Формируем отчет
        report = f"""
📊 Результат оценки кредитоспособности:

✅ Вероятность одобрения: {probability}%

📋 Использованные параметры:
• Возраст: {data['age']}
• Семейное положение: {'Женат/замужем' if data['marital'] else 'Холост/не замужем'}
• Наличие жилья: {'Да' if data['housing'] else 'Нет'}
• Действующие кредиты: {'Да' if data['loan'] else 'Нет'}
• Профессия: {data['job_category']}
• Образование: {data['education']}
• Срок кредита: {data['duration']} мес.
• Первый кредит в жизни: {'Да' if data['campaign'] == 0 else 'Нет'}
• Сумма кредита: {amount:,} ₽

�� Рекомендации:
"""
        
        if probability >= 80:
            report += "🎉 Отличные шансы на одобрение! Можете подавать заявку."
        elif probability >= 60:
            report += "👍 Хорошие шансы на одобрение. Рассмотрите возможность увеличения первоначального взноса."
        elif probability >= 40:
            report += "⚠️ Средние шансы. Рекомендуется улучшить кредитную историю или уменьшить сумму."
        else:
            report += "❌ Низкие шансы на одобрение. Рекомендуется поработать над улучшением кредитоспособности."
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Новая заявка")],
                [KeyboardButton(text="📊 История заявок")],
                [KeyboardButton(text="🔙 Назад")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(report, reply_markup=keyboard)
        await state.clear()
        
    except ValueError:
        await message.answer('Пожалуйста, введите число') 