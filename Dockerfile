FROM python:3.11-slim-bullseye

RUN mkdir /opt/app \
    && mkdir /opt/requirements \
    && addgroup --gid 4000 apprunner \
    && adduser --system --disabled-password --disabled-login --gecos "" --gid 4000 --uid 4000 apprunner \
    && chown -R apprunner:apprunner /opt/app \
    && chown -R apprunner:apprunner /opt/requirements \
    && chsh -s /bin/false apprunner

# Requirements
RUN pip install --upgrade pip

USER apprunner

WORKDIR /opt/app

ENV PATH="/home/apprunner/.local/bin:${PATH}"
COPY ./requirements/ /opt/requirements/
ARG requirements
RUN pip install -r /opt/requirements/${requirements:-"pro"}.txt

# Copy code
COPY . .

CMD python -m comandita
