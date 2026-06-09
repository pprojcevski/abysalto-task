#  ╭──────────────────────────────────────────────────────────╮
#  │                        Base - Stage                      │
#  ╰──────────────────────────────────────────────────────────╯

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

# adding non root user "worker", with no password, uid needed for workflow
RUN adduser \
    --disabled-password \
    --uid 4711 \
    worker \
    && mkdir /code \
    && chown worker:worker /code

RUN apt-get update && apt-get install -y \
    wkhtmltopdf=0.12.6-2+b1 \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=true
WORKDIR /code

#  ╭──────────────────────────────────────────────────────────╮
#  │                       Build - Stage                      │
#  ╰──────────────────────────────────────────────────────────╯
FROM base AS build

USER worker

WORKDIR /code
COPY --chown=worker:worker pyproject.toml ./
COPY --chown=worker:worker uv.lock ./

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

COPY --chown=worker:worker . ./

# Sync the project
RUN --mount=type=cache,target=/worker/.cache/uv \
    uv sync --frozen --compile-bytecode

#  ╭──────────────────────────────────────────────────────────╮
#  │                     Runtime - Stage                      │
#  ╰──────────────────────────────────────────────────────────╯
FROM base AS runtime
ENV PATH="/code/.venv/bin:$PATH"

COPY --from=build /code/.venv /code/.venv
COPY --from=build --chown=worker:worker /code /code

RUN chmod +x /code/scripts/entrypoint.sh

ENTRYPOINT []
CMD ["uv", "run","fastapi", "run", "/code/app/main.py", "--port", "8080", "--host", "0.0.0.0", "--proxy-headers"]
