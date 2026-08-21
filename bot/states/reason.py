from aiogram.fsm.state import State, StatesGroup


class ReasonStates(StatesGroup):
    waiting_reason = State()