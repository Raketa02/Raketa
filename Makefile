# ----------------------------------------------------------------------------
# Base Backend — developer & deployment helpers
# Override any variable on the command line:
#   make ecr-push AWS_REGION=us-east-1 ECR_REPOSITORY=my-repo
# ----------------------------------------------------------------------------
COMPOSE_DEV ?= docker compose -f docker-compose-dev.yml
IMAGE_NAME  ?= basebackend_api
TAG         ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

AWS_REGION       ?= eu-north-1
AWS_ACCOUNT_ID   ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REPOSITORY   ?= basebackend-api
ECR_URI          ?= $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPOSITORY)
ECS_CLUSTER      ?= basebackend-cluster
ECS_SERVICE      ?= basebackend-service

.PHONY: help install test lint format \
        build-dev up down logs ps shell migrate \
        build-prod ecr-login ecr-push ecs-deploy

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ----- local python
install:           ## install poetry deps
	poetry install

test:              ## run pytest
	poetry run pytest src/application/tests -q

lint:              ## ruff check
	poetry run ruff check .

format:            ## ruff format
	poetry run ruff format .

## ----- local docker
build-dev:         ## build dev image
	$(COMPOSE_DEV) build

up:                ## bring up the dev stack
	$(COMPOSE_DEV) up -d

down:              ## tear down the dev stack
	$(COMPOSE_DEV) down

logs:              ## tail api logs
	$(COMPOSE_DEV) logs -f api

ps:                ## list running services
	$(COMPOSE_DEV) ps

shell:             ## bash into the api container
	$(COMPOSE_DEV) exec api bash

migrate:           ## run alembic upgrade head inside the api container
	$(COMPOSE_DEV) exec api alembic upgrade head

## ----- production / ECR / ECS
build-prod:        ## build the production image (tagged for ECR)
	docker build -f docker/api/Dockerfile.prod -t $(IMAGE_NAME):$(TAG) -t $(ECR_URI):$(TAG) -t $(ECR_URI):latest .

ecr-login:         ## docker login to ECR
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

ecr-push: ecr-login build-prod ## push prod image to ECR
	docker push $(ECR_URI):$(TAG)
	docker push $(ECR_URI):latest

ecs-deploy:        ## force a new ECS deployment (rolls service onto latest task def)
	aws ecs update-service --cluster $(ECS_CLUSTER) --service $(ECS_SERVICE) --force-new-deployment --region $(AWS_REGION)
	aws ecs wait services-stable --cluster $(ECS_CLUSTER) --services $(ECS_SERVICE) --region $(AWS_REGION)
