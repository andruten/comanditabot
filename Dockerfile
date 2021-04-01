FROM python:3.9-slim-buster

RUN mkdir /app

WORKDIR /app

# Requirements
COPY ./requirements/ /app/requirements/
ARG REQS_FILE
RUN pip install --upgrade pip
RUN pip install -r /app/requirements/${REQS_FILE:-"requirements.txt"}

# Copy code
COPY ./comandita.py /app/
COPY ./commands/ /app/commands/
COPY ./clients/ /app/clients/
COPY ./tests/ /app/tests/
COPY pytest.ini /app/

CMD python comandita.py
