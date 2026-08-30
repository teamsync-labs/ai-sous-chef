FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY handlers ./handlers
COPY middlewares ./middlewares
COPY keyboards ./keyboards
COPY states ./states
COPY services ./services
COPY utils ./utils

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]
