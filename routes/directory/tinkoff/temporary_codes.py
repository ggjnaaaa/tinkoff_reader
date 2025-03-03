# routes/directory/tinkoff/temporary_codes.py

# Сторонние модули
from sqlalchemy.orm import Session

# Собственные модули
from models import TemporaryCode


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