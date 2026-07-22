"""
Конфигурация приложения.

Секреты и изменяемые параметры читаются из переменных окружения.
Локально их можно хранить в файле .env, а на Render — в разделе Environment.
"""
import os

from dotenv import load_dotenv

load_dotenv()

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY").strip()

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
NASA_IMAGES_SEARCH_URL = "https://images-api.nasa.gov/search"

# Бесплатный перевод через MyMemory Translation API.
TRANSLATION_ENABLED = os.getenv("TRANSLATION_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MYMEMORY_TRANSLATE_URL = "https://api.mymemory.translated.net/get"

# Необязательный контактный email, который MyMemory рекомендует передавать
# для приложений и повышенной нагрузки. Это не API-ключ.
MYMEMORY_EMAIL = os.getenv("MYMEMORY_EMAIL", "").strip()
