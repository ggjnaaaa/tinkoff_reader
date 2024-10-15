# main.py

# Стандартные библиотеки Python
from enum import Enum
import os

# Сторонние библиотеки
from selenium.webdriver.support.ui import WebDriverWait
from dotenv import load_dotenv

# Сторонние библиотеки - Исключения
from selenium.common.exceptions import TimeoutException

# Собственные модули
from driver_setup import create_chrome_driver
from tinkoff_auth import login_via_sms, login_via_otp, login_via_password
from utils import get_text

# Собственные модули - Исключения
from exceptions import LoginRedirectError

# Типы страниц при входе на сайт
class PageType(Enum):
    SMS_CODE = 'СМС-код'
    PASSWORD = 'Вход в Т‑Банк'
    OTP = 'Введите код'
    EXPENSES = 'Расходы'

# Функция для определения типа страницы и вызова соответствующей функции
def detect_login_type(driver):
    try:
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        # Ожидание любого слова из PageType
        WebDriverWait(driver, 5).until(
            lambda d: any(page_type.value in d.page_source for page_type in PageType)
        )

        # Возврат типа страницы
        for page_type in PageType:
            if page_type.value in driver.page_source:
                return page_type

    except TimeoutException:
        print("Время ожидания истекло, страница не загружена.")
        return None

    print("Не удалось определить тип страницы.")
    return None

# Функция для получения расходов
def get_cost(driver):
    try:
        selector = 'div.PieChart__value_gXIXVm' 
        cost = get_text(driver=driver, text_selector=selector, timeout=10)
        cost = cost.replace('\u00A0', '').replace('₽', '').strip()
        return cost
    except Exception:
        raise

# Основной код работы
def main():
    load_dotenv()

    phone_number = os.getenv("PHONE_NUMBER")
    password = os.getenv("PASSWORD")
    path_to_chrome_profile = os.getenv("PATH_TO_CHROME_PROFILE")
    otp_code = os.getenv("OTP_CODE")

    driver = create_chrome_driver(path_to_chrome_profile)

    try:
        driver.get("https://www.tbank.ru/events/feed/")

        # Определение типа входа, вход в акк и забор расходов
        detected_type = detect_login_type(driver)
        if detected_type:
            print(f"Обнаружен тип страницы: {detected_type}")
            try:
                # Вызываем соответствующую функцию
                if detected_type == PageType.SMS_CODE:
                    login_via_sms(driver=driver, phone_number=phone_number)
                elif detected_type == PageType.PASSWORD:
                    login_via_password(driver=driver, phone_number=phone_number, password=password, otp_code=otp_code)
                elif detected_type == PageType.OTP:
                    login_via_otp(driver=driver, otp_code=otp_code)
            except LoginRedirectError:
                login_via_password(driver=driver, phone_number=phone_number, password=password, otp_code=otp_code)
            print(get_cost(driver))
        else:
            print("Тип страницы не был обнаружен.")
    except Exception as e:
        print(str(e))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()