FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# ── Development ────────────────────────────────────────────────────────────────
FROM base AS development

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]

# ── Production ─────────────────────────────────────────────────────────────────
FROM base AS production

RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
