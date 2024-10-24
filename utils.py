# utils.py

# Стандартные библиотеки Python
from enum import Enum
from datetime import datetime

# Импорты Selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Собственные модули
from driver_setup import reset_interaction_time

# Исключения Selenium
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException, 
    StaleElementReferenceException
)

# Типы страниц при входе на сайт
class PageType(Enum):
    LOGIN_SMS_CODE = 'Мы отправим вам СМС-код'
    LOGIN_INPUT_SMS_CODE = 'Отправили код подтверждения'
    LOGIN_PHONE = 'Вход в Т‑Банк'
    LOGIN_PASSWORD = 'Пароль'
    LOGIN_CREATE_OTP = 'Придумайте код'
    LOGIN_OTP = 'Введите код для быстрого входа'
    EXPENSES = 'Расходы'

# Функция для определения типа страницы
def detect_page_type(driver):
    try:
        reset_interaction_time()
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        WebDriverWait(driver, 5).until(
            lambda d: any(page_type.value in d.page_source for page_type in PageType)
        )
        for page_type in PageType:
            if page_type.value in driver.page_source:
                return page_type
    except TimeoutException:
        return None

# Общая функция для получения элемента с обработкой ошибок
def get_element(driver, selector, timeout=5):
    try:
        reset_interaction_time()
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        return WebDriverWait(driver=driver, timeout=timeout).until(
           EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except TimeoutException as e:
        raise TimeoutException(f"Ошибка загрузки страницы: {driver.current_url}") from e
    except NoSuchElementException as e:
        raise NoSuchElementException(f"Элемент с селектором {selector} не найден на странице {driver.current_url}") from e
    except StaleElementReferenceException as e:
        raise StaleElementReferenceException(f"Элемент с селектором {selector} устарел на странице {driver.current_url}: {str(e)}") from e

# Функция записи инфы в поле ввода
def write_input(driver, element_selector, input, timeout=1):
    try:
        # Получаем элемент
        password_input = get_element(driver, element_selector, timeout)

        # Вводим номер телефона
        password_input.send_keys(input)
    except Exception as e:
        raise Exception(f"Произошла ошибка при вводе данных: {str(e)}") from e

# Функция нажатия на кнопку
def click_button(driver, button_selector, timeout=1):
    try:
        # Получаем элемент
        submit_button = get_element(driver, button_selector, timeout)

        # Кликаем на кнопку
        submit_button.click()
    except ElementClickInterceptedException as e:
        raise ElementClickInterceptedException(f"Клик по элементу с селектором {button_selector} был заблокирован на странице {driver.current_url}: {str(e)}") from e
    except Exception as e:
        raise Exception(f"Произошла ошибка при клике на элемент с селектором {button_selector}: {str(e)}") from e

# Функция получения текста
def get_text(driver, text_selector, timeout=5):
    try:
        # Получаем элемент
        element = get_element(driver, text_selector, timeout)

        # Возвращаем текст
        return element.text
    except Exception:
        raise
    
# Функция для проверки наличия сообщения об ошибке
def check_for_error_message(driver, error_selector, timeout=1):
    try:
        reset_interaction_time()
        # Ожидаем появления элемента с сообщением об ошибке
        element = get_element(driver, error_selector)
        return element  # Если элемент найден, возвращаем True
    except TimeoutException:
        return None  # Если по таймауту элемент не найден, возвращаем False
    
def collect_expense_details(driver, expense_element, timeout=5):
    date_time = expense_element.find_element(By.CSS_SELECTOR, 'span[data-qa-type="operation-popup-time"]').text 

    try:
        card_number = expense_element.find_element(By.CSS_SELECTOR, 'span.CardLogo--module__cardNumberText_qqtKVm').text
    except:
        card_number = "Номер карты не указан"

    description = "Не готово" #expense_element.find_element(By.CSS_SELECTOR, 'div.TimelineItem__description_vJMN-+E').text

    amount = expense_element.find_element(By.CSS_SELECTOR, 'span[data-qa-type="uikit/money.details-card-baseInfo-value"]').text

    transaction_type = expense_element.find_element(By.CSS_SELECTOR, 'span.UITimelineOperationPopup__subTextCategory_rvgxWY').text

    expense_data = {
        "date_time": date_time,
        "card_number": card_number,
        "description": description,
        "amount": amount,
        "transaction_type": transaction_type
    }

    return expense_data

def convert_to_datetime(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%d %B %Y, %H:%M")
    except ValueError:
        return None
    
def parse_amount(amount_str: str) -> float:
    # Убираем символы валюты и разделители, преобразуем в число
    amount_str = amount_str.replace('\u00A0', '').replace('₽', '').replace(',', '.').replace('−', '-').replace('\n', '').strip()
    return float(amount_str)