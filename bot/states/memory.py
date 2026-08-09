from aiogram.fsm.state import State, StatesGroup


class MemoryStates(StatesGroup):
    entering_title = State()
    entering_description = State()
    entering_date = State()