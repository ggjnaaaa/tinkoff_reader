# browser_utils.py

# Стандартные библиотеки Python
from enum import Enum

# Импорты Selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Собственные модули
from servises.driver_setup import reset_interaction_time

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
def get_element(driver, selector, by=By.CSS_SELECTOR, timeout=5):
    try:
        reset_interaction_time()
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        return WebDriverWait(driver=driver, timeout=timeout).until(
           EC.presence_of_element_located((by, selector))
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
        password_input = get_element(driver, element_selector, timeout=timeout)

        # Вводим номер телефона
        password_input.send_keys(input)
    except Exception as e:
        raise Exception(f"Произошла ошибка при вводе данных: {str(e)}") from e

# Функция нажатия на кнопку
def click_button(driver, button_selector, by=By.CSS_SELECTOR, timeout=1):
    try:
        # Получаем элемент
        submit_button = get_element(driver, button_selector, by, timeout)

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
        element = get_element(driver, text_selector, timeout=timeout)

        # Возвращаем текст
        return element.text
    except Exception:
        raise
    
# Функция для проверки наличия сообщения об ошибке
def check_for_error_message(driver, error_selector, timeout=1):
    try:
        reset_interaction_time()
        # Ожидаем появления элемента с сообщением об ошибке
        element = get_element(driver, error_selector, timeout=timeout)
        return element  # Если элемент найден, возвращаем True
    except TimeoutException:
        return None  # Если по таймауту элемент не найден, возвращаем False