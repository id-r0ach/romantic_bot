from aiogram.fsm.state import State, StatesGroup


class LetterStates(StatesGroup):
    choosing_date = State()   # Выбор пресета (неделя, месяц, год, своя)
    entering_date = State()   # Ввод даты: ДД.ММ.ГГГГ
    entering_time = State()   # Ввод времени: ЧЧ:ММ
    entering_text = State()   # Ввод текста письма
    confirming = State()      # Подтверждение