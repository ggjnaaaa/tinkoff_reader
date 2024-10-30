# general_utils.py

# Стандартные библиотеки Python
import os
import time
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

def expenses_redirect_by_period(period):
    driver = config.driver

    if period == 'week':
        driver.get('https://www.tbank.ru/events/feed/?preset=week')
    elif period == 'month' or not period:
        driver.get('https://www.tbank.ru/events/feed/')
    elif period == '3month':
        driver.get('https://www.tbank.ru/events/feed/?preset=3month')
    elif period == 'year':
        driver.get('https://www.tbank.ru/events/feed/?preset=year')
    elif period == 'all':
        driver.get('https://www.tbank.ru/events/feed/?preset=all')