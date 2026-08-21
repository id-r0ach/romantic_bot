import logging
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from database.models.reason import Reason, ReasonGift, ReasonGiftStatus
from database.repositories.reason import ReasonGiftRepository, ReasonRepository
from database.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class ReasonGiftService:
    def __init__(
        self,
        reason_gift_repo: ReasonGiftRepository,
        reason_repo: ReasonRepository,
        user_repo: UserRepository,
    ) -> None:
        self._reason_gift_repo = reason_gift_repo
        self._reason_repo = reason_repo
        self._user_repo = user_repo

    async def get_or_create_draft(
        self,
        author_id: int,
        couple_id: int,
        recipient_id: int,
    ) -> ReasonGift:
        """Возвращает существующий черновик автора или создаёт новый."""
        existing = await self._reason_gift_repo.get_by_author(
            author_id=author_id,
            couple_id=couple_id,
            statuses=[ReasonGiftStatus.DRAFT],
        )
        if existing:
            return existing

        gift = ReasonGift(
            couple_id=couple_id,
            author_id=author_id,
            recipient_id=recipient_id,
            status=ReasonGiftStatus.DRAFT,
        )
        return await self._reason_gift_repo.create(gift)

    async def add_reason(self, gift_id: int, text: str) -> Reason:
        """Добавляет новую причину в подарок с валидацией."""
        text = text.strip()
        if not text:
            raise ValueError("Напиши что-нибудь ❤️")
        if len(text) > 500:
            raise ValueError("Слишком длинно. Максимум 500 символов")

        count = await self._reason_repo.count_by_gift(gift_id)
        if count >= 100:
            raise ValueError("Максимум 100 причин в одном подарке")

        reason = Reason(
            gift_id=gift_id,
            position=count + 1,
            text=text,
        )
        return await self._reason_repo.create(reason)

    async def get_draft_status(
        self,
        author_id: int,
        couple_id: int,
    ) -> tuple[ReasonGift, int] | None:
        """Возвращает черновик автора и количество причин в нём."""
        gift = await self._reason_gift_repo.get_by_author(
            author_id=author_id,
            couple_id=couple_id,
            statuses=[ReasonGiftStatus.DRAFT],
        )
        if not gift:
            return None
        count = await self._reason_repo.count_by_gift(gift.id)
        return gift, count
    
    
    async def get_author_gift_status(
        self,
        author_id: int,
        couple_id: int,
    ) -> tuple[ReasonGift, int, int] | None:
        """
        Возвращает последний подарок автора (draft, active или finished) и прогресс.
        Формат: (gift, total_reasons, opened_reasons)
        """
        gift = await self._reason_gift_repo.get_by_author(
            author_id=author_id,
            couple_id=couple_id,
            statuses=[
                ReasonGiftStatus.DRAFT,
                ReasonGiftStatus.ACTIVE,
                ReasonGiftStatus.FINISHED,
            ],
        )
        if not gift:
            return None
        total = await self._reason_repo.count_by_gift(gift.id)
        opened = await self._reason_repo.count_opened_by_gift(gift.id)
        return gift, total, opened

    async def get_gift_stats(self, gift_id: int) -> tuple[int, int]:
        """Возвращает (total, opened) для конкретного подарка."""
        total = await self._reason_repo.count_by_gift(gift_id)
        opened = await self._reason_repo.count_opened_by_gift(gift_id)
        return total, opened
    
    async def can_open_today(self, gift: ReasonGift, recipient_id: int) -> bool:
        """Проверяет, может ли получатель открыть причину сегодня."""
        if gift.status != ReasonGiftStatus.ACTIVE:
            return False

        user = await self._user_repo.get_by_tg_id(recipient_id)
        tz_name = user.timezone if user and user.timezone else "UTC"
        tz = ZoneInfo(tz_name)
        local_now = datetime.now(tz)
        today_local = local_now.date()

        if gift.last_opened_at:
            last_opened = gift.last_opened_at
            if last_opened.tzinfo is None:
                last_opened = last_opened.replace(tzinfo=dt_timezone.utc)
            last_opened_local = last_opened.astimezone(tz)
            if last_opened_local.date() == today_local:
                return False

        next_reason = await self._reason_repo.get_next_unopened(gift.id)
        return next_reason is not None
    

    async def delete_draft(self, gift_id: int) -> None:
        """Удаляет черновик и все причины внутри него."""
        await self._reason_repo.delete_by_gift(gift_id)
        gift = await self._reason_gift_repo.get_by_id(gift_id)
        if gift:
            await self._reason_gift_repo.delete(gift)

    async def activate_gift(self, gift_id: int) -> ReasonGift:
        """Превращает черновик в активный подарок (валидация >= 10 причин)."""
        gift = await self._reason_gift_repo.get_by_id(gift_id)
        if not gift or gift.status != ReasonGiftStatus.DRAFT:
            raise ValueError("Подарок не найден или не в черновике")

        count = await self._reason_repo.count_by_gift(gift_id)
        if count < 10:
            raise ValueError(f"Нужно минимум 10 причин. Сейчас: {count}")

        await self._reason_gift_repo.update_status(
            gift_id=gift_id,
            status=ReasonGiftStatus.ACTIVE,
            activated_at=datetime.now(dt_timezone.utc),
        )

        updated = await self._reason_gift_repo.get_by_id(gift_id)
        if not updated:
            raise ValueError("Ошибка активации подарка")
        return updated

    async def get_active_gift_for_recipient(
        self,
        recipient_id: int,
        couple_id: int,
    ) -> tuple[ReasonGift, int, int] | None:
        """Возвращает активный подарок получателя и прогресс (total, opened)."""
        gift = await self._reason_gift_repo.get_active_for_recipient(
            recipient_id=recipient_id,
            couple_id=couple_id,
        )
        if not gift:
            return None
        total = await self._reason_repo.count_by_gift(gift.id)
        opened = await self._reason_repo.count_opened_by_gift(gift.id)
        return gift, total, opened

    async def open_next_reason(self, gift_id: int, recipient_id: int) -> Reason | None:
        """
        Открывает следующую неоткрытую причину.
        Возвращает None, если сегодня уже открывали или все причины открыты.
        """
        gift = await self._reason_gift_repo.get_by_id(gift_id)
        if not gift or gift.recipient_id != recipient_id:
            raise ValueError("Подарок не найден")
        if gift.status != ReasonGiftStatus.ACTIVE:
            raise ValueError("Подарок не активен")

        # Получаем локальную дату получателя для проверки лимита "одна в день"
        user = await self._user_repo.get_by_tg_id(recipient_id)
        tz_name = user.timezone if user and user.timezone else "UTC"
        tz = ZoneInfo(tz_name)
        local_now = datetime.now(tz)
        today_local = local_now.date()

        if gift.last_opened_at:
            last_opened = gift.last_opened_at
            if last_opened.tzinfo is None:
                last_opened = last_opened.replace(tzinfo=dt_timezone.utc)
            last_opened_local = last_opened.astimezone(tz)
            if last_opened_local.date() == today_local:
                # Сегодня уже открывал причину
                return None

        next_reason = await self._reason_repo.get_next_unopened(gift_id)
        now_utc = datetime.now(dt_timezone.utc)

        if not next_reason:
            # Все причины уже открыты — меняем статус на finished
            await self._reason_gift_repo.update_status(
                gift_id=gift_id,
                status=ReasonGiftStatus.FINISHED,
            )
            return None

        # Отмечаем причину как открытую
        await self._reason_repo.mark_opened(next_reason.id, now_utc)
        await self._reason_gift_repo.update_last_opened(gift_id, now_utc)

        # Проверяем, была ли это последняя причина
        remaining = await self._reason_repo.get_next_unopened(gift_id)
        if not remaining:
            await self._reason_gift_repo.update_status(
                gift_id=gift_id,
                status=ReasonGiftStatus.FINISHED,
            )

        return next_reason

    async def cancel_gifts_for_couple(self, couple_id: int) -> None:
        """Отменяет все активные и черновые подарки пары при расставании."""
        gifts = await self._reason_gift_repo.get_active_gifts_for_couple(couple_id)
        for gift in gifts:
            await self._reason_gift_repo.update_status(
                gift_id=gift.id,
                status=ReasonGiftStatus.CANCELLED,
            )
        logger.info(f"Отменено подарков при расставании пары {couple_id}: {len(gifts)}")

    async def get_author_progress(
        self,
        author_id: int,
        couple_id: int,
    ) -> tuple[int, int] | None:
        """Возвращает прогресс получателя для автора (total, opened)."""
        gift = await self._reason_gift_repo.get_by_author(
            author_id=author_id,
            couple_id=couple_id,
            statuses=[ReasonGiftStatus.ACTIVE, ReasonGiftStatus.FINISHED],
        )
        if not gift:
            return None
        total = await self._reason_repo.count_by_gift(gift.id)
        opened = await self._reason_repo.count_opened_by_gift(gift.id)
        return total, opened