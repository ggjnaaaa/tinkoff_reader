# expenses.py

# Библиотеки Python
import time

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from selenium.webdriver.common.by import By
from typing import List, Optional
from fastapi.templating import Jinja2Templates

# Собственные модули
import tinkoff.config as config
from servises.driver_setup import is_browser_active, reset_interaction_time
from servises.browser_utils import download_csv_from_expenses_page
from servises.general_utils import (
    wait_for_new_download, 
    expenses_redirect, 
    get_expense_categories_with_description,
    get_expense_categories,
    get_json_expense_from_csv
)
from tinkoff.models import (
    CategoryRequest,
    CategorySaveRequest
)

# База данных (условно)
categories_db = [
    {"id": 1, "category_name": "Продукты", "keywords": ["магазин", "продукты"]},
    {"id": 2, "category_name": "Транспорт", "keywords": ["бензин", "транспорт"]},
    # Дополнительно добавляем категории по необходимости
]

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Эндпоинт для отображения страницы расходов
@router.get("/tinkoff/expenses/page", response_class=HTMLResponse)
async def show_expenses_page(request: Request):
    # Передаем начальные параметры для рендеринга шаблона
    return templates.TemplateResponse("tinkoff/expenses.html", {"request": request})

# Эндпоинт для получения расходов за выбранный период
@router.get("/tinkoff/expenses/")
def get_expenses( 
    period: Optional[str] = Query("month"),  # Необязательный период
    rangeStart: Optional[str] = None,  # Необязательное начало периода
    rangeEnd: Optional[str] = None  # Необязательный конец периода
):
    if not is_browser_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Перенаправление на основную страницу.")
    else:
        reset_interaction_time()
    
    if expenses_redirect(period, rangeStart, rangeEnd):  # Перенаправление на страницу по соответствующему периоду
        time.sleep(1)  # Если было перенаправление, то небольшое ожидание

    start_time = time.time()  # Засекаем время, начиная с которого надо искать csv
    download_csv_from_expenses_page(config.driver)  # Качаем csv

    # Ждём появления нового CSV-файла
    file_path = wait_for_new_download(start_time=start_time)

    # Получаем словарь с категориями из бд
    categories_dict = get_expense_categories_with_description()

    return get_json_expense_from_csv(file_path, categories_dict)
    

# Эндпоинт для получения категорий
@router.get("/tinkoff/expenses/categories/")
def get_categories():
    return get_expense_categories()

# Эндпоинт для добавления новой категории
@router.post("/tinkoff/expenses/categories/")
def add_category(category: CategoryRequest):
    new_id = len(categories_db) + 1
    new_category = {
        "id": new_id,
        "category_name": category.category_name,
        "keywords": category.keywords or []
    }
    categories_db.append(new_category)
    return {"message": "Категория добавлена успешно", "category": new_category}

# Эндпоинт для сохранения категорий для операций
@router.post("/tinkoff/expenses/save-categories")
def save_categories(data: CategorySaveRequest):
    # Логика сохранения категории в базе данных для каждой операции (заглушка)
    # Здесь происходит связывание расходов с категориями в БД
    return {"message": "Категории сохранены успешно"}