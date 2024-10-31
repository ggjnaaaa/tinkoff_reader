# auth_tinkoff.py

# Стандартные библиотеки Python
import os
import re

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Body, Request, Query
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

# Собственные модули
import tinkoff.config as config
from tinkoff.models import LoginResponse
from servises.driver_setup import create_chrome_driver, close_driver, is_browser_active, reset_interaction_time
from servises.tinkoff_auth import paged_login, close_login_via_sms_page
from servises.browser_utils import get_text, detect_page_type, PageType, click_button

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Вход в тинькофф
@router.get("/tinkoff/")
def get_login_type(request: Request):
    tmp_driver = config.driver
    load_dotenv()
    config.DOWNLOAD_DIRECTORY = os.getenv("DOWNLOAD_DIRECTORY")

    if not is_browser_active():
        config.driver = create_chrome_driver(os.getenv("PATH_TO_CHROME_PROFILE"), 
                                             os.getenv("PATH_TO_CHROME_DRIVER"), 
                                             config.BROWSER_TIMEOUT)
        tmp_driver = config.driver
    else:
        reset_interaction_time()

    try:
        tmp_driver.get(config.EXPENSES_URL)
        detected_type = detect_page_type(tmp_driver)
        if detected_type:
            if detected_type == PageType.LOGIN_SMS_CODE:
                detected_type = close_login_via_sms_page(tmp_driver)

            page_path = detected_type.template_path()

            if detected_type == PageType.LOGIN_OTP:
                greeting_text = get_text(config.driver, "[automation-id='form-title']")

                # Регулярное выражение для поиска имени после "Здравствуйте, "
                match = re.search(r"Здравствуйте, (.+)!", greeting_text)
                if match:
                    user_name = match.group(1)  # Извлекаем первую группу, которая содержит имя
                else:
                    user_name = ''

                return templates.TemplateResponse(page_path, {"request": request, "name": user_name})

            return templates.TemplateResponse(page_path, {"request": request})
        else:
            config.driver = close_driver()
            raise HTTPException(status_code=400, detail="Не удалось определить тип страницы.")
    except Exception as e:
        config.driver = close_driver()
        raise HTTPException(status_code=500, detail=str(e))
    
# Вход в лк тинькофф
@router.post("/tinkoff/login/", response_model=LoginResponse)
def login(request: Request, data: str = Body(...)):
    if not config.driver:
        raise HTTPException(status_code=440, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        print(data)
        result = paged_login(config.driver, data)
        print(result)
        if result:
            # Используем LoginResponse для возвращения ответа
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
        page_type = detect_page_type(config.driver)

    if page_type == PageType.LOGIN_SMS_CODE:
        page_type = close_login_via_sms_page(config.driver)

    # Получаем путь к нужному шаблону
    template_path = page_type.template_path()

    

    if page_type == PageType.LOGIN_OTP:
        greeting_text = get_text(config.driver, "[automation-id='form-title']")

        # Регулярное выражение для поиска имени после "Здравствуйте, "
        match = re.search(r"Здравствуйте, (.+)!", greeting_text)
        if match:
            user_name = match.group(1)  # Извлекаем первую группу, которая содержит имя
        else:
            user_name = ''

        return templates.TemplateResponse(template_path, {"request": request, "name": user_name})
    
    return templates.TemplateResponse(template_path, {"request": request})

@router.get("/tinkoff/get_sms_timer/")
def get_sms_timer():
    try:
        # Получаем оставшееся время в секундах
        time_left = get_text(config.driver, 'span[automation-id="left-time"]')
        return {"time_left": time_left}

    except Exception as e:
        print(f"Ошибка при получении таймера: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить таймер")


@router.post("/tinkoff/resend_sms/")
def resend_sms():
    try:
        click_button(config.driver, 'button[automation-id="resend-button"]')
        return {"status": "success", "message": "SMS успешно отправлено"}

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отправить SMS повторно")

@router.post("/tinkoff/cancel_otp/")
def cancel_otp():
    try:
        click_button(config.driver, 'button[automation-id="cancel-button"]')
        next_page_type = detect_page_type(config.driver)
        if next_page_type:
            return LoginResponse(status="success", next_page_type=next_page_type)
        return LoginResponse(status="success", next_page_type=None)

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отменить вход по временному паролю.")