# auth_tinkoff.py

# Стандартные библиотеки Python
import os
import traceback

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Body, Request
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

# Собственные модули
import tinkoff.config as config
from servises.driver_setup import create_chrome_driver, close_driver, is_browser_active, reset_interaction_time
from servises.tinkoff_auth import paged_login, close_login_via_sms_page
from servises.browser_utils import get_text, detect_page_type, PageType, click_button

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Вход в тинькофф
@router.get("/tinkoff/")
async def get_login_type(request: Request):
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
        print(tmp_driver)
        print(detected_type)
        if detected_type:
            page_path = detected_type.template_path()

            if detected_type == PageType.LOGIN_SMS_CODE:
                close_login_via_sms_page(tmp_driver)
            
            return templates.TemplateResponse(page_path, {"request": request})
        else:
            config.driver = close_driver()
            raise HTTPException(status_code=400, detail="Не удалось определить тип страницы.")
    except Exception as e:
        config.driver = close_driver()
        raise HTTPException(status_code=500, detail=str(e))

# Вход в ЛК Тинькофф: обработка логина
@router.post("/tinkoff/login/")
async def login_process(request: Request, data: str = Body(...)):
    if not config.driver:
        raise HTTPException(status_code=440, detail="Сессия истекла. Пожалуйста, войдите заново.")

    try:
        result = paged_login(config.driver, data)
        if result:
            # Возвращаем JSON с указанием успешного входа и эндпоинта для перехода
            return {"status": "success", "next_page": "/tinkoff/next/"}
        return {"status": "failed", "message": "Ошибка входа"}
    except Exception as e:
        print("Ошибка в login_process:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка на сервере: {str(e)}")

# Универсальный эндпоинт для загрузки следующей страницы
@router.get("/tinkoff/next/")
async def next_page(request: Request):
    # Определяем нужный шаблон через detect_page_type
    template_path = detect_page_type(config.driver).template_path()
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