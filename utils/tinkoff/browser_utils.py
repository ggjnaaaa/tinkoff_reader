# browser_utils.py

# Стандартные библиотеки Python
from enum import Enum
import asyncio

# Сторонние библиотеки
from playwright.async_api import Page, expect

# Собственные модули
from utils.tinkoff.browser_manager import BrowserManager

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

async def detect_page_type(browser: BrowserManager, retries: int = 3):
    """Определяет тип страницы, основываясь на содержимом."""
    attempt_current_page = 0
    last_except = ''
    while attempt_current_page < retries:
        try:
            browser.reset_interaction_time()  # Если у тебя есть эта функция, сбрасываем время взаимодействия
            page = browser.page 

            # Ожидаем, что страница полностью загрузится
            await page.wait_for_load_state('networkidle', timeout=16000)  # Ожидание окончания сетевой активности

            if await page.is_visible('body'):
                # Пробуем получить содержимое страницы
                try:
                    content = await page.content()  # Получаем HTML-код страницы
                except Exception as e:
                    print(f"Не удалось получить контент страницы: {e}")
                    await asyncio.sleep(1)  # Небольшая задержка перед повторной попыткой
                    attempt_current_page += 1
                    continue  # Переходим к следующей попытке в цикле

                # Проверяем содержимое на соответствие типам страниц
                for page_type in PageType:
                    if page_type.value in content:
                        return page_type  # Возвращаем тип страницы, если найден
        except Exception as e:  # Ловим все исключения
            last_except = e
        finally:
            attempt_current_page += 1  # Увеличиваем счётчик попыток
    
    print(f"Ошибка при определении типа страницы: {last_except}")
    return None

# Общая асинхронная функция для получения элемента с обработкой ошибок
async def get_element(page: Page, selector: str, timeout: int = 5):
    """Находит элемент на странице с заданным селектором и ждёт его видимости в течение заданного времени."""
    ms_timeout = timeout * 1000
    el = page.locator(selector)
    await expect(el).to_be_visible(timeout=timeout)  # Ожидаем, что элемент станет видимым в течение timeout
    return el

# Асинхронная функция записи информации в поле ввода
async def write_input(page: Page, element_selector: str, input_text: str, timeout: int = 5):
    try:
        input_element = await get_element(page, element_selector, timeout=timeout)
        await input_element.fill(input_text)
    except Exception as e:
        raise Exception(f"Произошла ошибка при вводе данных: {str(e)}") from e

# Асинхронная функция нажатия на кнопку
async def click_button(page: Page, button_selector: str, timeout: int = 5):
    try:
        submit_button = await get_element(page, button_selector, timeout)
        await submit_button.click()
    except Exception as e:
        raise Exception(f"Произошла ошибка при клике на элемент с селектором {button_selector}: {str(e)}") from e

# Асинхронная функция получения текста
async def get_text(page: Page, text_selector: str, timeout: int = 5):
    try:
        element = await get_element(page, text_selector, timeout=timeout)
        return await element.inner_text()
    except Exception:
        raise
