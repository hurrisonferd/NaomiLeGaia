FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000 \
    MEMCONOS_DB_PATH=/data/memconos.db

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY gaiaos_api.py ./
COPY gaiaos_context_runtime.py ./
COPY gaiaos_app.py ./
COPY memcon_runtime.py ./
COPY memcon_entrypoint.py ./

EXPOSE 10000

CMD ["sh", "-c", "uvicorn memcon_entrypoint:app --host 0.0.0.0 --port ${PORT:-10000}"]
