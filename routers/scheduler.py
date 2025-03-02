# routes/scheduler.py

# Стандартные модули Python
from datetime import datetime

# Сторонние модули
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

# Собственные модули
from routers.directory.tinkoff.scheduler import set_export_time

from utils.tinkoff.scheduler_utils import update_scheduler

from dependencies import get_authenticated_user

from models import ScheduleData

from database import Session



router = APIRouter()

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@router.put("/tinkoff/schedular/")
async def update_schedule(schedule_data: ScheduleData, 
                          db: Session = Depends(get_db),
                          user: dict = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse):
        print("пользователь не аутентифицирован") # return user  # Если пользователь не аутентифицирован

    try:
        # Добавляем текущую дату к строке времени
        current_date = datetime.now().date()
        expenses_time_str = f"{current_date}T{schedule_data.expenses}"
        full_time_str = f"{current_date}T{schedule_data.full}"

        # Преобразуем строки в datetime.time объекты
        expenses_time = datetime.fromisoformat(expenses_time_str).time()
        full_time = datetime.fromisoformat(full_time_str).time()

        if expenses_time:
            set_export_time(db=db, export_type="expenses", export_time=expenses_time)
            print(f"Изменено время первой выгрузки: {expenses_time}")
        if full_time:
            set_export_time(db=db, export_type="full", export_time=full_time)
            print(f"Изменено время второй выгрузки: {full_time}")
        
        update_scheduler(expenses_time, full_time)
    except Exception as e:
        print(f"Ошибка при изменении времени выгрузки расходов: {str(e)}")
        return {"message": "Не удалось обновить расписание"}

    return {"message": "Расписание успешно обновлено", "expenses": expenses_time, "full": full_time}