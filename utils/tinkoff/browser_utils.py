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
            page_type = await get_page_type(browser)
            if page_type:
                return page_type
        except Exception as e:  # Ловим все исключения
            last_except = e
        finally:
            attempt_current_page += 1  # Увеличиваем счётчик попыток
    
    print(f"Ошибка при определении типа страницы: {last_except}")
    return None

async def detect_page_type_after_url_change(browser: BrowserManager, initial_url: str, retries: int = 3):
    """Ожидает, пока текущий URL изменится с `initial_url`, затем определяет тип страницы по содержимому."""
    attempt_current_page = 0
    last_except = None

    while attempt_current_page < retries:
        try:
            # Ждем, пока URL изменится с исходного
            url_changed = await wait_for_url_change_from(browser.page, initial_url)
            if not url_changed:
                print(f"Не удалось дождаться перехода с URL: {initial_url}")
                attempt_current_page += 1
                continue

            page_type = await get_page_type(browser)
            if page_type:
                return page_type
        except Exception as e:
            last_except = e
            print(f"Попытка {attempt_current_page + 1} завершилась ошибкой: {e}")
        finally:
            attempt_current_page += 1

    print(f"Не удалось определить тип страницы после {retries} попыток. Последняя ошибка: {last_except}")
    return None

async def wait_for_url_change_from(page: Page, initial_url: str, timeout: int = 10000):
    """Ожидает, пока текущий URL не изменится с `initial_url`."""
    try:
        await page.wait_for_function(
            f"window.location.href !== '{initial_url}'", timeout=timeout
        )
        return True
    except asyncio.TimeoutError:
        print(f"Timeout: ожидание перехода с {initial_url} завершилось неудачей.")
        return False
    except Exception as e:
        print(f"Ошибка при ожидании изменения URL: {e}")
        return False

async def get_page_type(browser: BrowserManager):
    browser.reset_interaction_time()  # Сбрасываем время взаимодействия, если функция доступна
    page = browser.page

    # Ожидаем окончания сетевой активности
    await browser.page.wait_for_function('document.readyState === "complete"', timeout=16000)

    if await page.is_visible('body'):
        try:
            content = await page.content()  # Получаем HTML-код страницы
        except Exception as e:
            print(f"Не удалось получить контент страницы: {e}")
            await asyncio.sleep(1)  # Задержка перед повторной попыткой
            return None

        # Проверяем содержимое на соответствие типам страниц
        for page_type in PageType:
            if page_type.value in content:
                return page_type  # Возвращаем тип страницы, если найден

# Общая асинхронная функция для получения элемента с обработкой ошибок
async def get_element(page: Page, selector: str, timeout: int = 5):
    """Находит элемент на странице с заданным селектором и ждёт его видимости в течение заданного времени."""
    ms_timeout = timeout * 1000
    # Ждем появления элемента
    await page.wait_for_selector(selector, timeout=ms_timeout)

    # Создаем локатор для элемента
    el = page.locator(selector)

    # Проверяем, что элемент видим
    await expect(el).to_be_visible(timeout=ms_timeout)  # Ожидаем, что элемент станет видимым в течение timeout
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