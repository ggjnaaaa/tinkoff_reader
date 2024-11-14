from sqlalchemy.orm import Session, selectinload
from datetime import datetime, timedelta
from sqlalchemy import and_, desc
from sqlalchemy.future import select
from typing import Optional, List, Dict
from fastapi import HTTPException, Query
from sqlalchemy.exc import IntegrityError

# Собственные модули
from utils.tinkoff.time_utils import (
    get_unix_time_ms_from_string,
    convert_unix_to_local_datetime
)
from models import (
    Expense, 
    CategoryExpenses,
    CategoryKeyword,
    TemporaryCode, 
    LastError
) 

def get_expenses_from_db(
    db: Session,
    unix_range_start: Optional[int] = None,
    unix_range_end: Optional[int] = None,
    timezone_str: str = "Europe/Moscow"  # Указание часового пояса
):
    """
    Получение расходов за выбранный период из базы данных.
    """
    query = db.query(Expense)
    
    if unix_range_start:
        query = query.filter(Expense.timestamp >= unix_range_start)
    if unix_range_end:
        query = query.filter(Expense.timestamp <= unix_range_end)

    query = query.order_by(desc(Expense.timestamp))
    expenses = query.all()
    
    # Получаем уникальные карты
    unique_cards = list({expense.card_number for expense in expenses})

    # Определяем минимальный и максимальный timestamp
    if expenses:
        min_timestamp = min(expense.timestamp for expense in expenses)
        max_timestamp = max(expense.timestamp for expense in expenses)
        period_message = generate_period_message(min_timestamp, max_timestamp, unix_range_start, unix_range_end)
    else:
        period_message = "Данные не найдены за выбранный период."

    categories_dict = get_categories_with_keywords(db)

    # Формируем итоговый ответ
    expenses_list = [
        {
            "id": expense.id,
            "date_time": convert_unix_to_local_datetime(expense.timestamp, timezone_str),
            "card_number": expense.card_number,
            "amount": float(abs(expense.amount)),
            "description": expense.description,
            "category": get_category_from_description(categories_dict, expense) or "Не указана"
        }
        for expense in expenses
    ]
    return {
        "expenses": expenses_list,
        "cards": unique_cards,
        "source": "database",
        "message": period_message
    }

def get_category_from_description(categories_dict, current_expense):
    for category_title, data in categories_dict.items():
        if any(keyword.lower() in current_expense.description.lower() for keyword in data["keywords"]):
            return category_title

def save_expenses_to_db(db, expenses, time_zone):
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


def get_categories_from_db(db):
    """
    Получение категорий из базы данных (без ключевых слов).
    """
    # Запрашиваем только категории
    query = select(CategoryExpenses)
    result = db.execute(query)
    
    # Извлекаем категории из результата
    categories = result.scalars().all()

    # Создаем список категорий
    categories_list = [
        {
            "id": category.id,
            "category_name": category.title  # Здесь название поля совпадает с ожидаемым в JavaScript
        }
        for category in categories
    ]
    
    return categories_list


def get_categories_with_keywords(db: Session):
    """
    Получение категорий с ключевыми словами из базы данных.
    """
    # Запрашиваем категории и присоединяем к ним ключевые слова с помощью join
    query = db.query(CategoryExpenses, CategoryKeyword.keyword).join(
        CategoryKeyword, CategoryKeyword.category_id == CategoryExpenses.id, isouter=True
    )

    # Извлекаем данные из результата запроса
    categories_dict = {}
    for category, keyword in query.all():
        if category.title not in categories_dict:
            categories_dict[category.title] = {"keywords": []}
        if keyword:
            categories_dict[category.title]["keywords"].append(keyword)
    
    return categories_dict

def save_keyword_to_db(db: Session, description: str, category_id: int):
    # Проверяем, если ключевое слово уже существует в таблице, независимо от категории
    existing_keyword = db.query(CategoryKeyword).filter(
        CategoryKeyword.keyword == description
    ).first()
    
    if not existing_keyword:
        # Создаем новую запись для ключевого слова
        new_keyword = CategoryKeyword(
            keyword=description,
            category_id=category_id
        )
        try:
            db.add(new_keyword)
            db.commit()  # Сохраняем изменения в базе данных
            db.refresh(new_keyword)  # Обновляем объект для получения ID, если нужно
            print(f"Ключевое слово '{description}' добавлено для категории с ID {category_id}")
        except IntegrityError:
            db.rollback()  # Откатить транзакцию в случае ошибки
            print(f"Ключевое слово '{description}' уже существует и не может быть добавлено.")
    else:
        # Если слово уже существует, обновляем категорию
        existing_keyword.category_id = category_id
        db.commit()
        print(f"Ключевое слово '{description}' обновлено для новой категории с ID {category_id}")
    
    return

def remove_keyword_from_category(db: Session, description: str):
    """Удаление ключевого слова из всех категорий."""
    db.query(CategoryKeyword).filter(CategoryKeyword.keyword == description).delete(synchronize_session=False)
    db.commit()
    print(f"Ключевое слово '{description}' удалено из всех категорий.")

def generate_period_message(min_timestamp, max_timestamp, unix_range_start, unix_range_end):
    unix_ms_day = 24 * 60 * 60 * 1000

    if min_timestamp - unix_range_start < unix_ms_day and unix_range_end - max_timestamp < unix_ms_day:
        return "Данные были загружены из БД. Данные за весь выбранный период загружены"
    elif abs(min_timestamp) > abs(unix_range_start) or abs(max_timestamp) < abs(unix_range_end):
        start_date = datetime.fromtimestamp(min_timestamp / 1000).strftime("%d.%m.%Y")
        end_date = datetime.fromtimestamp(max_timestamp / 1000).strftime("%d.%m.%Y")
        return f"Данные были загружены из БД за период {start_date} - {end_date}" if start_date != end_date else f"Данные были загружены из БД за день {start_date}"
    else:
        return "Данные были загружены из БД. Часть данных за выбранный период отсутствует"

def set_temporary_code(db: Session, code: str):
    """Задать новый временный код, перезаписывая старый, если он есть."""
    existing_code = db.query(TemporaryCode).first()
    if existing_code:
        existing_code.code = code
    else:
        new_code = TemporaryCode(code=code)
        db.add(new_code)
    db.commit()

def set_last_error(db: Session, error_text: str):
    """Записать последнюю ошибку, перезаписывая старую запись, если она есть."""
    existing_error = db.query(LastError).first()
    if existing_error:
        existing_error.error_text = error_text
        existing_error.error_time = datetime.now()
    else:
        new_error = LastError(error_text=error_text)
        db.add(new_error)
    db.commit()

def delete_last_error(db: Session):
    """Удалить последнюю ошибку из базы данных."""
    db.query(LastError).delete()
    db.commit()

def get_last_unreceived_error(db: Session):
    """Получить последнюю неполученную ошибку и отметить её как полученную."""
    last_error = db.query(LastError).filter_by(is_received=False).order_by(LastError.error_time.desc()).first()
    if last_error:
        last_error.is_received = True  # Отмечаем ошибку как полученную
        db.commit()
    return last_error