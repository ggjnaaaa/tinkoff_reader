# routes/directory/tinkoff/categories.py

# Сторонние модули
from fastapi import HTTPException
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.future import select

# Собственные модули
from models import CategoryExpenses, Expense


def get_categories_from_db(db):
    """
    Получение категорий из базы данных (с цветом).
    """
    # Запрашиваем категории с цветом
    query = select(CategoryExpenses).order_by(CategoryExpenses.id)
    result = db.execute(query)
    
    # Извлекаем категории из результата
    categories = result.scalars().all()

    # Создаем список категорий
    categories_list = [
        {
            "id": category.id,
            "category_name": category.title,
            "color": category.color  # Добавляем поле для цвета
        }
        for category in categories
    ]
    
    return categories_list


def update_expense_category(db: Session, expense_id: int, category_id: Optional[int]):
    """
    Обновляет категорию у расхода или очищает её.
    :param db: Сессия БД
    :param expense_id: ID расхода
    :param category_id: ID категории (или None для очистки)
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail=f"Расход с ID {expense_id} не найден")

    category = None
    if category_id == 'null' or category_id == '':
        category_id = None
        
    if category_id:
        category = db.query(CategoryExpenses).filter(CategoryExpenses.id == category_id).first()
        if not category:
            raise HTTPException(status_code=422, detail=f"Категория с ID {category_id} не найдена")
    
    print(f"Для расхода {expense.description} с id {expense.id} изменена категория на {category.title if category else None}")

    expense.category_id = category_id  # Устанавливаем или очищаем категорию
    db.commit()