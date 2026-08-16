# Интеграция LLM в бэкенд

## Рекомендуемая версия промпта
**`recipes_with_normalize_products`**

**Почему:**
- Один запрос → и нормализация, и рецепты (экономия на 2-й вызов)
- Уже включает все фиксы из eval-прогона
- JSON-ответ валидируется на стороне бэкенда

---

## Конфигурация

```yaml
# config/llm.yaml
llm:
  model: yandexgpt-pro
  temperature: 0.2
  max_tokens: 2000
  prompt_version: v1
  prompt_type: recipes_with_normalize_products
  timeout: 10
  retries: 2