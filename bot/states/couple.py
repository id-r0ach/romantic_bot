from aiogram.fsm.state import State, StatesGroup


class CoupleStates(StatesGroup):
    waiting_for_code = State()