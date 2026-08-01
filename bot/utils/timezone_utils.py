from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import logging

logger = logging.getLogger(__name__)


def get_common_timezones() -> list[str]:
    """Возвращает список популярных часовых поясов для выбора пользователем."""
    return [
        "Europe/Moscow",
        "Europe/Kyiv",
        "Europe/Minsk",
        "Europe/Berlin",
        "Europe/London",
        "America/New_York",
        "Asia/Almaty",
        "Asia/Tashkent",
        "Asia/Dubai",
        "UTC",
    ]


def validate_timezone(tz_name: str) -> bool:
    """
    Проверяет, является ли строка валидным названием часового пояса.
    Возвращает True, если пояс существует, иначе False.
    """
    try:
        ZoneInfo(tz_name)
        return True
    except ZoneInfoNotFoundError:
        logger.warning(f"Невалидный часовой пояс: {tz_name}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке часового пояса {tz_name}: {e}")
        return False


def to_utc(dt: datetime, tz_name: str) -> datetime:
    """
    Конвертирует наивное (без часового пояса) или локальное datetime 
    в UTC для сохранения в базу данных.
    
    :param dt: Объект datetime (предполагается, что он в локальном времени пользователя)
    :param tz_name: Строка с названием часового пояса пользователя (например, "Europe/Moscow")
    :return: Объект datetime с часовым поясом UTC
    """
    if not validate_timezone(tz_name):
        tz_name = "UTC" # Fallback на случай невалидного пояса
    
    target_tz = ZoneInfo(tz_name)
    
    # Если datetime "наивный" (без tzinfo), считаем, что он в локальном поясе пользователя
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=target_tz)
    
    # Конвертируем в UTC
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime, tz_name: str) -> datetime:
    """
    Конвертирует datetime из UTC (например, из БД) в локальное время пользователя для отображения.
    
    :param dt: Объект datetime (предполагается, что он в UTC)
    :param tz_name: Строка с названием часового пояса пользователя
    :return: Объект datetime в локальном часовом поясе
    """
    if not validate_timezone(tz_name):
        tz_name = "UTC"
    
    target_tz = ZoneInfo(tz_name)
    
    # Если datetime "наивный", считаем, что это UTC (стандарт для БД)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Конвертируем в локальный пояс
    return dt.astimezone(target_tz)