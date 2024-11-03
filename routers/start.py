# auth_tinkoff.py

# Сторонние библиотеки
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates



router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Основной процесс
@router.get("/", response_class=HTMLResponse)
def get_login_type(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})