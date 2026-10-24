# API Design v2

API принимает фото/текст с продуктами, а возвращает рецепты на их основе.
Используется мобильным приложением и Telegram-ботом через общий набор endpoint'ов.

**v2 отличается от v1 структурированным ответом распознавания**: каждый продукт содержит
количество, единицу измерения, источник распознавания и информацию о слиянии дубликатов.
Поддерживает два режима: одиночный (`single`) и накопительный (`accumulate`).

## Overview

Обработка запроса происходит в несколько этапов:

1. Пользователь отправляет `image` или `text` в `/app/api/v2/recognize`
2. Если пришло изображение → CV-модель распознаёт объекты на фото
3. LLM обрабатывает результат CV (или сырой текст), затем формирует **структурированный** список продуктов
4. Пользователь подтверждает список продуктов, передавая их в `/app/api/v2/recipes`
5. LLM генерирует рецепты на основе полученных продуктов

### Ключевые отличия v2 от v1

| Поле | v1 | v2 |
|------|----|----|
| Продукт | `string` | `{ name, quantity?, unit?, source?, added_at? }` |
| Режим | — | `single` / `accumulate` |
| Дубликаты | — | `duplicates_merged: number` |
| Источник | — | `photo` / `text` / `merged` |

---

## POST /app/api/v2/recognize

Распознаёт продукты по изображению или текстовому описанию.

**Request:** `{ text?: string, img_base64?: string }`

**Response 200:** `{ products: Product[], confidence: number, mode: string, duplicates_merged: number }`

**Errors:** 400 `missing_input`, 422 `no_products_found`, 502 `ai_service_error`

### Product

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | `string` | Название продукта |
| `quantity` | `number \| null` | Количество (null если не распознано) |
| `unit` | `"шт" \| "кг" \| "г" \| "л" \| "мл" \| null` | Единица измерения |
| `source` | `"photo" \| "text" \| "merged" \| null` | Источник распознавания |
| `added_at` | `number \| null` | Timestamp добавления (для accumulate-режима) |

### Режимы работы

| Режим | Описание |
|-------|----------|
| `single` | Один вход → один JSON (по умолчанию) |
| `accumulate` | Пользователь присылает несколько фото/сообщений подряд. LLM ведёт единый список продуктов по всей сессии, сливая дубликаты по правилам слияния |

### Example request

```json
{
  "text": "яйца, молоко, сыр"
}
```

### Example response (single mode)

```json
{
  "products": [
    {
      "name": "яйца",
      "quantity": null,
      "unit": null,
      "source": "text",
      "added_at": null
    },
    {
      "name": "молоко",
      "quantity": 1,
      "unit": "л",
      "source": "text",
      "added_at": null
    },
    {
      "name": "сыр",
      "quantity": null,
      "unit": null,
      "source": "text",
      "added_at": null
    }
  ],
  "confidence": 0.92,
  "mode": "single",
  "duplicates_merged": 0
}
```

### Example response (accumulate mode с merge)

```json
{
  "products": [
    {
      "name": "молоко",
      "quantity": 1.5,
      "unit": "л",
      "source": "merged",
      "added_at": 1729500000
    },
    {
      "name": "хлеб",
      "quantity": null,
      "unit": null,
      "source": "photo",
      "added_at": 1729500060
    }
  ],
  "confidence": 0.95,
  "mode": "accumulate",
  "duplicates_merged": 1
}
```

### Example response (конфликт единиц)

```json
{
  "products": [
    {
      "name": "яйца",
      "quantity": 10,
      "unit": "шт",
      "source": "merged",
      "added_at": 1729500000
    },
    {
      "name": "яйца",
      "quantity": 1,
      "unit": "кг",
      "source": "text",
      "added_at": 1729500060
    }
  ],
  "confidence": 0.6,
  "mode": "accumulate",
  "duplicates_merged": 0
}
```

### Example response (отказ)

```
Ошибка: Входные данные не являются списком продуктов. Повторите запрос.
```

### Example response (пустой список)

```json
{
  "products": [],
  "confidence": 0.0,
  "mode": "single",
  "duplicates_merged": 0
}
```

---

## POST /app/api/v2/recipes

Генерирует рецепты на основе структурированного списка продуктов.

**Request:** `{ products: ProductInput[] }`

**Response 200:** `{ recipes: { title: string, steps: string[] }[] }`

**Errors:** 400 `missing_input`, 502 `ai_service_error`

### ProductInput

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | `string` | Название продукта |
| `quantity` | `number \| null` | Количество |
| `unit` | `"шт" \| "кг" \| "г" \| "л" \| "мл" \| null` | Единица измерения |

### Example request

```json
{
  "products": [
    {
      "name": "яйца",
      "quantity": 3,
      "unit": "шт"
    },
    {
      "name": "сыр",
      "quantity": null,
      "unit": null
    }
  ]
}
```

### Example response

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

---

## GET /app/api/v2/health

**Request:** None

**Response 200:** `{ "db": "ok" }`

**Errors:** 503 `db_error`

### Example response

```json
{
  "db": "ok"
}
```

---

## Коды ошибок

| Код | error             | Message                                    |
|-----|-------------------|--------------------------------------------|
| 400 | missing_input     | Не передан ни image, ни text               |
| 422 | no_products_found | Не удалось распознать продукты             |
| 502 | ai_service_error  | Сервис CV/LLM недоступен или вернул ошибку |
| 503 | db_error          | База данных недоступна                     |

---

## AI Layer Interface

```python
from typing import Protocol, Literal

class ProductInfo(BaseModel):
    name: str
    quantity: float | None = None
    unit: Literal["шт", "кг", "г", "л", "мл"] | None = None
    source: Literal["photo", "text", "merged"] | None = None
    added_at: float | None = None


class RecognizeResultV2(BaseModel):
    products: list[ProductInfo]
    confidence: float
    mode: Literal["single", "accumulate"]
    duplicates_merged: int


class ProductInput(BaseModel):
    name: str
    quantity: float | None = None
    unit: Literal["шт", "кг", "г", "л", "мл"] | None = None


class RecipesResultV2(BaseModel):
    recipes: list[dict[str, str | list[str]]]


class AIEngine(Protocol):
    def recognize_products_v2(self, image: str = "", text: str = "") -> RecognizeResultV2:
        """Распознаёт продукты на фото или в тексте (v2: структурированный ответ)"""
        ...

    def generate_recipes_v2(self, products: list[ProductInput]) -> RecipesResultV2:
        """Генерирует рецепты на основе структурированного списка продуктов"""
        ...
```

Backend вызывает `recognize_products_v2` при получении запроса на распознование продукта
(эндпоинт `POST /app/api/v2/recognize`) и вызывает `generate_recipes_v2`, когда получен
запрос на генерацию рецептов по заданному списку продуктов.

---

## Миграция с v1 на v2

| Что | v1 | v2 |
|-----|----|----|
| Продукт | `string` | `ProductInfo` (5 полей) |
| Input для recipes | `list[str]` | `list[ProductInput]` |
| Режим | — | `single` / `accumulate` |
| Дубликаты | — | `duplicates_merged` |

**v1 остаётся рабочим** — клиенты могут мигрировать постепенно.
