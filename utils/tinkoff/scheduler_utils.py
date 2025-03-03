# utils/tinkoff/scheduler_utils.py

# Стандартные модули Python
import logging

# Сторонние модули


# Собственные модули
from utils.tinkoff.expense_scheduler import ExpenseScheduler

from routes.directory.tinkoff.scheduler import get_import_times

from database import Session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = None


def start_scheduler():
    global scheduler
    db = Session()
    export_times = get_import_times(db)
    if not export_times:
        return
    
    scheduler = ExpenseScheduler()
    scheduler.start_schedules(export_times)


def update_scheduler(expenses_time, full_time):
    global scheduler
    if not scheduler:
        start_scheduler()
    
    if expenses_time:
        scheduler.update_schedule(export_type="expenses", export_time=expenses_time)
    if full_time:
        scheduler.update_schedule(export_type="full", export_time=full_time)