# auth_tinkoff.py

# Стандартные библиотеки Python
import os, asyncio

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Body, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

# Собственные модули
from models import LoginResponse
import config as config
from config import (
    timer_selector, 
    resend_sms_button_selector, 
    cancel_button_selector, 
    browser_instance as browser
)

from utils.tinkoff.browser_manager import BrowserManager
from utils.tinkoff.tinkoff_auth import paged_login, close_login_via_sms_page, get_user_name_from_otp_login
from utils.tinkoff.browser_utils import get_text, detect_page_type, PageType, click_button, detect_page_type_after_url_change

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Вход в тинькофф
@router.get("/tinkoff/")
async def get_login_type(request: Request):
    global browser

    # Открытие браузера если закрыт, если открыт обновление времени выключения
    if await check_for_page(browser):
        browser.reset_interaction_time()
    elif await check_for_browser(browser):
        await browser.create_context_and_page()
    else:
        browser = BrowserManager(config.PATH_TO_CHROME_PROFILE,
                                 config.DOWNLOAD_DIRECTORY,
                                 config.BROWSER_TIMEOUT)
        await browser.create_context_and_page()

    try:
        await browser.page.goto(config.EXPENSES_URL, timeout=30000)  # Переход на страницу расходов
        detected_type = await detect_page_type(browser, 5)  # Асинхронное определение типа страницы

        if detected_type:
            # Отмена входа по смс, переход на вход через номер телефона
            if detected_type == PageType.LOGIN_SMS_CODE:
                detected_type = await close_login_via_sms_page(browser)
                if not detected_type:
                    raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")

            # Получаем путь к нужному шаблону
            page_path = detected_type.template_path()
            await save_browser_cache()

            if not page_path:
                raise HTTPException(status_code=307, detail="Ошибка загрузки страницы")

            # Вход по временному паролю
            if detected_type == PageType.LOGIN_OTP:
                return templates.TemplateResponse(page_path, {"request": request, "name": await get_user_name_from_otp_login(browser)})
            
            return templates.TemplateResponse(page_path, {"request": request})
        else:
            raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    except Exception as e:
        print(f"Ошибка в get_login_type(): {e}")
        raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    
# Обработка всех страниц входа
@router.post("/tinkoff/login/", response_model=LoginResponse)
async def login(request: Request, data: str = Body(...)):
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        current_page_type, result = await paged_login(browser, data, 10)  # Отправка данных, получает тип следующей страницы
        await save_browser_cache()
        if result:
            return LoginResponse(status="success", next_page_type=result, current_page_type=current_page_type) 
        raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    except:
        raise

# Универсальный эндпоинт для загрузки следующей страницы
@router.get("/tinkoff/next/")
async def next_page(request: Request, step: str | None = Query(default=None)):
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    # Определяем `page_type`, пытаясь преобразовать `step` в `PageType`
    if step:
        try:
            page_type = PageType.from_string(step)  # Используем метод класса
        except ValueError:
            raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    else:
        page_type = await detect_page_type(browser, 5)
        if not page_type:
            raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")

     # Отмена входа по смс, переход на вход через номер телефона
    if page_type == PageType.LOGIN_SMS_CODE:
        page_type = await close_login_via_sms_page(browser)

    # Получаем путь к нужному шаблону
    template_path = page_type.template_path()

    if not template_path:
        raise HTTPException(status_code=307, detail="Ошибка загрузки страницы")

    if page_type == PageType.LOGIN_OTP:
        return templates.TemplateResponse(template_path, {"request": request, "name": await get_user_name_from_otp_login(browser)})
    
    if page_type == PageType.EXPENSES:
        return RedirectResponse(url="/tinkoff/expenses/page")
    
    return templates.TemplateResponse(template_path, {"request": request})

# Эндпоинт для получения таймера при вводе смс
@router.get("/tinkoff/get_sms_timer/")
async def get_sms_timer():
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        await asyncio.sleep(1)
        # Получаем оставшееся время в секундах
        time_left = await get_text(browser.page, timer_selector)
        return {"time_left": time_left}

    except Exception as e:
        print(f"Ошибка при получении таймера: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить таймер")

# Эндпоинт для повторной отправки смс
@router.post("/tinkoff/resend_sms/")
async def resend_sms():
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        browser.reset_interaction_time()
        # Нажимаем на кнопку повторной отправки
        await click_button(browser.page, resend_sms_button_selector)
        await save_browser_cache()
        return {"status": "success", "message": "SMS успешно отправлено"}

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отправить SMS повторно")

# Эндпоинт для отмены входа по временному паролю
@router.post("/tinkoff/cancel_otp/")
async def cancel_otp():
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        browser.reset_interaction_time()
        next_page_type = await close_login_via_sms_page(browser) 
        await save_browser_cache()
        if next_page_type:
            return LoginResponse(status="success", next_page_type=next_page_type, current_page_type=None)
        raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отменить вход по временному паролю.")
    
async def check_for_browser(browser: BrowserManager):
    return browser and await browser.is_browser_active()

async def check_for_page(browser: BrowserManager):
    return browser and await browser.is_page_active()

def get_browser():
    return browser

async def save_browser_cache():
    if browser:
        await browser.save_browser_cache()