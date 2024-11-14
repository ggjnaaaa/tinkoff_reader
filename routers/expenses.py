# expenses.py

# Библиотеки Python
import time

# Сторонние библиотеки
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional
from fastapi.templating import Jinja2Templates
from playwright.async_api import Page

# Собственные модули
from routers.auth_tinkoff import get_browser, check_for_browser
from utils.tinkoff.expenses_utils import load_expenses_from_site
from utils.tinkoff.time_utils import (
    get_period_range,
)
from utils.tinkoff.browser_utils import PageType
from routers.directory.tinkoff_expenses import (
    get_expenses_from_db,
    get_categories_from_db,
    save_keyword_to_db,
    remove_keyword_from_category,
    get_last_unreceived_error,
    set_temporary_code
)
import config as config
from database import Session
from models import SaveKeywordsRequest, CategoryExpenses

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Эндпоинт для отображения страницы расходов
@router.get("/tinkoff/expenses/page", response_class=HTMLResponse)
async def show_expenses_page(request: Request):
    # Передаем начальные параметры для рендеринга шаблона
    return templates.TemplateResponse("tinkoff/expenses.html", {"request": request})#RedirectResponse(url="/tinkoff/expenses/")

# Эндпоинт для получения расходов за выбранный период
@router.get("/tinkoff/expenses/")
async def get_expenses( 
    request: Request,
    period: Optional[str] = None,  # Необязательный период
    rangeStart: Optional[str] = None,  # Необязательное начало периода
    rangeEnd: Optional[str] = None,  # Необязательный конец периода
    time_zone: str = Query(...), 
    db: Session = Depends(get_db)
):
    # Преобразуем указанный диапазон в Unix-формат
    unix_range_start, unix_range_end = get_period_range(
        timezone=time_zone,
        range_start=rangeStart,
        range_end=rangeEnd,
        period=period
    )
    
    # Проверяем доступность браузера
    browser = get_browser()
    if browser and await check_for_browser(browser):
        # Если браузер доступен, загружаем данные с сайта
        expenses_data = await load_expenses_from_site(browser, unix_range_start, unix_range_end, db, time_zone)
    else:
        # Если браузер недоступен, загружаем из базы, если данные существуют
        expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, time_zone)
        
        if not expenses_data["expenses"]:
            raise HTTPException(status_code=404, detail="Данные за выбранный период отсутствуют в базе данных.")
        
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return expenses_data

    # Иначе возвращаем HTML-шаблон
    return templates.TemplateResponse(PageType.EXPENSES.template_path(), {"request": request })

# Эндпоинт для получения всех категорий
@router.get("/tinkoff/expenses/categories/")
def get_categories(db: Session = Depends(get_db)):
    return get_categories_from_db(db)

@router.post("/tinkoff/expenses/keywords/")
async def save_keywords(request: SaveKeywordsRequest, db: Session = Depends(get_db)):
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

# Эндпоинт для сохранения временного пароля
@router.post("/tinkoff/save_otp/")
async def save_otp(
    otp: str = Query(...), 
    db: Session = Depends(get_db)):
    if otp and len(otp) == 4:
        set_temporary_code(db, otp)

@router.get("/tinkoff/expenses/last_error/")
def get_last_error_endpoint(db: Session = Depends(get_db)):
    last_error = get_last_unreceived_error(db)
    if last_error:
        return {"last_error": last_error.error_text}
    return {"last_error": None}