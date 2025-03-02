# routes/expenses.py

# Библиотеки Python
import json
import time

# Сторонние библиотеки
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

# Собственные модули
from routers.auth_tinkoff import get_browser, check_for_browser

from routers.directory.tinkoff.expenses import get_expenses_from_db
from routers.directory.tinkoff.errors import get_last_unreceived_error
from routers.directory.tinkoff.temporary_codes import set_temporary_code
from routers.directory.tinkoff.notifications import get_card_nums_for_transfer_notifications
from routers.directory.tinkoff.scheduler import get_import_times
from routers.directory.tinkoff.categories import (
    get_categories_from_db,
    save_keyword_to_db,
    remove_keyword_from_category
)
from routers.directory.bot import get_card_number_by_chat_id

from utils.bot import check_miniapp_token

from utils.tinkoff.expenses_utils import load_expenses_from_site
from utils.tinkoff.time_utils import get_period_range
from utils.tinkoff.browser_utils import PageType

import config as config
from database import Session
from models import SaveKeywordsRequest, CategoryExpenses
from auth import create_temp_token, verify_bot_token

from dependencies import get_authenticated_user


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Эндпоинт для отображения страницы расходов
@router.get("/tinkoff/expenses/page", response_class=HTMLResponse)
async def show_expenses_page(request: Request):
    # Передаем начальные параметры для рендеринга шаблона
    return templates.TemplateResponse("tinkoff/expenses.html", {"request": request})
    

@router.get("/tinkoff/expenses/")
async def get_expenses(
    request: Request,
    token: Optional[str] = Query(None),  # Если передан, значит, запрос от бота
    show_all_expenses: bool = Query(False),
    period: Optional[str] = None,
    rangeStart: Optional[str] = None,
    rangeEnd: Optional[str] = None,
    time_zone: str = Query("Europe/Moscow"),
    source: str = Query('db'),
    db: Session = Depends(get_db),
    user: dict = Depends(get_authenticated_user)
):
    """
    Универсальный эндпоинт для получения расходов. Работает и для бота, и для основного интерфейса.
    """
    card_num = None
    chat_id = None
    if token:
        # Запрос от бота
        card_num, chat_id = await process_bot_request(token, db)
    else:
        # Запрос от обычного пользователя
        if isinstance(user, RedirectResponse):
            pass
            # return user  # Если пользователь не аутентифицирован

    # Преобразуем диапазон в Unix-время
    unix_range_start, unix_range_end = get_period_range(
        timezone=time_zone,
        range_start=rangeStart,
        range_end=rangeEnd,
        period=period
    )

    try:
        if source == 'tinkoff':
            expenses_data = await get_expenses_from_tinkoff(unix_range_start, unix_range_end, db, time_zone)
        else:
            expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, time_zone, card_num, show_all_expenses)
    except Exception as e:
        print(f"Ошибка загрузки расходов: {e}")
        return response_with_token(request, 
                                    period, 
                                    rangeStart, 
                                    rangeEnd, 
                                    time_zone, 
                                    "Необходима авторизация")

    return generate_expense_response(request, expenses_data, 
                                     token is not None, 
                                     str(chat_id) in get_card_nums_for_transfer_notifications(db),
                                     get_import_times(db))


async def process_bot_request(token: str, db: Session) -> str:
    """Проверяет токен бота и возвращает номер карты."""
    try:
        user_data = verify_bot_token(token)
        chat_id = int(user_data.get("chat_id"))
        auth_date = int(user_data.get("auth_date", 0))

        if (int(time.time()) - auth_date) > 25 * 3600:
            raise HTTPException(status_code=401, detail="Токен истёк.")

        card_num = get_card_number_by_chat_id(db, chat_id)
        if not card_num:
            raise HTTPException(status_code=403, detail="Пользователь не найден.")
        return card_num, chat_id
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


async def get_expenses_from_tinkoff(start: int, end: int, db: Session, time_zone: str):
    """Загружает расходы с сайта Тинькофф."""
    browser = get_browser()
    if browser and await check_for_browser(browser):
        return await load_expenses_from_site(browser, start, end, db, time_zone)
    else:
        raise HTTPException(status_code=403, detail="Необходима авторизация.")


