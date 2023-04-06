FROM python:3.11-slim-bullseye as base
ARG API_ENV
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
WORKDIR /app

FROM base as builder
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.4.2
RUN pip install poetry==${POETRY_VERSION}
COPY ./app/pyproject.toml ./app/poetry.lock* /app/
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-root --no-ansi --no-interaction  \
    $(if [ "${API_ENV}" = "prod" ]; then echo "only main";fi)
COPY ./app /app
RUN poetry build && poetry run pip install --no-deps dist/*.whl

FROM python:3.11-slim-bullseye as final
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED 1
#RUN set -ex \
#    && apt-get update \
#    && apt-get upgrade -y \
#RUN set -ex apt-get autoremove -y \
#    && apt-get clean -y \
#    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN addgroup --system app && adduser --system --group app
#ENV PYTHONPATH=/app
COPY --from=builder /app/.venv ./.venv
COPY app/run.sh /app/prestart.sh ./
RUN chown -R app:app /app/
RUN chmod +x run.sh
USER app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["./run.sh"]
