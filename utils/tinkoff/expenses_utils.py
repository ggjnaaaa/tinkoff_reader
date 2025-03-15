# utils/tinkoff/expenses_utils.py

# Стандартные модули Python
import os
import csv
import time
import asyncio
from datetime import datetime

# Сторонние модули
from fastapi import HTTPException
import aiofiles
from playwright.async_api import Page
import pytz
from fuzzywuzzy import fuzz
import chardet

# Собственные модули
import config as config

from utils.tinkoff.browser_manager import BrowserManager
from utils.tinkoff.browser_utils import (
    PageType,
    detect_page_type,
    click_button
)

from routes.directory.tinkoff.expenses import save_expenses_to_db

from routes.auth_tinkoff import (
    save_browser_cache,
    check_for_page
)


async def load_expenses_from_site(browser, unix_range_start, unix_range_end, db, time_zone):
    """
    Возвращает расходы с расходов Тинькофф.
    """
    try:
        # Переход на сайт и проверка, что открыта нужная страница
        if not await check_for_page(browser):
            await browser.create_context_and_page()
            await browser.page.goto(config.EXPENSES_URL)

        try:
            await check_expenses_page(browser=browser)
        except Exception:
            raise HTTPException(status_code=500, detail="Ошибка при переходе на страницу расходов.")

        # Перенаправление на страницу по периоду и скачивание CSV
        if await expenses_redirect(browser.page, unix_range_start, unix_range_end):
            await save_browser_cache()
            time.sleep(1)  # Ожидание после перенаправления
        
        start_time = time.time()
        await download_csv_from_expenses_page(browser.page, 20)
        file_path = await wait_for_new_download(start_time=start_time, timeout=20)

        # Обработка CSV и сохранение в БД
        expenses = await get_json_expenses_from_csv(db, file_path, time_zone)

        return {
            "message": "Данные были успешно загружены с сайта.",
            "source": "site",
            **expenses
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Ошибка при загрузке расходов с Тинькофф")


async def download_csv_from_expenses_page(page: Page, timeout=5):
    """
    Загружает CSV файл со страницы расходов.
    """
    await click_button(page, '[data-qa-id="export"]', timeout)
    await click_button(page, '//span[text()="Выгрузить все операции в CSV"]', timeout)


async def wait_for_new_download(start_time=None, timeout=10):
    """
    Ожидает загрузки первого файла, созданного после времени `start_time`.
    """
    if not start_time:
        start_time = time.time()

    end_time = start_time + timeout
    while time.time() < end_time:
        # Проверяем файлы в директории загрузок
        for filename in os.listdir(config.DOWNLOAD_DIRECTORY):
            file_path = os.path.join(config.DOWNLOAD_DIRECTORY, filename)
            
            # Проверяем, что файл был создан после `start_time`
            if os.path.getmtime(file_path) > start_time:
                # Проверяем, чтобы файл не был временным (с расширением .crdownload)
                if not filename.endswith('.crdownload'):
                    return file_path  # Возвращаем путь к загруженному файлу
        
        await asyncio.sleep(0.5)  # Ждём, чтобы не перегружать процессор
    raise TimeoutError(f"Новый файл не был загружен в течение {timeout} секунд.")


async def expenses_redirect(page: Page, unix_range_start: str, unix_range_end: str):
    """
    Перенаправляет на страницу с заданным периодом.
    """
    new_url = f'https://www.tbank.ru/events/feed/?rangeStart={unix_range_start}&rangeEnd={unix_range_end}&preset=calendar'
    if new_url != page.url:
        await page.goto(new_url, wait_until='domcontentloaded')
        await page.wait_for_url(new_url)  # Ожидаем, пока URL не изменится на нужный
        return True
    return False


async def check_expenses_page(browser: BrowserManager):
    """
    Проверка и попытка перехода на страницу расходов.
    """
    # Проверка на тип текущей страницы
    page = browser.page
    page_type = await detect_page_type(browser)
    
    if page_type != PageType.EXPENSES:
        # Переход на страницу расходов, если находимся не на ней
        await page.goto(config.EXPENSES_URL, timeout=30000)
        page_type = await detect_page_type(browser)
        
        # Если после перехода не получилось попасть на страницу расходов
        if page_type != PageType.EXPENSES:
            raise HTTPException(status_code=307, detail="Не удалось открыть страницу расходов. Перенаправление.")


async def get_json_expenses_from_csv(db, file_path, target_timezone):
    """
    Обрабатывает CSV в JSON по заданному пути к файлу.
    """
    total_expense = 0.0
    categorized_expenses = []

    await asyncio.sleep(0.5)

    # Чтение CSV-файла
    async with aiofiles.open(file_path, mode='rb') as file:
        content = await file.read()
            
        # Автоматическое определение кодировки
        detected_encoding = chardet.detect(content)['encoding']
        decoded_content = content.decode(detected_encoding or 'utf-8', errors='replace')

        # Разделяем содержимое на строки
        lines = decoded_content.splitlines()
        
        # Читаем заголовки из первой строки
        headers = [header.strip('"') for header in lines[0].strip().split(';')]
        
        reader = csv.DictReader(
            lines[1:],
            delimiter=';',
            fieldnames=headers,
            quotechar='"'
        )
        
        transactions = []
        for row in reader:
            amount = float(row["Сумма платежа"].replace(",", "."))
            description = row["Описание"]
            status = row["Статус"]
            date = row["Дата платежа"]

            # Проверка на "Перевод между счетами"
            if ( 
                description == "Перевод между счетами" 
                or description == "Пополнение брокерского счета"
                or description == "Оплата покупки в рассрочку"
                or not status == "OK"
                or date == ""
            ):
                continue

            # Конвертация времени
            msk_time = datetime.strptime(row["Дата операции"], "%d.%m.%Y %H:%M:%S")
            msk_timezone = pytz.timezone("Europe/Moscow")
            timezone = pytz.timezone(target_timezone) if isinstance(target_timezone, str) else target_timezone
            utc_time = msk_timezone.localize(msk_time).astimezone(timezone)

            transactions.append({
                "datetime": utc_time.replace(tzinfo=None),
                "card": row["Номер карты"],
                "amount": amount,
                "description": description,
                "category": row["Категория"]
            })
        # Сортируем транзакции по дате и времени
        transactions.sort(key=lambda x: x["datetime"], reverse=True)

        i = 0
        while i < len(transactions) - 1:
            current = transactions[i]
            next_transaction = transactions[i + 1]

            transaction_time = current["datetime"].replace(second=0)
            next_transaction_time = next_transaction["datetime"].replace(second=0)

            # Проверка на дублирующие записи
            if (
                fuzz.token_sort_ratio(current["description"], next_transaction["description"]) > 70  # Если сходство описаний больше 70%
                and abs((next_transaction_time - transaction_time).total_seconds()) <= 60  # Если разница не больше минуты
                and abs(current["amount"]) == abs(next_transaction["amount"])  # Если одинаковая стоимость
                and (current["amount"] * next_transaction["amount"] < 0)  # Если одно из чисел - отрицательное
                and current["category"] != "Переводы"
            ):
                # Если текущая и следующая транзакции совпадают по условиям, удаляем обе
                i += 2  # Пропускаем обе записи
                continue

            # Обработка текущей транзакции как расхода
            if current["amount"] < 0:
                current["category"] = None
                total_expense += abs(current["amount"])

                categorized_expenses.append({
                    "date_time": current["datetime"].strftime("%d.%m.%Y %H:%M:%S"),
                    "card_number": current["card"],
                    "transaction_type": "расход",
                    "amount": abs(current["amount"]),
                    "description": current["description"],
                    "category": "Не указана"
                })
            i += 1

        # Проверка последнего элемента, если он не был частью пары для удаления
        if i == len(transactions) - 1:
            last_transaction = transactions[i]
            if last_transaction["amount"] < 0:
                total_expense += abs(last_transaction["amount"])

                categorized_expenses.append({
                    "date_time": last_transaction["datetime"].strftime("%d.%m.%Y %H:%M:%S"),
                    "card_number": last_transaction["card"],
                    "transaction_type": "расход",
                    "amount": abs(last_transaction["amount"]),
                    "description": last_transaction["description"],
                    "category": "Не указана"
                })
        
        unique_cards = list({categorized_expense["card_number"] for categorized_expense in categorized_expenses})

    os.remove(file_path)

    saved_expenses = save_expenses_to_db(db, categorized_expenses, target_timezone)

    return {
        "total_expense": total_expense,
        "cards": unique_cards,
        "expenses": saved_expenses
    }