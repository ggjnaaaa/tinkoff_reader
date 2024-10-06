from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Функция с созданием и настройкой драйвера на хром
def create_chrome_driver(chrome_driver_path):
    # Настраиваем параметры Chrome
    service = Service(chrome_driver_path)
    chrome_options = Options()
    chrome_options.add_argument("--incognito")  # Включаем режим инкогнито
    chrome_options.add_argument("--headless")   # Включаем headless-режим (без открытия окна)
    chrome_options.add_argument("--disable-gpu")  # Отключаем GPU (ускорение)
    chrome_options.add_argument("--window-size=1920x1080")  # Задаем размер окна для корректного рендеринга

    # Запускаем браузер с заданными параметрами
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

# Функция для авторизации
def login_to_account(driver, phone_number, password):
    driver.get("https://www.tbank.ru/login/")  # Прямая ссылка на страницу входа
    submit_button_selector = 'button[automation-id="button-submit"]'

    # Ввод номера телефона
    write_input(driver, 'input[name="phone"]', phone_number)
    click_button(driver, submit_button_selector)
    
    # Ввод кода из СМС
    sms_code = input("Введите код из смс: ")
    write_input(driver, 'input[automation-id="otp-input"]', sms_code)

    # Ввод пароля
    write_input(driver, 'input[automation-id="password-input"]', password)
    click_button(driver, submit_button_selector)

    # Отказ от создания код-пароля для быстрого входа
    click_button(driver,'button[automation-id="cancel-button"]')

# Функция записи инфы в поле ввода
def write_input(driver, element_selector, input):
    try:
        # Явное ожидание перед вводом инфы
        password_input = WebDriverWait(driver=driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
        )

        # Вводим номер телефона
        password_input.send_keys(input)
    except Exception as e:
        print(f"Произошла ошибка при вводе данных: {str(e)}")

# Функция нажатия на кнопку
def click_button(driver, button_selector):
    try:
        # Явное ожидание перед поиском кнопки
        submit_button = WebDriverWait(driver=driver, timeout=10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
        )
        submit_button.click()  # Кликаем на кнопку
    except Exception as e:
        print(f"Произошла ошибка при нажатии на кнопку: {str(e)}")

# Функция для перехода в раздел баланса
def navigate_to_balance(driver):
    click_button(driver, 'a[href^="/mybank/accounts/debit/"]')

def get_cost(driver):
    try:
        # Ожидание появления элемента с классом abkrps9TW
        element = WebDriverWait(driver=driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.abkrps9TW'))
        )

        # Очищаем текст от символов валюты и лишних пробелов 
        return element.text.replace(' ', '').replace('₽', '').strip()
    except Exception as e:
        print(f"Произошла ошибка при получении расходов: {str(e)}")
        return None

# Основной код работы
def main():
    chrome_driver_path = "C:\\Users\\nastg\\Downloads\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"
    driver = create_chrome_driver(chrome_driver_path)

    try:
        phone_number = "ТВОЙ_НОМЕР"
        password = "ТВОЙ_ПАРОЛЬ"

        login_to_account(driver, phone_number, password)  # Вход в аккаунт
        navigate_to_balance(driver)  # Переход к балансу
        print("РАСХОДЫ: " + get_cost(driver))

    finally:
        driver.quit()

if __name__ == "__main__":
    main()