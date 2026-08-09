from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import NavAction, TreeAction
from services.couple_service import CoupleService
from services.tree_service import TreeService

router = Router()


def _get_progress_bar(
    total_xp: int,
    current_level_xp: int,
    next_level_xp: int | None,
) -> str:
    """
    Строит текстовый прогресс-бар из 10 символов.

    Пример:
        ██████░░░░
    """
    if next_level_xp is None:
        return "█" * 10

    denominator = next_level_xp - current_level_xp

    if denominator <= 0:
        return "█" * 10

    progress = (total_xp - current_level_xp) / denominator
    progress = max(0.0, min(progress, 1.0))

    filled = int(progress * 10)

    return "█" * filled + "░" * (10 - filled)


@router.callback_query(StateFilter(None), TreeAction.filter(F.action == "show"))
async def cb_show_tree(
    callback: CallbackQuery,
    couple_service: CoupleService,
    tree_service: TreeService,
) -> None:
    """Показывает дерево отношений."""
    user_id = callback.from_user.id

    couple = await couple_service.get_couple(user_id)

    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    tree = await tree_service.get_tree(couple.id)

    level = tree["level"]
    emoji = tree["emoji"]
    name = tree["name"]
    total_xp = tree["total_xp"]
    current_level_xp = tree["current_level_xp"]
    next_level_xp = tree["next_level_xp"]
    xp_to_next = tree["xp_to_next"]
    days_together = tree["days_together"]
    breakdown = tree["breakdown"]

    progress_bar = _get_progress_bar(
        total_xp=total_xp,
        current_level_xp=current_level_xp,
        next_level_xp=next_level_xp,
    )

    text = (
        f"🌳 <b>Ваше дерево:</b> {emoji} {name} (уровень {level})\n\n"
    )

    if next_level_xp is None:
        text += (
            f"Прогресс: {progress_bar} {total_xp} XP\n"
            f"✨ Достигнут максимальный уровень!\n\n"
        )
    else:
        text += (
            f"Прогресс: {progress_bar} {total_xp} / {next_level_xp} XP\n\n"
        )

    text += (
        f"📅 Вместе: {days_together} дн. (+{breakdown['days_xp']} XP)\n"
        f"📖 Воспоминаний: {breakdown['memories_count']} "
        f"(+{breakdown['memories_xp']} XP)\n"
        f"💌 Писем доставлено: {breakdown['letters_delivered_count']} "
        f"(+{breakdown['letters_xp']} XP)\n"
    )

    if next_level_xp is not None:
        text += f"\nДо следующего уровня: {xp_to_next} XP"

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=NavAction(action="back").pack(),
                )
            ]
        ]
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=back_kb,
            parse_mode="HTML",
        )

    await callback.answer()