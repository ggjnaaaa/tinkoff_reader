# tinkoff_expenses.py

# Стандартные модули Python
from typing import Optional
from datetime import datetime

# Сторонние модули
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sqlalchemy.future import select
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

from config import TRANSFER_NOTIFICATION_USERS


def get_expenses_from_db(
    db: Session,
    unix_range_start: Optional[int] = None,
    unix_range_end: Optional[int] = None,
    timezone_str: str = "Europe/Moscow",
    card_number: Optional[str] = None,
    sort_order: str = "desc"  # Новый параметр: "asc" (от раннего) или "desc" (от позднего)
):
    """
    Получение расходов за выбранный период из базы данных.
    """
    query = db.query(Expense)

    # Фильтрация по дате
    if unix_range_start:
        query = query.filter(Expense.timestamp >= unix_range_start)
    if unix_range_end:
        query = query.filter(Expense.timestamp <= unix_range_end)

    # Фильтрация по номеру карты
    if card_number:
        if card_number in TRANSFER_NOTIFICATION_USERS:
            query = query.filter(
                (Expense.card_number == "*" + card_number) | (Expense.card_number == "")
            )
        else:
            query = query.filter(Expense.card_number == "*" + card_number)

    # Сортировка по дате
    if sort_order == "desc":
        query = query.order_by(desc(Expense.timestamp))  # Сортировка от позднего к раннему
    else:
        query = query.order_by(Expense.timestamp)  # Сортировка от раннего к позднему

    expenses = query.all()

    # Определяем минимальный и максимальный timestamp
    if expenses:
        min_timestamp = min(expense.timestamp for expense in expenses)
        max_timestamp = max(expense.timestamp for expense in expenses)
        period_message = generate_period_message(min_timestamp, max_timestamp, unix_range_start, unix_range_end, card_number)
    else:
        period_message = "Данные не найдены за выбранный период."

    categories_dict = get_categories_with_keywords(db)

    # Формируем итоговый ответ
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

    result = {
        "expenses": expenses_list,
        "message": period_message
    }

    if not card_number:
        unique_cards = list({expense.card_number for expense in expenses})
        result.update({"cards": unique_cards, "source": "database"})

    return result


def get_category_from_description(categories_dict, current_expense):
    """
    Получение категории по описанию.
    """
    for category_title, data in categories_dict.items():
        if any(keyword.lower() in current_expense.description.lower() for keyword in data["keywords"]):
            return category_title


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
            "category_name": category.title
        }
        for category in categories
    ]
    
    return categories_list


def get_categories_with_keywords(db):
    """
    Получение категорий с ключевыми словами из базы данных.
    """
    # Запрашиваем категории и ключевые слова
    query = (
        select(
            CategoryExpenses.id,  # ID категории
            CategoryExpenses.title,  # Название категории
            CategoryKeyword.keyword  # Ключевое слово
        )
        .join(
            CategoryKeyword,
            CategoryKeyword.category_id == CategoryExpenses.id,
            isouter=True  # Левое соединение, чтобы захватить категории без ключевых слов
        )
    )
    result = db.execute(query)
    
    # Обрабатываем результат
    categories = {}
    for category_id, category_title, keyword in result:
        if category_id not in categories:
            categories[category_title] = {
                "id": category_id,
                "keywords": []
            }
        if keyword:  # Добавляем только существующие ключевые слова
            categories[category_title]["keywords"].append(keyword)
    
    return categories


def save_keyword_to_db(db: Session, description: str, category_id: int):
    """
    Сохранение ключевых слов в бд.
    """
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
    """
    Удаление ключевого слова из всех категорий.
    """
    db.query(CategoryKeyword).filter(CategoryKeyword.keyword == description).delete(synchronize_session=False)
    db.commit()
    print(f"Ключевое слово '{description}' удалено из всех категорий.")


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


def set_temporary_code(db: Session, code: str):
    """
    Задать новый временный код, перезаписывая старый, если он есть.
    """
    existing_code = db.query(TemporaryCode).first()
    if existing_code:
        existing_code.code = code
    else:
        new_code = TemporaryCode(code=code)
        db.add(new_code)
    db.commit()


def get_temporary_code(db: Session) -> str:
    """
    Получить временный код. 
    Если записей нет или их больше одной, выбросить ошибку. 
    При наличии нескольких записей удалить лишние.
    """
    codes = db.query(TemporaryCode).all()

    if not codes:
        raise ValueError("Временный код не найден.")
    
    if len(codes) > 1:
        # Удаляем все записи и выбрасываем ошибку
        db.query(TemporaryCode).delete()
        db.commit()
        raise ValueError("Найдено несколько временных кодов. Все записи удалены.")

    # Если есть только одна запись, возвращаем её код
    return codes[0].code


def set_last_error(db: Session, error_text: str):
    """
    Записать последнюю ошибку, перезаписывая старую запись, если она есть.
    """
    existing_error = db.query(LastError).first()
    if existing_error:
        existing_error.error_text = error_text
        existing_error.error_time = datetime.now()
    else:
        new_error = LastError(error_text=error_text)
        db.add(new_error)
    db.commit()


def delete_last_error(db: Session):
    """
    Удалить последнюю ошибку из базы данных.
    """
    db.query(LastError).delete()
    db.commit()


def get_last_unreceived_error(db: Session):
    """
    Получить последнюю неполученную ошибку и отметить её как полученную.
    """
    last_error = db.query(LastError).filter_by(is_received=False).order_by(LastError.error_time.desc()).first()
    if last_error:
        last_error.is_received = True  # Отмечаем ошибку как полученную
        db.commit()
    return last_error