def generate_expense_response(
        request: Request, 
        expenses_data: dict, 
        is_bot: bool, 
        can_view_all_expenses: bool, 
        import_times: dict
    ):
    """Формирует JSON или HTML-ответ."""
    if not expenses_data["expenses"]:
        error_message = "Данные за выбранный период отсутствуют."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse(status_code=200, content={"error_message": error_message})
        return templates.TemplateResponse(PageType.EXPENSES.template_path(), {
                                                                                "request": request, 
                                                                                "error_message": error_message, 
                                                                                "expenses": [], 
                                                                                "is_miniapp": is_bot,
                                                                                "can_view_all_expenses": can_view_all_expenses,
                                                                                "first_import_time": import_times["expenses"],
                                                                                "second_import_time": import_times["full"],
                                                                                })

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse(content=expenses_data)

    return templates.TemplateResponse(PageType.EXPENSES.template_path(), {
                                                                            "request": request, 
                                                                            "expenses": json.dumps(expenses_data), 
                                                                            "is_miniapp": is_bot,
                                                                            "can_view_all_expenses": can_view_all_expenses,
                                                                            "first_import_time": import_times["expenses"],
                                                                            "second_import_time": import_times["full"],
                                                                            })


def response_with_token(request, period, rangeStart, rangeEnd, time_zone, message):
    """
    Подготовка ответа о перенаправлении с токеном
    """
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        response = JSONResponse(
            content={
                "message": message,
                "redirect_url": "/tinkoff/"
            }
        )
    else:
        response = RedirectResponse(url="/tinkoff/", status_code=303)
    
    set_temp_token(response, period, rangeStart, rangeEnd, time_zone)
    return response


def set_temp_token(response, period, rangeStart, rangeEnd, time_zone):
    """
    Устанавливает временный токен для перенаправления.
    """
    temp_data = {
        "period": None if rangeStart and rangeEnd else period,
        "rangeStart": rangeStart,
        "rangeEnd": rangeEnd,
        "time_zone": time_zone,
        "source": "tinkoff"
    }
    temp_token = create_temp_token(temp_data)
    response.set_cookie(key="temp_token", 
                        value=temp_token, 
                        httponly=True)
    return response


@router.get("/tinkoff/expenses/categories/")
def get_categories(db: Session = Depends(get_db)):
    """
    Эндпоинт для получения всех категорий.
    """
    return get_categories_from_db(db)


@router.post("/tinkoff/expenses/keywords/")
async def save_keywords(
    request: SaveKeywordsRequest, 
    db: Session = Depends(get_db),
    user: dict = Depends(get_authenticated_user), 
    token: Optional[str] = Query(None)
):
    """
    Эндпоинт для сохранения ключевых слов категорий.
    """
    if token:
        # Запрос от бота
        if not check_miniapp_token(token):
            return
    else:
        # Запрос от обычного пользователя
        if isinstance(user, RedirectResponse):
            pass # return user  # Если пользователь не аутентифицирован
    
    for keyword in request.keywords:
        if keyword.category_name == "":
            # Удаляем ключевое слово, если оно привязано к какой-либо категории
            remove_keyword_from_category(db, keyword.description)
        else:
            # Ищем ID категории по названию
            category = db.query(CategoryExpenses).filter(CategoryExpenses.title == keyword.category_name).first()
            if category:
                save_keyword_to_db(db, keyword.description, category.id)
            else:
                raise HTTPException(status_code=422, detail=f"Категория {keyword.category_name} не найдена")
    return JSONResponse(content={"message": "Ключевые слова успешно сохранены"})


@router.post("/tinkoff/save_otp/")
async def save_otp(
    otp: str = Query(...), 
    db: Session = Depends(get_db),
    user: dict = Depends(get_authenticated_user),
    token: Optional[str] = Query(None)
):
    """
    Эндпоинт для сохранения временного пароля.
    """
    if token:
        # Запрос от бота
        if not check_miniapp_token(token):
            return
    else:
        # Запрос от обычного пользователя
        if isinstance(user, RedirectResponse):
            pass # return user  # Если пользователь не аутентифицирован
    
    if otp and len(otp) == 4:
        set_temporary_code(db, otp)


@router.get("/tinkoff/expenses/last_error/")
def get_last_error(db: Session = Depends(get_db)):
    """
    Эндпоинт для получения последней ошибки при автовыгрузке расходов.
    """
    last_error = get_last_unreceived_error(db)
    if last_error:
        return {"last_error": last_error.error_text}
    return {"last_error": None}