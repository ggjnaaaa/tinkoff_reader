# main.py

# Сторонние библиотеки
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from threading import Thread

# Собственные модули
from routers import (
    auth_tinkoff,
    expenses,
    general,
    start,
    bot
)
from utils.tinkoff.fixed_time_import_expenses import start_scheduler
 
# FastAPI и роутер
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры к приложению
app.include_router(auth_tinkoff.router)
app.include_router(expenses.router)
app.include_router(general.router)
app.include_router(start.router)
app.include_router(bot.router)

# Запуск планировщика в отдельном потоке
scheduler_thread = Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()