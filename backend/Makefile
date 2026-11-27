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

.PHONY: help install test test-affected test-group test-durations split-partition coverage lint lint-imports format typecheck check test-gates openapi \
        gen-cohort \
        build-dev up down down-v logs ps shell migrate seed seed-host sim-location \
        photo-flag-rate photo-flag-rate-host rankings-rebuild rankings-rebuild-host \
        discovery-rebuild discovery-rebuild-host \
        build-prod ecr-login ecr-push ecs-deploy

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

## ----- local python
install:           ## install poetry deps
	poetry install

# The suite runs in parallel (ADR-0181): one worker per core, work-stealing
# because durations are uneven — a handful of tests (the seed command, the cohort,
# the runs under two hash seeds) take 10–60 s, most take milliseconds. WORKERS=0 runs serially, in-process and in collection order, which
# is how an order-dependent failure is chased; WORKERS=2 is a CI runner's size.
# PYTEST_ARGS goes on the end: `make test PYTEST_ARGS=-x`.
WORKERS   ?= auto
XDIST     := -n $(WORKERS) --dist worksteal

test:              ## run pytest, one worker per core (WORKERS=0 is serial; no coverage)
	poetry run pytest tests -q $(XDIST) $(PYTEST_ARGS)

# The inner loop, never the gate (ADR-0181 §2): pytest-testmon runs only the
# tests whose recorded dependencies changed since its last run, and re-runs the
# ones that failed. The first run records every test; the data is .testmondata,
# which git ignores. `-p no:cov` switches pytest-cov off, so testmon's tracer is
# the only one in the run: a `--cov` that reaches this target is refused, not
# traced twice.
# It cannot see a test that reads the source as text, a JSON spec or fixture file,
# or code run in a subprocess — so `make test` still runs at the end of every ticket.
test-affected:     ## only the tests the change since the last such run can affect (testmon)
	poetry run pytest tests -q -p no:cov --testmon $(XDIST) $(PYTEST_ARGS)

# Balanced groups for CI's shards (ADR-0181 §5; #489 runs one per runner): the
# suite split into SPLITS groups by the durations committed in .test_durations,
# with xdist inside each. `least_duration`
# deals the longest tests first, each to the lightest group, so the seed tests
# spread across shards instead of sharing one. A test the file does not know gets
# the average, so a stale file unbalances the groups and never drops a test.
DURATIONS ?= .test_durations
SPLIT     := --splitting-algorithm least_duration --durations-path $(DURATIONS)

test-group:        ## run group GROUP of SPLITS, in parallel — one CI shard's share
	@[ -n "$(GROUP)" ] && [ -n "$(SPLITS)" ] || { echo "usage: make test-group GROUP=<k> SPLITS=<N>" >&2; exit 2; }
	poetry run pytest tests -q $(XDIST) $(SPLIT) --splits $(SPLITS) --group $(GROUP) $(PYTEST_ARGS)

# Commit the result. `--clean-durations` drops the tests that no longer exist.
# Under xdist every worker's timings reach the controller, which writes last.
test-durations:    ## re-record .test_durations from a whole run, for balanced groups
	poetry run pytest tests -q $(XDIST) --store-durations --clean-durations --durations-path $(DURATIONS)

split-partition:   ## show the groups for SPLITS=2 and 3 add up to the suite, stale file too
	poetry run python -m scripts.split_partition $(DURATIONS)

# Coverage is off by default: it makes a run 2.4x slower and nothing gates on it
# (ADR-0181). This measures it on demand — the whole suite, the term-missing
# report on screen, and coverage.xml, which CI can keep as an artifact.
coverage:          ## run pytest with coverage over app/ (term-missing + coverage.xml)
	poetry run pytest tests -q --cov=app --cov-report=term-missing --cov-report=xml

lint:              ## ruff check
	poetry run ruff check .

lint-imports:      ## enforce the engines/kernel import boundaries (.importlinter)
	poetry run lint-imports

test-gates:        ## verify the kernel/engines purity gates still fire
	bash scripts/test-purity-gates.sh

format:            ## ruff format
	poetry run ruff format .

# `scripts` as well as `app`: the cohort generator, the shard split and its
# arithmetic, and the taskdef proof are code the build leans on, and a type
# error there is a gate that silently stops checking.
typecheck:         ## mypy
	poetry run mypy app scripts

check: lint lint-imports typecheck test  ## the full local gate (matches CI)

# The seed cohort's population, generated from a seed and committed as a file
# (app/seeds/cohort.json). **Inputs only** — no level, no uncertainty and no
# band, because those are the engine's answers and a committed copy of an answer
# is a number nothing keeps honest. A diff here is a change to the fixture every
# Play screen is developed against, and it is readable per member because every
# draw is keyed off that member's handle.
gen-cohort:        ## rewrite the seed cohort's committed population
	poetry run python -m scripts.gen_cohort

