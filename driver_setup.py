# driver_setup.py

# Сторонние библиотеки
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Функция с созданием и настройкой драйвера на хром
def create_chrome_driver(path_to_chrome_profile):
    # Настраиваем параметры Chrome
    chrome_options = Options()
    chrome_options.add_argument(path_to_chrome_profile)  # Путь к папке профиля
    chrome_options.add_argument("--headless")   # Включаем headless-режим (без открытия окна)
    chrome_options.add_argument("--disable-gpu")  # Отключаем GPU (ускорение)
    chrome_options.add_argument("--window-size=1920x1080")  # Задаем размер окна для корректного рендеринга

    # Запускаем браузер с заданными параметрами
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)#
    
    return driver