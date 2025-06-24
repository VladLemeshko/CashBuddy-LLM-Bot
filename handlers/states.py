from aiogram.fsm.state import State, StatesGroup

class AddTransaction(StatesGroup):
    type = State()
    category = State()
    amount = State()

class GoalStates(StatesGroup):
    name = State()
    amount = State()
    deadline = State()
    period = State()
    confirm_amount = State()
    priority = State()
    edit_confirm_amount = State()

class AskAgentState(StatesGroup):
    waiting_for_question = State()

class GoalDepositStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_amount = State()

class CreditStates(StatesGroup):
    age = State()
    marital = State()
    housing = State()
    loan = State()
    job = State()
    education = State()
    duration = State()
    campaign = State()
    loan_amount = State() 