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

class AskAgentState(StatesGroup):
    waiting_for_question = State()

class GoalDepositStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_amount = State() 