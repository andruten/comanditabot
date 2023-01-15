FROM python:3.11-slim-bullseye

RUN mkdir /app \
    && addgroup --gid 4000 apprunner \
    && adduser --system --disabled-password --disabled-login --gecos "" --gid 4000 --uid 4000 apprunner \
    && chown -R apprunner:apprunner /app \
    && chsh -s /bin/false apprunner

# Requirements
RUN pip install --upgrade pip

USER apprunner

WORKDIR /app

ENV PATH="/home/apprunner/.local/bin:${PATH}"
COPY ./requirements/ /app/requirements/
ARG requirements
RUN pip install -r /app/requirements/${requirements:-"pro"}.txt

# Copy code
COPY . .

CMD python -m comandita
