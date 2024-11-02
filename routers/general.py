# general.py

# Сторонние библиотеки
from fastapi import APIRouter

# Собственные модули
from tinkoff.config import browser_instance

router = APIRouter()

# Пользователь перешел на другую страницу
@router.post("/tinkoff/disconnect/")
async def disconnect():
    print("Пользователь покинул страницу. Закрываем context.")
    browser_instance.close_context_and_page()
    return {"message": "Браузер закрыт"}