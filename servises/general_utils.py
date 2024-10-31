# general_utils.py

# Стандартные библиотеки Python
import os, csv, os, time
from datetime import datetime
from fastapi import HTTPException

# Импорты Selenium
from selenium.webdriver.common.by import By

# Собственные модули
import tinkoff.config as config

# Вспомогательная функция для конвертации даты в Unix-время в секундах
def convert_to_unix(date_str: str) -> int:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)  # Конвертируем в миллисекунды для соответствия с примером
    except ValueError:
        raise HTTPException(status_code=400, detail="Неправильный формат даты")

# Ожидает загрузки нового файла с указанным расширением, созданного после времени `start_time`
def wait_for_new_download(filename_extension=".csv", start_time=None, timeout=10):
    if not start_time:
        start_time = time.time()

    end_time = start_time + timeout
    while time.time() < end_time:
        # Проверяем файлы в директории загрузок
        for filename in os.listdir(config.DOWNLOAD_DIRECTORY):
            file_path = os.path.join(config.DOWNLOAD_DIRECTORY, filename)
            # Проверяем, что файл имеет нужное расширение и был создан после `start_time`
            if filename.endswith(filename_extension) and os.path.getmtime(file_path) > start_time:
                return file_path
        time.sleep(0.5)  # Ждём, чтобы не перегружать процессор
    raise TimeoutError(f"Файл с расширением {filename_extension} не был загружен в течение {timeout} секунд.")

def expenses_redirect(period=None, rangeStart=None, rangeEnd=None):
    # Открываем страницу расходов в зависимости от периода
    if rangeStart and rangeEnd:
        new_url = f'https://www.tbank.ru/events/feed/?rangeStart={rangeStart}&rangeEnd={rangeEnd}&preset=calendar'
        if new_url != config.driver.current_url:
            config.driver.get(new_url)
            return True
        return False
    elif period:
        return expenses_redirect_by_period(period)
    else:
        raise HTTPException(status_code=500, detail="Ошибка входа в тинькофф. Пожалуйста, войдите заново.")

def expenses_redirect_by_period(period):
    driver = config.driver
    new_url = ''

    if period == 'week':
        new_url ='https://www.tbank.ru/events/feed/?preset=week'
    elif period == 'month' or not period:
        new_url ='https://www.tbank.ru/events/feed/'
    elif period == '3month':
        new_url ='https://www.tbank.ru/events/feed/?preset=3month'
    elif period == 'year':
        new_url ='https://www.tbank.ru/events/feed/?preset=year'
    elif period == 'all':
        new_url ='https://www.tbank.ru/events/feed/?preset=all'

    if new_url != driver.current_url:
        driver.get(new_url)
        return True
    return False

# ЗДЕСЬ В json ВЫВОДИТЬ СТАТЬИ (ключ - айдишник, значение - статья)
def get_expense_categories():
    # Заглушка
    return [
        {"id": 1, "category_name": "Услуги банка"},
        {"id": 2, "category_name": "Прочее"}
    ]

# ЗДЕСЬ В СЛОВАРЕ ВЫВОДИТЬ СТАТЬИ (ключ - описание, значение - статья)
def get_expense_categories_with_description():
    # Заглушка
    categories_dict = {}
    categories_dict["Плата за оповещения об операциях"] = "Услуги банка"
    categories_dict["Перевод между счетами"] = "Прочее"

    return categories_dict

def get_json_expense_from_csv(file_path, categories_dict):
    total_income = 0.0
    total_expense = 0.0
    categorized_expenses = []

    # Чтение CSV-файла
    with open(file_path, mode='r', encoding='windows-1251') as file:
        reader = csv.DictReader(file, delimiter=';')

        for row in reader:
            amount = float(row["Сумма операции"].replace(",", "."))
            description = row["Описание"]
            card = row["Номер карты"]
            datetime_operation = row["Дата операции"]
            transaction_type = "расход" if amount < 0 else "доход"
            total_expense += abs(amount) if amount < 0 else 0
            total_income += amount if amount > 0 else 0

            # Получаем категорию из словаря
            category = categories_dict.get(description, "Выберите статью")

            # Добавляем операцию в результат
            categorized_expenses.append({
                "date_time": datetime_operation,
                "card_number": card,
                "transaction_type": transaction_type,
                "amount": abs(amount),
                "description": description,
                "category": category
            })

    os.remove(file_path)  # Удаление файла

    result = {
        "total_income": total_income,
        "total_expense": total_expense,
        "expenses": categorized_expenses
    }

    return result