"""FSM states used by the Telegram bot."""
from aiogram.fsm.state import State, StatesGroup


class PracticeStates(StatesGroup):
    solving_task = State()
    waiting_answer = State()
    getting_explanation = State()
    can_see_answer = State()


class DocStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_format = State()
