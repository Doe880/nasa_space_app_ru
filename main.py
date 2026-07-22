"""
Главный файл приложения.

Запуск (из папки nasa_space_app):
    uvicorn main:app --reload

После запуска сайт будет доступен по адресу http://127.0.0.1:8000
"""
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from nasa_client import NasaApiError, get_apod, search_moon_images

app = FastAPI(title="NASA Space Explorer")

# Подключаем папку со статикой (CSS) и папку с HTML-шаблонами
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница со ссылками на разделы."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/apod", response_class=HTMLResponse)
async def apod_page(
    request: Request,
    picture_date: Optional[str] = Query(
        default=None,
        alias="date",
        description="Дата в формате YYYY-MM-DD, необязательно",
    ),
):
    """
    Страница с "Астрономической картинкой дня".
    Можно передать ?date=2024-01-01, чтобы посмотреть картинку за конкретный день.
    """
    error = None
    apod_data = None

    # NASA APOD доступен начиная с 16 июня 1995 года
    parsed_date: Optional[date] = None
    if picture_date:
        try:
            parsed_date = datetime.strptime(picture_date, "%Y-%m-%d").date()
            if parsed_date > date.today():
                error = "Нельзя выбрать дату в будущем."
                parsed_date = None
        except ValueError:
            error = "Некорректный формат даты. Используйте YYYY-MM-DD."

    if error is None:
        try:
            apod_data = await get_apod(parsed_date)
        except NasaApiError as exc:
            error = str(exc)

    return templates.TemplateResponse(
        "apod.html",
        {
            "request": request,
            "apod": apod_data,
            "error": error,
            "selected_date": picture_date or "",
        },
    )


@app.get("/moon", response_class=HTMLResponse)
async def moon_page(request: Request, page: int = 1):
    """Галерея снимков Луны из NASA Image and Video Library."""
    error = None
    images = []
    try:
        images = await search_moon_images(query="moon", page=page)
    except NasaApiError as exc:
        error = str(exc)

    return templates.TemplateResponse(
        "moon.html",
        {
            "request": request,
            "images": images,
            "error": error,
            "page": page,
        },
    )
