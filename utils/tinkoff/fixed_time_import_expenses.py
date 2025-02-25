# fixed_time_import_expenses.py

# Стандартные модули Python
import time
import asyncio
from datetime import datetime, timezone
import requests
from contextlib import contextmanager

# Сторонние модули
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from fastapi import Depends

# Собственные модули
import config

from database import Session

from models import Users, TgTmpUsers

from routers.auth_tinkoff import check_for_browser, check_for_page
from routers.directory.tinkoff_expenses import (
    set_last_error,
    get_temporary_code,
    save_expenses_to_db,
    get_categories_with_keywords,
    get_expenses_from_db,
    get_chat_ids_for_error_notifications,
    get_chat_ids_for_transfer_notifications
)

from utils.tinkoff.browser_input_utils import otp_page
from utils.tinkoff.time_utils import get_period_range
from utils.tinkoff.browser_manager import BrowserManager
from utils.tinkoff.browser_utils import (
    detect_page_type, 
    PageType, 
    detect_page_type_after_url_change
)
from utils.tinkoff.expenses_utils import (
    expenses_redirect,
    download_csv_from_expenses_page,
    get_json_expenses_from_csv,
    wait_for_new_download
)


from utils.tinkoff.expenses_google_sheets import sync_expenses_to_sheet_no_id


# Часовой пояс Москвы
moscow_tz = pytz.timezone("Europe/Moscow")


async def load_expenses():
    print(f"Начата автозагрузка расходов (Время (UTC): {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')})")
    retries = 3
    attempts_completed = 0
    last_error = ""
    db = None
    browser = None

    while attempts_completed < retries:
        try:
            db = Session()

            if await check_for_page(browser):
                browser.reset_interaction_time()
            elif await check_for_browser(browser):
                await browser.create_context_and_page()
            else:
                browser = BrowserManager(config.PATH_TO_CHROME_PROFILE,
                                        config.DOWNLOAD_DIRECTORY,
                                        config.BROWSER_TIMEOUT)
                await browser.create_context_and_page()
            
            await browser.page.goto(config.EXPENSES_URL, timeout=30000)  # Переход на страницу расходов
            detected_type = await detect_page_type(browser, 20)  # Асинхронное определение типа страницы

            if detected_type:
                # Отмена входа по смс, переход на вход через номер телефона
                if detected_type == PageType.EXPENSES:
                    pass
                
                elif detected_type == PageType.LOGIN_OTP:
                    otp = ""
                    try:
                        otp = get_temporary_code(db)
                    except ValueError:
                        attempts_completed = retries
                        raise
                    except:
                        raise

                    initial_url = browser.page.url
                    await otp_page(browser, otp)
                    if await detect_page_type_after_url_change(browser, initial_url, 15) != PageType.EXPENSES:
                        raise Exception("Временная проблема автозагрузки")

                else:
                    raise Exception("Проблема со входом при автозагрузке. Требуется повторный вход")
                
            else:
                raise Exception("Проблема с определением типа страницы при автозагрузке расходов")

            unix_range_start, unix_range_end = get_period_range(
                timezone="Europe/Moscow",
                range_start=None,
                range_end=None,
                period="week"
            )
            await load_expenses_from_site(browser, unix_range_start, unix_range_end, db, "Europe/Moscow")
            print(f"Успешно завершена автозагрузка расходов (Время (UTC): {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')})")
            if browser:
                await browser.close_browser()
            send_expense_notification(db)
            sync_expenses_to_sheet_no_id(db, "day")
            return
        except Exception as e:
            last_error = e
            attempts_completed += 1

    print(f"Автозагрузка расходов завершена с ошибкой (Время (UTC): {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')}) : ${last_error}")
    if browser:
        await browser.close_browser()
    if db:
        set_last_error(db, str(last_error))
    else:
        print(f"Невозможно записать сообщение об ошибке в БД. Ошибка: {last_error}")

    get_error_notification_chat_ids(db)


# Обёртка для вызова асинхронной функции в синхронном контексте
def async_to_sync(async_func):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если нет текущего цикла событий, создаём новый
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_func())


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=moscow_tz)
    # Используем обёртку для вызова асинхронной функции
    scheduler.add_job(lambda: async_to_sync(load_expenses), CronTrigger(hour=21, minute=0, timezone=moscow_tz))
    scheduler.start()
    try:
        while True:
            time.sleep(1)  # Поддерживаем поток активным
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


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


def send_expense_notification(db):
    """
    Вызывает эндпоинт на сервере бота для рассылки уведомлений пользователям у которых были расходы за сегодня.
    """
    try:
        # Получаем уникальные карты за сегодня
        try:
            unique_cards = set([card.lstrip('*') for card in get_today_uniq_cards(db)])  # Убираем звезды из начала карт
        except Exception as e:
            print(f"{e}")
            return

        transfer_chat_ids = get_chat_ids_for_transfer_notifications(db)
        chat_ids = None

        if not unique_cards and not transfer_chat_ids:
            return
        
        if unique_cards:
            # Получение chat_id из TgTmpUsers с проверкой наличия card_number в Users
            chat_ids = db.query(TgTmpUsers.chat_id).join(Users).filter(
                Users.card_number.in_(unique_cards)  # Фильтруем только по картам из unique_cards
            ).all()
        
        # Преобразование результата в список
        chat_ids = list(set(str(chat_id[0]) for chat_id in chat_ids) | set(transfer_chat_ids))

        response = requests.post(
            config.AUTO_SAVE_MAILING_BOT_API_URL,
            json={"chat_ids": chat_ids},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при отправке данных на сервер бота: {e}")


def get_error_notification_chat_ids(db):
    """
    Получает chat_id из TgTmpUsers с проверкой наличия card_number в Users для списка пользователей для рассылки ошибок.

    :param db: Сессия базы данных
    :param error_notification_users: Список номеров карты пользователей для рассылки ошибок
    :return: Список chat_id
    """
    try:
        chat_ids = get_chat_ids_for_error_notifications(db)

        response = requests.post(
            config.AUTO_SAVE_ERROR_MAILING_BOT_API_URL,
            json={"chat_ids": chat_ids},
            timeout=10
        )
        response.raise_for_status()

        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при отправке данных на сервер бота: {e}")


def get_today_uniq_cards(db):

    # Определяем временные диапазоны
    unix_range_start, unix_range_end = get_period_range(
        timezone="Europe/Moscow",
        period='day'
    )

    # Получаем данные расходов
    expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, "Europe/Moscow")
    cards = expenses_data.get("cards", None)

    if cards:
        return set(cards)
    
    raise Exception('Расходы за день отсутствуют')

