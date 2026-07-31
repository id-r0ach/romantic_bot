from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_kb() -> ReplyKeyboardMarkup:
    """
    Возвращает постоянную reply-клавиатуру главного меню.
    """
    buttons = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💑 Пара")],
        [KeyboardButton(text="⚙️ Настройки")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел..."
    )