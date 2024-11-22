# expenses.py

# Библиотеки Python
import json

# Сторонние библиотеки
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Optional

# Собственные модули
from routers.auth_tinkoff import get_browser, check_for_browser
from routers.directory.tinkoff_expenses import (
    get_expenses_from_db,
    get_categories_from_db,
    save_keyword_to_db,
    remove_keyword_from_category,
    get_last_unreceived_error,
    set_temporary_code
)

from utils.tinkoff.expenses_utils import load_expenses_from_site
from utils.tinkoff.time_utils import get_period_range
from utils.tinkoff.browser_utils import PageType

import config as config
from database import Session
from models import SaveKeywordsRequest, CategoryExpenses
from auth import create_temp_token


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
    period: Optional[str] = None,
    rangeStart: Optional[str] = None,
    rangeEnd: Optional[str] = None,
    time_zone: str = Query(...),
    source: str = Query('db'),
    db: Session = Depends(get_db)
):
    """
    Эндпоинт для получения расходов. Загружает данные из базы данных или с сайта, в зависимости от параметра `source`.
    """
    # Определяем временные диапазоны
    unix_range_start, unix_range_end = get_period_range(
        timezone=time_zone,
        range_start=rangeStart,
        range_end=rangeEnd,
        period=period
    )

    try:
        # Логика загрузки расходов
        if source == 'tinkoff':
            browser = get_browser()

            if browser and await check_for_browser(browser):
                # Если браузер активен, загружаем данные
                try:
                    expenses_data = await load_expenses_from_site(browser, unix_range_start, unix_range_end, db, time_zone)
                except Exception as e:
                    return response_with_token(request, 
                                               period, 
                                               rangeStart, 
                                               rangeEnd, 
                                               time_zone, 
                                               "Ошибка загрузки расходов. Попробуйте снова позже.")
            else:
                return response_with_token(request, 
                                               period, 
                                               rangeStart, 
                                               rangeEnd, 
                                               time_zone, 
                                               "Необходима авторизация")
        else:
            # Загружаем данные из базы данных
            expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, time_zone)
    except Exception as e:
        print(f"Ошибка загрузки расходов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка выгрузки расходов. Повторите попытку позже.")

    # Возврат JSON или страницы
    if not expenses_data["expenses"]:
        error_message = "Данные за выбранный период отсутствуют."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse(
                status_code=200,
                content={"error_message": error_message}
            )
        return templates.TemplateResponse(
            PageType.EXPENSES.template_path(),
            {"request": request, "error_message": error_message, "expenses": []},
            status_code=200
        )
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse(content=expenses_data)
    
    return templates.TemplateResponse(PageType.EXPENSES.template_path(), {"request": request, "expenses": json.dumps(expenses_data)})


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
async def save_keywords(request: SaveKeywordsRequest, db: Session = Depends(get_db)):
    """
    Эндпоинт для сохранения ключевых слов категорий.
    """
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
    db: Session = Depends(get_db)
):
    """
    Эндпоинт для сохранения временного пароля.
    """
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