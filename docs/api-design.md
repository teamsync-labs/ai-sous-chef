API принимает фото/текст с продуктами, а возвращает рецепты на их основе.
Используется мобильным приложением и Telegram-ботом через общий набор endpoint'ов
## Overview

Обработка запроса происходит в несколькот этапов:

1. Пользователь отправляет `image` или `text` в `/api/recognize`
2. Если пришло изображение -> CV-модель распознает объекты на фото
3. LLM обрабатывает результат CV (или же сырой текст), затем формирует чистый список продуктов
4. Пользователь подтверждает список продуктов, передавая их в `/api/recipes`
5. LLM енерирует рецепты на основе полученных продуктов

### POST /api/recognize

Request: { image?: string, text?: string }

Response 200: { products: string[], confidence: number }

Errors: 400 missing_input, 422 no_products_found, 502 ai_service_error

Example request:

```json
{
  "text": "яйца, молоко, сыр"
}
```

Example response:

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

### POST /api/recipes

Request: { products: string[] }

Response 200: { recipes: { title: string, steps: string[] }[] }

Errors: 400 missing_input, 502 ai_service_error

Example request:

```json
{
  "products": ["яйца", "сыр", "молоко"]
}
```

Example response:

```json
{
  "recipes": [
    {
      "title": "Яичница",
      "steps": [
        "Разбить яйца",
        "Добавить молоко",
        "Разогретьь на сковороде"
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

### GET /api/health

Request: None

Response 200: { "db": "ok" }

Errors: 503 db_error

Example response:

```json
{
  "db": "ok"
}
```

## Коды ошибок

| Код | error             | Message                                    |
|-----|-------------------|--------------------------------------------|
| 400 | missing_input     | Не передан ни image, ни text               |
| 422 | no_products_found | Не удалось распознать продукты             |
| 502 | ai_service_error  | Сервис CV/LLM недоступен или вернул ошибку |
| 503 | db_error          | База данных недоступна                     |

## AI Layer Interface

```python
class AIEngine(Protocol):
    def recognize_products(self, image: str = "", text: str = "") -> RecognizeResult:
        """Распознает продукты на фото или в тексте"""
        ...

    def generate_recipes(self, products: list[str]) -> RecipesResult:
        """На основе списка продуктов генерирует множество рецептов со списком действий"""
        ...
```

Backend вызывает recognize_products при получении запроса на распознование продукта (эндпоинт `POST /api/recognize`)
и вызывает generate_recipes, когда получен запрос на генерацию рецептов по заданному списку продуктов 

