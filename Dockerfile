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

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

# Copy code
COPY . .

CMD ["python", "-m", "comandita"]
