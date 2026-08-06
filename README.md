# AI Sous-Chef

Персональный ИИ-помощник на кухне — учебный проект командной стажировки TeamSync Labs.

Пользователь фотографирует продукты или перечисляет ингредиенты, а приложение помогает подобрать рецепт и провести через приготовление.

**Статус:** Development

## Roadmap

MVP · фаза 1 · «Что приготовить?»

| Неделя | Цель |
|--------|------|
| 1 | ☐ Kickoff & Dev Setup |
| 2 | ☐ Backend, mobile, bot — каркасы; первые AI-эксперименты |
| 3 | ☐ Фото продуктов, распознавание, интеграция с LLM |
| 4 | ☐ Генерация и отображение рецептов |
| 5 | ☐ UX, обработка ошибок, стабилизация сценариев |
| 6 | ☐ Полировка, публичный релиз, демо MVP |

При необходимости — ещё 1–2 недели на завершение оставшихся задач.

## Структура

```
backend/
  app/               HTTP API, бизнес-логика, интеграции с LLM
  bot/               Telegram-клиент (тот же backend, отдельного API нет)
  tests/
mobile/              Android-приложение (Kotlin)
frontend/            сайт-визитка и страница команды
prompts/             промпты, evals, фикстуры для AI-аналитика
docs/                vision и прочая документация
infra/               деплой и окружения
.github/workflows/   CI/CD
```

## Документация

- [Vision](docs/vision.md)
- [Yandex Cloud API: CV + LLM](docs/ai/yandex-api-quickstart.md)
- [Участие в разработке](CONTRIBUTING.md)

## Локальный запуск

### Требования
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### Запуск
1. Склонируйте репозиторий (если ещё не сделали):
   ```bash
   git clone https://github.com/teamsync-labs/ai-sous-chef.git
   cd ai-sous-chef
   ```

2. Скопируйте env:
   ```bash
   cp .env.example .env
   ```

3. Запустите весь стек (frontend + API + PostgreSQL + nginx):
   ```bash
   docker compose up --build
   ```
   В `.env` задано `COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml`, поэтому
   снаружи один порт `NGINX_PORT` (по умолчанию `8080`).

4. Проверьте:
   - сайт: [http://localhost:8080](http://localhost:8080)
   - health: [http://localhost:8080/health](http://localhost:8080/health) → `{"db":"ok"}`
   - docs: [http://localhost:8080/docs](http://localhost:8080/docs)
   - API: `/app/api/...` через тот же порт

Prod-overlay (на VPS): `docker-compose.prod.yml`, порт `3101`.

### Остановка
```bash
docker compose down
```

### Healthcheck
```bash
docker compose ps
curl -fsS http://localhost:8080/health
```

Статический сайт можно открыть напрямую: `frontend/index.html`.

Telegram-бот и mobile в этот compose не входят.
