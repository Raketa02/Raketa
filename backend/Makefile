# ----------------------------------------------------------------------------
# Rakieta backend — developer & deployment helpers.
# Run every target from `backend/`. Repo-wide helpers live in ../Makefile.
# Override any variable on the command line:
#   make ecr-push AWS_REGION=us-east-1 ECR_REPOSITORY=my-repo
# ----------------------------------------------------------------------------
COMPOSE_LOCAL ?= docker compose -f docker-compose-local.yml
IMAGE_NAME  ?= rakieta_api
TAG         ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

AWS_REGION       ?= eu-north-1
AWS_ACCOUNT_ID   ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REPOSITORY   ?= rakieta-api
ECR_URI          ?= $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPOSITORY)
ECS_CLUSTER      ?= rakieta-cluster
ECS_SERVICE      ?= rakieta-service

.PHONY: help install test lint lint-imports format typecheck check test-gates openapi \
        build-dev up down logs ps shell migrate \
        build-prod ecr-login ecr-push ecs-deploy

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ----- local python
install:           ## install poetry deps
	poetry install

test:              ## run pytest
	poetry run pytest tests -q

lint:              ## ruff check
	poetry run ruff check .

lint-imports:      ## enforce the engines/kernel import boundaries (.importlinter)
	poetry run lint-imports

test-gates:        ## verify the kernel/engines purity gates still fire
	bash scripts/test-purity-gates.sh

format:            ## ruff format
	poetry run ruff format .

typecheck:         ## mypy
	poetry run mypy app

check: lint lint-imports typecheck test  ## the full local gate (matches CI)

## ----- API contract
openapi:           ## emit the contract as two documents (player + club)
	poetry run python -m app.api.contract

## ----- local docker
build-dev:         ## build dev image
	$(COMPOSE_LOCAL) build

up:                ## bring up the dev stack (Postgres 17 + API + Redis)
	$(COMPOSE_LOCAL) up -d

down:              ## tear down the dev stack
	$(COMPOSE_LOCAL) down

logs:              ## tail api logs
	$(COMPOSE_LOCAL) logs -f api

ps:                ## list running services
	$(COMPOSE_LOCAL) ps

shell:             ## bash into the api container
	$(COMPOSE_LOCAL) exec api bash

migrate:           ## run alembic upgrade head inside the api container
	$(COMPOSE_LOCAL) exec api alembic upgrade head

## ----- production / ECR / ECS
## DORMANT — AWS deployment is not in use; development is entirely local
## (see ../docs/adr/0010-local-first-development-aws-deferred.md). These targets
## are kept working for when it resumes. They are blocked for agent sessions by
## .claude/hooks/guard-bash.sh and need a human plus a configured AWS account.
## Reactivating starts with reviewing taskdef.json against app/core/config.py —
## dormant infra drifts from the code silently.
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
