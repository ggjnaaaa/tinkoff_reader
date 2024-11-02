# expenses.py

# Библиотеки Python
import time
from typing import List

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from typing import Optional
from fastapi.templating import Jinja2Templates

# Собственные модули
from tinkoff.config import browser_instance as browser
from utils.tinkoff.browser_utils import download_csv_from_expenses_page
from utils.tinkoff.general_utils import (
    wait_for_new_download, 
    expenses_redirect, 
    get_expense_categories_with_description,
    get_json_expense_from_csv
)
from tinkoff.models import (
    CategoryRequest,
    KeywordsUpdateRequest,
    DeleteCategoryRequest
)

# Имитируем "БД" с помощью словарей
categories_db = {1: "Продукты", 2: "Транспорт", 3: "Развлечения"}  # id: название статьи
keywords_db = {}  # id: ключевые слова

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Эндпоинт для отображения страницы расходов
@router.get("/tinkoff/expenses/page", response_class=HTMLResponse)
async def show_expenses_page(request: Request):
    print("ПЕРЕХОД НА РАСХОДЫ")
    # Передаем начальные параметры для рендеринга шаблона
    return templates.TemplateResponse("tinkoff/expenses.html", {"request": request})

# Эндпоинт для получения расходов за выбранный период
@router.get("/tinkoff/expenses/")
async def get_expenses( 
    period: Optional[str] = Query("month"),  # Необязательный период
    rangeStart: Optional[str] = None,  # Необязательное начало периода
    rangeEnd: Optional[str] = None  # Необязательный конец периода
):
    if not await  browser.is_browser_active() or not await  browser.is_page_active():
        raise HTTPException(status_code=307, detail="Сессия истекла. Перенаправление на основную страницу.")
    else:
        browser.reset_interaction_time()
    
    page = browser.page

    if await expenses_redirect(page, period, rangeStart, rangeEnd):  # Перенаправление на страницу по соответствующему периоду
        time.sleep(1)  # Если было перенаправление, то небольшое ожидание

    start_time = time.time()  # Засекаем время, начиная с которого надо искать csv
    await download_csv_from_expenses_page(page)  # Качаем csv

    # Ждём появления нового CSV-файла
    file_path = await wait_for_new_download(start_time=start_time)

    # Получаем словарь с категориями из бд
    categories_dict = await get_expense_categories_with_description()

    return await get_json_expense_from_csv(file_path, categories_dict)
    

# Эндпоинт для получения всех категорий
@router.get("/tinkoff/expenses/categories/")
async def get_categories():
    return [{"id": cat_id, "category_name": name} for cat_id, name in categories_db.items()]


# Эндпоинт для добавления категорий
@router.post("/tinkoff/expenses/categories/")
async def add_categories(request: CategoryRequest):
    start_id = max(categories_db.keys()) + 1 if categories_db else 1
    for category in request.categories:
        categories_db[start_id] = category
        start_id += 1
    return {"message": "Категории добавлены"}


# Эндпоинт для удаления категорий
@router.delete("/tinkoff/expenses/categories/")
async def delete_category(request: DeleteCategoryRequest):
    for cat_id in request.ids:
        categories_db.pop(cat_id, None)
        keywords_db = {k: v for k, v in keywords_db.items() if v != cat_id}  # Удаляем связанные ключевые слова
    return {"message": "Категории удалены"}


# Эндпоинт для сохранения ключевых слов
@router.post("/tinkoff/expenses/keywords/")
async def save_keywords(request: KeywordsUpdateRequest):
    for item in request.keywords:
        description = item.get("description")
        category_id = item.get("category_id")
        if not description or category_id not in categories_db:
            raise HTTPException(status_code=400, detail="Некорректные данные")
        keywords_db[description] = category_id  # Обновляем или добавляем
    return {"message": "Ключевые слова сохранены"}