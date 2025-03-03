# routes/general.py

# Сторонние модули
from fastapi import APIRouter

# Собственные модули
from routes.auth_tinkoff import get_browser


router = APIRouter()


# Пользователь перешел на другую страницу
@router.post("/tinkoff/disconnect/")
async def disconnect():
    print("Пользователь покинул страницу. Закрываем context.")
    browser = get_browser()
    if browser:
        await browser.close_browser()
    return {"message": "Браузер закрыт"}