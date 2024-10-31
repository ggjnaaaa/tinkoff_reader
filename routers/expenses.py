# expenses.py

# Библиотеки Python
import time
import csv
import os

# Сторонние библиотеки
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from selenium.webdriver.common.by import By
from typing import List, Optional
from fastapi.templating import Jinja2Templates

# Собственные модули
import tinkoff.config as config
from servises.driver_setup import is_browser_active
from servises.browser_utils import click_button, detect_page_type, PageType
from servises.general_utils import wait_for_new_download, expenses_redirect_by_period
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
    
    # Открываем страницу расходов в зависимости от периода
    if rangeStart and rangeEnd:
        config.driver.get(f'https://www.tbank.ru/events/feed/?rangeStart={rangeStart}&rangeEnd={rangeEnd}&preset=calendar')
    else:
        expenses_redirect_by_period(period)

    time.sleep(1)
    if detect_page_type(config.driver) != PageType.EXPENSES:
        raise HTTPException(status_code=307, detail="Сессия истекла. Перенаправление на основную страницу.")

    tmp_driver = config.driver
    start_time = time.time()

    click_button(tmp_driver, '[data-qa-id="export"]', timeout=5)
    click_button(tmp_driver, '//span[text()="Выгрузить все операции в CSV"]', By.XPATH, timeout=5)

    total_income = 0.0
    total_expense = 0.0
    categorized_expenses = []

    # Ждём появления нового CSV-файла
    file_path = wait_for_new_download(start_time=start_time)

    # Читаем данные из файла
    with open(file_path, mode='r', encoding='windows-1251') as file:
        reader = csv.DictReader(file, delimiter=';')

        for row in reader:
            amount = float(row["Сумма операции"].replace(",", "."))
            description = row["Описание"]
            category = row["Категория"]
            card = row["Номер карты"]
            datetime_operation = row["Дата операции"]

            # Определяем тип операции
            if category == "Переводы" or "между счетами" in description:
                transaction_type = "нейтральный"
            elif amount > 0:
                transaction_type = "доход"
                total_income += amount
            else:
                transaction_type = "расход"
                total_expense += abs(amount)

            '''# Получаем или добавляем статью в БД
            expense_category = expense_categories_db.get(description, "Не определено")
            if expense_category == "Не определено":
                # Логика для добавления статьи и шаблона в БД
                expense_category = add_expense_category(description)'''

            # Добавляем операцию в результат
            categorized_expenses.append({
                "date_time": datetime_operation,
                "card_number": card,
                "transaction_type": transaction_type,
                "amount": abs(amount),
                "description": description,
                "category": 'не готово'#expense_category
            })

    # Удаляем скачанный файл после обработки
    os.remove(file_path)

    # Итоговый результат
    result = {
        "total_income": total_income,
        "total_expense": total_expense,
        "expenses": categorized_expenses
    }

    return result

# Эндпоинт для получения категорий
@router.get("/tinkoff/expenses/categories/")
def get_categories():
    categories = []
    for i in range(5):
        categories.append({
            "id": i,
            "category_name": f"category{i+1}"
        })
    return categories

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