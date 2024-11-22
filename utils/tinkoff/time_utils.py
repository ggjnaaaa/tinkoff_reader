# time_utils.py

# Стандартные модули Python
from datetime import timezone, datetime, timedelta

# Сторонние модули
import pytz
from pytz import UTC
from dateutil.relativedelta import relativedelta


def get_period_range(timezone: str, range_start: str = None, range_end: str = None, period: str = 'month'):
    """
    Преобразовывает строковые значения периодов (как дефолтных, так и заданных) в юникс время.
    """
    if range_start and range_end:
        start,end = get_period_from_range(range_start, range_end, timezone)
    elif period:
        start,end = get_period_from_default_range(period, timezone)

    return get_unix_time_ms_from_date(start), get_unix_time_ms_from_date(end)


def get_period_from_default_range(period, timezone):
    """
    Преобразовывает дефолтные периоды в юникс время.
    """
    # Определяем текущую дату и время с учётом переданного часового пояса
    tz = pytz.timezone(timezone)
    now = datetime.now(tz).replace(microsecond=0)

    if period == "day":
        start = now.replace(hour=0, minute=0, second=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    elif period == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)

    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = (start + relativedelta(months=1) - timedelta(days=1)).day
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    elif period == "3month":
        # Начало 3-месячного периода: отнимаем два месяца от текущей даты и переходим к первому дню этого месяца
        start = now.replace(day=1) - relativedelta(months=2)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        # Конец 3-месячного периода: последний день текущего месяца
        end = now.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

    else:
        raise ValueError("Unsupported period type. Use 'day', 'week', 'month', '3month', or 'year'.")

    return start, end


def get_period_from_range(range_start, range_end, user_timezone_name):
    """
    Преобразовывает заданные периоды в юникс время.
    """
    user_timezone = pytz.timezone(user_timezone_name)  # Используем функцию timezone из pytz
        
    # Преобразуем start_date и end_date в datetime с временной зоной пользователя
    start_datetime = user_timezone.localize(datetime.strptime(range_start, "%Y-%m-%d"))
    end_datetime = user_timezone.localize(datetime.strptime(range_end, "%Y-%m-%d"))

    # Добавляем время для начала и конца дня
    start_of_day = start_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = end_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start_of_day, end_of_day


def get_unix_time_ms_from_date(date):
    """
    Преобразовывает дату с часовым поясом в юникс время.
    """
    return int(date.astimezone(UTC).timestamp() * 1000)


def get_unix_time_ms_from_string(date_str: str, timezone_str: str) -> int:
    """
    Преобразовывает дату из строки + часовой пояс в юникс время.
    """
    # Преобразование строки в объект datetime
    date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
    
    # Применение часового пояса
    user_timezone = pytz.timezone(timezone_str)
    localized_date = user_timezone.localize(date)
    
    # Преобразование в Unix-время в миллисекундах
    unix_time_ms = int(localized_date.timestamp() * 1000)
    
    return unix_time_ms


def convert_unix_to_local_datetime(unix_time_ms: int, timezone_str: str) -> str:
    """
    Преобразовывает юникс время в дату и время по часовому поясу.
    """
    unix_time_sec = unix_time_ms / 1000
    utc_dt = datetime.fromtimestamp(unix_time_sec, tz=timezone.utc)
    
    user_timezone = pytz.timezone(timezone_str)
    local_dt = utc_dt.astimezone(user_timezone)

    formatted_dt = local_dt.strftime("%d.%m.%Y %H:%M:%S")
    
    return formatted_dt