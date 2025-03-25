# utils/tinkoff/expenses_google_sheets.py

import locale
import re
import logging

from pytz import timezone
from datetime import datetime
import gspread

from routes.directory.tinkoff.expenses import get_expenses_from_db
from utils.tinkoff.time_utils import get_period_range

from config import GOOGLE_SHEETS_URL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

moscow_tz = timezone('Europe/Moscow')
locale.setlocale(locale.LC_TIME, "ru_RU.utf8")  # Устанавливаем русскую локаль

try:
    gc = gspread.service_account(filename="credentials.json")
    sht2 = gc.open_by_url(GOOGLE_SHEETS_URL)
    worksheet = sht2.get_worksheet(0)
except Exception as e:
    logger.error(f"Ошибка при инициализации gspread: {str(e)}")

MONTHS_NOMINATIVE = {
    "января": "ЯНВАРЬ", "февраля": "ФЕВРАЛЬ", "марта": "МАРТ",
    "апреля": "АПРЕЛЬ", "мая": "МАЙ", "июня": "ИЮНЬ",
    "июля": "ИЮЛЬ", "августа": "АВГУСТ", "сентября": "СЕНТЯБРЬ",
    "октября": "ОКТЯБРЬ", "ноября": "НОЯБРЬ", "декабря": "ДЕКАБРЬ"
}


def sync_expenses_to_sheet_no_id(db, period="3month", timezone_str="Europe/Moscow"):
    """
    Синхронизация расходов из базы данных в Google Sheets. ВЕРСИЯ БЕЗ АЙДИШНИКОВ.
    Теперь поддерживает:
    - Группировку по датам
    - Дополнительные столбцы (Статья, Уточнение, Комментарий)
    - Учёт оплат задним числом
    - Вывод месяца при его смене
    - Вывод числа и месяца при смене дня
    - Закрашивание строк с датами
    """

    # Получаем расходы за нужный период
    unix_range_start, unix_range_end = get_period_range(timezone=timezone_str, period=period)

    expenses_data = get_expenses_from_db(
        db=db,
        unix_range_start=unix_range_start,
        unix_range_end=unix_range_end,
        timezone_str=timezone_str,
        sort_order='asc'
    )

    # Получаем текущие данные
    existing_rows = worksheet.get_all_values()

    last_month = None
    last_date = None
    if (existing_rows and len(existing_rows) > 0 and len(existing_rows[0]) > 0):
        # Вычисляем последний месяц и дату
        last_month, last_date = get_last_month_and_date([row[0] for row in existing_rows]) 

    # Формируем данные для добавления
    expenses_to_add = get_expenses_to_add(preprocess_existing_expenses(existing_rows), expenses_data, last_date)

    update_existing_categories(db, existing_rows, timezone_str)

    if not expenses_to_add:
        logger.info("Нет новых расходов для добавления.")
        return

    # Группируем по дате
    expenses_to_add.sort(key=lambda x: datetime.strptime(x[0], "%d %B %Y"))


    updates = get_updates_to_table(existing_rows, expenses_to_add, last_month, last_date)

    # Выполняем пакетное обновление
    worksheet.batch_update(updates, value_input_option="USER_ENTERED")
    

    logger.info("Синхронизация завершена.")


def get_last_month_and_date(existing_rows):
    """
    Функция для извлечения последнего месяца и последней даты из строк таблицы,
    начиная с конца.

    :param existing_rows: Список строк таблицы (переданный через worksheet.get_all_values()).
    :return: Кортеж (last_month, last_date) или (None, None), если не найдено.
    """
    # Отфильтровываем пустые строки
    existing_rows = [row for row in existing_rows if row and len(row) > 0]

    last_date = None
    last_month = None

    # Проходим с конца
    for row in reversed(existing_rows):
        if row in MONTHS_NOMINATIVE.values():  # Если это месяц
            last_month = row
        elif is_date_string(row) and not last_date:  # Если это дата
            last_date = row
        if last_date and last_month:
            return last_month, last_date  # Как только нашли, возвращаем

    # Если ничего не нашли, возвращаем None
    return None, None


def is_date_string(date_str):
    """
    Проверяет, является ли строка датой в формате '1 мая' или '01 мая'.

    :param date_str: Строка для проверки.
    :return: True, если строка является датой, иначе False.
    """
    # Регулярное выражение для даты вида '1 мая' или '01 мая'
    date_pattern = r"^(0?\d{1,2})\s{1,5}(" + "|".join(MONTHS_NOMINATIVE.keys()) + r")$"

    # Проверяем, соответствует ли строка регулярному выражению
    return bool(re.match(date_pattern, date_str))


