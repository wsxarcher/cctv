ARG POETRY_VERSION=1.5.1
ARG BASE_IMAGE=python:3.11-bookworm

FROM $BASE_IMAGE as builder
ARG POETRY_VERSION
RUN pip install poetry==$POETRY_VERSION

ARG DEBIAN_FRONTEND=noninteractive

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /final

COPY pyproject.toml ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

FROM $BASE_IMAGE
ARG POETRY_VERSION
RUN pip install poetry==$POETRY_VERSION

WORKDIR /final

ENV VIRTUAL_ENV="/final/.venv"
ENV PATH="/final/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder /final/pyproject.toml ./pyproject.toml

COPY project ./project

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

RUN poetry install

CMD ["start"]