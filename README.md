## Сторонние библиотеки:
pip install pytest-playwright  
pip install uvicorn  
pip install fastapi  
pip install jinja2  
pip install aiofiles  
pip install pytz  
pip install fuzzywuzzy (+pip install python-Levenshtein, если вылезает предупреждение UserWarning при запуске сервера)  
pip install python-jose  
pip install passlib  
pip install gspread gspread-formatting  
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2  


```playwright install chromium``` (чтобы установить драйвер для playwright, выполнить 1 раз)

## Как пользоваться:
1. Устанавливаем все библиотеки + драйвер (выполнить все команды выше)
2. Заполняем поля в config.py (помечены стрелками) и создаём соответствующие директории:
    * PATH_TO_CHROME_PROFILE - директория с кэшем хрома
    * DOWNLOAD_DIRECTORY - директория с загрузками (программно очищается)

    \*директории можно создать в корне проекта и назвать chrome_data и downloads, поскольку занесены в .gitignore
3. Заполняем файл credentials.json (нужен для работы с гугл таблицами)
4. В корне проекта выполняем ```uvicorn main:app --reload --port 8000```
5. Заходим в браузер на 127.0.0.1:8000
6. Чтобы вкл/выкл отображение окна в функции initialize_browser (в файле /utils/tinkoff/browser_manager.py) в строчке ```headless=True``` пишем ```True``` - для отображения окна, ```False``` - для скрытия окна

## Создание таблиц в PostgreSQL:
```SQL
-- Таблица "Расходы" с датой, номером карты, суммой, описанием и категорией
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL, -- Время в Unix-формате
    card_number VARCHAR(10), -- В формате "*1234"
    amount DECIMAL(10, 2) NOT NULL, -- Сумма операции
    description TEXT,
    category_id INTEGER REFERENCES category_expenses(id)
);

-- Таблица "Категории" с ID и названием
CREATE TABLE IF NOT EXISTS category_expenses (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    color TEXT
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

-- Таблица рассылки уведомлений 
CREATE TABLE user_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receive_error_notifications BOOLEAN DEFAULT FALSE,  -- Кому отправлять ошибки
    receive_transfer_notifications BOOLEAN DEFAULT FALSE,  -- Кому отправлять все расходы
    UNIQUE (user_id)
);

-- Таблица для фиксации изменения времени выгрузки
CREATE TABLE tinkoff_schedule (
    id SERIAL PRIMARY KEY,
    export_type TEXT CHECK (export_type IN ('expenses', 'full')) NOT NULL, -- тип выгрузки
    export_time TIME NOT NULL, -- время выполнения
    created_at TIMESTAMP DEFAULT now()
);
```

## История изменений (начиная с новых)

### 20.03.25
Изменено:
1. Исправлен баг с категориями (сбрасывались при переходе между страницами пагинациями)


### 15.03.25
Изменено:
1. Сделан кастомный селектор, учитывающий цвета категорий:
<p align="center">
  <img src="./result_imgs/selector/new_selector_color" alt="Новый селектор с цветами" width="150"/>
  <br>
  <i>Новый селектор с цветами. Идет вниз с ограничением</i>
</p>

<p align="center">
  <img src="./result_imgs/selector/new_selector_color_selected" alt="Новый селектор с цветами" width="150"/>
  <br>
  <i>Новый селектор с цветами. Идет вверх без ограничений</i>
</p>

2. Если у категорий нет цветов, то будут отображаться простым белым списком:
<p align="center">
  <img src="./result_imgs/selector/new_selector_no_color" alt="Новый селектор без цветов" width="150"/>
  <br>
  <i>Новый селектор без цветов</i>
</p>

<p align="center">
  <img src="./result_imgs/selector/new_selector_no_color_selected" alt="Новый селектор без цветов" width="150"/>
  <br>
  <i>Новый селектор без цветов. Выделенный</i>
</p>

Чтобы обновить бд под цвета (логики изменения цвета пока нет):
```
ALTER TABLE category_expenses ADD COLUMN color TEXT;
```

