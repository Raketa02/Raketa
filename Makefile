# ----------------------------------------------------------------------------
# Raketa monorepo — root helpers.
#
# Each app owns its own commands: backend/Makefile, and the pnpm scripts in
# frontend_player/, frontend_club/ and frontend_public/. Targets here are only
# for things that genuinely span apps.
# ----------------------------------------------------------------------------
.PHONY: help gen-api openapi check check-backend check-player check-club check-public \
        test-hooks test-drift contract-freshness test-contract-freshness \
        poetry-pin test-poetry-pin taskdef test-taskdef ci-ok test-ci-ok test-memory-peak \
        shards-add-up test-shards-add-up \
        afk-install afk-build afk

help:              ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# API contract — the backend is the source of truth (docs/adr/0006).
# ----------------------------------------------------------------------------
openapi:           ## emit the API contracts (backend/openapi.{player,dev,club,public}.json)
	$(MAKE) -C backend openapi

# Freshness, not drift, and the two are different questions. `test-drift` below
# asserts a client's generated types reproduce from the document; this asserts
# the *documents* reproduce from the code. The dev console (#256) has no client
# and no codegen, so freshness is the only analogue its contract has — and it
# closes a hole on the player side too, where a stale document is invisible to a
# drift check that regenerates the client's types from it.
contract-freshness: ## verify every emitted OpenAPI document reproduces from the code
	bash .github/scripts/check-contract-freshness.sh

test-contract-freshness: ## verify the contract-freshness check still fires
	bash .github/scripts/test-contract-freshness.sh

# The clients: every app whose package.json declares `gen:api`, asked of
# .github/scripts/contract-clients.sh — the answer check-contract-drift.sh reads
# too, so the two cannot disagree about who is a client. Three today, each
# generating from its own document (docs/adr/0187 §5): frontend_player,
# frontend_club and frontend_public.
CLIENTS := $(shell bash .github/scripts/contract-clients.sh)

gen-api: openapi   ## regenerate every client's wire types from its own contract
	@for app in $(CLIENTS); do \
	  echo "→ $$app"; (cd $$app && pnpm gen:api) || exit 1; \
	done
	@echo "Regenerated the wire types of $(CLIENTS)."
	@echo "Commit them along with the backend/openapi.*.json that moved."
	@echo "CI diffs each client (make test-drift covers the check itself)."

# ----------------------------------------------------------------------------
# Gates. Each app's own `check` is the real one; these just fan out.
# ----------------------------------------------------------------------------
check-backend:     ## backend: lint + typecheck + test
	$(MAKE) -C backend check

check-player:      ## player app: lint + typecheck + test
	cd frontend_player && pnpm check

check-club:        ## club website: lint + format + typecheck + tokens + Playwright
	cd frontend_club && pnpm check

check-public:      ## public site: lint + format + typecheck + tokens + Playwright
	cd frontend_public && pnpm check

check: check-backend check-player check-club check-public  ## every app's gate

# ----------------------------------------------------------------------------
# Guardrails. Run after touching anything in .claude/hooks/.
# ----------------------------------------------------------------------------
test-hooks:        ## verify the ownership + bash guardrails still match
	bash .claude/hooks/test-hooks.sh

test-drift:        ## verify the contract drift check still fires, for every client
	bash .github/scripts/test-contract-drift.sh

# The Poetry that writes backend/poetry.lock and the Poetry every build pins to
# read it are two different numbers in four files, and nothing compared them
# until #153. Cross-app because the pins are in backend/, .github/ and .sandbuket/.
poetry-pin:        ## verify every pinned Poetry can read backend/poetry.lock
	bash .github/scripts/check-poetry-pin-drift.sh

test-poetry-pin:   ## verify the poetry pin check still fires
	bash .github/scripts/test-poetry-pin-drift.sh

# The ECS task definition describes a container; app/core/config.py and
# docker/api/startup.prod.sh are what actually runs in it. Nothing compared them,
# and only `local` runs, so nothing ever exercised the artifact: it could not have
# started at all (#341), and its kill deadline was a dead heat with the drain it
# was meant to outlive (#345). This exercises the application rather than
# describing it — neither rule holds a list or a number of its own, which is what
# keeps the check from becoming one more copy of the fact it polices.
# Cross-app because the artifact is in backend/ and the gate is in .github/.
taskdef:           ## verify backend/deploy/ecs/taskdef.json agrees with the app it runs
	bash .github/scripts/check-taskdef.sh

test-taskdef:      ## verify both of the task-definition check's rules still fire
	bash .github/scripts/test-taskdef.sh

# CI is a dozen parallel jobs behind one summary, `ci-ok` (docs/adr/0181 §4), and
# the summary is only worth reading if nothing under it can fail unseen. Its
# verdict needs a real run's `needs` context, so what runs here is the half a
# workflow edit can break: every job reaches ci-ok, and ci-ok runs `if: always()`.
# Cross-app because the workflow gates both apps.
ci-ok:             ## verify ci-ok needs every job in ci.yml and runs whatever they did
	bash .github/scripts/check-ci-ok.sh wiring

test-ci-ok:        ## verify ci-ok's verdict and wiring checks still fire
	bash .github/scripts/test-ci-ok.sh

test-memory-peak:  ## verify CI's memory recorder passes every exit status through
	bash .github/scripts/test-memory-peak.sh

# The backend's tests run as a matrix of groups, one per runner (docs/adr/0181
# §5), and splitting is the one change to the gate that could make a green run
# test less. Each group writes a JUnit report of what it ran; this holds their
# union against the suite, collected once — every test in exactly one group. It
# reads a run's reports, so REPORTS is a directory of them: CI's add-up job has
# one, and a laptop can make one with `make -C backend test-group … PYTEST_ARGS=
# --junitxml=<dir>/group-<k>-of-<N>.xml`, as test-shards-add-up.sh does.
# Cross-app because the reading is the backend's and the gate is CI's.
shards-add-up:     ## verify the group reports in REPORTS=<dir> add up to the backend suite
	@[ -n "$(REPORTS)" ] || { echo "usage: make shards-add-up REPORTS=<directory of group reports>" >&2; exit 2; }
	bash .github/scripts/check-shards-add-up.sh "$(REPORTS)"

test-shards-add-up: ## verify the shards-add-up check still fires
	bash .github/scripts/test-shards-add-up.sh

# ----------------------------------------------------------------------------
# AFK agent loop (sandbuket). See tools/afk/README.md.
# ----------------------------------------------------------------------------
afk-install:       ## install the AFK tooling into tools/afk
	poetry -C tools/afk install

afk-build:         ## build the sandbox image (aligned to your UID/GID)
	docker build -t sandbuket:raketa \
	  --build-arg AGENT_UID=$$(id -u) --build-arg AGENT_GID=$$(id -g) \
	  -f .sandbuket/Dockerfile .sandbuket

afk:               ## run the AFK loop (ARGS="10 --branch agent/foo")
	poetry -C tools/afk run python afk.py $(ARGS)
