# routes/directory/tinkoff/expenses.py

# Стандартные модули Python
from typing import Optional

# Сторонние модули
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sqlalchemy.future import select

# Собственные модули
from utils.tinkoff.time_utils import (
    get_unix_time_ms_from_string,
    convert_unix_to_local_datetime
)

from models import Expense

from routes.directory.tinkoff.utils import generate_period_message
from routes.directory.tinkoff.categories import get_categories_with_keywords, get_category_from_description
from routes.directory.tinkoff.notifications import get_card_nums_for_transfer_notifications


def filter_by_date(query, unix_range_start, unix_range_end):
    if unix_range_start:
        query = query.filter(Expense.timestamp >= unix_range_start)
    if unix_range_end:
        query = query.filter(Expense.timestamp <= unix_range_end)
    return query


def filter_by_card_number(query, db, card_number, show_all_expenses):
    transfer_notifications_users = get_card_nums_for_transfer_notifications(db)
    is_card_number_in_transfer_users = card_number in transfer_notifications_users
    show_all_expenses = show_all_expenses if is_card_number_in_transfer_users else False
    
    if card_number and not show_all_expenses:
        if card_number in transfer_notifications_users:
            query = query.filter(
                (Expense.card_number == "*" + card_number) | (Expense.card_number == "")
            )
        else:
            query = query.filter(Expense.card_number == "*" + card_number)
    return query


def sort_expenses(query, sort_order):
    if sort_order == "desc":
        query = query.order_by(desc(Expense.timestamp))  # Сортировка от позднего к раннему
    else:
        query = query.order_by(Expense.timestamp)  # Сортировка от раннего к позднему
    return query


def generate_period_message_for_expenses(expenses, unix_range_start, unix_range_end, card_number):
    if expenses:
        min_timestamp = min(expense.timestamp for expense in expenses)
        max_timestamp = max(expense.timestamp for expense in expenses)
        return generate_period_message(min_timestamp, max_timestamp, unix_range_start, unix_range_end, card_number)
    else:
        return "Данные не найдены за выбранный период."


def format_expenses_response(expenses, categories_dict, timezone_str, card_number):
    expenses_list = [
        {
            "id": expense.id,
            "amount": float(abs(expense.amount)),
            "description": expense.description,
            "category": get_category_from_description(categories_dict, expense) or "Не указана"
        }
        for expense in expenses
    ]
    
    # Добавление дополнительных полей, если номер карты не указан
    if not card_number:
        for expense_item, expense in zip(expenses_list, expenses):
            expense_item.update({
                "date_time": convert_unix_to_local_datetime(expense.timestamp, timezone_str),
                "card_number": expense.card_number
            })

    return expenses_list



def get_expenses_from_db(
    db: Session,
    unix_range_start: Optional[int] = None,
    unix_range_end: Optional[int] = None,
    timezone_str: str = "Europe/Moscow",
    card_number: Optional[str] = None,
    show_all_expenses: bool = False,
    sort_order: str = "desc"  # "asc" (от раннего) или "desc" (от позднего)
):
    """
    Получение расходов за выбранный период из базы данных.
    """
    query = db.query(Expense)
    
    # Применение фильтрации по дате
    query = filter_by_date(query, unix_range_start, unix_range_end)
    
    # Применение фильтрации по номеру карты
    query = filter_by_card_number(query, db, card_number, show_all_expenses)
    
    # Применение сортировки
    sort_order = 'asc' if card_number else sort_order
    query = sort_expenses(query, sort_order)
    
    expenses = query.all()
    
    # Генерация сообщения о периоде
    period_message = generate_period_message_for_expenses(expenses, unix_range_start, unix_range_end, card_number)
    
    categories_dict = get_categories_with_keywords(db)
    
    # Формирование списка расходов
    expenses_list = format_expenses_response(expenses, categories_dict, timezone_str, card_number)
    
    result = {
        "expenses": expenses_list,
        "message": period_message
    }
    
    if not card_number:
        unique_cards = list({expense.card_number for expense in expenses})
        result.update({"cards": unique_cards, "source": "database"})
    
    return result


def save_expenses_to_db(db, expenses, time_zone):
    """
    Сохранение расходов в бд.
    """
    for expense in expenses:
        # Перевод времени в Unix-формат
        timestamp = get_unix_time_ms_from_string(expense["date_time"], time_zone)

        # Проверяем, существует ли расход с такими же параметрами
        query = select(Expense).where(
            and_(
                Expense.timestamp == timestamp,
                Expense.card_number == expense["card_number"],
                Expense.amount == expense["amount"],
                Expense.description == expense["description"],
            )
        )

        result = db.execute(query)
        existing_expense = result.scalars().first()

        # Если такого расхода нет, добавляем его в базу
        if existing_expense is None:
            new_expense = Expense(
                timestamp=timestamp,
                card_number=expense["card_number"],
                amount=expense["amount"],
                description=expense["description"],
            )
            db.add(new_expense)
    
    # Сохраняем все изменения в базе данных
    db.commit()