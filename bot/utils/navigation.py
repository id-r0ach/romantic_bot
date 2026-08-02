from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_kb import get_main_menu_kb


async def back_to_main_menu(target: Message | CallbackQuery, state: FSMContext) -> None:
    """
    Универсальный возврат в главное меню.
    Гарантирует сброс состояния и наличие reply-клавиатуры.
    """
    # 1. Всегда сбрасываем состояние при возврате в главное меню
    await state.clear()

    if isinstance(target, CallbackQuery):
        # 2. Убираем "часики" загрузки в клиенте Telegram
        await target.answer()
        
        # 3. Безопасно удаляем сообщение с inline-клавиатурой
        if target.message:
            await target.message.delete()
            chat_id = target.message.chat.id
            bot = target.message.bot
            
            # 4. Отправляем новое сообщение от имени бота
            await bot.send_message(
                chat_id=chat_id,
                text="🏠 Главное меню",
                reply_markup=get_main_menu_kb()
            )
    else:
        # Если вызов произошел из обычного Message (на будущее)
        await target.answer(
            text="🏠 Главное меню",
            reply_markup=get_main_menu_kb()
        )