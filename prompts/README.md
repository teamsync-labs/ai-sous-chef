# Промпты AI Sous-Chef

Runtime читает только версии из `pin.json` и папки `{сценарий}/{версия}/`.

## Pin (переключение версии)

Файл [`pin.json`](pin.json) — какая версия сейчас в проде:

```json
{
  "recognize": "v1",
  "recipes": "v1"
}
```

Смена версии: положить `recognize/v2/` (или `recipes/v2/`) и обновить `pin.json`. Откат — вернуть pin на предыдущую папку.

## Структура версии

```text
prompts/
  pin.json
  recognize/v1/system.md
  recognize/v1/user.md      # плейсхолдер {{ input }}
  recipes/v1/system.md      # плейсхолдер {{ products }}
  recipes/v1/user.md
```

- `recognize` → `/app/api/recognize`
- `recipes` → `/app/api/recipes`
- `v1` = baseline: текст как в проде до выноса из `ai_engine` (не «лучший eval»)

Плейсхолдеры подставляет backend простой заменой `{{ name }}`. Jinja в runtime не используется.

## Новая версия (аналитик)

1. Скопировать `v1` → `v2`, править тексты.
2. Прогнать eval при необходимости (`prompts/evals/`).
3. PR: новые файлы + смена `pin.json` (или отдельно согласовать pin с backend).

## Legacy

Файлы вроде `normalize_products.md`, `recipes/system_v2.md`, `user.md.j2` — черновики/история eval. Backend их не загружает.
