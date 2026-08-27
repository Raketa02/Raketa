# ----------------------------------------------------------------------------
# Raketa monorepo — root helpers.
#
# Each app owns its own commands: backend/Makefile, and the pnpm scripts in
# frontend_player/. Targets here are only for things that genuinely span apps.
# ----------------------------------------------------------------------------
.PHONY: help gen-api openapi check check-backend check-player \
        test-hooks test-drift gen-judged-pairings judged-pairings \
        test-judged-pairings poetry-pin test-poetry-pin afk-install afk-build afk

help:              ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# API contract — the backend is the source of truth (docs/adr/0006).
# ----------------------------------------------------------------------------
openapi:           ## emit the API contract (backend/openapi.player.json)
	$(MAKE) -C backend openapi

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
# read it are two different numbers in five files, and nothing compared them
# until #153. Cross-app because the pins are in backend/ and .github/ both.
poetry-pin:        ## verify every pinned Poetry can read backend/poetry.lock
	bash .github/scripts/check-poetry-pin-drift.sh

test-poetry-pin:   ## verify the poetry pin check still fires
	bash .github/scripts/test-poetry-pin-drift.sh

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
