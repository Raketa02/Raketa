# ----------------------------------------------------------------------------
# Raketa backend — developer & deployment helpers.
# Run every target from `backend/`. Repo-wide helpers live in ../Makefile.
# Override any variable on the command line:
#   make ecr-push AWS_REGION=us-east-1 ECR_REPOSITORY=my-repo
# ----------------------------------------------------------------------------
COMPOSE_LOCAL ?= docker compose -f docker-compose-local.yml
IMAGE_NAME  ?= raketa_api
TAG         ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

AWS_REGION       ?= eu-north-1
AWS_ACCOUNT_ID   ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REPOSITORY   ?= raketa-api
ECR_URI          ?= $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPOSITORY)
ECS_CLUSTER      ?= raketa-cluster
ECS_SERVICE      ?= raketa-service

.PHONY: help install test lint lint-imports format typecheck check test-gates openapi \
        gen-walkthroughs gen-cohort \
        build-dev up down logs ps shell migrate seed seed-host \
        rebuild-candidate-index rebuild-candidate-index-host \
        photo-flag-rate photo-flag-rate-host \
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

# `scripts` as well as `app`: the judged-pairings harness runs the engine over a
# spec and writes tables back into it, and an implicit `Any` in the machine that
# derives a Fit is the same defect there as it is one directory over.
typecheck:         ## mypy
	poetry run mypy app scripts

check: lint lint-imports typecheck test  ## the full local gate (matches CI)

# The three walkthroughs are golden files at the pure seam: a fixed population, a
# fixed clock, a fixed ruleset and the complete expected answer. **A diff is a
# design change and must be argued for in the pull request** — which is the whole
# point, because it makes a weight change visible instead of quiet. This target
# rewrites them; it is never run by CI.
gen-walkthroughs:  ## rewrite the matchmaking walkthrough golden files
	UPDATE_GOLDEN=1 poetry run pytest tests/unit/test_matchmaking_walkthroughs.py -q

# The seed cohort's population, generated from a seed and committed as a file
# (app/seeds/cohort.json). **Inputs only** — no level, no uncertainty and no
# band, because those are the engine's answers and a committed copy of an answer
# is a number nothing keeps honest. A diff here is a change to the fixture every
# Play screen is developed against, and it is readable per member because every
# draw is keyed off that member's handle.
gen-cohort:        ## rewrite the seed cohort's committed population
	poetry run python -m scripts.gen_cohort

## ----- API contract
## One document per surface. `openapi.player.json` is what the client generates
## its wire types from; `openapi.dev.json` is the dev console's one path and has
## no client at all, which is why it is gated by a freshness check at the
## repository root (`make contract-freshness`) rather than by the drift check.
openapi:           ## emit the API contracts (openapi.player.json, openapi.dev.json)
	poetry run python -m app.api.contract

## ----- local docker
build-dev:         ## build dev image
	$(COMPOSE_LOCAL) build

up:                ## bring up the dev stack (Postgres 17 + API + MinIO + photo-review + Redis)
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

## ----- seed data
## Deterministic accounts, created by executing the same use cases a request
## executes (app/seeds/). Needs the schema to exist — `make up` migrates on
## start. The production guard is in the seed module and runs on import, not
## here: a make target is not what runs inside a container.
seed:              ## seed deterministic dev accounts into the running stack's database
	$(COMPOSE_LOCAL) exec api python -m app.seeds

seed-host:         ## the same seed from the host — needs .env, like host-run uvicorn
	poetry run python -m app.seeds

## ----- the candidate index (docs/adr/0110)
## The index is a projection of the event log, so a corrupt one is a command and
## not an incident: this empties the tables and folds the whole log back in.
## There is deliberately no admin route — a button that drops and rebuilds an
## index is a button eventually pressed in the wrong place.
rebuild-candidate-index:  ## rebuild the candidate index from the event log, in the running stack
	$(COMPOSE_LOCAL) exec api python -m app.modules.matchmaking.infrastructure.rebuild_cli

rebuild-candidate-index-host: ## the same rebuild from the host — needs .env, like seed-host
	poetry run python -m app.modules.matchmaking.infrastructure.rebuild_cli

## ----- the on-court threshold (#316)
## Read-only. Every verdict recorded the similarity vector it was taken from, so
## the flag rate at a candidate line is arithmetic over stored object metadata —
## no image is re-scored, nothing is written and the sidecar is not asked. The
## default is a twentieth-interval sweep; `make photo-flag-rate THRESHOLDS="0.55
## 0.6"` asks about particular lines instead.
photo-flag-rate:   ## the on-court flag rate at each candidate threshold, from stored notes
	$(COMPOSE_LOCAL) exec api python -m app.modules.player_profile.infrastructure.flag_rate_cli $(THRESHOLDS)

photo-flag-rate-host: ## the same reading from the host — needs .env, like seed-host
	poetry run python -m app.modules.player_profile.infrastructure.flag_rate_cli $(THRESHOLDS)

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
