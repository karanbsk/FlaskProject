# Dockerfile.prod (modified - bullseye runtime)
FROM python:3.11-slim AS builder
WORKDIR /src
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# install build deps (builder only)
RUN apt-get update \
 && apt-get install -y --no-install-recommends --only-upgrade build-essential gcc libssl-dev libsqlite3-0 openssl libssl3 || true \
 #&& apt-get install -y --no-install-recommends --only-upgrade libsqlite3-0 openssl libssl3 || true \
 && apt-get purge -y sqlite3 libsqlite3-0 libsqlite3-dev || true \
 && apt-get autoremove -y --purge \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt /src/

RUN python -m pip install --upgrade pip setuptools wheel

RUN python -m pip wheel --wheel-dir=/wheels -r requirements.txt

RUN python -m pip install --no-index --find-links=/wheels -r requirements.txt --target=/install \
 && rm -rf /wheels

COPY . /src

# ----- runtime stage using slim-bullseye -----
FROM python:3.11-slim AS prod
WORKDIR /app

# IMPORTANT: combine update+purge in single RUN (avoids misconfig DS017)
# runtime: remove sqlite if present, upgrade openssl/libssl, cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade build-essential libsqlite3-0 openssl libssl3 || true && \
    apt-get purge -y sqlite3 libsqlite3-0 libsqlite3-dev || true && \
    apt-get autoremove -y --purge && \
    rm -rf /var/lib/apt/lists/*


# Remove python sqlite extension from lib-dynload if present (only do this if your app doesn't need sqlite)
RUN if [ -d /usr/local/lib/python3.11/lib-dynload ]; then \
      rm -f /usr/local/lib/python3.11/lib-dynload/_sqlite3*.so || true; \
    fi

RUN rm -rf /usr/local/lib/python3.11/site-packages/*

# Copy installed python packages (from builder)
COPY --from=builder /install /usr/local/lib/python3.11/site-packages

# Copy app
COPY  --chown=appuser:appuser --from=builder /src/ /app/

RUN rm -rf requirements* .dockerignore* pyproject.toml /app/tests/ pytest*

# Optional: create non-root user & fix perms
RUN useradd --create-home appuser \
 && chown -R appuser:appuser /app /usr/local/lib/python3.11/site-packages
USER appuser

ENV APP_CONFIG=production

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
