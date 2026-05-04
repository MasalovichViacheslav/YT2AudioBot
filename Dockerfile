# Stage 1: builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY . .

RUN uv sync --frozen --no-dev


# Stage 2: runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/bot ./bot
COPY --from=builder /app/config ./config
COPY --from=builder /app/services ./services

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /app/temp

CMD ["python", "-m", "bot.main"]