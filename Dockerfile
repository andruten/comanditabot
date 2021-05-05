FROM python:3.9-slim-buster

RUN mkdir /app \
    && addgroup --gid 4000 apprunner \
    && adduser --system --disabled-password --disabled-login --gecos "" --gid 4000 --uid 4000 apprunner \
    && chown -R apprunner:apprunner /app \
    && chsh -s /bin/false apprunner

USER apprunner

WORKDIR /app

# Requirements
COPY ./requirements/ /app/requirements/
ARG REQS_FILE
RUN pip install --upgrade pip
RUN pip install -r /app/requirements/${REQS_FILE:-"requirements.txt"}

# Copy code
COPY ./comandita.py /app/
COPY ./commands/ /app/commands/
COPY ./messages/ /app/messages/
COPY ./clients/ /app/clients/
COPY ./tests/ /app/tests/
COPY pytest.ini /app/
COPY .coveragerc /app/

CMD python comandita.py
