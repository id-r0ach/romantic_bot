from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_for_timezone = State()
    waiting_for_anniversary_time = State()