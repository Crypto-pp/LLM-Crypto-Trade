# Stage 1: Builder
FROM python:3.11-slim-bullseye AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim-bullseye

RUN useradd -m -u 1000 alerter

COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=alerter:alerter . .

USER alerter

CMD ["python", "-m", "src.workers.alert_worker"]
