.PHONY:
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
DOCKER := docker

check_env:
ifeq ("$(wildcard .env)","")
	cp env.sample .env
endif

start: check_env ## Start all or c=<name> containers in FOREGROUND
	@$(DOCKER) --env-file .env -ti comanditabot

build: check_env ##
	@$(DOCKER) build . -t comanditabot:production

build_dev: check_env ##
	@$(DOCKER) build --build-arg REQS_FILE=dev-requirements.txt . -t comanditabot:development

test: check_env
	@$(DOCKER) run --env-file .env -ti comanditabot:development pytest
