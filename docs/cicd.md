# CI/CD — AI Sous-Chef

Модель: сборка образов на GitHub Actions runner → `docker save` → scp → `docker load` на VPS → `compose up` **без** `--build`. Registry нет.

## Workflows

| Событие | Workflow | Действие |
|---------|----------|----------|
| PR → `main` / `dev` | `ci.yml` | сборка Docker-образов + import-smoke backend |
| merge PR → `main` | `deploy-main.yml` | deploy **prod** |
| merge PR → `dev` | `deploy-dev.yml` | deploy **dev** (Environment пока не создаём) |
| `workflow_dispatch` | `deploy-main.yml` / `deploy-dev.yml` | ручной redeploy |

Прямой push в `main`/`dev` деплой **не** запускает.

## Environment `prod` (сейчас)

VPS: `157.22.207.238` · пользователь `ai-sous-chef-prod` · код `/var/www/ai-sous-chef/prod`

### Secrets

| Name | Значение |
|------|----------|
| `SSH_PRIVATE_KEY` | `~/.ssh/ai-sous-chef_deploy_prod` (private) |
| `POSTGRES_PASSWORD` | сырой пароль (можно со спецсимволами `$`, `!`, `@`, `#` …) |

**Не нужен** `DATABASE_URL`: его собирает `scripts/vps-write-deploy-env.sh` из `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` с **URL-encode** пароля. Если secret `DATABASE_URL` уже создан — удали, чтобы не путаться.

### Variables (только эти)

| Name | Значение |
|------|----------|
| `SERVER_HOST` | `157.22.207.238` |
| `SERVER_USER` | `ai-sous-chef-prod` |
| `SERVER_PATH` | `/var/www/ai-sous-chef/prod` |
| `DATA_PATH` | `/var/www/ai-sous-chef/prod_data` |
| `COMPOSE_PROJECT_NAME` | `ai-sous-chef-prod` |
| `NGINX_PORT` | `3101` |
| `ACCESS_VIA_DOMAIN` | `false` |
| `APP_DOMAIN` | `ai-sous-chef.ru` |

**Удалить из Environment, если уже добавили:** `NGINX_BIND`, `HEALTHCHECK_URL`, `APP_PUBLIC_URL`, `IMAGE_PREFIX`, `IMAGE_TAG`, `POSTGRES_USER`, `POSTGRES_DB`, `DATABASE_URL`.

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
| `IMAGE_TAG` | короткий SHA |
| `IMAGE_PREFIX` | `ai-sous-chef` |
| `POSTGRES_USER` / `POSTGRES_DB` | `postgres` / `ai_sous_chef` |

Сейчас (`ACCESS_VIA_DOMAIN=false`): `http://157.22.207.238:3101/health`.  
После host nginx + TLS: `ACCESS_VIA_DOMAIN=true` → `https://ai-sous-chef.ru/health`.

## Environment `dev` (позже)

Те же имена. Порт `3100`, пути `…/dev` и `dev_data`, `COMPOSE_PROJECT_NAME=ai-sous-chef-dev`. Environment в GitHub пока **не** создаём.

## Ручной redeploy

Actions → **Deploy Prod** → Run workflow.
