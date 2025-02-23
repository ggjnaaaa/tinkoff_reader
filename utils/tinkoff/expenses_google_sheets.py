
import locale
import re

from pytz import timezone
from datetime import datetime
import gspread

from routers.directory.tinkoff_expenses import get_expenses_from_db
from utils.tinkoff.time_utils import get_period_range

from config import GOOGLE_SHEETS_URL


moscow_tz = timezone('Europe/Moscow')
locale.setlocale(locale.LC_TIME, "ru_RU.utf8")  # Устанавливаем русскую локаль

try:
    gc = gspread.service_account(filename="credentials.json")
    sht2 = gc.open_by_url(GOOGLE_SHEETS_URL)
    worksheet = sht2.get_worksheet(0)
except Exception as e:
    print(f"Ошибка при инициализации gspread: {str(e)}")

MONTHS_NOMINATIVE = {
    "января": "ЯНВАРЬ", "февраля": "ФЕВРАЛЬ", "марта": "МАРТ",
    "апреля": "АПРЕЛЬ", "мая": "МАЙ", "июня": "ИЮНЬ",
    "июля": "ИЮЛЬ", "августа": "АВГУСТ", "сентября": "СЕНТЯБРЬ",
    "октября": "ОКТЯБРЬ", "ноября": "НОЯБРЬ", "декабря": "ДЕКАБРЬ"
}


def sync_expenses_to_sheet_no_id(db, period="week", timezone_str="Europe/Moscow"):
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

    # Собираем существующие расходы, чтобы избежать дублирования
    existing_expenses = set()
    for row in existing_rows[1:]:  # Пропускаем заголовок
        if len(row) >= 4:  # Проверяем, что есть необходимые поля
            existing_expenses.add((row[0], row[1], row[2], row[3]))

    # Формируем данные для добавления
    expenses_to_add = get_expenses_to_add(preprocess_existing_expenses(existing_rows), expenses_data)

    if not expenses_to_add:
        print("Нет новых расходов для добавления.")
        return

    # Группируем по дате
    expenses_to_add.sort(key=lambda x: datetime.strptime(x[0], "%d %B %Y"))


    updates = get_updates_to_table(existing_rows, expenses_to_add, last_month, last_date)

    # Выполняем пакетное обновление
    worksheet.batch_update(updates, value_input_option="USER_ENTERED")
    

    print("Синхронизация завершена.")


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
    last_200_rows = existing_rows#[-200:]  # Берём последние 200 строк
    processed_expenses = []

    current_date = None  # Последняя найденная дата

    for row in last_200_rows:
        if not row or len(row) < 6:  # Пропускаем пустые или слишком короткие строки
            continue

        first_cell = row[0].strip()  # Проверяем первый столбец

        if is_date_string(first_cell):  # Если это дата
            current_date = first_cell  # Обновляем текущую дату
            year = datetime.now().year  # Подставляем текущий год
            current_date = f"{current_date} {year}"
        elif current_date and not first_cell:  # Если в первой ячейке что-то есть, но это не дата
            cleaned_amount = row[2].replace('\xa0', '')  # Убираем неразрывные пробелы
            processed_expenses.append((current_date, row[1], cleaned_amount, row[3]))
        
        if row[3] == "Пополнение Кубышки":
            pass

    return set(processed_expenses)  # Возвращаем множество для быстрого поиска


def get_expenses_to_add(existing_expenses, expenses_data):
    expenses_to_add = []

    for expense in expenses_data["expenses"]:
        date_time = datetime.strptime(expense["date_time"], "%d.%m.%Y %H:%M:%S").strftime("%d  %B %Y")

        card_number = expense["card_number"]
        amount = "{:.2f}".format(expense["amount"]).replace('.', ',')
        description = expense["description"]
        category = expense["category"]
        article = expense.get("article", "")
        detail = expense.get("detail", "")
        comment = expense.get("comment", "")

        # Проверяем, есть ли запись
        if (date_time, card_number, amount, description) not in existing_expenses:
            expenses_to_add.append([date_time, card_number, amount, description, article, category, detail, comment])

    return expenses_to_add



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
        ]

        if expense[5] != "Не указана":
            updates.append({"range": f"F{row_index}", "values": [[expense[5]]]})


        row_index += 1
    
    return updates