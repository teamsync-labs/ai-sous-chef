# Yandex Cloud API: быстрый старт (CV + LLM)

Практический гайд для воспроизведения рабочих запросов к облаку.

Секреты (`YANDEX_FOLDER_ID`, `YANDEX_API_KEY`) передаются **лично**, в репозиторий не коммитить.

## Используемые модели

| Роль | Модель | URI |
|------|--------|-----|
| CV: фото → продукты | Qwen3.6-35B (AI Studio, `image-text-to-text`) | `gpt://<folder_id>/qwen3.6-35b-a3b/latest` |
| LLM: продукты → рецепт | YandexGPT Pro | `gpt://<folder_id>/yandexgpt/latest` |

> **Yandex Vision OCR** для MVP-сценария «еда на фото» не подходит: читает текст/этикетки, не объекты. Plan B аналитика (YOLO) — локальный, не через YC API.

## 1. Переменные окружения

```bash
export YANDEX_FOLDER_ID="..."   # ID каталога default
export YANDEX_API_KEY="..."     # API-ключ сервисного аккаунта
```

Либо положить в `.env` бэкенда:

```env
YANDEX_FOLDER_ID=...
YANDEX_API_KEY=...
```

## 2. Окружение Python

Из корня backend:

```bash
cd backend
source .venv/bin/activate
# если openai ещё нет:
pip install openai
```

Нужен пакет `openai` (уже в `backend/app/requirements.txt`).

## 3. CV: фото → список продуктов (Qwen)

Подготовить JPEG (WebP под расширением `.png` API не принимает):

```bash
python - <<'PY'
from PIL import Image
Image.open("/path/to/photo").convert("RGB").save("/tmp/food.jpg", "JPEG", quality=90)
print("ok")
PY
```

Запрос (Responses API). Важно: `max_output_tokens` указывать **не меньше 2000–4000** — иначе модель тратит лимит на reasoning и `output_text` будет пустым (`status=incomplete`).

```bash
python - <<'PY'
import base64, os
from openai import OpenAI

folder = os.environ["YANDEX_FOLDER_ID"]
key = os.environ["YANDEX_API_KEY"]
model = f"gpt://{folder}/qwen3.6-35b-a3b/latest"

with open("/tmp/food.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

client = OpenAI(
    api_key=key,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project=folder,
)

response = client.responses.create(
    model=model,
    temperature=0.3,
    max_output_tokens=4000,
    input=[{
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": "Перечисли продукты/ингредиенты на фото списком. Только названия, без рецепта.",
            },
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{b64}",
            },
        ],
    }],
)

print("status=", response.status)
print(response.output_text)
PY
```

Ожидание: `status=completed` и список продуктов.

## 4. LLM: продукты → рецепт (YandexGPT Pro)

Текстовый Chat Completions (картинку Pro не принимает — только список продуктов):

```bash
python - <<'PY'
import os
from openai import OpenAI

folder = os.environ["YANDEX_FOLDER_ID"]
key = os.environ["YANDEX_API_KEY"]
model = f"gpt://{folder}/yandexgpt/latest"

products = [
    "молоко",
    "болгарский перец",
    "яблоко",
    "виноград",
    "курица",
    "морковь",
    "бананы",
    "брокколи",
    "помидоры",
    "огурцы",
]

client = OpenAI(
    api_key=key,
    base_url="https://ai.api.cloud.yandex.net/v1",
    project=folder,
)

prompt = (
    "По списку продуктов предложи 1 короткий рецепт на русском. "
    "Ответ строго JSON: {\"title\": string, \"steps\": string[]}. "
    f"Продукты: {', '.join(products)}"
)

response = client.chat.completions.create(
    model=model,
    temperature=0.3,
    max_tokens=1200,
    messages=[{"role": "user", "content": prompt}],
)

print(response.choices[0].message.content)
PY
```

Ожидание: JSON с `title` и `steps` (иногда модель оборачивает в markdown-блок \`\`\`json — это нормально на этапе smoke-теста).

Минимальный smoke без SDK (curl):

```bash
curl -s https://llm.api.cloud.yandex.net/v1/chat/completions \
  -H "Authorization: Api-Key $YANDEX_API_KEY" \
  -H "x-folder-id: $YANDEX_FOLDER_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gpt://$YANDEX_FOLDER_ID/yandexgpt/latest\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Скажи одним словом: работает\"}],
    \"max_tokens\": 50
  }"
```

## 5. Типичные проблемы

| Симптом | Решение |
|---------|---------|
| `403 Forbidden` на модели | Модель недоступна в каталоге / нет роли; проверить AI Studio → Модели |
| `Can't decode image` | Файл не того формата (часто WebP с именем `.png`) → конвертировать в JPEG |
| `Argument list too long` у curl | Не передавать base64 в argv — писать JSON в файл (`-d @body.json`) |
| `status=incomplete`, пустой текст | Увеличить `max_output_tokens` (reasoning съедает бюджет) |
| Ключ в git | Не коммитить `.env`; только плейсхолдеры в `.env.example` |

## Связанные документы

- [MVP AI stack](mvp-ai-stack.md) — выбор моделей и оценки
- [CV comparison](cv-comparison.md)
- [LLM comparison](llm-comparison.md)
