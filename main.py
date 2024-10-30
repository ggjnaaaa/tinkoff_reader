# main.py

# Сторонние библиотеки
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Собственные модули
from routers import (
    auth_tinkoff,
    expenses,
    general,
    start
)
 
# FastAPI и роутер
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Разрешаем CORS для всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры к приложению
app.include_router(auth_tinkoff.router)
app.include_router(expenses.router)
app.include_router(general.router)
app.include_router(start.router)