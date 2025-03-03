# routes/tinkoff/browser_session.py

# Стандартные модули Python
import os

# Сторонние модули
from fastapi import APIRouter, HTTPException, Body, Request, Query, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

# Собственные модули
import config as config

from routes.auth_tinkoff import check_for_browser, get_browser

from dependencies import get_authenticated_user

from utils.google_drive_file_utils import upload_file


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post('/tinkoff/reset_session/')
async def reset_session(user: dict = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse):
        print("пользователь не аутентифицирован")#return user  # Если пользователь не аутентифицирован

    browser = get_browser()
    if await check_for_browser(browser):
        await browser.close_browser()

    file_path = config.PATH_TO_CHROME_PROFILE + "/storage_state.json"
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "success", "message": "Сессия сброшена."}
        else:
            return {"status": "error", "message": "Файл не найден, сессия уже сброшена."}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка при удалении файла: {e}"}


@router.post('/tinkoff/save_session/')
async def save_session_to_google(user: dict = Depends(get_authenticated_user)):
    if isinstance(user, RedirectResponse):
        print("пользователь не аутентифицирован")#return user  # Если пользователь не аутентифицирован
    
    try:
        upload_file(config.PATH_TO_CHROME_PROFILE + "/storage_state.json")
        return {"status": "success", "message": "Файл успешно выгружен."}
    except Exception as e:
        print(f"Произошла ошибка при выгрузке файла в гугл диск: {e}")
        return {"status": "error", "message": "Произошла ошибка при выгрузке файла."}
    
    