# ----------------------------------------------------------------------------
# Raketa monorepo — root helpers.
#
# Each app owns its own commands: backend/Makefile, and the pnpm scripts in
# frontend_player/. Targets here are only for things that genuinely span apps.
# ----------------------------------------------------------------------------
.PHONY: help gen-api openapi check check-backend check-player \
        test-hooks test-drift poetry-pin test-poetry-pin afk-install afk-build afk

help:              ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

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