def preprocess_existing_expenses(existing_rows):
    """
    Создаёт копию последних 200 строк и заполняет столбец с датами.
    """
    processed_expenses = {}
    current_date = None  # Последняя найденная дата

    for row in existing_rows:
        if not row or len(row) < 9:  # Пропускаем пустые или слишком короткие строки
            continue

        first_cell = row[0].strip()  # Проверяем первый столбец

        if is_date_string(first_cell):  # Если это дата
            current_date = first_cell  # Обновляем текущую дату
            year = datetime.now().year  # Подставляем текущий год
            current_date = f"{current_date} {year}"
        elif current_date and not first_cell:  # Если в первой ячейке что-то есть, но это не дата
            expense_id = row[8].strip()  # Столбец I содержит ID
            if expense_id:  # Если ID существует
                cleaned_amount = row[2].replace('\xa0', '')  # Убираем неразрывные пробелы
                processed_expenses[expense_id] = (
                    current_date,  # Дата
                    row[1],        # Номер карты
                    cleaned_amount,  # Сумма
                    row[3],       # Описание
                    row[5] if len(row) > 5 else "",  # Категория
                )
        
        if row[3] == "Пополнение Кубышки":
            pass

    return processed_expenses  # Возвращаем множество для быстрого поиска


def get_expenses_to_add(existing_expenses, expenses_data, last_date):
    expenses_to_add = []

    last_date_obj = None
    if last_date:
        try:
            # Добавляем текущий год к last_date (формат "20  марта")
            current_year = datetime.now().year
            last_date_str = f"{last_date} {current_year}"
            last_date_obj = datetime.strptime(last_date_str, "%d  %B %Y")
        except ValueError as e:
            logger.error(f"Ошибка парсинга last_date: {e}")

    for expense in expenses_data["expenses"]:
        expense_id  = expense.get('id')
        if str(expense_id)  in existing_expenses:
            continue

        date_time = datetime.strptime(expense["date_time"], "%d.%m.%Y %H:%M:%S")
        date_time_str = date_time.strftime("%d  %B %Y")
        

        if last_date_obj and date_time < last_date_obj:
            continue

        card_number = expense["card_number"]
        amount = "{:.2f}".format(expense["amount"]).replace('.', ',')
        description = expense["description"]
        category = expense["category"]
        article = expense.get("article", "")
        detail = expense.get("detail", "")
        comment = expense.get("comment", "")

        expenses_to_add.append([date_time_str, card_number, amount, description, article, category, detail, comment, expense_id])

    return expenses_to_add


def update_existing_categories(db, existing_rows, timezone_str):
    """
    Обновляет категории в существующих строках на основе переданных keywords.
    """
    unix_range_start, unix_range_end = get_period_range(timezone=timezone_str, period="3month")
    db_expenses = get_expenses_from_db(
        db=db,
        unix_range_start=unix_range_start,
        unix_range_end=unix_range_end,
        sort_order='asc'
    )["expenses"]

    db_categories = {
        str(expense["id"]): expense["category"] 
        for expense in db_expenses
        if expense.get("id") and expense.get("category")
    }

    updates = []
    
    for row_num, row in enumerate(existing_rows[1:], start=2):  # Пропускаем заголовок
        if len(row) < 9 or not row[8]:
            continue

        expense_id = row[8].strip()
        sheet_category = row[5] if len(row) > 5 else "" 
        db_category = db_categories.get(expense_id) if not db_categories.get(expense_id) == "Не указана" else ""

        # Если категория в БД существует и отличается от той, что в таблице
        if deep_clean_string(db_category) != deep_clean_string(sheet_category):
            updates.append({
                "range": f"F{row_num}",
                "values": [[db_category]]
            })

    if updates:
        try:
            worksheet.batch_update(updates, value_input_option="USER_ENTERED")
            logger.info(f"Обновлено {len(updates)} категорий в Google Sheets")
        except Exception as e:
            logger.error(f"Ошибка при обновлении категорий: {str(e)}")
    else:
        logger.info("Не найдено расхождений в категориях между БД и Google Sheets")


def deep_clean_string(s):
    """Удаляет ВСЕ непечатаемые символы"""
    if not s:
        return s
    cleaned = ''.join(char for char in str(s) if char.isprintable() or char.isspace())
    return ' '.join(cleaned.split())


def get_updates_to_table(existing_rows, expenses_to_add, last_month, last_date):
    row_index = len(existing_rows) + 1  # Начальный индекс строки (без заголовка)
    updates = []

    for expense in expenses_to_add:
        date = datetime.strptime(expense[0], "%d %B %Y")  # Берём только дату без времени
        day = date.strftime("%d  %B")
        month = date.strftime("%B")
        date = date.strftime("%d.%m.%Y")
        month = MONTHS_NOMINATIVE[month]

        # Если месяц изменился — записываем его
        if month != last_month:
            updates.append({"range": f"A{row_index}:H{row_index}", "values": [[month] + [""]*7]})
            row_index += 1
            last_month = month

        # Если день изменился — записываем "02 февраля"
        if day != last_date:
            updates.append({"range": f"A{row_index}:H{row_index}", "values": [[date] + [""]*7]})
            row_index += 1
            last_date = day

        # Формируем список обновлений
        updates += [
            {"range": f"B{row_index}", "values": [[expense[1]]]},  # Карта
            {"range": f"C{row_index}", "values": [[expense[2]]]},  # Сумма
            {"range": f"D{row_index}", "values": [[expense[3]]]},  # Описание
            {"range": f"I{row_index}", "values": [[expense[8]]]},  # id
        ]

        if expense[5] != "Не указана":
            updates.append({"range": f"F{row_index}", "values": [[expense[5]]]})


        row_index += 1
    
    return updates