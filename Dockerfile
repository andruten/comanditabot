FROM python:3.10-slim-bullseye

RUN apt update -qqq && apt install \
      --no-install-recommends --no-install-suggests -y -qqq \
      ffmpeg \
      git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean \
    && mkdir /app \
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

ARG REQS_FILE
RUN pip install -r /app/requirements/${REQS_FILE:-"requirements.txt"}

# Copy code
COPY . .

CMD python -m comandita
