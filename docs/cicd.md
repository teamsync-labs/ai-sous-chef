# CI/CD — AI Sous-Chef

Модель: сборка образов на GitHub Actions runner → `docker save` → scp → `docker load` на VPS → `compose up` **без** `--build`. Registry нет.

Backend-образ: `docker build -f backend/Dockerfile … .` (context — корень репо), внутрь копируется `prompts/` (`pin.json` + версии).

Образы: `frontend`, `backend`, `bot`. Telegram-бот — сервис в том же compose (`API_BASE=http://backend:8000/app/api`), secret `TG_TOKEN`.

## Workflows

| Событие | Workflow | Действие |
|---------|----------|----------|
| PR → `main` / `dev` | `ci.yml` | сборка образов frontend/backend/bot + import-smoke backend |
| merge PR → `main` | `deploy-main.yml` | deploy **prod** |
| merge PR → `dev` | `deploy-dev.yml` | deploy **dev** (Environment пока не создаём) |
| `workflow_dispatch` | `deploy-main.yml` / `deploy-dev.yml` | ручной redeploy |

Прямой push в `main`/`dev` деплой **не** запускает.

## Environment `prod`

Пользователь на VPS: `ai-sous-chef-prod`. Хост, пути и порт — только в GitHub Variables (в репо не дублируем).

### Secrets

| Name | Значение |
|------|----------|
| `SSH_PRIVATE_KEY` | deploy-ключ пользователя `ai-sous-chef-prod` (private) |
| `POSTGRES_PASSWORD` | сырой пароль (можно со спецсимволами `$`, `!`, `@`, `#` …) |
| `TG_TOKEN` | токен Telegram-бота (BotFather) |
| `TG_PROXY_URL` | URL прокси до Telegram API |
| `YANDEX_API_KEY` | API-ключ Yandex Cloud (нужен при `AI_MODE=real`) |
| `YANDEX_FOLDER_ID` | ID каталога Yandex Cloud (нужен при `AI_MODE=real`) |
| `CONSENT_JOURNAL_API_KEY` | ключ API журнала согласий |
| `API_KEY_BOT` | ключ клиента API для бота (`X-Api-Key` на `/app/api`) |
| `API_KEY_APP` | ключ клиента API для приложения (`X-Api-Key` на `/app/api`) |
| `API_KEY_SITE` | ключ сайта для `channel=site` (в `cookie-notice.js`; не открывает recognize/recipes) |

**Не нужен** `DATABASE_URL`: его собирает `scripts/vps-write-deploy-env.sh` из `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` с **URL-encode** пароля. Лишний secret `DATABASE_URL` в Environment лучше удалить, чтобы не путаться.

### Variables (только эти)

| Name | Смысл |
|------|--------|
| `SERVER_HOST` | IP или hostname VPS |
| `SERVER_USER` | `ai-sous-chef-prod` |
| `SERVER_PATH` | каталог кода на VPS (без публикации в docs) |
| `DATA_PATH` | каталог данных на VPS |
| `COMPOSE_PROJECT_NAME` | `ai-sous-chef-prod` |
| `NGINX_PORT` | `3101` |
| `ACCESS_VIA_DOMAIN` | `false` до host nginx+TLS |
| `APP_DOMAIN` | `ai-sous-chef.ru` |
| `AI_MODE` | `stub` или `real` (по умолчанию в скрипте — `stub`) |
| `CONSENT_JOURNAL_URL` | URL журнала согласий |
| `CONSENT_PUBLIC_BASE` | публичный префикс документов согласий |

Из Environment не используются (лишние — убрать): `NGINX_BIND`, `HEALTHCHECK_URL`, `APP_PUBLIC_URL`, `IMAGE_PREFIX`, `IMAGE_TAG`, `POSTGRES_USER`, `POSTGRES_DB`, `DATABASE_URL`.

### Требования на VPS

На сервере нужны: Docker Engine, Compose plugin, **`rsync`**, OpenSSH. Deploy-пользователь — в группе `docker`.

```bash
# под root
apt-get update && apt-get install -y rsync
```

### Экранирование паролей (как в geek-tik)

`.env` пишет `vps-write-deploy-env.sh`:

1. Значения в `"…"`, не `printf %q` (shell-экранирование ломает Compose/`--env-file`).
2. Для `${VAR}` в compose: `$` → `$$`, экранируются `\` и `"`.
3. В `DATABASE_URL` пароль проходит `urllib.parse.quote` — спецсимволы в URL не ломают разбор.

### Что вычисляет deploy (не vars)

| Поле | Логика |
|------|--------|
| `NGINX_BIND` / `APP_PUBLIC_URL` / `HEALTHCHECK_URL` | `scripts/resolve-public-urls.sh` |
| `DATABASE_URL` | из `POSTGRES_*` + URL-encode |
| `REDIS_URL` | по умолчанию `redis://redis:6379/0` (secret не нужен) |
| `AI_MODE` | из var `AI_MODE`, иначе `stub` |
| `IMAGE_TAG` | короткий SHA |
| `IMAGE_PREFIX` | `ai-sous-chef` |
| `POSTGRES_USER` / `POSTGRES_DB` | `postgres` / `ai_sous_chef` |

Пока `ACCESS_VIA_DOMAIN=false`: healthcheck по `http://$SERVER_HOST:$NGINX_PORT/health`.  
После host nginx + TLS: `ACCESS_VIA_DOMAIN=true` → `https://$APP_DOMAIN/health`.

После `compose up` CI всегда делает `--force-recreate --no-deps nginx`: образ `nginx:alpine` не меняется, а upstream IP backend/frontend после recreate иначе остаются закэшированными → 502 и публичный 503/maintenance.

Хостовый nginx: [`deploy/host-nginx/`](../deploy/host-nginx/) (vhost + maintenance). Копируется на VPS вручную — см. README там.

## Environment `dev` (позже)

Те же имена. Порт `3100`, отдельные `SERVER_PATH`/`DATA_PATH`/`COMPOSE_PROJECT_NAME`. Environment в GitHub пока **не** создаём.

## Ручной redeploy

Actions → **Deploy Prod** → Run workflow.
