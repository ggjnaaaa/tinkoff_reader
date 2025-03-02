# utils/bot.py 

# Стандартные модули Python
import time

# Сторонние модули
from fastapi import HTTPException

# Собственные модули
from auth import verify_bot_token


def check_miniapp_token(token: str):
    """
    Проверяет токенизированный доступ и записывает данные в tg_tmp_users.
    """
    try:
        # Проверяем токен и извлекаем данные
        user_data = verify_bot_token(token)
        chat_id = int(user_data.get("chat_id"))
        auth_date = int(user_data.get("auth_date", 0))

        if (int(time.time()) - auth_date) > 25 * 3600:
            raise HTTPException(status_code=401, detail="Токен истёк. Запросите ссылку заново.")

        if not chat_id:
            raise HTTPException(status_code=400, detail="Некорректный токен: отсутствует chat_id.")

        return True
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))