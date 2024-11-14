# general.py

# Сторонние библиотеки
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

# Собственные модули
from routers.auth_tinkoff import get_browser

router = APIRouter()

# Пользователь перешел на другую страницу
@router.post("/tinkoff/disconnect/")
async def disconnect():
    print("Пользователь покинул страницу. Закрываем context.")
    browser = get_browser()
    if browser:
        await browser.close_browser()
    return {"message": "Браузер закрыт"}