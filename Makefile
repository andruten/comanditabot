DOCKER := docker

.PHONY:

check_env:
ifeq ("$(wildcard .env)","")
	cp env.sample .env
endif

run: check_env build
	@$(DOCKER) run -d --name comanditabot --restart on-failure:3 --env-file .env comanditabot:latest

run_detached: check_env build
	@$(DOCKER) run --rm -d --restart on-failure:3 --env-file .env -ti comanditabot:latest

run_dev: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -ti comanditabot:latest

build:
	@$(DOCKER) build . -t comanditabot:latest

build_dev: check_env
	@$(DOCKER) build --build-arg requirements=dev . -t comanditabot:latest

bash: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -ti comanditabot:latest bash

lint: check_env build_dev
	@$(DOCKER) run --rm --env-file .env comanditabot:latest flake8 .

test: check_env build_dev
	@$(DOCKER) run --rm --env-file .env comanditabot:latest python -m pytest .
