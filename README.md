### Сторонние библиотеки:
pip install pytest-playwright  
pip install uvicorn  
pip install fastapi  
pip install jinja2  
pip install aiofiles  
pip install pytz  
pip install fuzzywuzzy (+pip install python-Levenshtein, если вылезает предупреждение UserWarning при запуске сервера)  
pip install python-jose  
pip install passlib  


```playwright install chromium``` (чтобы установить драйвер для playwright, выполнить 1 раз)

### Как пользоваться:
1. Устанавливаем все библиотеки + драйвер (выполнить все команды выше)
2. Заполняем поля в config.py и создаём соответствующие директории:
    * PATH_TO_CHROME_PROFILE - директория с кэшем хрома
    * DOWNLOAD_DIRECTORY - директория с загрузками (программно очищается)

    \*директории можно создать в корне проекта и назвать chrome_data и downloads, поскольку занесены в .gitignore
3. В корне проекта выполняем ```uvicorn main:app --reload --port 8000```
4. Заходим в браузер на 127.0.0.1:8000
5. Чтобы вкл/выкл отображение окна в функции initialize_browser (в файле /utils/tinkoff/browser_manager.py) в строчке ```headless=True``` пишем ```True``` - для отображения окна, ```False``` - для скрытия окна

Создание таблиц в PostgreSQL:
```SQL
-- Таблица "Расходы" с датой, номером карты, суммой, описанием и категорией
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL, -- Время в Unix-формате
    card_number VARCHAR(10), -- В формате "*1234"
    amount DECIMAL(10, 2) NOT NULL, -- Сумма операции
    description TEXT
);

-- Таблица "Ключевые слова" для хранения ID статьи и ключевых фраз
CREATE TABLE IF NOT EXISTS category_expenses_keywords (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES category_expenses(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL UNIQUE -- Ключевые слова должны быть уникальными по всей таблице
);

-- Таблица "Категории" с ID и названием
CREATE TABLE IF NOT EXISTS category_expenses (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL
);

-- Таблица "Временный код"
CREATE TABLE temporary_code (
    id SERIAL PRIMARY KEY,
    code CHAR(4) NOT NULL
);

-- Таблица "Последняя ошибка"
CREATE TABLE last_error (
    id SERIAL PRIMARY KEY,
    error_text TEXT NOT NULL,
    error_time TIMESTAMP DEFAULT NOW(),
    is_received BOOLEAN DEFAULT FALSE
);
```

### 09.10.24
Добавлено:
* реагирование на различные виды входа
* обработка ошибок
* разделение приложения по файлам
* получение входной информации через .env файл, пример в .env.example
* сохранение сессий входа

Проблемы:
* приложение зависает примерно на 10 секунд при создании OTP перед вводом пароля

### 15.10.24
Исправлено:
* приложение теперь не зависает

### 24.10.24
Добавлено:
* Приложение работает на фастапи
* Есть отдельная папка (HTML-Example) с примером использования

Проблемы:
* ~~Долгий сбор расходов и незавершенная таблица~~
* ~~Некорректный расчет общей суммы доходов если были переводы между счетами~~
* ~~Долгое определение типа страницы~~
* ~~Пароль не стирается в браузере селениума при неверном вводе~~
* Работа приложения не изолирована для конкретного пользователя
* Есть много мест где надо лучше обработать ошибки
* Оказалось что драйвер лучше заранее установить, иначе часто возникают проблемы при автоматической загрузке 

Нужно добавить:
* Работу с бд (запись отредактированных данных в бд и их извлечение)
* Исправить все проблемы

### 03.11.24
Добавлено:
* Взаимодействие с браузером переписано под playwright
* Добавлено взаимодействие между фронтом и бэком через jinja2
* Проект структурирован по папкам
* Наложены стили на страницы
* Селекторы лежат в конфиге

