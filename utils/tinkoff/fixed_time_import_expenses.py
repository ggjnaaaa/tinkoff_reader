# fixed_time_import_expenses.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import asyncio
import threading

def scheduled_task():
    print("Задача выполнена!")

# Инициализируем и запускаем планировщик
def start_scheduler():
    scheduler = AsyncIOScheduler(timezone=timezone('Europe/Moscow'))
    scheduler.add_job(scheduled_task, CronTrigger(hour=1, minute=8))
    scheduler.start()

# Запуск в отдельном потоке
scheduler_thread = threading.Thread(target=start_scheduler)
scheduler_thread.start()