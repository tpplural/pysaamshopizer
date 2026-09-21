# MS-01 reference-data — Python 3.12 / FastAPI
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations

RUN pip install --upgrade pip && pip install .

EXPOSE 8001

# Alembic upgrade head runs on startup (dev/test); the app also runs the one-time seed when empty.
CMD ["uvicorn", "reference_data.main:app", "--host", "0.0.0.0", "--port", "8001"]
