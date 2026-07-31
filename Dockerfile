FROM python:3.13-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.13-slim AS runtime

WORKDIR /app

COPY --from=builder /install /usr/local

COPY fastapi_backend ./fastapi_backend

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LITELLM_DROP_PARAMS=true

RUN mkdir -p /app/output/reports /app/output/logos

EXPOSE 8000

CMD ["uvicorn", "fastapi_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
