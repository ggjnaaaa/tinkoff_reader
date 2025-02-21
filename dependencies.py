from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from auth import decode_access_token

def is_telegram_web_app(request: Request) -> bool:
    # Проверяем наличие специфичных заголовков Telegram Web Apps
    return (
        request.headers.get("x-telegram-web-app") is not None
        or request.headers.get("user-agent", "").startswith("TelegramWeb")
    )

# Функция для получения токена из cookie
def get_token_from_cookie(request: Request):
    token = request.cookies.get("token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return token


# Функция для получения текущего пользователя из токена
def get_current_user(token: str):
    payload = decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return payload

async def get_authenticated_user(request: Request):
    # Проверка токена и текущего пользователя
    token = get_token_from_cookie(request)
    if isinstance(token, RedirectResponse):
        return token
    payload = get_current_user(token)
    if isinstance(payload, RedirectResponse):
        return payload
    return payload