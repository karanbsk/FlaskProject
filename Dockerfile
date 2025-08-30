#Dockerfile
# ---- builder: install core dependencies ----
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install prod dependencies into /install
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

COPY . /app

# ---- dev: development image ----
FROM builder AS dev

# Install dev packages into /install
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt 

ENV PATH=/install/bin:$PATH \
    FLASK_APP=wsgi \
    FLASK_RUN_HOST=0.0.0.0


WORKDIR /app

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]

# ---- prod: production image ----
FROM python:3.11-slim AS prod

ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependencies and app from builder
COPY --from=builder /install /usr/local
#COPY --from=builder /app /app

# Copy only the folders/files needed for prod
COPY app/ ./app/
COPY wsgi.py .
COPY config.py .
COPY migrations/ ./migrations/

# Add non-root user
RUN useradd -u 1000 --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
# Entrypoint script to run migrations and start the app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
ENV GUNICORN_WORKERS=3
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app", "--workers", "${GUNICORN_WORKERS}", "--threads", "2"]
