# routes/auth_tinkoff.py

# Стандартные модули Python
import asyncio

# Сторонние модули
from fastapi import APIRouter, HTTPException, Body, Request, Query, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

# Собственные модули
from models import LoginResponse
from auth import decode_access_token

import config as config
from config import (
    timer_selector, 
    resend_sms_button_selector, 
    browser_instance as browser
)

from utils.bot import check_miniapp_token
from utils.tinkoff.browser_manager import BrowserManager
from utils.tinkoff.browser_input_utils import paged_login, close_login_via_sms_page, get_user_name_from_otp_login, skip_control_questions
from utils.tinkoff.browser_utils import get_text, detect_page_type, PageType, click_button

from database import Session

# from dependencies import get_authenticated_user


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@router.get("/tinkoff/")
async def get_login_type(request: Request, background_tasks: BackgroundTasks, token: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    """
    Вход в тинькофф.
    Инициализирует браузер, если нужно.
    Переходит на расходы.
    """
    global browser
    
    if token:
        if not check_miniapp_token(token):
            return
    else:
        pass
        # return

    
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
        await browser.page.goto(config.EXPENSES_URL, wait_until="domcontentloaded")  # Переход на страницу расходов
        detected_type = await detect_page_type(browser, 10)  # Асинхронное определение типа страницы

        if detected_type:
            return await next_page(request=request, background_tasks=background_tasks, step=detected_type.value, token=token, db=db)
        else:
            raise HTTPException(status_code=500, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    except Exception as e:
        print(f"Ошибка в get_login_type(): {e}")
        raise HTTPException(status_code=500, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    

@router.post("/tinkoff/login/", response_model=LoginResponse)
async def login(request: Request, data: str = Body(...), token: Optional[str] = Query(default=None)):
    """
    Ввод инфы в инпуты
    """
    if token:
        if not check_miniapp_token(token):
            return
    else:
        pass
        # return

    
    # Если страница неактивна кидаем ошибку
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        current_page_type, next_page_type = await paged_login(browser, data, 10)  # Отправка данных, получает тип нынешней и следующей страницы
        await save_browser_cache()  # Сохранение кэша браузера

        if next_page_type:
            return LoginResponse(status="success", next_page_type=next_page_type, current_page_type=current_page_type) 
        raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")
    except:
        raise


@router.get("/tinkoff/next/")
async def next_page(request: Request, 
                    background_tasks: BackgroundTasks,
                    step: str | None = Query(default=None), 
                    db: Session = Depends(get_db), 
                    token: Optional[str] = Query(default=None)):
    """
    Универсальный эндпоинт для загрузки следующей страницы.
    """
    if token:
        if not check_miniapp_token(token):
            return
    else:
        pass
        # return

    
    # Если страница неактивна кидаем ошибку
    if not browser or not await browser.is_page_active():
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
    
    if page_type == PageType.CONTROL_QUESTIONS:
        page_type = await skip_control_questions(browser)

    # Получаем путь к нужному шаблону
    template_path = page_type.template_path()

    if not template_path:
        raise HTTPException(status_code=307, detail="Ошибка загрузки страницы")

    if page_type == PageType.LOGIN_OTP:
        return templates.TemplateResponse(template_path, {"request": request, "name": await get_user_name_from_otp_login(browser), "is_miniapp": bool(token)})
    
    if page_type == PageType.EXPENSES:
        if token:
            from utils.tinkoff.fixed_time_import_expenses import resume_load_expenses
            background_tasks.add_task(resume_load_expenses, db, token)
            return templates.TemplateResponse("tinkoff/success_login.html", {"request": request})
        redirect = redirect_by_token(request)
        if redirect:
            return redirect
    
    return templates.TemplateResponse(template_path, {"request": request, "is_miniapp": bool(token)})


@router.get("/tinkoff/get_sms_timer/")
async def get_sms_timer():
    """
    Эндпоинт для получения таймера при вводе смс.
    """
    # Если страница неактивна кидаем ошибку
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


@router.post("/tinkoff/resend_sms/")
async def resend_sms():
    """
    Эндпоинт для повторной отправки смс.
    """
    # Если страница неактивна кидаем ошибку
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


@router.post("/tinkoff/cancel_otp/")
async def cancel_otp():
    """
    Эндпоинт для отмены входа по временному паролю.
    """
    # Если страница неактивна кидаем ошибку
    if not await browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        browser.reset_interaction_time()
        # Закрываем вход по смс
        next_page_type = await close_login_via_sms_page(browser) 
        await save_browser_cache()
        if next_page_type:
            return LoginResponse(status="success", next_page_type=next_page_type, current_page_type=None)
        raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Попробуйте войти снова")

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отменить вход по временному паролю.")
    

async def check_for_browser(browser: BrowserManager):
    """
    Проверяем работоспособность браузера.
    """
    return browser and await browser.is_browser_active()


async def check_for_page(browser: BrowserManager):
    """
    Проверяем работоспособность страницы.
    """
    return browser and await browser.is_page_active()


def get_browser() -> BrowserManager:
    """
    Возвращаем браузер.
    """
    return browser


async def save_browser_cache():
    """
    Сохраняем кэш браузера.
    """
    if browser:
        await browser.save_browser_cache()


def redirect_by_token(request: Request):
    """
    Проверяет наличие временного токена и перенаправляет, если он есть.
    """
    temp_token = request.cookies.get("temp_token")
    if temp_token:
        temp_data = decode_access_token(temp_token)
        if temp_data:
            query_params = f"?time_zone={temp_data['time_zone']}&source={temp_data['source']}"
            if temp_data["period"]:
                query_params += f"&period={temp_data['period']}"
            elif temp_data["rangeStart"] and temp_data["rangeEnd"]:
                query_params += f"&rangeStart={temp_data['rangeStart']}&rangeEnd={temp_data['rangeEnd']}"

            new_url = f"/tinkoff/expenses/{query_params}"
            response = RedirectResponse(url=new_url)
            response.delete_cookie("temp_token")
            return response
    return None
