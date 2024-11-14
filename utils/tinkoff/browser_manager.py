# browser_manager.py

# Стандартные библиотеки Python
import asyncio, shutil, os, json

# Сторонние модули
from playwright.async_api import async_playwright

class BrowserManager:
    def __init__(self, path_to_profile, download_dir, timeout):
        """Инициализация BrowserManager с путем к профилю, папкой загрузок и таймаутом."""
        self.path_to_profile = path_to_profile
        self.download_dir = download_dir
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        self.last_interaction_time = None

    async def initialize_browser(self):
        """Инициализирует браузер, если он еще не запущен."""
        if self.browser is None:
            play = await async_playwright().start()
            self.browser = await play.chromium.launch(
                headless=True,
                args=["--start-maximized", '--disable-blink-features=AutomationControlled'],
                downloads_path = self.download_dir
            )
            print("Браузер запущен")

    async def create_context_and_page(self):
        """Создает контекст и страницу, если они не активны."""
        await self.initialize_browser()
        if self.context is None:
            # Создаем и сохраняем пустой JSON состояния, если его нет
            storage_state_file = os.path.join(self.path_to_profile, "storage_state.json")
            if not os.path.exists(storage_state_file):
                with open(storage_state_file, 'w') as f:
                    json.dump({}, f)
            
            # Создаем контекст
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
                storage_state=storage_state_file,
                accept_downloads=True,  # Включаем возможность загрузки
                permissions=["notifications"]
            )

            self.page = await self.context.new_page()
            print("Контекст и страница созданы")

        # Обновляем время последнего взаимодействия
        self.reset_interaction_time()
        asyncio.create_task(self.close_after_timeout())

    async def close_context_and_page(self):
        """Закрывает контекст и страницу, сохраняет состояние."""
        if self.context:
            await self.save_browser_cache()
            await self.context.close()
            self.context = None
            self.page = None
            print("Контекст и страница закрыты")

            await self.clearing_downloads_directory()
    
    async def save_browser_cache(self):
        if self.context:
            storage_state_file = os.path.join(self.path_to_profile, "storage_state.json")
            await self.context.storage_state(path=storage_state_file)

    def reset_interaction_time(self):
        """Сбрасывает таймер последнего взаимодействия."""
        self.last_interaction_time = asyncio.get_event_loop().time()

    async def close_after_timeout(self):
        """Закрывает контекст и страницу, если время ожидания превышено."""
        while True:
            await asyncio.sleep(5)
            if self.last_interaction_time and asyncio.get_event_loop().time() - self.last_interaction_time > self.timeout:
                await self.close_context_and_page()
                break

    async def clearing_downloads_directory(self):
        """Очищает директорию загрузок."""
        for filename in os.listdir(self.download_dir):
            file_path = os.path.join(self.download_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Ошибка при очистке файла {file_path}: {str(e)}")

    async def is_browser_active(self):
        """Проверяет, подключен ли браузер и активен ли он."""
        return self.browser and self.browser.is_connected()
    
    async def is_page_active(self):
        """Проверяет, работает ли страница."""
        try:
            if not self.page:
                return False
            title = await self.page.title()  # Попытка получить заголовок страницы
            return True
        except Exception as e:
            return False

    async def close_browser(self):
        """Закрывает браузер и освобождает ресурсы."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            print("Браузер закрыт")
