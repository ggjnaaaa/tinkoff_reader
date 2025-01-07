from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from database import Session
#from models import AirBalonWeather
from typing import Optional
from pytz import timezone
from datetime import datetime, timedelta
import gspread
#from babel.dates import format_date

from routers.directory.tinkoff_expenses import get_expenses_from_db
from utils.tinkoff.time_utils import get_period_range


router = APIRouter()
templates = Jinja2Templates(directory="templates")
moscow_tz = timezone('Europe/Moscow')


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

try:
    gc = gspread.service_account(filename="credentials.json")
    sht2 = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/15Oaloc-K-I45DcrCltEFk-y5RFdH7GhLddNKbZylgzU/edit?usp=sharing'
    )
    worksheet = sht2.get_worksheet(0)
except Exception as e:
    print(f"Ошибка при инициализации gspread: {str(e)}")

'''
@router.get("/bot_air_balon", response_class=HTMLResponse)
async def directory(
    request: Request,
username: str,
    db: Session = Depends(get_db),
):

    weathers = db.query(AirBalonWeather).all()
    return templates.TemplateResponse(
        "air_balon.html",
        {"request": request, "weathers": weathers, "username": username},
    )


@router.post("/submit_balloon")
async def submit_balloon(
        username: str = Form(""),
        nalchik_tethered_flight: str = Form(""),
        terminal_tethered_flight: str = Form(""),
        nalchik_free_flight: str = Form(""),
        terminal_free_flight: str = Form(""),
        weather: str = Form(""),
        comment: Optional[str] = Form(None)
):
    worksheet.format('A:A', {
        "numberFormat": {
            "type": "DATE_TIME",
            "pattern": "dd.mm.yyyy hh:mm"
        }
    })

    # Обработка свободных полетов, приведение типов
    nalchik_free_flight = int(nalchik_free_flight) if nalchik_free_flight else None

    # Используем завтрашнюю дату вместо текущей
    current_time = datetime.now(moscow_tz)
    new_date = current_time.strftime("%d.%m.%Y")
    new_row = [
        current_time.strftime("%d.%m.%Y %H:%M"), username, nalchik_tethered_flight, terminal_tethered_flight,
        nalchik_free_flight, terminal_free_flight, weather, comment
    ]

    # Получение всех данных из таблицы
    all_values = worksheet.get_all_values()
    if all_values:  # Если таблица не пустая
        last_row = all_values[-1]  # Последняя строка таблицы
        last_date = last_row[0].split(" ")[0]  # Извлекаем дату последней записи

        # Проверяем, чтобы значение даты не содержало текст
        try:
            last_date_obj = datetime.strptime(last_date, "%d.%m.%Y")  # Пробуем преобразовать в объект даты
        except ValueError:
            last_date_obj = None  # Если преобразование не удалось, пропускаем обработку даты

        if last_date_obj:  # Если дата успешно преобразована
            # Преобразуем даты в объекты datetime и получаем месяцы
            last_month = format_date(last_date_obj, "MMMM", locale="ru")  # Название месяца на русском
            new_month = format_date(current_time, "MMMM", locale="ru")

            if last_month != new_month:  # Если месяцы отличаются
                # Добавляем строку с названием нового месяца
                worksheet.append_row([new_month.capitalize()] + [""] * (len(last_row) - 1),
                                     value_input_option="USER_ENTERED")
            elif last_date < new_date:  # Если даты отличаются (новая больше)
                # Добавляем строку с новой датой
                worksheet.append_row([new_date] + [""] * (len(last_row) - 1), value_input_option="USER_ENTERED")

    # Добавление новой строки
    worksheet.append_row(new_row, value_input_option="USER_ENTERED")

    return JSONResponse(content={"message": "Данные успешно отправлены"})

'''


def sync_expenses_to_sheet(db, period="week", timezone_str="Europe/Moscow"):
    """
    Синхронизация расходов из базы данных в Google Sheets. ВЕРСИЯ С АЙДИШНИКАМИ
    """
    # Получаем расходы за период
    unix_range_start, unix_range_end = get_period_range(
        timezone=timezone_str,
        range_start='2024-01-01',
        range_end='2025-01-01'
    )

    expenses_data = get_expenses_from_db(
        db=db,
        unix_range_start=unix_range_start,
        unix_range_end=unix_range_end,
        timezone_str=timezone_str,
        sort_order='asc'
    )

    # Получаем текущие данные из таблицы
    existing_rows = worksheet.get_all_values()
    existing_expenses = {
        row[0]: row[1:]  # Ключ — `id`, значение — остальные данные
        for row in existing_rows[1:]  # Пропускаем заголовок
    }

    # Обрабатываем новые данные
    for expense in expenses_data["expenses"]:
        expense_id = str(expense["id"])
        date_time = expense["date_time"]
        card_number = expense["card_number"]
        amount = "{:.2f}".format(expense["amount"]).rstrip('0').rstrip('.').replace('.', ',')
        description = expense["description"]
        category = expense["category"]

        # Если запись с таким `id` есть
        if expense_id in existing_expenses:
            existing_data = existing_expenses[expense_id]

            # Формируем строку для сравнения
            updated_data = [date_time, card_number, amount, description, category]

            # Если данные отличаются, обновляем запись
            if existing_data != updated_data:
                # Находим индекс строки для обновления
                row_index = list(existing_expenses.keys()).index(expense_id) + 2  # +2 из-за заголовка
                worksheet.update(f"B{row_index}:F{row_index}", [updated_data])
        else:
            # Если записи нет, добавляем новую строку
            worksheet.append_row([expense_id, date_time, card_number, amount, description, category])

'''
def sync_expenses_to_sheet_no_id(db, period="week", timezone_str="Europe/Moscow"):
    """
    Синхронизация расходов из базы данных в Google Sheets. ВЕРСИЯ БЕЗ АЙДИШНИКОВ
    """
    # Получаем расходы за последние 7 дней
    unix_range_start, unix_range_end = get_period_range(
        timezone="Europe/Moscow",
        period=period
    )

    expenses_data = get_expenses_from_db(
        db=db,
        unix_range_start=unix_range_start,
        unix_range_end=unix_range_end,
        timezone_str=timezone_str
    )

    # Получаем текущие данные из таблицы
    existing_rows = worksheet.get_all_values()
    existing_expenses = {
        (row[0], row[1], row[2], row[3]): row[4]
        for row in existing_rows[1:]  # Пропускаем заголовок
    }
    existing_expenses_tuples = [tuple(expense) for expense in existing_expenses]

    # Добавляем новые расходы
    for expense in expenses_data["expenses"]:
        date_time = expense["date_time"]
        card_number = expense["card_number"]
        amount = "{:.2f}".format(expense["amount"]).rstrip('0').rstrip('.').replace('.',',')
        description = expense["description"]
        category = expense["category"]

        # Проверяем, есть ли запись в таблице
        if (date_time, card_number, str(amount), description) not in existing_expenses_tuples:
            worksheet.append_row([date_time, card_number, amount, description, category])
'''