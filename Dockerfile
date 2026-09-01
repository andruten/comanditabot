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

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=node /usr/local/bin/node /usr/local/bin/node

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Copy code
COPY . .

CMD ["python", "-m", "comandita"]
