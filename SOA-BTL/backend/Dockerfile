# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OPENAPI_SPEC_DIR=/app/backend/openapi/openapi_modular/openapi_modular

WORKDIR /app/backend

RUN useradd --create-home --uid 10001 app
COPY --chown=app:app backend/ ./
RUN python -m pip install --no-cache-dir -r requirements.txt

USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/docs/', timeout=3).close()"]

CMD ["waitress-serve", "--listen=0.0.0.0:8000", "--threads=4", "wsgi:app"]

FROM base AS test
USER root
RUN python -m pip install --no-cache-dir -r requirements-dev.txt
USER app
HEALTHCHECK NONE
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp=/tmp/student-assistant-tests"]

FROM base AS runtime
