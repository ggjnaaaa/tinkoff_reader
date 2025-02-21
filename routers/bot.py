# bot.py

import time
import json

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from routers.directory.bot import check_user_and_store_tg_tmp_user, get_card_number_by_chat_id
from database import Session
from auth import verify_bot_token

from routers.directory.tinkoff_expenses import get_expenses_from_db

from utils.tinkoff.time_utils import get_period_range

from models import TokenizedUrlRequest, Users, TgTmpUsers


router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


@router.post("/bot/check_access/")
async def check_access(request: TokenizedUrlRequest, db: Session = Depends(get_db)):
    """
    Проверяет токенизированный доступ и записывает данные в tg_tmp_users.
    """
    try:
        # Проверяем токен
        user_data = verify_bot_token(request.token)

        # Получаем данные пользователя
        tg_nickname = user_data.get("username")
        chat_id = int(user_data.get("chat_id"))

        if not tg_nickname or not chat_id:
            raise HTTPException(status_code=400, detail="Неполные данные в токене.")

        # Проводим проверку пользователя и сохраняем данные
        user, message = check_user_and_store_tg_tmp_user(db, tg_nickname, chat_id)
        if not user:
            raise HTTPException(status_code=403, detail=message)

        return {"detail": message}

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))