3. Обновлена логика работы с категориями, теперь категория добавляется не по описанию
расхода, а по id (теперь одна категория не будет автоматически привязываться к расходам
с одинаковым описанием). Чтобы обновить бд под новую логику:
```
ALTER TABLE expenses ADD COLUMN category_id INTEGER REFERENCES category_expenses(id);
DROP TABLE category_expenses_keywords;
```


### 05.03.25
Добавлено:  
Миниапп закрывается после сохранения изменений.

Изменено:  
1. Исправлена выгрузка расходов в миниаппе.
2. Бот теперь загружает расходы по всем картам по умолчанию.


### 03.03.25
Добавлено:
1. Кнопка в боковое меню, позволяющая выгрузить в гугл диск кэш браузера (нужен только файл
для апи гугла)
2. Если файла кэша нет в папке, то сначала попытка выгрузить с гугла, если его там не было,
то создаётся пустой

Изменено:  
Исправление мелких багов.


### 02.03.25
Изменено:
1. В боте теперь ресходы от раннего к позднему
2. Исправлен баг с выводом расходов в боте (не появлялся чекбокс "вывести расходы")


### 01.03.25
Добавлено:
1. Теперь пользователь может самостоятельно менять время выгрузки расходов
2. Есть 2 времени автовыгрузки:
    * в первое идет выгрузка в бд и рассылка сообщений пользователям
    * во второе повторная выгрузка в бд + в гугл таблицы
3. Добавлен промежуток "последние 26 часов", используется в автовыгрузке

Изменено:
1. При ошибке автовыгрузки учитывается время, когда пользователь вошел для 
повторной загрузки. Если время автовыгрузки прошло или до него осталось меньше 
пяти минут, то она происходит


### 25.02.25
Изменено:
* Добавлена новая таблица в бд, раньше вместо неё были 2 списка в конфиге  
    через таблицу user_notifications задаются:
    * те, кому можно смотреть все расходы (receive_transfer_notifications)
    * кому приходят ошибки автовыгрузки (receive_error_notifications)
* В боте добавлен чекбокс для пользователей с receive_transfer_notifications = true.
Когда чекбокс неактивен показываются только расходы по карте + переводы, 
иначе выводятся все расходы за день.


### 24.02.25
Изменено:
* Улучшен вывод расходов в гугл таблицу:
    * группировка по месяцам и числам
    * учитываются прошлые расходы
    * при определенных настройках таблицы можно добиться результатов как на скрине
    * данные вставляются одним запросом, что позволяет избежать превышение лимита обращений к апи таблиц

Задачи:
* Изучить возможности вставки данных в середину таблицы


### 21.02.25 (сводка по всем коммитам с 15.11.24)
Добавлено:
* Работа с ботом. В частности:
    * при автовыгрузке отправляется запрос к апи бота (в зависимости от результатов выгрузки)
    * если автовыгрузка завершилась неудачно, отправляется просьба о повторном входе пользователю с конкретной картой. В случае удачного входа автовыгрузка повторяется
    * если автовыгрузка завершилась удачно, всем держателям карт, по которым были списания сегодня, отправляются уведомления
    * страницы были адаптированы под бота (нет шапки сайта, таблица уменьшена, убраны лишние фильтры, нет пагинации)
* Расходы также выгружаются в гугл таблицу
* Исправлены ошибки (проблемы с выбором категорий и прочее)
* Изменен интерфейс сайта:
    * другая цветовая схема
    * тостовые уведомления появляются в столбик (раньше накладывались друг на друга)
    * для таблицы расходов добавлен горизонтальный скролл если она не помещается в экран (заметно в обычной версии на телефонах)
* Прочие мелкие изменения


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


### 15.10.24
Исправлено:
* приложение теперь не зависает


### 09.10.24
Добавлено:
* реагирование на различные виды входа
* обработка ошибок
* разделение приложения по файлам
* получение входной информации через .env файл, пример в .env.example
* сохранение сессий входа

Проблемы:
* приложение зависает примерно на 10 секунд при создании OTP перед вводом пароля