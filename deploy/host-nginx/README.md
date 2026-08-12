# Хостовый nginx (вне compose)

Каталог попадает на VPS через rsync в `$SERVER_PATH/deploy/host-nginx/`.
Конфиг в `/etc/nginx/...` сам не подхватывается — копирование в sites-available вручную.

## Файлы

| Файл | Назначение |
|------|------------|
| `ai-sous-chef-prod.conf` | vhost → `127.0.0.1:3101` |
| `maintenance.html` | страница 502/503/504 на время recreate стека |

## Порядок на VPS (root)

### 1. HTTP vhost

Требования: хостовый `nginx`, в UFW открыты `80`/`443`. Файлы на диске — после деплоя (rsync).

```bash
install -d -m 755 /etc/nginx/sites-available /etc/nginx/sites-enabled
cp "$SERVER_PATH/deploy/host-nginx/ai-sous-chef-prod.conf" \
  /etc/nginx/sites-available/ai-sous-chef-prod.conf
ln -sfn /etc/nginx/sites-available/ai-sous-chef-prod.conf \
  /etc/nginx/sites-enabled/ai-sous-chef-prod.conf
nginx -t && systemctl reload nginx
```

`$SERVER_PATH` — значение GitHub Variable (каталог кода prod).

Проверка:

```bash
curl -fsS -H 'Host: ai-sous-chef.ru' http://127.0.0.1/health \
  || curl -fsS -H 'Host: ai-sous-chef.ru' http://SERVER_IP/health
# снаружи: http://ai-sous-chef.ru/health → {"db":"ok"}
```

Если ISPmanager держит `listen <IP>:80` на чужом vhost — в conf этого проекта тоже
нужен `listen <IP>:80` (не голый `listen 80`), иначе запросы уходят в default_server.

### 2. TLS (certbot)

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d ai-sous-chef.ru -d www.ai-sous-chef.ru
```

После выпуска сертификата обновлённый `/etc/nginx/sites-available/ai-sous-chef-prod.conf`
возвращается в репо (`deploy/host-nginx/`) как источник правды с SSL-блоками.
У www→apex редирект должен быть на **https** (certbot иногда оставляет `http://`).

### 3. Закрыть прямой доступ по порту compose

В GitHub Environment `prod` выставить `ACCESS_VIA_DOMAIN=true` и выполнить Redeploy.
Compose-nginx слушает `127.0.0.1:3101`. Healthcheck — `https://ai-sous-chef.ru/health`.
