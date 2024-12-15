# bot.py

import time
import json

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from routers.directory.bot import check_user_and_store_tg_tmp_user, get_card_number_by_chat_id
from database import Session
from auth import verify_token

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
        user_data = verify_token(request.token)

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


@router.get("/bot/expenses/")
async def get_bot_expenses(
    request: Request,
    token: str = Query(...),
    period: Optional[str] = None,
    rangeStart: Optional[str] = None,
    rangeEnd: Optional[str] = None,
    time_zone: str = Query("Europe/Moscow"),
    db: Session = Depends(get_db)
):
    """
    Эндпоинт для получения расходов из бота.
    """
    card_num = None
    try:
        # Проверяем токен и извлекаем данные
        user_data = verify_token(token)
        chat_id = int(user_data.get("chat_id"))
        auth_date = int(user_data.get("auth_date", 0))

        if (int(time.time()) - auth_date) > 25 * 3600:
            raise HTTPException(status_code=401, detail="Токен истёк. Запросите ссылку заново.")

        if not chat_id:
            raise HTTPException(status_code=400, detail="Некорректный токен: отсутствует chat_id.")

        # Проверяем, существует ли chat_id в базе
        card_num = get_card_number_by_chat_id(db, chat_id)
        if not card_num:
            raise HTTPException(status_code=403, detail="Пользователь не найден или номер карты отсутствует в бд.")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Определяем временные диапазоны
    unix_range_start, unix_range_end = get_period_range(
        timezone=time_zone,
        range_start=rangeStart,
        range_end=rangeEnd,
        period=period
    )

    try:
        # Получаем данные расходов
        expenses_data = get_expenses_from_db(db, unix_range_start, unix_range_end, time_zone, card_num)
    except Exception as e:
        print(f"Ошибка загрузки расходов для бота: {e}")
        raise HTTPException(status_code=500, detail="Ошибка выгрузки расходов.")
    
    if not expenses_data["expenses"]:
        error_message = "Данные за выбранный период отсутствуют."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse(
                status_code=200,
                content={"error_message": error_message}
            )
        return templates.TemplateResponse(
            "tinkoff/expenses_bot.html",
            {"request": request, "error_message": error_message, "expenses": []},
            status_code=200
        )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse(content=expenses_data)
    
    return templates.TemplateResponse(
        "tinkoff/expenses_bot.html",
        {
            "request": request,
            "expenses": json.dumps(expenses_data)
        }
    )