## ----- API contract
## One document per surface. `openapi.player.json` is what the player app
## generates its wire types from, `openapi.club.json` the club website's and
## `openapi.public.json` the public site's (docs/adr/0187 §5); `openapi.dev.json`
## is the games test console's and has no client at all, which is why it is
## gated by a freshness check at the repository root (`make contract-freshness`)
## rather than by the drift check.
openapi:           ## emit the API contracts (openapi.{player,dev,club,public}.json)
	poetry run python -m app.api.contract

## ----- local docker
build-dev:         ## build dev image
	$(COMPOSE_LOCAL) build

up:                ## bring up the dev stack (Postgres 17 + API + MinIO + photo-review + Redis)
	$(COMPOSE_LOCAL) up -d

down:              ## tear down the dev stack
	$(COMPOSE_LOCAL) down

down-v:            ## tear down the dev stack AND drop its volumes — a fresh store next `make up`
	$(COMPOSE_LOCAL) down -v

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
##
## It waits for the API to report healthy before writing anything. Every job's
## first run is at startup, and two of them rewrite what a seed has just
## written: the rating catch-up moves the played history's Levels, and the
## photo backfill reviews the photograph the seed declares nobody looked at.
## Seeding straight after `make up` raced both (2026-10-05). For the same
## reason, a database the API has started on since its seed cannot be seeded
## again. `make down-v && make up && make seed` is the reset.
##
## Then it stops the API and seeds from a one-off container of the same image,
## so nothing writes beside it: the outbox worker and the jobs that write
## proposals every few seconds deadlocked the seed on the Stripe sandbox, whose
## calls hold each transaction open for a second or more (2026-10-20). The seed
## runs its use cases in process and never calls the API. The API starts again
## whatever the seed answered.
seed:              ## seed deterministic dev accounts into the running stack's database
	@api=$$($(COMPOSE_LOCAL) ps -q api); \
	if [ -z "$$api" ]; then echo "The API is not running. make up first." >&2; exit 1; fi; \
	for _ in $$(seq 120); do \
	  [ "$$(docker inspect -f '{{.State.Health.Status}}' $$api)" = healthy ] && exit 0; \
	  sleep 1; \
	done; \
	echo "The API did not report healthy within 120 s. See make logs." >&2; exit 1
	$(COMPOSE_LOCAL) stop api
	$(COMPOSE_LOCAL) run --rm --no-deps api python -m app.seeds; \
	status=$$?; $(COMPOSE_LOCAL) start api; exit $$status

seed-host:         ## the same seed from the host — needs .env, like host-run uvicorn
	poetry run python -m app.seeds

# Where the seed is centred, as `make seed` will read it: the shell's SEED_CENTRE,
# else .env.docker's, else the reference (London). The value is parsed by the
# seed's own parser below rather than restated here, so the simulator and the
# population cannot be pinned to two different cells.
SEED_CENTRE ?= $(shell grep -E '^SEED_CENTRE=' .env.docker 2>/dev/null | tail -1 | cut -d= -f2-)

sim-location:      ## pin the booted iOS simulator to the seed's centre (SEED_CENTRE, .env.docker, or London)
	@centre=$$(SEED_CENTRE="$(SEED_CENTRE)" poetry run python -c \
	  "from app.seeds.catalog import CENTRE; print(f'{CENTRE.latitude},{CENTRE.longitude}')" 2>/dev/null) \
	  && xcrun simctl location booted set "$$centre" \
	  && echo "iOS simulator pinned to $$centre — the seed's centre. Re-run after every simulator boot."

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

## ----- the ranking (#768)
## Every ranking row folded from every rating stream, as the outbox delivery
## folds one: owed once, to a store that held results before the ranking
## shipped. Running it twice changes nothing.
rankings-rebuild:  ## fold every ranking row from the rating history in the event store
	$(COMPOSE_LOCAL) exec api python -m app.modules.rankings.infrastructure.rebuild_cli

rankings-rebuild-host: ## the same rebuild from the host — needs .env, like seed-host
	poetry run python -m app.modules.rankings.infrastructure.rebuild_cli

discovery-rebuild:  ## write every player-directory entry and current level from the event store
	$(COMPOSE_LOCAL) exec api python -m app.modules.discovery.infrastructure.rebuild_cli

discovery-rebuild-host: ## the same rebuild from the host — needs .env, like seed-host
	poetry run python -m app.modules.discovery.infrastructure.rebuild_cli

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
