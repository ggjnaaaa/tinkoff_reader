# routes/directory/tinkoff/utils.py

# Стандартные модули Python
from typing import Optional
from datetime import datetime


def generate_period_message(
    min_timestamp: Optional[int],
    max_timestamp: Optional[int],
    unix_range_start: Optional[int],
    unix_range_end: Optional[int],
    card_number: Optional[str] = None
):
    """
    Генерация сообщения о загрузке данных в бд.
    """
    unix_ms_day = 24 * 60 * 60 * 1000

    card_message = f"по карте {card_number}" if card_number else "по всем картам"

    if min_timestamp and max_timestamp:
        if min_timestamp - unix_range_start < unix_ms_day and unix_range_end - max_timestamp < unix_ms_day:
            return f"Данные были загружены из БД. Данные за весь выбранный период загружены {card_message}."
        elif abs(min_timestamp) > abs(unix_range_start) or abs(max_timestamp) < abs(unix_range_end):
            start_date = datetime.fromtimestamp(min_timestamp / 1000).strftime("%d.%m.%Y")
            end_date = datetime.fromtimestamp(max_timestamp / 1000).strftime("%d.%m.%Y")
            if start_date != end_date:
                return f"Данные были загружены из БД за период {start_date} - {end_date} {card_message}."
            else:
                return f"Данные были загружены из БД за день {start_date} {card_message}."
    return f"Данные были загружены из БД. Часть данных за выбранный период отсутствует {card_message}."