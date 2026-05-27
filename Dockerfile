FROM linuxserver/unrar:latest AS unrar
FROM python:3.14-alpine AS base
WORKDIR /app
RUN apk --no-cache upgrade && apk --no-cache add lftp

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.16-python3.14-alpine /usr/local/bin/uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM base AS release
# Copy compiled unrar
COPY --from=unrar /usr/bin/unrar-alpine /usr/bin/unrar
# Copy the installed python dependencies from the builder
COPY --from=builder /app/.venv /app/.venv
# Copy the app
COPY --chown=1000:1000 downloader ./downloader
ENV PATH="/app/.venv/bin:$PATH"

USER 1000:1000
CMD ["python", "-m", "downloader.main"]
