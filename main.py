
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from nasa_client import NasaApiError, get_apod, search_moon_images


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="NASA Space Explorer")

# Абсолютные пути корректно работают и локально, и на Render.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/apod", response_class=HTMLResponse)
async def apod_page(
    request: Request,
    picture_date: Optional[str] = Query(
        default=None,
        alias="date",
        description="Дата в формате YYYY-MM-DD",
    ),
    lang: str = Query(default="ru", description="Язык описания: ru или en"),
):
    """Страница Astronomy Picture of the Day с выбором языка."""
    error = None
    translation_error = None
    apod_data = None
    parsed_date: Optional[date] = None

    # Неизвестные значения языка безопасно заменяем на русский.
    lang = "en" if lang.lower() == "en" else "ru"

    if picture_date:
        try:
            parsed_date = datetime.strptime(picture_date, "%Y-%m-%d").date()

            if parsed_date < date(1995, 6, 16):
                error = "Архив APOD начинается с 16 июня 1995 года."
            elif parsed_date > date.today():
                error = "Нельзя выбрать дату в будущем."
        except ValueError:
            error = "Некорректный формат даты. Используйте YYYY-MM-DD."

    if error is None:
        try:
            apod_data = await get_apod(parsed_date)
        except NasaApiError as exc:
            error = str(exc)

    if apod_data:
        title_en = apod_data.get("title_en") or apod_data.get("title", "")
        explanation_en = (
            apod_data.get("explanation_en")
            or apod_data.get("explanation", "")
        )

        if lang == "en":
            apod_data["title_display"] = title_en
            apod_data["explanation_display"] = explanation_en
        else:
            # После успешного перевода nasa_client сохраняет русские значения
            # в title и explanation. При ошибке там остаётся английский оригинал.
            apod_data["title_display"] = apod_data.get("title") or title_en
            apod_data["explanation_display"] = (
                apod_data.get("explanation") or explanation_en
            )

            if not apod_data.get("translation_available", False):
                translation_error = apod_data.get("translation_error")

    return templates.TemplateResponse(
        request=request,
        name="apod.html",
        context={
            "apod": apod_data,
            "error": error,
            "translation_error": translation_error,
            "selected_date": picture_date or "",
            "lang": lang,
            "today": date.today().isoformat(),
        },
    )


@app.get("/moon", response_class=HTMLResponse)
async def moon_page(request: Request, page: int = 1):
    """Галерея изображений Луны из NASA Image and Video Library."""
    page = max(page, 1)
    error = None
    images = []

    try:
        images = await search_moon_images(query="moon", page=page)
    except NasaApiError as exc:
        error = str(exc)

    return templates.TemplateResponse(
        request=request,
        name="moon.html",
        context={
            "images": images,
            "error": error,
            "page": page,
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Проверка доступности приложения для Render."""
    return {"status": "ok"}