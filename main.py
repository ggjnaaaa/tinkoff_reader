# main.py

# Стандартные библиотеки Python
import os

# Сторонние библиотеки
from fastapi import FastAPI, APIRouter, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from selenium.webdriver.common.by import By

# Собственные модули
from driver_setup import create_chrome_driver, close_driver, is_browser_active, reset_interaction_time, stop_interaction_time
from tinkoff_auth import paged_login, close_login_via_sms_page
from utils import get_text, detect_page_type, PageType, convert_to_datetime, collect_expense_details, click_button, parse_amount, get_element


# Тайм-аут для неактивности, после которого браузер будет закрыт (в секундах)
BROWSER_TIMEOUT = 180  # 1 минута
EXPENSES_URL = "https://www.tbank.ru/events/feed/"
 
# FastAPI и роутер
app = FastAPI()
# Разрешаем CORS для всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Работа с драйвером
driver = None
current_url = None

# Pydantic модель для входных данных
class LoginRequest(BaseModel):
    phone_number: str
    password: str
    otp_code: str

# Функция для получения расходов
def get_cost(driver):
    try:
        selector = 'div.PieChart__value_gXIXVm'
        cost = get_text(driver=driver, text_selector=selector, timeout=10)
        cost = cost.replace('\u00A0', '').replace('₽', '').strip()
        return cost
    except Exception as e:
        raise e

# Основной процесс
@router.get("/process/")
def get_login_type():
    global driver, current_url

    load_dotenv()

    print("LGHKGL")
    print(driver)
 
    print(is_browser_active(driver))
    if not driver or not is_browser_active(driver):
        print("БРАУЗЕР ОТКРЫВАЕТСЯ")
        driver = create_chrome_driver(os.getenv("PATH_TO_CHROME_PROFILE"), BROWSER_TIMEOUT)
    else:
        reset_interaction_time()

    print("LJLHGLHGLG:G:K")
    try:
        driver.get(EXPENSES_URL)
        detected_type = detect_page_type(driver)
        print(detected_type)
        if detected_type:
            if detected_type == PageType.LOGIN_SMS_CODE:
                close_login_via_sms_page(driver)
            current_url = driver.current_url
            return {"status": "success", "next_page_type": detected_type.name}
        else:
            driver = close_driver(driver)
            raise HTTPException(status_code=400, detail="Не удалось определить тип страницы.")
    except Exception as e:
        driver = close_driver(driver)
        raise HTTPException(status_code=500, detail=str(e))
    
# Вход в лк тинькофф
@app.post("/process/login/")
def login(data: str = Body(..., embed=False)):
    if not driver:
        raise HTTPException(status_code=440, detail="Сессия истекла. Пожалуйста, войдите заново.")
    
    try:
        return paged_login(driver, data)
    except Exception:
        raise

@app.get("/process/get_sms_timer/")
def get_sms_timer():
    try:
        # Получаем оставшееся время в секундах
        time_left = get_text(driver, 'span[automation-id="left-time"]')
        return {"time_left": time_left}

    except Exception as e:
        print(f"Ошибка при получении таймера: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить таймер")


@app.post("/process/resend_sms/")
def resend_sms():
    try:
        click_button(driver, 'button[automation-id="resend-button"]')
        return {"status": "success", "message": "SMS успешно отправлено"}

    except Exception as e:
        print(f"Ошибка при нажатии на кнопку: {e}")
        raise HTTPException(status_code=500, detail="Не удалось отправить SMS повторно")

@app.get("/process/expenses/")
def get_expenses(
    start_date: str = Query(None),  # Необязательное начало периода
    end_date: str = Query(None)  # Необязательный конец периода
):
    if not driver:
        raise HTTPException(status_code=307, detail="Сессия истекла. Перенаправление на основную страницу.")
    
    #driver.get(EXPENSES_URL)
    #if detect_page_type(driver) != PageType.EXPENSES:
    #    print(detect_page_type(driver))
    #    raise HTTPException(status_code=307, detail="Сессия истекла. Перенаправление на основную страницу.")

    # Преобразуем даты в формат datetime, если они переданы
    start_datetime = convert_to_datetime(start_date) if start_date else None
    end_datetime = convert_to_datetime(end_date) if end_date else None

    # Открываем страницу расходов через WebDriver
    #driver.get('URL_страницы_расходов')

    expenses = []
    total_income = 0
    total_expense = 0

    # Загружаем все элементы расходов, пока кнопка "Показать еще" доступна
    while True:
        try:
            click_button(driver=driver, button_selector='button[data-qa-file="UITimelineOperationsList"]', timeout=10)
        except:
            break

    expense_elements = driver.find_elements(By.CSS_SELECTOR, 'div.UITimelineOperationItem__root_aeIfsN')

    for expense_element in expense_elements:
        expense_element.click() 
        expense_data = collect_expense_details(driver, get_element(driver, 'div[data-qa-type="details-card"]'))
        click_button(driver=driver, button_selector='button[data-qa-file="DetailsCardPopup"]')

        # Если указаны start_date и end_date, фильтруем данные по времени
        expense_datetime = convert_to_datetime(expense_data["date_time"])
        if start_datetime and end_datetime:
            if not (start_datetime <= expense_datetime <= end_datetime):
                continue

        expenses.append(expense_data)

        # Считаем общую сумму доходов и расходов
        amount = parse_amount(expense_data["amount"])
        if amount < 0:
            total_expense += amount
        else:
            total_income += amount
            
    return {
        "expenses": expenses,
        "total_income": total_income,
        "total_expense": total_expense
    }

# Пользователь перешел на другую страницу
@app.post("/process/disconnect/")
def disconnect():
    global driver
    print("Пользователь покинул страницу. Закрываем браузер.")
    stop_interaction_time()
    driver = None
    return {"message": "Браузер закрыт"}



# Подключаем роутер к приложению
app.include_router(router)