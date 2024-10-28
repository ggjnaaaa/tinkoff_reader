# auth_tinkoff.py

# Стандартные библиотеки Python
import os

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Body
from dotenv import load_dotenv

# Собственные модули
import config
from servises.driver_setup import create_chrome_driver, close_driver, is_browser_active, reset_interaction_time
from servises.tinkoff_auth import paged_login, close_login_via_sms_page
from servises.browser_utils import get_text, detect_page_type, PageType, click_button

router = APIRouter()

# Основной процесс
@router.get("/tinkoff/")
def get_login_type():
    tmp_driver = config.driver
    load_dotenv()

    config.DOWNLOAD_DIRECTORY = os.getenv("DOWNLOAD_DIRECTORY")

    print("LGHKGL")
    print(tmp_driver)
 
    print(is_browser_active())
    if not is_browser_active():
        print("БРАУЗЕР ОТКРЫВАЕТСЯ")
        config.driver = create_chrome_driver(os.getenv("PATH_TO_CHROME_PROFILE"), 
                                             os.getenv("PATH_TO_CHROME_DRIVER"), 
                                             config.BROWSER_TIMEOUT)
        tmp_driver = config.driver
    else:
        reset_interaction_time()

    print("LJLHGLHGLG:G:K")
    try:
        tmp_driver.get(config.EXPENSES_URL)
        detected_type = detect_page_type(tmp_driver)
        print(detected_type)
        if detected_type:
            if detected_type == PageType.LOGIN_SMS_CODE:
                close_login_via_sms_page(tmp_driver)
            return {"status": "success", "next_page_type": detected_type.name}
        else:
            config.driver = close_driver()
            raise HTTPException(status_code=400, detail="Не удалось определить тип страницы.")
    except Exception as e:
        config.driver = close_driver()
        raise HTTPException(status_code=500, detail=str(e))
    
# Вход в лк тинькофф
@router.post("/tinkoff/login/")
def login(data: str = Body(..., embed=False)):
    if not config.driver:
        raise HTTPException(status_code=440, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        return paged_login(config.driver, data)
    except Exception:
        raise

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