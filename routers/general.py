# general.py

# Сторонние библиотеки
from fastapi import APIRouter

# Собственные модули
from servises.driver_setup import stop_interaction_time

router = APIRouter()

# Пользователь перешел на другую страницу
@router.post("/tinkoff/disconnect/")
def disconnect():
    global driver
    print("Пользователь покинул страницу. Закрываем браузер.")
    stop_interaction_time()
    driver = None
    return {"message": "Браузер закрыт"}