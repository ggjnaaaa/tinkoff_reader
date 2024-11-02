# browser_utils.py

# Стандартные библиотеки Python
from enum import Enum

# Импорты Playwright
from playwright.async_api import Page, expect, TimeoutError as PlaywrightTimeoutError

# Собственные модули
from utils.tinkoff.driver_setup import reset_interaction_time

# Типы страниц при входе на сайт
class PageType(Enum):
    LOGIN_SMS_CODE = 'Мы отправим вам СМС-код'
    LOGIN_INPUT_SMS_CODE = 'Отправили код подтверждения'
    LOGIN_PHONE = 'Вход в Т‑Банк'
    LOGIN_PASSWORD = 'Пароль'
    LOGIN_CREATE_OTP = 'Придумайте код'
    LOGIN_OTP = 'Введите код для быстрого входа'
    EXPENSES = 'Расходы'

    @classmethod
    def from_string(cls, step: str):
        """Преобразует строку в соответствующий объект PageType."""
        for page_type in cls:
            if page_type.value == step:
                return page_type
        raise ValueError(f"Неверный тип шага: {step}")

    def template_path(self):
        paths = {
            PageType.LOGIN_SMS_CODE: "",
            PageType.LOGIN_INPUT_SMS_CODE: "tinkoff/sms_code.html",
            PageType.LOGIN_PHONE: "tinkoff/login_phone.html",
            PageType.LOGIN_PASSWORD: "tinkoff/login_password.html",
            PageType.LOGIN_CREATE_OTP: "tinkoff/create_otp.html",
            PageType.LOGIN_OTP: "tinkoff/login_otp.html",
            PageType.EXPENSES: "tinkoff/expenses.html",
        }
        return paths.get(self)

# Функция для определения типа страницы
async def detect_page_type(page: Page, retries=3):
    attempt_current_page = 0
    while attempt_current_page < retries:
        try:
            reset_interaction_time()
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            for page_type in PageType:
                if page_type.value in content:
                    return page_type
            attempt_current_page += 1
        except PlaywrightTimeoutError:
            return None

# Общая асинхронная функция для получения элемента с обработкой ошибок
async def get_element(page: Page, selector: str, timeout: int = 30000):
    """Находит элемент на странице с заданным селектором и ждёт его видимости в течение заданного времени."""
    el = page.locator(selector)
    await expect(el).to_be_visible(timeout=timeout)  # Ожидаем, что элемент станет видимым в течение timeout
    return el

# Асинхронная функция записи информации в поле ввода
async def write_input(page: Page, element_selector, input_text, timeout=1):
    try:
        input_element = await get_element(page, element_selector, timeout=timeout)
        await input_element.fill(input_text)
    except Exception as e:
        raise Exception(f"Произошла ошибка при вводе данных: {str(e)}") from e

# Асинхронная функция нажатия на кнопку
async def click_button(page: Page, button_selector, timeout=1):
    try:
        submit_button = await get_element(page, button_selector, timeout)
        await submit_button.click()
    except Exception as e:
        raise Exception(f"Произошла ошибка при клике на элемент с селектором {button_selector}: {str(e)}") from e

# Асинхронная функция получения текста
async def get_text(page: Page, text_selector, timeout=5):
    try:
        element = await get_element(page, text_selector, timeout=timeout)
        return await element.inner_text()
    except Exception:
        raise

# Асинхронная функция для проверки наличия сообщения об ошибке
async def check_for_error_message(page: Page, error_selector, timeout=5):
    try:
        reset_interaction_time()
        error = await get_text(page, error_selector, timeout=timeout)
        return error
    except Exception:
        return None

# Асинхронная функция для загрузки CSV со страницы расходов
async def download_csv_from_expenses_page(page: Page):
    await click_button(page, '[data-qa-id="export"]', timeout=5)
    await click_button(page, '//span[text()="Выгрузить все операции в CSV"]', timeout=5)