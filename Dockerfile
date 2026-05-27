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

RUN apt-get update && apt-get install -y --no-install-recommends curl unzip \
    && curl -fsSL https://deno.land/install.sh | sh \
    && apt-get purge -y curl unzip && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

ENV DENO_INSTALL="/root/.deno"
ENV PATH="$DENO_INSTALL/bin:/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/bot ./bot
COPY --from=builder /app/config ./config
COPY --from=builder /app/services ./services
COPY --from=builder /app/models ./models
COPY --from=builder /app/utils ./utils

RUN mkdir -p /app/temp

CMD ["python", "-m", "bot.main"]