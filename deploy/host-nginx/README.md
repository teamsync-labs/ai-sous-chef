# Хостовый nginx (вне compose)

Каталог уезжает на VPS с rsync в `$SERVER_PATH/deploy/host-nginx/`.
Конфиг в `/etc/nginx/...` **не** подхватывается сам — копируем вручную.

## Файлы

| Файл | Назначение |
|------|------------|
| `ai-sous-chef-prod.conf` | vhost → `127.0.0.1:3101` |
| `maintenance.html` | страница 502/503/504 на время recreate стека |

## Порядок на VPS (root)

### 1. HTTP vhost (сейчас)

Нужны: пакеты `nginx` (хостовый), уже открытые `80`/`443` в UFW.

```bash
# после деплоя, чтобы maintenance.html был на диске:
install -d -m 755 /etc/nginx/sites-available /etc/nginx/sites-enabled
cp "$SERVER_PATH/deploy/host-nginx/ai-sous-chef-prod.conf" \
  /etc/nginx/sites-available/ai-sous-chef-prod.conf
ln -sfn /etc/nginx/sites-available/ai-sous-chef-prod.conf \
  /etc/nginx/sites-enabled/ai-sous-chef-prod.conf
nginx -t && systemctl reload nginx
```

`$SERVER_PATH` = значение GitHub Variable (каталог кода prod).

Проверка:

```bash
curl -fsS -H 'Host: ai-sous-chef.ru' http://127.0.0.1/health
# снаружи: http://ai-sous-chef.ru/health → {"db":"ok"}
```

Если ISPmanager держит `listen <IP>:80` на чужом vhost — в нашем conf тоже
пропиши `listen <IP>:80` (не голый `listen 80`), иначе запросы уйдут в default_server.

### 2. TLS (certbot)

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d ai-sous-chef.ru -d www.ai-sous-chef.ru
```

После успеха скопируй обновлённый `/etc/nginx/sites-available/ai-sous-chef-prod.conf`
обратно в репо (`deploy/host-nginx/`) — источник правды с SSL-блоками.

### 3. Закрыть прямой доступ по порту compose

GitHub Environment `prod`: `ACCESS_VIA_DOMAIN=true` → Redeploy.
Compose-nginx станет на `127.0.0.1:3101`. Healthcheck — `https://ai-sous-chef.ru/health`.
