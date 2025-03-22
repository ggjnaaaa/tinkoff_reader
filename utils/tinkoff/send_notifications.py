# utils/tinkoff/send_notifications.py

# Стандартные модули Python
import requests
from datetime import datetime
from collections import defaultdict

# Собственные модули
import config

from models import Users, TgTmpUsers

from routes.directory.tinkoff.expenses import get_expenses_from_db
from routes.directory.tinkoff.notifications import get_chat_ids_for_error_notifications, get_chat_ids_for_transfer_notifications
from routes.directory.tinkoff.users_info import get_all_cards_by_chat_ids

from utils.tinkoff.time_utils import get_period_range


def send_expense_notification(db):
    """
    Вызывает эндпоинт на сервере бота для рассылки уведомлений.
    """
    try:
        # Получаем расходы за сегодня
        today_expenses = get_today_expenses(db)

        # Считаем суммы по картам
        expenses_by_cards = calculate_expenses_by_cards(today_expenses)

        # Получаем уникальные карты (включая пустую строку)
        unique_cards = set(card.lstrip('*') for card in expenses_by_cards.keys())

        # Получаем transfer_chat_ids и chat_ids
        transfer_chat_ids = get_chat_ids_for_transfer_notifications(db)
        chat_ids = None

        if unique_cards:
            # Получение chat_id из TgTmpUsers с проверкой наличия card_number в Users
            chat_ids = db.query(TgTmpUsers.chat_id).join(Users).filter(
                Users.card_number.in_(unique_cards)  # Фильтруем только по картам из unique_cards
            ).all()
        
        # Преобразование результата в список
        chat_ids = list(set(str(chat_id[0]) for chat_id in chat_ids)) #| set(transfer_chat_ids))

        # Получаем сегодняшнюю дату в формате "19 ноября"
        today_date = format_today_date()

        # Подготавливаем данные для отправки
        notification_data = prepare_notification_data(db, expenses_by_cards, transfer_chat_ids, chat_ids)

        # Отправляем данные на сервер бота
        response = requests.post(
            config.AUTO_SAVE_MAILING_BOT_API_URL,
            json={
                "notification_data": notification_data,  # Словарь с суммами для каждого chat_id
                "today_date": today_date  # Сегодняшняя дата
            },
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
    

def get_today_expenses(db):
    # Определяем временные диапазоны
    unix_range_start, unix_range_end = get_period_range(
        timezone="Europe/Moscow",
        range_start='2023-01-01',
        range_end='2025-03-22'
        # period='day'
    )

    # Получаем данные расходов
    expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, "Europe/Moscow")

    return expenses_data


def calculate_expenses_by_cards(expenses):
    """
    Возвращает словарь, где ключ — это номер карты, а значение — сумма расходов по этой карте.
    """
    expenses_by_cards = defaultdict(float)

    for expense in expenses.get('expenses'):
        card_number = expense['card_number']
        amount = expense['amount']
        expenses_by_cards[card_number] += amount 
    
    expenses_by_cards = {card: round(total, 2) for card, total in expenses_by_cards.items()}

    return expenses_by_cards


def format_today_date():
    """
    Возвращает сегодняшнюю дату в формате "19 марта".
    """
    today = datetime.now()
    return today.strftime("%d %B").replace(" 0", " ") 


def prepare_notification_data(db, expenses_by_cards, transfer_chat_ids, chat_ids):
    """
    Подготавливает данные для отправки уведомлений.
    Возвращает словарь, где ключ — это chat_id, а значение — сумма расходов.
    """
    # Общая сумма всех расходов
    total_expenses = sum(expenses_by_cards.values())

    all_chat_ids = set(transfer_chat_ids + chat_ids) 
    cards_by_chat_id = get_all_cards_by_chat_ids(db, all_chat_ids)

    notification_data = {}

    for chat_id in transfer_chat_ids:
        cards = cards_by_chat_id.get(chat_id, []) 
        sum_transfers = expenses_by_cards.get('', 0)
        sum_by_card = sum(expenses_by_cards.get("*" + card, 0) for card in cards)
        notification_data[chat_id] = (
            f"{total_expenses} \n"
            f"Сумма по переводам: {sum_transfers} \n"
            f"Сумма по вашей карте: {sum_by_card}"
        )

    for chat_id in chat_ids:
        if chat_id in notification_data:
            continue

        cards = cards_by_chat_id.get(chat_id, []) 
        total_for_chat = sum(expenses_by_cards.get("*" + card, 0) for card in cards)
        notification_data[chat_id] = str(total_for_chat)

    return notification_data

