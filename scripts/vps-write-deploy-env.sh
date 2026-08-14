#!/usr/bin/env bash
# Пишет .env для Docker Compose (не bash source).
# Не использовать printf %q: shell-экранирование ломает пароли в compose/--env-file
# (урок loterna → fix в geek-tik: docs/deploy.md, scripts/vps-write-deploy-env.sh).
set -euo pipefail

ENV_FILE="${1:?usage: vps-write-deploy-env.sh <outfile>}"

: >"$ENV_FILE"

# Значения для ${VAR} в compose.yml: `$` → `$$`, иначе Compose съест `$fragment`.
write_kv_compose() {
  local key="$1"
  local value="$2"
  local escaped="$value"
  escaped="${escaped//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"
  escaped="${escaped//\$/\$\$}"
  printf '%s="%s"\n' "$key" "$escaped" >>"$ENV_FILE"
}

: "${IMAGE_PREFIX:?}"
: "${IMAGE_TAG:?}"
: "${COMPOSE_PROJECT_NAME:?}"
: "${POSTGRES_USER:?}"
: "${POSTGRES_PASSWORD:?}"
: "${POSTGRES_DB:?}"
: "${NGINX_PORT:?}"
: "${NGINX_BIND:?}"
: "${ACCESS_VIA_DOMAIN:?}"
: "${APP_DOMAIN:?}"
: "${APP_PUBLIC_URL:?}"
: "${HEALTHCHECK_URL:?}"
: "${DATA_PATH:?}"
: "${TG_TOKEN:?}"
: "${TG_PROXY_URL:?}"
: "${API_BASE:=http://backend:8000/app/api}"
: "${REDIS_URL:=redis://redis:6379/0}"

# DATABASE_URL собираем сами: пароль URL-encode (спецсимволы @:#/?% и т.д.).
# Отдельный secret DATABASE_URL не нужен — иначе легко разъехаться с POSTGRES_PASSWORD.
pass_enc="$(
  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" python3 -c \
    'import os, urllib.parse; print(urllib.parse.quote(os.environ["POSTGRES_PASSWORD"], safe=""))'
)"
DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${pass_enc}@postgresql:5432/${POSTGRES_DB}"

write_kv_compose IMAGE_PREFIX "$IMAGE_PREFIX"
write_kv_compose IMAGE_TAG "$IMAGE_TAG"
write_kv_compose COMPOSE_PROJECT_NAME "$COMPOSE_PROJECT_NAME"

write_kv_compose POSTGRES_USER "$POSTGRES_USER"
write_kv_compose POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
write_kv_compose POSTGRES_DB "$POSTGRES_DB"
write_kv_compose DATABASE_URL "$DATABASE_URL"
write_kv_compose REDIS_URL "$REDIS_URL"

write_kv_compose NGINX_PORT "$NGINX_PORT"
write_kv_compose NGINX_BIND "$NGINX_BIND"
write_kv_compose ACCESS_VIA_DOMAIN "$ACCESS_VIA_DOMAIN"
write_kv_compose APP_DOMAIN "$APP_DOMAIN"
write_kv_compose APP_PUBLIC_URL "$APP_PUBLIC_URL"
write_kv_compose HEALTHCHECK_URL "$HEALTHCHECK_URL"

write_kv_compose DATA_PATH "$DATA_PATH"

write_kv_compose TG_TOKEN "$TG_TOKEN"
write_kv_compose TG_PROXY_URL "$TG_PROXY_URL"
write_kv_compose API_BASE "$API_BASE"

chmod 600 "$ENV_FILE"
