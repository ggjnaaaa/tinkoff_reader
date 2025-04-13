# main.py

# Сторонние библиотеки
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from threading import Thread

# Собственные модули
from routes import (
    auth_tinkoff,
    general,
    start,
    bot,
    expenses,
    scheduler,
    browser_session
)

from utils.tinkoff.scheduler_utils import start_scheduler
from utils.tinkoff.sync_google_category import start_inactivity_scheduler
 
# FastAPI и роутер
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры к приложению
app.include_router(auth_tinkoff.router)
app.include_router(expenses.router)
app.include_router(general.router)
app.include_router(start.router)
app.include_router(bot.router)
app.include_router(scheduler.router)
app.include_router(browser_session.router)

# Запуск планировщика в отдельном потоке
Thread(target=start_scheduler, daemon=True).start()
Thread(target=start_inactivity_scheduler, daemon=True).start()


