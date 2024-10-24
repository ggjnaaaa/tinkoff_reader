# driver_setup.py

# Стандартные библиотеки Python
import time
import threading

# Сторонние библиотеки
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Глобальная переменная для хранения времени последнего взаимодействия
last_interaction_time = time.time()

# Функция с созданием и настройкой драйвера на хром
def create_chrome_driver(path_to_chrome_profile, timeout):
    #chrome_driver_path = "D:/myProgs/TinkoffReader/chromedriver-win64/chromedriver.exe"
    # Настраиваем параметры Chrome
    chrome_options = Options()
    chrome_options.add_argument(path_to_chrome_profile)  # Путь к папке профиля
    #chrome_options.add_argument("--headless")   # Включаем headless-режим (без открытия окна)
    chrome_options.add_argument("--disable-gpu")  # Отключаем GPU (ускорение)
    chrome_options.add_argument("--window-size=1920x1080")  # Задаем размер окна для корректного рендеринга
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Отключить автоматизацию
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")  # Чтобы запросы не выглядели как от селениума

    #chrome_options.add_argument("--disable-extensions")  # Включаем безопасный режим

    # Запускаем браузер с заданными параметрами
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) # webdriver.Chrome(service=Service(executable_path=chrome_driver_path), options=chrome_options) #

    # Запускаем таймер для закрытия браузера
    timer_thread = threading.Thread(target=close_browser_after_timeout, args=(driver, timeout))
    reset_interaction_time()
    timer_thread.start()
    
    return driver

# Функция для закрытия драйвера (например, если бездействует долго)
def close_driver(driver):
    try:
        if driver:
            driver.quit()
        return None
    except Exception as e:
        print(f"Ошибка при закрытии драйвера: {str(e)}")

def is_browser_active(driver):
    try:
        # Попытка получить текущий URL, если браузер закрыт, то будет вызвано исключение
        if not driver:
            return False
        driver.current_url
        return True  # Браузер активен
    except WebDriverException:
        return False  # Браузер закрыт

# Функция для сброса времени последнего взаимодействия
def reset_interaction_time():
    global last_interaction_time
    last_interaction_time = time.time()

# Функция для сброса времени последнего взаимодействия
def stop_interaction_time():
    global last_interaction_time
    last_interaction_time = None

# Функция для закрытия браузера после тайм-аута
def close_browser_after_timeout(driver, timeout):
    global last_interaction_time
    while True:
        print("-", end="")
        if not last_interaction_time or time.time() - last_interaction_time > timeout or not driver:
            print("Время ожидания истекло, закрываю браузер...")
            close_driver(driver)
            break
        time.sleep(5)  # Проверяем каждые 5 секунд