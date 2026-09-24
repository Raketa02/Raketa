# ----------------------------------------------------------------------------
# Raketa monorepo — root helpers.
#
# Each app owns its own commands: backend/Makefile, and the pnpm scripts in
# frontend_player/. Targets here are only for things that genuinely span apps.
# ----------------------------------------------------------------------------
.PHONY: help gen-api openapi check check-backend check-player \
        test-hooks test-drift contract-freshness test-contract-freshness \
        gen-judged-pairings judged-pairings \
        test-judged-pairings gen-ruleset-diff ruleset-diff test-ruleset-diff \
        poetry-pin test-poetry-pin taskdef test-taskdef ci-ok test-ci-ok test-memory-peak \
        afk-install afk-build afk

help:              ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# API contract — the backend is the source of truth (docs/adr/0006).
# ----------------------------------------------------------------------------
openapi:           ## emit the API contracts (backend/openapi.{player,dev}.json)
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

gen-api: openapi   ## regenerate the client's wire types from the contract
	cd frontend_player && pnpm gen:api
	@echo "Regenerated frontend_player/src/generated/."
	@echo "Commit it along with backend/openapi.player.json."
	@echo "CI diffs them (make test-drift covers the check itself)."

# ----------------------------------------------------------------------------
# The six judged pairings — the same generate-commit-diff idiom as gen-api, one
# document over. docs/specs/matchmaking/judged-pairings.json holds the six as
# INPUTS and a verdict per case (docs/adr/0122); every term value, every weight
# and every Fit is derived by the live ruleset and written back into the tables.
#
# Cross-app because the harness is the backend's and the tables it writes are
# the repository's specs. It also re-derives QUALITY_FLOOR's bound, which is the
# half a diff cannot do: ranking-weights.md §11 has always demanded that turning
# a term on re-runs the six cases and may move the floor, and now it fails.
# ----------------------------------------------------------------------------
gen-judged-pairings: ## re-derive the six judged pairings and regenerate their tables
	cd backend && poetry run python -m scripts.judged_pairings
	@echo "Commit the result along with whatever moved the numbers."
	@echo "CI regenerates and diffs it (make test-judged-pairings covers the check)."

judged-pairings:   ## verify the judged tables reproduce and the floor still holds
	bash .github/scripts/check-judged-pairings.sh

test-judged-pairings: ## verify the judged-pairings check still fires
	bash .github/scripts/test-judged-pairings.sh

# ----------------------------------------------------------------------------
# The ruleset diff — the same generate-commit-diff idiom, third instance, and
# this one is a release gate. docs/adr/0119: **shipping a ruleset is an offline
# diff and a deploy**; canary cannot measure its own success and shadow buys a
# slower version of an answer already on hand, so the diff is what is left and
# it has to be a build gate rather than a habit.
#
# The synthetic corpus (the-replay-harness.md §2.1) is generated from a seed and
# its answers are committed. Regenerating after a ruleset change prints the diff
# — the classification, the verdict rates, the floor crossings — which is what
# the pull request argues for. The other half of the gate is a signature and
# says so: the recorded-corpus diff needs a restore and cannot run in CI.
#
# Cross-app because the harness is the backend's and the artifacts it writes are
# the repository's specs, exactly as the judged pairings are.
# ----------------------------------------------------------------------------
gen-ruleset-diff:  ## re-run the synthetic corpus and rewrite its committed answers
	cd backend && poetry run python -m scripts.ruleset_diff
	@echo "Commit both artifacts along with whatever moved the numbers."
	@echo "CI regenerates and diffs them (make test-ruleset-diff covers the check)."

ruleset-diff:      ## verify the committed diff reproduces, under two hash seeds
	bash .github/scripts/check-ruleset-diff.sh

test-ruleset-diff: ## verify the ruleset-diff check still fires
	bash .github/scripts/test-ruleset-diff.sh

# ----------------------------------------------------------------------------
# Gates. Each app's own `check` is the real one; these just fan out.
# ----------------------------------------------------------------------------
check-backend:     ## backend: lint + typecheck + test
	$(MAKE) -C backend check

check-player:      ## player app: lint + typecheck + test
	cd frontend_player && pnpm check

check: check-backend check-player  ## every app's gate

# ----------------------------------------------------------------------------
# Guardrails. Run after touching anything in .claude/hooks/.
# ----------------------------------------------------------------------------
test-hooks:        ## verify the ownership + bash guardrails still match
	bash .claude/hooks/test-hooks.sh

test-drift:        ## verify the contract drift check still fires
	bash .github/scripts/test-contract-drift.sh

# The Poetry that writes backend/poetry.lock and the Poetry every build pins to
# read it are two different numbers in four files, and nothing compared them
# until #153. Cross-app because the pins are in backend/ and .github/ both.
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
