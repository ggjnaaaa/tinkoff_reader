# driver_setup.py

# Стандартные библиотеки Python
import os, asyncio, shutil, json

# Playwright для работы с браузером
from playwright.async_api import async_playwright

# Собственные модули
import tinkoff.config as config

# Глобальная переменная для хранения времени последнего взаимодействия
last_interaction_time = asyncio.get_event_loop().time()

# Функция создания и настройки Playwright-браузера
async def create_browser_context():
    path_to_chrome_profile = config.PATH_TO_CHROME_PROFILE
    timeout = config.BROWSER_TIMEOUT
    
    # Проверка, существует ли файл состояния
    storage_state_file = os.path.join(path_to_chrome_profile, "storage_state.json")
    
    # Если файл не существует, создаем пустой
    if not os.path.exists(storage_state_file):
        with open(storage_state_file, 'w') as f:
            json.dump({}, f)  # Создаем пустой JSON
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=False,
        args=["--start-maximized", 
            '--disable-blink-features=AutomationControlled']
    )
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        storage_state=storage_state_file,
        permissions=["notifications"]
    )
    page = await context.new_page()

    config.browser = browser
    config.context = context
    config.page = page

    asyncio.create_task(close_browser_after_timeout(context, timeout))
        
    return page

# Функция для закрытия контекста (аналог Selenium driver.quit())
async def close_context():
    try:
        if config.context:
            path_to_chrome_profile = config.PATH_TO_CHROME_PROFILE
            storage_state_file = os.path.join(path_to_chrome_profile, "storage_state.json")

            # Сохраняем текущее состояние браузера перед закрытием
            await config.context.storage_state(path=storage_state_file)

            # Закрываем драйвер
            await config.context.close()
            config.context = None
            config.page = None
    except Exception as e:
        print(f"Ошибка при закрытии контекста: {str(e)}")

async def is_browser_active():
    try:
        # Проверка активности браузера
        if not config.page:
            return False
        await config.page.title()  # Получаем заголовок страницы для проверки
        return True
    except Exception:
        return False

# Функция для сброса времени последнего взаимодействия
def reset_interaction_time():
    global last_interaction_time
    last_interaction_time = asyncio.get_event_loop().time()

# Остановка отслеживания взаимодействий
def stop_interaction_time():
    global last_interaction_time
    last_interaction_time = None

# Функция для закрытия браузера после тайм-аута
async def close_browser_after_timeout(context, timeout):
    global last_interaction_time
    while True:
        await asyncio.sleep(5)
        if asyncio.get_event_loop().time() - last_interaction_time > timeout:
            print("Время ожидания истекло, закрываю браузер...")
            await close_context()
            await clearing_downloads_directory()
            break

# Очистка всей директории с загрузками
async def clearing_downloads_directory():
    folder = config.DOWNLOAD_DIRECTORY
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Ошибка при очистке файла {file_path}: {str(e)}")
