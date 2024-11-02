# auth_tinkoff.py

# Стандартные библиотеки Python
import os

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Body, Request, Query
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

# Собственные модули
from tinkoff.models import LoginResponse
import tinkoff.config as config
from tinkoff.config import (
    timer_selector, 
    resend_sms_button_selector, 
    cancel_button_selector, 
    browser_instance as browser
)

from utils.tinkoff.browser_manager import BrowserManager
from utils.tinkoff.tinkoff_auth import paged_login, close_login_via_sms_page, get_user_name_from_otp_login
from utils.tinkoff.browser_utils import get_text, detect_page_type, PageType, click_button

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Вход в тинькофф
@router.get("/tinkoff/")
async def get_login_type(request: Request):
    global browser

    load_dotenv()  # Загрузка .env файла
    config.DOWNLOAD_DIRECTORY = os.getenv("DOWNLOAD_DIRECTORY")
    config.PATH_TO_CHROME_PROFILE = os.getenv("PATH_TO_CHROME_PROFILE")

    # Открытие браузера если закрыт, если открыт обновление времени выключения
    if browser and await browser.is_page_active():
        browser.reset_interaction_time()
    elif browser and await browser.is_browser_active():
        browser.create_context_and_page()
    else:
        browser = BrowserManager(config.PATH_TO_CHROME_PROFILE,
                                 config.DOWNLOAD_DIRECTORY,
                                 config.BROWSER_TIMEOUT)
        await browser.create_context_and_page()

    try:
        await browser.page.goto(config.EXPENSES_URL)  # Переход на страницу расходов
        detected_type = await detect_page_type(browser, 20)  # Асинхронное определение типа страницы

        if detected_type:
            # Отмена входа по смс, переход на вход через номер телефона
            if detected_type == PageType.LOGIN_SMS_CODE:
                detected_type = await close_login_via_sms_page(browser)

            # Получаем путь к нужному шаблону
            page_path = detected_type.template_path()

            # Вход по временному паролю
            if detected_type == PageType.LOGIN_OTP:
                return templates.TemplateResponse(page_path, {"request": request, "name": get_user_name_from_otp_login(browser)})
            print(8)

            return templates.TemplateResponse(page_path, {"request": request})
        else:
            await browser.close_context_and_page()
            raise HTTPException(status_code=400, detail="Не удалось определить тип страницы.")
    except Exception as e:
        print(e)
        await browser.close_context_and_page()
        raise HTTPException(status_code=500, detail=str(e))
    
# Обработка всех страниц входа
@router.post("/tinkoff/login/", response_model=LoginResponse)
async def login(request: Request, data: str = Body(...)):
    if not await browser.is_page_active():
        raise HTTPException(status_code=440, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        result = await paged_login(browser, data)  # Отправка данных, получает тип следующей страницы
        if result:
            return LoginResponse(status="success", next_page_type=result) 
        return LoginResponse(status="failed", next_page_type=None)
    except:
        raise

# Универсальный эндпоинт для загрузки следующей страницы
@router.get("/tinkoff/next/")
async def next_page(request: Request, step: str | None = Query(default=None)):
    # Определяем `page_type`, пытаясь преобразовать `step` в `PageType`
    if step:
        try:
            page_type = PageType.from_string(step)  # Используем метод класса
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный тип шага")
    else:
        page_type = await detect_page_type(browser)

     # Отмена входа по смс, переход на вход через номер телефона
    if page_type == PageType.LOGIN_SMS_CODE:
        page_type = await close_login_via_sms_page(browser)

    # Получаем путь к нужному шаблону
    template_path = page_type.template_path()

    if page_type == PageType.LOGIN_OTP:
        return templates.TemplateResponse(template_path, {"request": request, "name": get_user_name_from_otp_login(browser)})
    
    return templates.TemplateResponse(template_path, {"request": request})

# Эндпоинт для получения таймера при вводе смс
@router.get("/tinkoff/get_sms_timer/")
async def get_sms_timer():
    try:
        # Получаем оставшееся время в секундах
        time_left = await get_text(browser, timer_selector)
        return {"time_left": time_left}

    except Exception as e:
        print(f"Ошибка при получении таймера: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить таймер")

# Эндпоинт для повторной отправки смс
@router.post("/tinkoff/resend_sms/")
async def resend_sms():
    try:
        # Нажимаем на кнопку повторной отправки
        await click_button(config.page, resend_sms_button_selector)
        return {"status": "success", "message": "SMS успешно отправлено"}

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отправить SMS повторно")

# Эндпоинт для отмены входа по временному паролю
@router.post("/tinkoff/cancel_otp/")
async def cancel_otp():
    try:
        # Нажимаем на кнопку отмены и возвращаем тип следующей страницы
        await click_button(config.page, cancel_button_selector)
        next_page_type = await detect_page_type(browser)
        if next_page_type:
            return LoginResponse(status="success", next_page_type=next_page_type)
        return LoginResponse(status="success", next_page_type=None)

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отменить вход по временному паролю.")