# AI Sous-Chef

Персональный ИИ-помощник на кухне — проект командной стажировки https://geek-tik.tech.

Пользователь фотографирует продукты или перечисляет ингредиенты, а приложение помогает подобрать рецепт и провести через приготовление.

**Статус:** Development

## Roadmap

MVP · фаза 1 · «Что приготовить?»

| Неделя | Цель |
|--------|------|
| 1 | ☑ Kickoff & Dev Setup |
| 2 | ☑ Backend, bot — каркасы |
| 3 | ☑ API recognize/recipes (mock); промпты |
| 4 | ☑ Telegram: фото/текст → recognize; Docker/CI |
| 5 | ☐ Реальный CV/LLM; подтверждение продуктов в боте |
| 6 | ☐ Генерация и выдача рецептов в боте |
| 7 | ☐ Mobile: каркас и сценарии фото/текст |
| 8 | ☐ UX, стабилизация, публичный релиз, демо |

## Структура

```
backend/
  app/               HTTP API, бизнес-логика, интеграции с LLM
  bot/               Telegram-клиент (тот же backend, отдельного API нет)
  tests/
frontend/            сайт-визитка и страница команды
prompts/             промпты, evals, фикстуры для AI-аналитика
docs/                vision и прочая документация
infra/               деплой и окружения
.github/workflows/   CI/CD
```

Мобильное приложение — отдельный репозиторий: [teamsync-labs/ai-sous-chef-app](https://github.com/teamsync-labs/ai-sous-chef-app).

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

3. Задайте в `.env` токен бота (`TG_TOKEN=…` от BotFather). Без него контейнер `bot` не стартует.

4. Запустите стек (frontend + API + bot + PostgreSQL + Redis + nginx):
   ```bash
   docker compose up --build
   ```
   В `.env` задано `COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml`, поэтому
   снаружи один порт `NGINX_PORT` (по умолчанию `8080`).
   Redis поднимается вместе со стеком (`REDIS_URL=redis://redis:6379/0`); отдельно его
   ставить не нужно. Порт наружу не публикуется — доступ только из сети compose.

5. Проверьте:
   - сайт: [http://localhost:8080](http://localhost:8080)
   - health: [http://localhost:8080/health](http://localhost:8080/health) → `{"db":"ok"}`
   - docs: [http://localhost:8080/docs](http://localhost:8080/docs)
   - API: `/app/api/...` через тот же порт
   - bot: `docker compose ps` — сервис `bot` в статусе Up
   - redis: `docker compose ps` — сервис `redis` healthy

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
