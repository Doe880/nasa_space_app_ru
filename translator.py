"""Бесплатный перевод текстов APOD с английского языка на русский."""

from __future__ import annotations

import html
import re
from collections import OrderedDict
from typing import Iterable

import httpx

from config import MYMEMORY_EMAIL, MYMEMORY_TRANSLATE_URL, TRANSLATION_ENABLED


class TranslationError(Exception):
    """Ошибка внешнего сервиса перевода."""


# MyMemory принимает максимум 500 байт в параметре q.
# Оставляем небольшой запас для безопасной отправки текста.
_MAX_SEGMENT_BYTES = 450
_CACHE_LIMIT = 256
_translation_cache: OrderedDict[str, str] = OrderedDict()


def _remember(source: str, translated: str) -> None:
    """Сохранить перевод в небольшом кэше текущего процесса."""
    _translation_cache[source] = translated
    _translation_cache.move_to_end(source)

    while len(_translation_cache) > _CACHE_LIMIT:
        _translation_cache.popitem(last=False)


def _split_by_bytes(text: str, max_bytes: int) -> list[str]:
    """Разбить длинный фрагмент так, чтобы каждый кусок помещался в лимит API."""
    words = text.split()
    if not words:
        return []

    result: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate.encode("utf-8")) <= max_bytes:
            current.append(word)
            continue

        if current:
            result.append(" ".join(current))
            current = []

        # На случай одного очень длинного слова делим его посимвольно.
        if len(word.encode("utf-8")) > max_bytes:
            piece = ""
            for char in word:
                next_piece = piece + char
                if len(next_piece.encode("utf-8")) > max_bytes:
                    if piece:
                        result.append(piece)
                    piece = char
                else:
                    piece = next_piece
            if piece:
                current = [piece]
        else:
            current = [word]

    if current:
        result.append(" ".join(current))

    return result


def _split_text(text: str) -> list[str]:
    """Разбить описание на предложения и уложить их в лимит MyMemory."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    segments: list[str] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence.encode("utf-8")) <= _MAX_SEGMENT_BYTES:
            segments.append(sentence)
        else:
            segments.extend(_split_by_bytes(sentence, _MAX_SEGMENT_BYTES))

    return segments


async def _translate_segment(client: httpx.AsyncClient, segment: str) -> str:
    cached = _translation_cache.get(segment)
    if cached is not None:
        _translation_cache.move_to_end(segment)
        return cached

    params = {
        "q": segment,
        "langpair": "en|ru",
        "mt": "1",
    }
    if MYMEMORY_EMAIL:
        params["de"] = MYMEMORY_EMAIL

    response = await client.get(MYMEMORY_TRANSLATE_URL, params=params)
    response.raise_for_status()

    payload = response.json()
    response_status = payload.get("responseStatus", 200)
    translated = payload.get("responseData", {}).get("translatedText", "")

    if str(response_status) != "200" or not translated:
        details = payload.get("responseDetails") or "пустой ответ сервиса"
        raise TranslationError(f"MyMemory не выполнил перевод: {details}")

    translated = html.unescape(str(translated)).strip()
    if translated.upper().startswith("MYMEMORY WARNING"):
        raise TranslationError(translated)

    _remember(segment, translated)
    return translated


async def translate_to_russian(
    text: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    """
    Перевести английский текст на русский.

    Если перевод отключён или исходный текст пустой, возвращается исходный текст.
    """
    if not TRANSLATION_ENABLED or not text.strip():
        return text

    segments = _split_text(text)
    if not segments:
        return text

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=20, follow_redirects=True)

    try:
        translated_segments = []
        for segment in segments:
            translated_segments.append(await _translate_segment(client, segment))
        return " ".join(translated_segments)
    finally:
        if owns_client:
            await client.aclose()


async def translate_many_to_russian(texts: Iterable[str]) -> list[str]:
    """Перевести несколько строк через одно HTTP-соединение."""
    source_texts = list(texts)
    if not TRANSLATION_ENABLED:
        return source_texts

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        result = []
        for text in source_texts:
            result.append(await translate_to_russian(text, client=client))
        return result
