.PHONY:

check_env:
ifeq ("$(wildcard .env)","")
	cp env.sample .env
endif

start: check_env
	docker run --env-file .env -ti comanditabot:production

start_dev: check_env
	docker run --env-file .env -ti comanditabot:development

build:
	docker build . -t comanditabot:production

build_dev: check_env
	docker build --build-arg REQS_FILE=dev-requirements.txt . -t comanditabot:development

test: check_env
	docker run --env-file .env -ti comanditabot:development pytest
