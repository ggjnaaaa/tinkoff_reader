# general.py

# Сторонние библиотеки
from fastapi import APIRouter

# Собственные модули
from utils.tinkoff.driver_setup import stop_interaction_time
import tinkoff.config as config

router = APIRouter()

# Пользователь перешел на другую страницу
@router.post("/tinkoff/disconnect/")
async def disconnect():
    print("Пользователь покинул страницу. Закрываем браузер.")
    stop_interaction_time()
    return {"message": "Браузер закрыт"}