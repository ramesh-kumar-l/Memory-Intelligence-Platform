# Single-process image matching MIP's single-writer SQLite model (ADR-0007).
# Do not run with --workers > 1: the in-memory rate limiter and the SQLite
# writer are both single-process by design (22-deployment.md).
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY mip ./mip

RUN pip install --no-cache-dir .

ENV MIP_DB_PATH=/data/mip.db
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/v1/health').status == 200 else 1)"

CMD ["uvicorn", "mip.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
