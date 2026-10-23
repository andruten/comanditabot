FROM node:22-bookworm-slim AS node

FROM python:3.14-slim-bookworm AS builder

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Requirements
RUN pip install --upgrade pip

COPY ./requirements/ .
ARG requirements
RUN pip install -r ${requirements:-"pro"}.txt

FROM python:3.14-slim-bookworm

WORKDIR /app

RUN mkdir -p /data

RUN apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Non-root user; /data must be writable for the bot state volume and
# /app for pytest coverage files when the dev image runs the test suite
RUN groupadd --system bot \
    && useradd --system --gid bot --home-dir /app --shell /usr/sbin/nologin bot \
    && chown bot:bot /app /data

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=node /usr/local/bin/node /usr/local/bin/node

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Copy code
COPY . .

USER bot

CMD ["python", "-m", "comandita"]
