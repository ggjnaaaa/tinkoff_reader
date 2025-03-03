# utils/tinkoff/send_notifications.py

# Стандартные модули Python
import requests

# Собственные модули
import config

from models import Users, TgTmpUsers

from routes.directory.tinkoff.expenses import get_expenses_from_db
from routes.directory.tinkoff.notifications import get_chat_ids_for_error_notifications, get_chat_ids_for_transfer_notifications

from utils.tinkoff.time_utils import get_period_range


def send_expense_notification(db):
    """
    Вызывает эндпоинт на сервере бота для рассылки уведомлений пользователям у которых были расходы за сегодня.
    """
    try:
        # Получаем уникальные карты за сегодня
        try:
            unique_cards = set([card.lstrip('*') for card in get_today_uniq_cards(db)])  # Убираем звезды из начала карт
        except Exception as e:
            print(f"{e}")
            return

        transfer_chat_ids = get_chat_ids_for_transfer_notifications(db)
        chat_ids = None

        if not unique_cards and not transfer_chat_ids:
            return
        
        if unique_cards:
            # Получение chat_id из TgTmpUsers с проверкой наличия card_number в Users
            chat_ids = db.query(TgTmpUsers.chat_id).join(Users).filter(
                Users.card_number.in_(unique_cards)  # Фильтруем только по картам из unique_cards
            ).all()
        
        # Преобразование результата в список
        chat_ids = list(set(str(chat_id[0]) for chat_id in chat_ids) | set(transfer_chat_ids))

        response = requests.post(
            config.AUTO_SAVE_MAILING_BOT_API_URL,
            json={"chat_ids": chat_ids},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при отправке данных на сервер бота: {e}")


def send_error_notification(db):
    """
    Отправляет сообщение об ошибке определенным пользователям
    """
    try:
        chat_ids = get_chat_ids_for_error_notifications(db)

        response = requests.post(
            config.AUTO_SAVE_ERROR_MAILING_BOT_API_URL,
            json={"chat_ids": chat_ids},
            timeout=10
        )
        response.raise_for_status()

        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при отправке данных на сервер бота: {e}")


def get_today_uniq_cards(db):

    # Определяем временные диапазоны
    unix_range_start, unix_range_end = get_period_range(
        timezone="Europe/Moscow",
        period='day'
    )

    # Получаем данные расходов
    expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, "Europe/Moscow")
    cards = expenses_data.get("cards", None)

    if cards:
        return set(cards)
    
    raise Exception('Расходы за день отсутствуют')