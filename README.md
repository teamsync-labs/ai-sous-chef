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
- [Участие в разработке](CONTRIBUTING.md)

## Локальный запуск frontend

### Требования
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### Запуск
1. Склонируйте репозиторий (если ещё не сделали):
   ```bash
   git clone https://github.com/teamsync-labs/ai-sous-chef.git
   cd ai-sous-chef
   ```

2. Запустите фронтенд:
   ```bash
   docker compose up frontend --build
   ```

3. Откройте в браузере: [http://localhost:8080](http://localhost:8080)

### Остановка
```bash
docker compose down
```

### Healthcheck
Сервис автоматически проверяет работоспособность через `GET /`. Статус можно проверить:
```bash
docker inspect ai-sous-chef-frontend --format='{{.State.Health.Status}}'
```

## Локальный запуск backend

### Требования
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### Переменные окружения
Скопируйте `.env.example` в `.env` и при необходимости измените значения:

```bash
cp .env.example .env
```

Основные переменные:
- `POSTGRES_USER` — пользователь PostgreSQL (по умолчанию: `postgres`)
- `POSTGRES_PASSWORD` — пароль PostgreSQL (по умолчанию: `postgres`)
- `POSTGRES_DB` — имя базы данных (по умолчанию: `ai_sous_chef`)
- `DATABASE_URL` — строка подключения к БД (по умолчанию: `postgresql://postgres:postgres@postgresql:5432/ai_sous_chef`)

### Запуск
1. Склонируйте репозиторий и перейдите в корень проекта.
2. Запустите бекенд и базу данных:
   ```bash
   docker compose up backend postgresql --build
   ```
3. API будет доступно по адресу: [http://localhost:8000](http://localhost:8000)
4. Документация Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### Остановка
```bash
docker compose down
```

### Healthcheck
- `GET /health` — проверка статуса API и подключения к БД. Ответ: `{"db":"ok"}`.

### Требования
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### Запуск
1. Склонируйте репозиторий (если ещё не сделали):
   ```bash
   git clone https://github.com/teamsync-labs/ai-sous-chef.git
   cd ai-sous-chef
   ```

2. Запустите фронтенд:
   ```bash
   docker compose up frontend --build
   ```

3. Откройте в браузере: [http://localhost:8080](http://localhost:8080)

### Остановка
```bash
docker compose down
```

### Healthcheck
Сервис автоматически проверяет работоспособность через `GET /`. Статус можно проверить:
```bash
docker inspect ai-sous-chef-frontend --format='{{.State.Health.Status}}'
```

Инфраструктура и сервисы добавляются по мере реализации.

Статический сайт можно открыть напрямую: `frontend/index.html`.

Инструкции по /*backend*/, mobile и боту появятся в README, когда появятся каркасы приложений.
