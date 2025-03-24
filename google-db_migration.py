# Перенос айдишников из бд в гугл таблицы и категорий из гугл таблицы в бд

import gspread
from datetime import datetime

from routes.directory.tinkoff.expenses import get_expenses_from_db
from routes.directory.tinkoff.categories import get_categories_from_db, update_expense_category
from utils.tinkoff.time_utils import get_period_range

from utils.tinkoff.expenses_google_sheets import is_date_string

from database import Session

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def get_all_expenses_from_db(db, timezone_str="Europe/Moscow"):
    """Получает все данные из базы данных."""
    try:
        unix_range_start, unix_range_end = get_period_range(timezone=timezone_str, period="year")
        expenses_data = get_expenses_from_db(
            db=db,
            unix_range_start=unix_range_start,
            unix_range_end=unix_range_end,
            timezone_str=timezone_str,
            sort_order='asc'
        )
        return expenses_data["expenses"]
    except Exception as e:
        print(f"Ошибка при извлечении данных из базы данных: {str(e)}")
        return []


def format_date_from_sheet(date_str):
    """Преобразует дату из Google Sheets в формат 'dd.mm.yyyy'."""
    try:
        date_obj = datetime.strptime(date_str, "%d  %B %Y")
        return date_obj.strftime("%d.%m.%Y")
    except Exception as e:
        print(f"Ошибка при преобразовании даты из Google Sheets: {str(e)}")
        return None


def format_date_from_db(date_str):
    """Преобразует дату из PostgreSQL в формат 'dd.mm.yyyy'."""
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        return date_obj.strftime("%d.%m.%Y")
    except Exception as e:
        print(f"Ошибка при преобразовании даты из PostgreSQL: {str(e)}")
        return None


def get_db_expenses_dict(db_expenses):
    db_expenses_dict = {}
    for expense in db_expenses:
        key = (
            format_date_from_db(expense["date_time"]),  # Приводим дату к формату 'dd.mm.yyyy'
            expense["card_number"],
            str(expense["amount"]),  # Приводим amount к строке для сравнения
            expense["description"]
        )

        # Если ключ уже существует, добавляем расход в список
        if key in db_expenses_dict:
            db_expenses_dict[key].append(expense)
        else:
            db_expenses_dict[key] = [expense]  # Создаем новый список с расходом

    return db_expenses_dict


def get_categories_dict(categories_list):
    """
    Создает словарь категорий, где ключ — название категории, а значение — её ID.
    """
    return {category["category_name"].strip(): category["id"] for category in categories_list}


def match_expenses(sheet_expenses, db_expenses, row_indices, categories):
    """
    Сопоставляет данные из Google Sheets и базы данных.
    Возвращает:
    - expenses_to_update_in_db: Список расходов для обновления в БД.
    - expenses_to_update_in_sheet: Список расходов для обновления в Google Sheets.
    """
    expenses_to_update_in_db = []
    expenses_to_update_in_sheet = []

    # Создаем словарь для быстрого поиска по уникальным ключам
    db_expenses_dict = get_db_expenses_dict(db_expenses)

    for sheet_expense in sheet_expenses:
        date, card_number, amount, description, category = sheet_expense
        key_to_db = (format_date_from_sheet(date), card_number, str(float(amount.replace(',', '.').replace('₽', ''))), description)
        key_to_sheets = (date, card_number, amount, description)

        if key_to_db in db_expenses_dict and key_to_sheets in row_indices:
            db_expense = db_expenses_dict[key_to_db].pop(0)
            row_index = row_indices[key_to_sheets]

            expenses_to_update_in_db.append({
                "expense_id": db_expense["id"],
                "category_id": categories.get(category.strip())
            })
            expenses_to_update_in_sheet.append({
                "row_index": row_index,
                "id": db_expense["id"]
            })

            # Если список расходов для этого ключа пуст, удаляем ключ
            if not db_expenses_dict[key_to_db]:
                del db_expenses_dict[key_to_db]

    return expenses_to_update_in_db, expenses_to_update_in_sheet


def update_db_with_categories(db, expenses_to_update_in_db):
    """Пакетно обновляет категории в базе данных."""
    try:
        for expense in expenses_to_update_in_db:
            update_expense_category(db, expense['expense_id'], expense['category_id'])
        print(f"Обновлено {len(expenses_to_update_in_db)} записей в базе данных.")
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {str(e)}")


def update_sheet_with_ids(expenses_to_update_in_sheet):
    """Пакетно обновляет Google Sheets с ID из базы данных."""
    try:
        updates = []
        for expense in expenses_to_update_in_sheet:
            updates.append({
                "range": f"I{expense['row_index']}",
                "values": [[expense["id"]]]
            })

        if updates:
            worksheet.batch_update(updates, value_input_option="USER_ENTERED")
            print(f"Обновлено {len(updates)} записей в Google Sheets.")
    except Exception as e:
        print(f"Ошибка при обновлении Google Sheets: {str(e)}")


def sync_expenses_with_id(db, period="week", timezone_str="Europe/Moscow"):
    """
    Синхронизация расходов с добавлением ID и категорий.
    Минимизирует количество запросов к БД и Google Sheets.
    """
    # Загружаем все данные из Google Sheets и БД
    existing_rows = worksheet.get_all_values()
    
    sheet_expenses, row_indices = preprocess_existing_expenses(existing_rows)
    db_expenses = get_all_expenses_from_db(db, timezone_str)
    db_categories = get_categories_dict(get_categories_from_db(db))

    # Сопоставляем данные в памяти
    expenses_to_update_in_db, expenses_to_update_in_sheet = match_expenses(sheet_expenses, db_expenses, row_indices, db_categories)

    # Пакетно обновляем БД и Google Sheets
    update_db_with_categories(db, expenses_to_update_in_db)
    update_sheet_with_ids(expenses_to_update_in_sheet)

    print("Синхронизация с ID и категориями завершена.")


def preprocess_existing_expenses(existing_rows):
    """
    Создаёт копию последних 200 строк и заполняет столбец с датами.
    """
    last_200_rows = existing_rows#[-200:]  # Берём последние 200 строк
    processed_expenses = []
    row_indices = {}

    current_date = None  # Последняя найденная дата

    for idx, row in enumerate(last_200_rows, start=1):
        if not row or len(row) < 6:  # Пропускаем пустые или слишком короткие строки
            continue

        first_cell = row[0].strip()  # Проверяем первый столбец

        if is_date_string(first_cell):  # Если это дата
            current_date = f"{first_cell} {datetime.now().year}"
        elif current_date and not first_cell:  # Если в первой ячейке что-то есть, но это не дата
            cleaned_amount = row[2].replace('\xa0', '')  # Убираем неразрывные пробелы
            key = (current_date, row[1], cleaned_amount, row[3])
            processed_expenses.append((current_date, row[1], cleaned_amount, row[3], row[5]))
            row_indices[key] = idx
        
        if row[3] == "Пополнение Кубышки":
            pass

    return processed_expenses, row_indices


def start():
    with Session() as db:
        sync_expenses_with_id(db)

if __name__ == '__main__':
    try:
        gc = gspread.service_account(filename="credentials.json")
        sht2 = gc.open_by_url("https://docs.google.com/spreadsheets/d/1-Y9Gg6bf9c6j8PhLEqSgjtFAXuX4uE9S1k00eNwMjrM/edit?usp=sharing")
        worksheet = sht2.get_worksheet(0)
        start()
    except Exception as e:
        print(f"Ошибка при инициализации gspread: {str(e)}")