# utils/tinkoff/fixed_time_import_expenses.py

# Стандартные модули Python
import time
import logging
from datetime import datetime, timezone, timedelta
import pytz

# Сторонние модули
from fastapi import HTTPException

# Собственные модули
import config

from database import Session

from routes.directory.tinkoff.errors import set_last_error
from routes.directory.tinkoff.expenses import save_expenses_to_db
from routes.directory.tinkoff.categories import get_categories_with_keywords
from routes.directory.tinkoff.scheduler import get_import_times
from routes.directory.tinkoff.temporary_codes import get_temporary_code

from utils.tinkoff.time_utils import get_period_range
from utils.tinkoff.browser_manager import BrowserManager
from utils.tinkoff.expenses_google_sheets import sync_expenses_to_sheet_no_id
from utils.tinkoff.browser_utils import PageType, detect_page_type
from utils.tinkoff.browser_input_utils import otp_page, check_for_error_message
from utils.tinkoff.send_notifications import send_error_notification, send_expense_notification
from utils.tinkoff.expenses_utils import (
    expenses_redirect,
    download_csv_from_expenses_page,
    get_json_expenses_from_csv,
    wait_for_new_download
)

from auth import verify_bot_token


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Московский часовой пояс
moscow_tz = pytz.timezone("Europe/Moscow")


async def resume_load_expenses(db, token):
    # Получаем текущее время в Москве
    now = datetime.now(moscow_tz)

    # Декодируем auth_date из Unix timestamp
    user_data = verify_bot_token(token)
    auth_date = int(user_data.get("auth_date", 0))
    error_date = datetime.fromtimestamp(auth_date, moscow_tz).date()

    # Получаем времена из базы
    schedule_time = get_import_times(db)
    expense_time = schedule_time["expenses"]
    full_time = schedule_time["full"]

    # Конвертируем `time` в `datetime` для удобного сравнения
    expense_datetime = moscow_tz.localize(datetime.combine(error_date, expense_time))
    full_datetime = moscow_tz.localize(datetime.combine(error_date, full_time))
    
    # Добавляем 5-минутный интервал
    five_min = timedelta(minutes=5)

    # Проверяем условия
    if now >= expense_datetime and now >= full_datetime:
        await load_expenses("all")  # Оба времени прошли
    elif now >= expense_datetime and (full_datetime - datetime.now(moscow_tz) <= five_min):
        await load_expenses("all")  # Expense прошло, до Full < 5 мин
    elif now >= full_datetime and (expense_datetime - datetime.now(moscow_tz) <= five_min):
        await load_expenses("all")  # Full прошло, до Expense < 5 мин
    elif now >= expense_datetime and (full_datetime - datetime.now(moscow_tz) > five_min):
        await load_expenses("expenses") # Expense прошло, до Full > 5 мин
    elif now >= full_datetime and (expense_datetime - datetime.now(moscow_tz) > five_min):
        await load_expenses("full")  # Full прошло, до Expense > 5 мин



async def load_expenses(export_type: str):
    """
    Загружает расходы и отправляет пользователям уведомления.
    """
    logger.info(f"Начата автозагрузка расходов (Время (UTC): {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')})  |  тип выгрузки: {export_type}")
    retries = 3
    attempts_completed = 0
    last_error = ""
    db, browser = None, None
    while attempts_completed < retries:
        try:
            db, browser = await setup_browser_and_db()
            await go_to_expenses(browser, db)
            expenses = await fetch_expenses(browser, db)
            if export_type == "expenses":
                send_expense_notification(db)
            elif export_type == "full":
                sync_expenses_to_sheet_no_id(db, "rolling26hours")
            elif export_type == "all":
                send_expense_notification(db)
                sync_expenses_to_sheet_no_id(db, "rolling26hours")
            logger.info(f"Успешно завершена автозагрузка расходов (Время (UTC): {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')})")
            return
        except ValueError as e:
            last_error = e
            attempts_completed = retries
        except Exception as e:
            last_error = e
            attempts_completed += 1
        finally:
            await cleanup(browser, db)
            
    logger.warning(f"Автозагрузка расходов завершена с ошибкой (Время (UTC): {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')}) : ${last_error}")
    await handle_error(last_error, db, browser)


async def fetch_expenses(browser, db):
    """
    Загружает расходы с сайта и сохраняет в БД.
    """
    unix_range_start, unix_range_end = get_period_range(
        timezone="Europe/Moscow", range_start=None, range_end=None, period="week"
    )
    return await load_expenses_from_site(browser, unix_range_start, unix_range_end, db, "Europe/Moscow")


async def go_to_expenses(browser, db):
    await browser.page.goto(config.EXPENSES_URL, timeout=30000)  # Переход на страницу расходов
    detected_type = await detect_page_type(browser, 40)  # Асинхронное определение типа страницы

    if detected_type:
        # Отмена входа по смс, переход на вход через номер телефона
        if detected_type == PageType.EXPENSES:
            pass
        
        elif detected_type == PageType.LOGIN_OTP:
            otp = get_temporary_code(db)

            await otp_page(browser, otp)
            if await check_for_error_message(browser, 2):
                raise ValueError("Неверный временный код")
            if await detect_page_type(browser, 15) != PageType.EXPENSES:
                raise Exception("Временная проблема автозагрузки")

        else:
            raise Exception("Проблема со входом при автозагрузке. Требуется повторный вход")
        
    else:
        raise Exception("Проблема с определением типа страницы при автозагрузке расходов")


async def setup_browser_and_db():
    """
    Подключает БД и браузер.
    """
    db = Session()
    browser = BrowserManager(config.PATH_TO_CHROME_PROFILE, config.DOWNLOAD_DIRECTORY, config.BROWSER_TIMEOUT)
    await browser.create_context_and_page()
    return db, browser


async def handle_error(error, db, browser):
    """
    Логирование ошибок и уведомление.
    """
    if db:
        set_last_error(db, str(error))
    send_error_notification(db)


async def cleanup(browser, db):
    """
    Закрывает браузер и соединение с БД.
    """
    if browser:
        await browser.close_browser()
    if db:
        db.close()


async def load_expenses_from_site(browser, unix_range_start, unix_range_end, db, time_zone):
    """
    Возвращает расходы с расходов Тинькофф.
    """
    try:
        # Перенаправление на страницу по периоду и скачивание CSV
        if await expenses_redirect(browser.page, unix_range_start, unix_range_end):
            time.sleep(1)  # Ожидание после перенаправления
        start_time = time.time()
        await download_csv_from_expenses_page(browser.page, 20)
        file_path = await wait_for_new_download(start_time=start_time, timeout=20)

        # Обработка CSV и сохранение в БД
        categories_dict = get_categories_with_keywords(db)
        expenses = await get_json_expenses_from_csv(file_path, categories_dict, time_zone)
        save_expenses_to_db(db, expenses["expenses"], time_zone)

        return expenses
    except:
        raise Exception("Ошибка при загрузке расходов с Тинькофф")