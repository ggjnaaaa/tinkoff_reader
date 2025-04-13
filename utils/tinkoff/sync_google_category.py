# utils/tinkoff/sync_google_category.py

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
import queue
import threading
from typing import Literal

import gspread
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from routes.directory.tinkoff.categories import get_categories_from_db, update_expense_category

from database import Session

from config import GOOGLE_SHEETS_API_EXPENSES_SCRIPT, GOOGLE_SHEETS_URL



SyncTask = Literal["sync_categories", "auto_export", "shutdown"]  # Типы задач для очереди
sync_queue = queue.Queue(maxsize=10)  # Очередь задач (макс. 100 задач в очереди)
sheets_lock = threading.Lock()  # Блокировка для gspread (на все операции с таблицей)

# Отключаем стандартные логи APScheduler
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('apscheduler.scheduler').propagate = False
logging.getLogger('apscheduler.executors.default').propagate = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
current_job = None

_gsheets_client = None
_gsheets_worksheet = None


def sync_worker():
    logger.info("Синхронизатор категорий запущен")
    
    while True:
        try:
            # Получаем задачу из очереди (блокирующий вызов)
            task: SyncTask = sync_queue.get(block=True)
            
            if task == "shutdown":
                logger.info("Завершение работы синхронизатора")
                sync_queue.task_done()
                break
                
            elif task == "sync_categories":
                logger.debug("Начало синхронизации категорий")
                try:
                    # Безопасная работа с таблицей
                    with sheets_lock:
                        get_categories_from_google_sheets()
                except Exception as e:
                    logger.error(f"Ошибка синхронизации: {e}")
                finally:
                    sync_queue.task_done()

        except Exception as e:
            logger.critical(f"Критическая ошибка в worker: {e}", exc_info=True)


def request_sync():
    try:
        sync_queue.put("sync_categories", block=True, timeout=5)
        logger.debug("Запрос на синхронизацию добавлен в очередь")
        sync_queue.join()
        logger.debug("Синхронизация завершена")
    except queue.Full:
        logger.warning("Очередь синхронизации переполнена")


def shutdown_sync():
    sync_queue.put("shutdown")
    scheduler.shutdown()


def init_gsheets():
    global _gsheets_client, _gsheets_worksheet
    _gsheets_client = gspread.service_account("credentials.json")
    _gsheets_worksheet = _gsheets_client.open_by_url(GOOGLE_SHEETS_URL).worksheet("HiddenChanges")


def start_inactivity_scheduler():
    init_gsheets()

    # Запускаем worker-поток
    worker_thread = threading.Thread(
        target=sync_worker,
        name="GoogleSheetsSyncWorker",
        daemon=True  # Автозавершение при выходе из main
    )
    worker_thread.start()

    scheduler.start()  
    schedule_next_run(immediate=True)

def schedule_next_run(immediate=False):
    global current_job
    
    # Удаляем предыдущую задачу если существует
    if current_job and current_job in scheduler.get_jobs():
        try:
            scheduler.remove_job(current_job.id)
        except Exception as e:
            logger.debug(f"Задача уже удалена: {e}")
    
    # Определяем время следующего выполнения
    if immediate:
        next_run_time = datetime.now() + timedelta(seconds=30)
    else:
        next_run_time = datetime.now() + timedelta(minutes=3)  # Пауза 3 минуты
    
    # Создаем новую задачу
    current_job = scheduler.add_job(
        lambda: asyncio.run(check_for_inactivity()),
        'date',
        run_date=next_run_time,
        max_instances=1
    )

    logger.debug(f"Запланирована следующая проверка на {next_run_time}")


async def check_for_inactivity():
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                GOOGLE_SHEETS_API_EXPENSES_SCRIPT,
                params={"action": "check_inactivity"},
                timeout=aiohttp.ClientTimeout(total=60.0)
            ) as response:
                
                if response.status == 200:
                    response_text = (await response.text()).strip().lower()
                    
                    if response_text == "true: ready to process":
                        print(response_text)
                        print("Категории обновлены")
                        get_categories_from_google_sheets()
                        schedule_next_run(immediate=False)
                    elif "no changes detected" in response_text:
                        print("Нет изменений")
                        schedule_next_run(immediate=False)
                    elif "waiting period not passed" in response_text:
                        print("Время ожидания не прошло")
                        schedule_next_run(immediate=True)
                    else:
                        logger.warning(f"Неизвестный ответ от GAS: {response_text}")
                        schedule_next_run(immediate=True)
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка запроса. Код: {response.status}\n{error_text}")
                    schedule_next_run(immediate=True)
    
    except Exception as e:
        logger.error(f"Ошибка проверки на неактивность: {str(e)}")
        schedule_next_run(immediate=True)


def get_categories_from_google_sheets():
    db = Session()
    try:
        db_categories = {category["category_name"].strip().lower(): category["id"] for category in get_categories_from_db(db)}

        google_categories = get_hidden_sheet_categories()

        for category_name, expense_id in google_categories.items():
            if category_name in db_categories:
                print(expense_id, db_categories[category_name])
                update_expense_category(db, expense_id, db_categories[category_name])
            else:
                logger.info(f"Категория {category_name} не нашлась в базе данных")
    finally:
        db.close()


def get_hidden_sheet_categories():
    try:
        values = _gsheets_worksheet.get_all_values()

        logger.info(values)
        
        categories = {}
        for value in values:
            if value[3] and value[4]:
                categories[value[3].strip().lower()] = value[4]
        
        _gsheets_worksheet.clear()
        
        return categories
    
    except Exception as e:
        logger.error("Ошибка при получении категорий из HiddenSheet: %s", str(e))
