# Бесплатный русский перевод APOD

В проект добавлен файл `translator.py`. Он переводит заголовок и описание
Astronomy Picture of the Day через бесплатный REST API MyMemory.

## Что изменилось

- `apod.title` и `apod.explanation` теперь содержат русский перевод.
- Английский оригинал сохраняется в `apod.title_en` и `apod.explanation_en`.
- При ошибке сервиса перевода страница продолжает работать и показывает английский текст.
- Текст автоматически разбивается на короткие фрагменты, поскольку MyMemory
  принимает не более 500 байт в одном запросе.
- Внутри процесса работает небольшой кэш переводов.

## Локальный `.env`

```env
NASA_API_KEY=ваш_ключ_NASA
TRANSLATION_ENABLED=true
MYMEMORY_EMAIL=your-email@example.com
```

`MYMEMORY_EMAIL` необязателен и не является API-ключом.

## Render

Добавьте в **Environment**:

```text
NASA_API_KEY = ваш_ключ_NASA
TRANSLATION_ENABLED = true
MYMEMORY_EMAIL = ваш_email
```

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Шаблон `apod.html`

Менять шаблон не обязательно, если он уже выводит:

```jinja2
{{ apod.title }}
{{ apod.explanation }}
```

Эти поля теперь автоматически приходят на русском языке.

Для показа английского оригинала можно дополнительно использовать:

```jinja2
<details>
    <summary>Показать оригинал на английском</summary>
    <h3>{{ apod.title_en }}</h3>
    <p>{{ apod.explanation_en }}</p>
</details>
```
