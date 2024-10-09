# utils.py

# Импорты Selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Исключения Selenium
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException, 
    StaleElementReferenceException
)

# Общая функция для получения элемента с обработкой ошибок
def get_element(driver, selector, timeout=5):
    try:
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
        # Ожидаем появления элемента с сообщением об ошибке
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, error_selector))
        )
        return True  # Если элемент найден, возвращаем True
    except TimeoutException:
        return False  # Если по таймауту элемент не найден, возвращаем False
    
