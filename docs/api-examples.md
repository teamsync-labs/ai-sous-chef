# Curl-примеры API

> Маршруты используют префикс `/app/api`, заданный в `APIRouter`.

## Распознавание продуктов

### `POST /app/api/recognize`

Передаёт текст со списком продуктов и возвращает нормализованный список продуктов с оценкой уверенности.

```bash
curl -X POST "http://127.0.0.1:8000/app/api/recognize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "яйца, молоко, сыр"
  }'
```

Пример успешного ответа:

```json
{
  "products": [
    "яйца",
    "молоко",
    "сыр"
  ],
  "confidence": 0.85
}
```

Также эндпоинт принимает поле `image` вместо `text`:

```bash
curl -X POST "http://127.0.0.1:8000/app/api/recognize" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "<строковое представление изображения>"
  }'
```

Точный формат значения `image` определяется моделью `RecognizeInput`.

Возможные ошибки:

- `400 missing_input` — не передано ни `image`, ни `text`;
- `422 no_products_found` — продукты не удалось распознать;
- `502 ai_service_error` — сервис CV или LLM недоступен либо вернул ошибку.

## Генерация рецептов

### `POST /app/api/recipes`

Принимает подтверждённый список продуктов и генерирует рецепты на их основе.

```bash
curl -X POST "http://127.0.0.1:8000/app/api/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      "яйца",
      "сыр",
      "молоко"
    ]
  }'
```

Пример успешного ответа:

```json
{
  "recipes": [
    {
      "title": "Яичница",
      "steps": [
        "Разбить яйца",
        "Добавить молоко",
        "Разогреть на сковороде"
      ]
    },
    {
      "title": "Яичница с сыром",
      "steps": [
        "Разбить яйца",
        "Добавить молоко",
        "Добавить сыр",
        "Разогреть на сковороде"
      ]
    }
  ]
}
```

Возможные ошибки:

- `400 missing_input` — список продуктов не передан;
- `502 ai_service_error` — сервис LLM недоступен либо вернул ошибку.

## Запуск команд в Unix-консолях

Примеры для Bash и Zsh в Linux и macOS:

```bash
curl -X POST "http://127.0.0.1:8000/app/api/recognize" \
  -H "Content-Type: application/json" \
  -d '{"text":"яйца, молоко, сыр"}'
```

```bash
curl -X POST "http://127.0.0.1:8000/app/api/recipes" \
  -H "Content-Type: application/json" \
  -d '{"products":["яйца","сыр","молоко"]}'
```

## Запуск команд в Windows PowerShell

Примеры для PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/app/api/recognize" -ContentType "application/json; charset=utf-8" -Body (@{text="яйца, молоко, сыр"} | ConvertTo-Json -Compress)
```

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/app/api/recipes" -ContentType "application/json; charset=utf-8" -Body (@{products=@("яйца","сыр","молоко")} | ConvertTo-Json -Compress)
```

## Swagger UI

После запуска FastAPI документация обычно доступна по адресу:

```text
http://127.0.0.1:8000/docs
```

Источник структуры запросов и ответов:  
<https://github.com/teamsync-labs/ai-sous-chef/blob/main/docs/api-design.md>
