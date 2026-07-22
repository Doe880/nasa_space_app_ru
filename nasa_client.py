"""Логика обращения к внешним API NASA и перевода APOD."""

from datetime import date
from typing import Any, Optional

import httpx

from config import NASA_API_KEY, NASA_APOD_URL, NASA_IMAGES_SEARCH_URL
from translator import TranslationError, translate_many_to_russian


class NasaApiError(Exception):
    """Ошибка при обращении к API NASA."""


async def get_apod(target_date: Optional[date] = None) -> dict[str, Any]:
    """
    Получить Astronomy Picture of the Day.

    Поля title и explanation заменяются русским переводом. Оригинальные
    значения сохраняются в title_en и explanation_en.
    """
    params = {"api_key": NASA_API_KEY}
    if target_date is not None:
        params["date"] = target_date.isoformat()

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(NASA_APOD_URL, params=params)

    if response.status_code != 200:
        content_type = response.headers.get("content-type", "не указан")
        remaining = response.headers.get("x-ratelimit-remaining", "неизвестно")
        detail = response.text[:500]
        raise NasaApiError(
            f"NASA APOD API вернул ошибку {response.status_code}. "
            f"Content-Type: {content_type}. "
            f"Остаток лимита: {remaining}. Ответ: {detail}"
        )

    apod_data: dict[str, Any] = response.json()

    title_en = str(apod_data.get("title", ""))
    explanation_en = str(apod_data.get("explanation", ""))

    apod_data["title_en"] = title_en
    apod_data["explanation_en"] = explanation_en
    apod_data["translation_available"] = False
    apod_data["translation_error"] = None

    try:
        title_ru, explanation_ru = await translate_many_to_russian(
            [title_en, explanation_en]
        )
        apod_data["title"] = title_ru
        apod_data["explanation"] = explanation_ru
        apod_data["translation_available"] = True
    except (TranslationError, httpx.HTTPError, ValueError) as exc:
        # Ошибка перевода не должна ломать страницу APOD.
        # Шаблон продолжит показывать исходный английский текст.
        apod_data["translation_error"] = str(exc)

    return apod_data


async def search_moon_images(
    query: str = "moon",
    page: int = 1,
) -> list[dict[str, Any]]:
    """Найти изображения в NASA Image and Video Library."""
    params = {
        "q": query,
        "media_type": "image",
        "page": page,
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(NASA_IMAGES_SEARCH_URL, params=params)

    if response.status_code != 200:
        raise NasaApiError(
            f"NASA Images API вернул ошибку {response.status_code}: "
            f"{response.text[:500]}"
        )

    data = response.json()
    items = data.get("collection", {}).get("items", [])

    results = []
    for item in items:
        item_data = item.get("data", [{}])[0]
        links = item.get("links", [])
        thumbnail = links[0]["href"] if links else None

        if thumbnail is None:
            continue

        results.append(
            {
                "title": item_data.get("title", "Без названия"),
                "description": item_data.get("description", ""),
                "date_created": item_data.get("date_created", ""),
                "thumbnail": thumbnail,
            }
        )

    return results
