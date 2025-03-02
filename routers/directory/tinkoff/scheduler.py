# routes/directory/tinkoff/scheduler.py

from sqlalchemy.orm import Session
from models import Schedule  # Импорт модели
from datetime import time


def get_import_times(db: Session) -> dict:
    """
    Получить все времена экспорта пользователя в виде словаря {export_type: export_time}.
    """
    schedules = db.query(Schedule).all()
    return {s.export_type: s.export_time for s in schedules}


def set_export_time(db: Session, export_type: str, export_time: time):
    """
    Установить или обновить время экспорта для указанного типа.
    """
    schedule = db.query(Schedule).filter(
        Schedule.export_type == export_type
    ).first()

    if schedule:
        schedule.export_time = export_time  # Обновляем
    else:
        new_schedule = Schedule(export_type=export_type, export_time=export_time)
        db.add(new_schedule)  # Добавляем новую запись

    db.commit()


def delete_export_time(db: Session, export_type: str):
    """
    Удалить запись времени экспорта.
    """
    db.query(Schedule).filter(
        Schedule.export_type == export_type
    ).delete()
    db.commit()