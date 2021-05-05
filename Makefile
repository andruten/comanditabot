.PHONY:

check_env:
ifeq ("$(wildcard .env)","")
	cp env.sample .env
endif

run: check_env build
	docker run --rm --env-file .env -ti comanditabot:production

run_detached: check_env build
	docker run --rm -d --restart on-failure:3 --env-file .env -ti comanditabot:production

run_dev: check_env build_dev
	docker run --rm --env-file .env -ti comanditabot:development

build:
	docker build . -t comanditabot:production

build_dev: check_env
	docker build --build-arg REQS_FILE=dev-requirements.txt . -t comanditabot:development

push:
	docker build -t andruten/comanditabot:production .
	docker push andruten/comanditabot:production

bash: check_env build_dev
	docker run --rm --env-file .env -ti comanditabot:development bash

test: check_env build_dev
	docker run --rm --env-file .env -ti comanditabot:development python -m pytest .