Исправленные проблемы:
* ~~Долгий сбор расходов и незавершенная таблица~~
* ~~Некорректный расчет общей суммы доходов если были переводы между счетами~~
* ~~Долгое определение типа страницы~~
* ~~Пароль не стирается в браузере селениума при неверном вводе~~
* Работа приложения будет изолирована на другом этапе
* Обработка ошибок всё ещё требует внимания
* Драйвер теперь устанавливается через команду ```playwright install chromium``` во время установки других зависимостей

Добавить/изменить:
* Переход с расходов на вход (например, если в браузере у тинькофф закончилась сессия, а пользователь выбирает новый период расходов, то нужно перевести его снова на вход)
* Убрать спам кнопок
* Доделать статьи + бд
* Проработать страницы:
    * при нажатии кнопки "отправить" она поднимается немного выше
    * расстояние между кнопками на расходах
    * список статье слишком узкий
    * при входе на страницу ввода смс видно кнопку повторной отправвки


### 15.11.24
Добавлено:
* Пути к папкам теперь прописываются в конфиге вместо .env
* Значок загрузки на страницах при обращении к серверу
* Убран спам кнопок с помощью объекта который появляется со значком загрузки
* Различные предупреждения
* Расходы, временный пароль, статьи, последняя ошибка (для автономного вытягивания расходов каждый день) грузятся в бд
* По умолчанию расходы выгружаются с бд
* Не нужен вход в тинькофф для выгрузки расходов
* Пагинация на странице расходов
* Статьи применяются автоматически по описанию
* Улучшен подсчет расходов
* Немного улучшен фронт

Задачи:
* Доработать фронт, адаптировать под компьютер, планшет, телефон
* Сделать автовыгрузку расходов в 21:00 МСК
* Код ревью


### 22.11.24
Добавлено:
* Улучшена обработка расходов
* Если после перезагрузки страницы расходов произошла ошибка, то 
* Автовыгрузка расходов в 21:00 МСК
* Улучшен выбор источника выбора источника расходов, теперь они выбираются с помощью радиокнопки
* Улучшен интерфейс, теперь на многих устройствах выглядит корректно
* Добавлены комментарии в код на бэке
* Слегка изменена логика на бэке
* При обновлении страницы она нормально прогружается заново



В рамках разработки модуля я использовала PostgreSQL для хранения данных, а обучалась на SQLite и MS SQL Server. Ниже приведены ключевые таблицы для хранения данных:
1. Таблица расходов (expenses):
Хранит данные о расходах, включая дату, номер карты, сумму и описание
Основные поля:
id (SERIAL, PRIMARY KEY) — id расхода
timestamp (BIGINT) — время операции в Unix-формате
card_number (VARCHAR) — номер карты
amount (DECIMAL(10, 2)) — сумма операции
description (TEXT) — описание операции
2. Таблица ключевых слов для категорий расходов (category_expenses_keywords):
Хранит ключевые слова, связанные с категориями расходов
Основные поля:
id (SERIAL, PRIMARY KEY) — id ключевого слова
category_id (INTEGER, FOREIGN KEY) — ссылка на категорию расходов (с внешним ключом на таблицу category_expenses)
keyword (VARCHAR(255)) — уникальное ключевое слово, связанное с категорией
3. Таблица категорий расходов (category_expenses):
Хранит категории расходов
Основные поля:
id (SERIAL, PRIMARY KEY) — id категории
title (TEXT) — название категории (например, "Еда", "Транспорт")
4. Таблица временного кода (temporary_code):
Хранит временные код для входа в аккаунт Тинькофф при автовыгрузке расходов
Основные поля:
id (SERIAL, PRIMARY KEY) — id кода
code (CHAR(4)) — временный код
5. Таблица последней ошибки (last_error):
Хранит информацию о последних ошибках, если они возникли в процессе автовыгрузке, при входе после возникновения, ошибка всплывает у пользователя
Основные поля:
id (SERIAL, PRIMARY KEY) — id ошибки
error_text (TEXT) — описание ошибки
error_time (TIMESTAMP) — время возникновения ошибки
is_received (BOOLEAN) — флаг, указывающий, была ли ошибка показана пользователю

