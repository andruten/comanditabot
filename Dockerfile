FROM python:3.9-slim-buster

RUN mkdir /app

WORKDIR /app

COPY ./comandita.py /app/
COPY ./commands/ /app/commands/
COPY ./tests/ /app/tests/
COPY ./*requirements.txt /app/
COPY pytest.ini /app/

ARG REQS_FILE
RUN pip install --upgrade pip && \
    pip install -r /app/${REQS_FILE:-"requirements.txt"}

CMD python comandita.py
