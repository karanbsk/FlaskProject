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
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt
COPY . .

ENV PATH=/install/bin:$PATH \
    FLASK_APP=wsgi \
    APP_CONFIG=development

WORKDIR /app

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]

# ---- prod: production image ----
FROM python:3.11-slim AS prod

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependencies and app from builder
COPY --from=builder /install /usr/local
#COPY --from=builder /app /app

# Copy only the folders/files needed for prod
COPY app/ ./app/
COPY wsgi.py .
COPY config.py .

# Add non-root user
RUN useradd -u 1000 --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app", "--workers", "3", "--threads", "2"]
