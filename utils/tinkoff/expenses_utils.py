# general_utils.py

# Стандартные библиотеки Python
import os, csv, time, asyncio

# Сторонние библиотеки
from fastapi import HTTPException
import aiofiles
from playwright.async_api import Page
from datetime import datetime
import pytz
from fuzzywuzzy import fuzz

# Собственные модули
import config as config
from utils.tinkoff.browser_manager import BrowserManager
from routers.directory.tinkoff_expenses import (
    get_categories_with_keywords,
    save_expenses_to_db
)
from routers.auth_tinkoff import (
    save_browser_cache, 
    check_for_page
)
from utils.tinkoff.browser_utils import (
    PageType, 
    detect_page_type,
    click_button
)

async def load_expenses_from_site(browser, unix_range_start, unix_range_end, db, time_zone):
    # Переход на сайт и проверка, что открыта нужная страница
    if not await check_for_page(browser):
        await browser.create_context_and_page()
        await browser.page.goto(config.EXPENSES_URL)

    try:
        await check_expenses_page(browser=browser)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при переходе на страницу расходов.")

    # Перенаправление на страницу по периоду и скачивание CSV
    if await expenses_redirect(browser.page, unix_range_start, unix_range_end):
        await save_browser_cache()
        time.sleep(1)  # Ожидание после перенаправления

    start_time = time.time()
    await download_csv_from_expenses_page(browser.page, 20)
    file_path = await wait_for_new_download(start_time=start_time, timeout=20)

    # Обработка CSV и сохранение в БД
    categories_dict = get_categories_with_keywords(db)
    expenses = await get_json_expenses_from_csv(file_path, categories_dict, time_zone)
    save_expenses_to_db(db, expenses["expenses"], time_zone)

    return {
        "message": "Данные были успешно загружены с сайта.",
        "source": "site",
        **expenses
    }

# Асинхронная функция для загрузки CSV со страницы расходов
async def download_csv_from_expenses_page(page: Page, timeout=5):
    await click_button(page, '[data-qa-id="export"]', timeout)
    await click_button(page, '//span[text()="Выгрузить все операции в CSV"]', timeout)

# Ожидает загрузки первого файла, созданного после времени `start_time`
async def wait_for_new_download(start_time=None, timeout=10):
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
    new_url = f'https://www.tbank.ru/events/feed/?rangeStart={unix_range_start}&rangeEnd={unix_range_end}&preset=calendar'
    if new_url != page.url:
        await page.goto(new_url)
        await page.wait_for_url(new_url)  # Ожидаем, пока URL не изменится на нужный
        return True
    return False

async def check_expenses_page(browser: BrowserManager):
    # 3. Проверка на тип текущей страницы
    page = browser.page
    page_type = await detect_page_type(browser)
    
    if page_type != PageType.EXPENSES:
        # Переход на страницу расходов, если находимся не на ней
        await page.goto(config.EXPENSES_URL, timeout=30000)
        page_type = await detect_page_type(browser)
        
        # Если после перехода не получилось попасть на страницу расходов
        if page_type != PageType.EXPENSES:
            raise HTTPException(status_code=307, detail="Не удалось открыть страницу расходов. Перенаправление.")

async def get_json_expenses_from_csv(file_path, categories_dict, target_timezone):
    total_expense = 0.0
    categorized_expenses = []

    print(file_path)
    await asyncio.sleep(0.5)

    # Чтение CSV-файла
    async with aiofiles.open(file_path, mode='r', encoding='windows-1251') as file:
        reader = csv.DictReader(await file.readlines(), delimiter=';')
        
        transactions = []
        for row in reader:
            amount = float(row["Сумма платежа"].replace(",", "."))
            description = row["Описание"]
            status = row["Статус"]

            # Проверка на "Перевод между счетами"
            if ( 
                description == "Перевод между счетами" 
                or description == "Пополнение брокерского счета"
                or not status == "OK"
            ):
                continue

            # Конвертация времени
            msk_time = datetime.strptime(row["Дата операции"], "%d.%m.%Y %H:%M:%S")
            msk_timezone = pytz.timezone("Europe/Moscow")
            target_timezone = pytz.timezone(target_timezone) if isinstance(target_timezone, str) else target_timezone
            utc_time = msk_timezone.localize(msk_time).astimezone(target_timezone)

            transactions.append({
                "datetime": utc_time.replace(tzinfo=None),
                "card": row["Номер карты"],
                "amount": amount,
                "description": description,
                "category": None
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
            ):
                # Если текущая и следующая транзакции совпадают по условиям, удаляем обе
                i += 2  # Пропускаем обе записи
                continue

            # Обработка текущей транзакции как расхода
            if current["amount"] < 0:
                total_expense += abs(current["amount"])
                # Определение категории по названию
                for category_title, data in categories_dict.items():
                    if any(keyword.lower() in current["description"].lower() for keyword in data["keywords"]):
                        current["category"] = category_title  # Сохраняем название категории
                        break

                categorized_expenses.append({
                    "date_time": current["datetime"].strftime("%d.%m.%Y %H:%M:%S"),
                    "card_number": current["card"],
                    "transaction_type": "расход",
                    "amount": abs(current["amount"]),
                    "description": current["description"],
                    "category": current["category"]
                })
            i += 1

        # Проверка последнего элемента, если он не был частью пары для удаления
        if i == len(transactions) - 1:
            last_transaction = transactions[i]
            if last_transaction["amount"] < 0:
                total_expense += abs(last_transaction["amount"])
                for category_title, data in categories_dict.items():
                    if any(keyword.lower() in last_transaction["description"].lower() for keyword in data["keywords"]):
                        last_transaction["category"] = data["id"]
                        break

                categorized_expenses.append({
                    "date_time": last_transaction["datetime"].strftime("%d.%m.%Y %H:%M:%S"),
                    "card_number": last_transaction["card"],
                    "transaction_type": "расход",
                    "amount": abs(last_transaction["amount"]),
                    "description": last_transaction["description"],
                    "category": last_transaction["category"]
                })
        
        unique_cards = list({categorized_expense["card_number"] for categorized_expense in categorized_expenses})

    os.remove(file_path)

    return {
        "total_expense": total_expense,
        "cards": unique_cards,
        "expenses": categorized_expenses
    }