Для запуска проекта потребуется python 3.11+

Все команды вводим в терминале/командной строке

## Установка Базы Данных (БД) Postgres
1. Скачиваем Docker Compose по ссылке https://docs.docker.com/get-started/get-docker/
2. Устанавливаем указанное ПО по инструкции внутри программы
3. Проверяем установку в командной строке
```bash
docker-compose --version
```
Должно быть что-то подобное `Docker Compose version v*.*.*`
4. Запускаем Базу Данных
```bash
docker-compose up -d postgresql
```

Для остановки Базы Данных:
```bash
docker-compose down postgresql
```

## Поднятие FastAPI сервера

1. Устанавливаем виртуальное окружение
```bash
python -m venv .venv
```
2. Активировать виртуальное окружение
На Windows:
```bash
.\.venv\Scripts\Activate.ps1  
```
На Linux:
```bash
source .venv/bin/activate
```
3. Переходим в папку `backend`
```bash
cd backend
```
4. Устанавливаем зависимости
```bash
pip install -r app/requirements.txt
```
5. В папке app по примеру файла `.env.example` создаем свой файл с названием .env и вставляем туда переменные из `.env.example`
6. Создаем структуру Базы Данных
```bash
alembic upgrade head
```
7. Запускаем сервер
```bash
uvicorn app.main:app --reload
```

Для остановки сервера нажмите `Ctrl + C`

Для открытия документации API:
- Swagger UI: http://localhost:8000/docs