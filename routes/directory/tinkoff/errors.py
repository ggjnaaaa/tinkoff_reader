# routes/directory/tinkoff/errors.py

# Стандартные модули Python
from datetime import datetime

# Сторонние модули
from sqlalchemy.orm import Session

# Собственные модули
from models import LastError


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