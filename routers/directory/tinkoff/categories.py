# routes/directory/tinkoff/categories.py

# Сторонние модули
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

# Собственные модули
from models import CategoryExpenses, CategoryKeyword


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
        if category_title not in categories:
            categories[category_title] = {
                "id": category_id,
                "keywords": []
            }
        if keyword:  # Добавляем только существующие ключевые слова
            categories[category_title]["keywords"].append(keyword)
    
    return categories


def get_category_from_description(categories_dict, current_expense):
    """
    Получение категории по описанию.
    """
    for category_title, data in categories_dict.items():
        if any(keyword.lower() in current_expense.description.lower() for keyword in data["keywords"]):
            return category_title
        

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