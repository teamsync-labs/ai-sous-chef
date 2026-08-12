## Redis: кэш одинаковых AI-запросов

### Scope

Кэшируем ответы AI для:

- `/api/recipes` — обязательно.
- `/api/recognize` — кэш по products после CV

Кэш общий, т.е. без привязки к пользователю (без per-suer)

### Схема ключа

Формат ключа:

`ai-cache:{cache_version}:{endpoint}:model={model_name}:prompt={prompt_version}:{scope}`

#### /api/recipes

- `cache_version`: `v1`
- `endpoint`: `recipes`
- `model_name`: имя модели (например, `gpt-4o-mini`)
- `prompt_version`: версия промпта (например, `recipes_v1`)
- `scope`: `products={normalized_products}`

Нормализация `normalized_products`:

- все названия продуктов в lowercase
- trim пробелов по краям
- множественные пробелы сведены к одному
- сортировка по алфавиту
- удаление дубликатов
- соединение через запятую

Пример:

`ai-cache:v1:recipes:model=yamdex-global:prompt=recipes_v1:products=apple,banana,carrot`

#### /api/recognize (после CV)

Формат:

`ai-cache:v1:recognize:model=cv_v1:products={normalized_products}`

### Значение

В кэше хранится полный ответ AI в том формате, в котором он отдаётся клиенту:

- `/api/recipes`: JSON с рецептами.
- `/api/recognize`: JSON с распознанными продуктами.

### TTL

- `/api/recipes`: `TTL = 1800` секунд (30 минут).
- `/api/recognize`: `TTL = 600` секунд (10 минут).

При изменении модели, промпта или схемы нормализации увеличиваем `cache_version` (`v2`, `v3` и т.д.), чтобы не переиспользовать старые ответы.

### Поведение при недоступности Redis

Режим `fail-open`:

- если Redis недоступен:
  - backend не использует кэш
  - ходит в LLM/CV напрямую
  - возвращает ответ клиенту
  - логирует ошибку Redis

### Что не кладём в кэш

- ответы с ошибками LLM/CV (5xx
- пустые или некорректные ответы, которые считаются ошибкой по API-дизайну

### Контракт для backend

- **Ключ**: как описано выше (включая `cache_version`, `endpoint`, `model`, `prompt`, `scope`)
- **Значение**: сериализованный успешный ответ AI
- **TTL**: по endpoint (`recipes`: 1800 сек, `recognize`: 600 сек)
- **Fallback**:
  - cache miss → вызвать LLM/CV, записать успешный ответ в Redis, вернуть клиенту
  - Redis недоступен → вызвать LLM/CV, не использовать кэш
  - ошибка LLM/CV → не писать в Redis, вернуть ошибку клиенту
