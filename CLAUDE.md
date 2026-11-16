# Raketa — Monorepo

A racket-sport platform. **Today, end to end:** a player signs up, picks a nickname, joins
groups, answers a questionnaire for a Skill rating in a sport where a group first asks for one,
and is proposed games — the last yes books a
club's court and charges every seat — while a club runs its courts, bookings and money on its
website. **Independently deployable** apps share one repository and one domain language, and
communicate **only over HTTP**. There are four
([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)),
each with its own CI lane.

| App | Path | Stack |
| --- | --- | --- |
| Backend API | `backend/` | FastAPI, Clean/hexagonal, DDD, event sourcing, Poetry |
| Player app | `frontend_player/` | React Native + Expo + TypeScript (iOS & Android); also the Administrator's profile |
| Club website | `frontend_club/` | Next.js, server-side cookie session — *scaffolded by #522* |
| Public site | `frontend_public/` | Next.js, server-rendered, no session — *scaffolded by #525* |

> **The repository was reset on 2026-08-25** to sign-up, sign-in and onboarding. The club
> console, the pairing / balance-forecast / Match Fit engines, the kernel's money module and
> the unwritten Clubs / Courts / Matches / Money / Now contexts were all removed, along with
> the ADRs and specs that decided only them. If you remember a term or a file from one of
> those, it is gone on purpose — see the
> [ADR index](docs/adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps). Courts,
> bookings and money are **decided again** by
> [ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) — the group's Games
> deck and Fill in, specified in `docs/specs/games-and-fill-in/` — and are built, money behind the
> payments port ([ADR-0190](docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)).
>
> **The older way of making a game was removed on 2026-10-06** (#569): *Classic play* — the Players
> deck and radar, Chats, challenges and plans, Find a game, the searches, the candidate index and
> the "who fits whom" ranking — together with the feature flag that hid it, and the ADRs and
> specs that described only them. The Games deck is the one way a game is made; see the
> [ADR index](docs/adr/README.md#the-2026-10-06-classic-play-removal--the-second-gap).

## Start the session inside the app you are changing

```bash
cd backend && claude          # likewise frontend_player/
```

**YOU MUST launch from the app directory. This is mechanical, not etiquette.** Claude
Code loads settings, hooks and skills from the directory it starts in — not from
ancestors. A session started in `backend/` loads `backend/.claude/settings.json`, which
registers the ownership guardrails and that app's permissions. A session started at the
repo root loads the root's settings instead and owns *everything*.

Launch at the root only for work that is genuinely cross-app: ADRs, the shared glossary,
the hooks themselves, `make gen-api`.

## Invariants

- **Never import across apps.** They are separate deployables; the only contract between
  them is HTTP ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).
- **The backend owns the API contract.** It emits one OpenAPI document per surface, and
  each client generates its wire types from its own and no other, never hand-writing a DTO
  mirroring a backend response ([ADR-0006](docs/adr/0006-backend-owns-api-contract.md)).
  There are four (ADR-0187 §5): `backend/openapi.player.json` for the player app,
  `openapi.club.json` for the club website, `openapi.public.json` for the public site, and
  the **dev console**'s `openapi.dev.json`
  ([ADR-0194](docs/adr/0194-the-games-test-console-acts-as-seed-accounts-and-writes-history-never-time.md)).
  Regenerate with `make gen-api`, which regenerates all three clients, and commit the
  result — CI regenerates and diffs each
  client, so a contract change shipped without its client types fails the build
  ([`.github/scripts/check-contract-drift.sh`](.github/scripts/check-contract-drift.sh),
  which takes any app whose `package.json` declares `gen:api`, proven still to fire by
  `make test-drift`).
  **The dev console grows more than one path and still has no client**: today its one
  roster route, and from #590 a route per action, situation and job the games test console
  presses. Its one page is their only caller, so nothing generates types from it. Its
  analogue of the drift check is a **freshness** check: re-emit every document and diff the
  JSON, which is also the only thing that would catch a stale client document — that
  client's drift check regenerates its types *from* the document and finds them in perfect
  agreement. Which documents there are is the emit's answer, never a list in the check
  ([`.github/scripts/check-contract-freshness.sh`](.github/scripts/check-contract-freshness.sh),
  `make contract-freshness`, proven still to fire by `make test-contract-freshness`).
- **One Poetry writes `backend/poetry.lock` and every pin reads it.** The version is
  pinned in four places across `backend/`, `.github/` and `.sandbuket/`, and each must be
  at least the version stamped in the lock's header. Poetry only *warns* when a pin is too
  old and still exits 0, so this drifted two majors unnoticed (#153); the next
  `lock-version` bump would have failed every pin at once. Regenerating the lock and
  bumping the pins is one commit, checked by
  [`.github/scripts/check-poetry-pin-drift.sh`](.github/scripts/check-poetry-pin-drift.sh)
  (`make poetry-pin`, proven still to fire by `make test-poetry-pin`). Poetry 2.x
  unbundled `poetry export`, so a site that exports also installs `poetry-plugin-export`.
- **The deployment artifact agrees with the application, and a gate is what says so.**
  `backend/deploy/ecs/taskdef.json` describes a container; `backend/app/core/config.py`
  and `backend/docker/api/startup.prod.sh` are what actually runs in it. Nothing compared
  them, and only `local` runs, so nothing ever exercised the artifact. `make taskdef` asks
  it two questions, both by **executing** the application rather than restating it — and
  **neither rule holds a list or a number of its own**, because a copy is how the
  disagreement started.
  - **Would it start?** The settings object is built out of exactly what the file
    supplies, and its refusals are the verdict. For eleven days the answer was no: the
    file selected `production` and supplied no `REDIS_URL`, no `PHOTO_STORAGE_SECRET_KEY`
    and no `ALLOW_ORIGINS` (#341).
  - **Would it be killed mid-shutdown?** `stopTimeout` is read against gunicorn's
    `--graceful-timeout`, which is **the number that leads**. Unset is not unbounded —
    Fargate supplies 30, exactly the graceful timeout, so SIGKILL landed on the second the
    master would have force-killed its own stragglers (#345). Change one, change the
    other; a longer drain never fixes a connection already closed.

  It asserts presence and deadlines, never the values behind the secret ARNs, and reads
  nothing from AWS ([`.github/scripts/check-taskdef.sh`](.github/scripts/check-taskdef.sh),
  `make taskdef`, proven still to fire by `make test-taskdef`).
- **One session changes one app.** A `PreToolUse` hook blocks writes that cross an app
  boundary. A block is information — surface it, don't route around it. See
  [`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).
- **Domain terms are defined once,** in [`CONTEXT.md`](CONTEXT.md). Each app's
  `CONTEXT.md` adds only its own *technical* vocabulary and never redefines a domain term.
- **The four environment names are shared vocabulary** — `local`, `development`, `staging`,
  `production`, spelled identically in every app
  ([`docs/environments.md`](docs/environments.md)). **The environment may select
  configuration defaults; it may never select behaviour a domain test could observe.** Only
  `local` runs today; selecting another fails at start rather than falling back.
- **A client's shape is that client's own.** `frontend_player/` follows feature-first Clean
  Architecture ([ADR-0009](docs/adr/0009-feature-first-clean-architecture-frontends.md)).
  The club website and the public site each have their own standard, in their own
  `CLAUDE.md` ([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §6), and a rule learned in one client **does not** transfer to another.

## Safety — never do these without an explicit human request

- Run deployment or release commands (`make build-prod`, `ecr-*`, `ecs-*`,
  `docker push`, `aws ecs|ecr`, `eas build|submit`, `vercel`).
- Create or modify a real `.env*` / secret / certificate / credential file. Edit the
  `.env*.example` template instead and let a human copy it.
- Rewrite git history or force-push (`git push --force`, `reset --hard`, `clean -f`,
  `branch -D`).
- Edit an already-applied Alembic migration.
- Change public API behavior without calling it out in the plan first.

The first three are enforced by `.claude/hooks/guard-bash.sh`. A blocked command is the
guardrail doing its job.

## Repo-wide docs

- [`CONTEXT.md`](CONTEXT.md) — the shared domain glossary. **Source of truth for domain
  terms.** A term it doesn't define has no settled meaning yet; see
  [`docs/agents/domain.md`](docs/agents/domain.md) before naming something new.
- [`CONTEXT-MAP.md`](CONTEXT-MAP.md) — topology: which file owns which vocabulary.
- [`docs/environments.md`](docs/environments.md) — **the four environment names and the
  deployment contract.** `local`, `development`, `staging`, `production`, spelled identically
  by every app; the refusals, the scheme rule, the test taxonomy, feature flags vs
  environment configuration, expand-and-contract, and the checklist for turning on a remote
  environment. Only `local` runs. Decided by [ADR-0028](docs/adr/0028-four-environment-model-and-typed-configuration.md)
  and [ADR-0029](docs/adr/0029-seed-data-through-aggregates-never-in-production.md).
- [`docs/adr/`](docs/adr/) — decisions affecting the system or the contract between apps.

After changing either hook, run `make test-hooks` (109 assertions). A guardrail that
silently stops matching is worse than none, because you stop watching for it. The same
argument is why `make test-drift`, `make test-poetry-pin`, `make test-taskdef`,
`make test-shards-add-up` and `make test-ci-ok` exist: each drives its check against a
deliberately broken tree and asserts it goes red. After adding a CI job, run `make ci-ok`
— the job must also be in `ci-ok`'s `needs`, or it can fail unseen.

## Agent skills

### Issue tracker

GitHub Issues on `Raketa02/Raketa`, via the `gh` CLI — **not** the dead
`RobertConstantin02/rakieta` this repo detached from, whose issues are not this repo's.
`gh` is authenticated for two accounts and does not stay switched; the symptom is
"could not resolve to a Repository", never a 403. Blocking edges live in the issue body
and a spec is labelled `prd`, not `ready-for-agent` — both are load-bearing for the AFK
loop, while `/wayfinder` uses GitHub's native dependencies instead. See
[`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Triage labels

The five canonical triage roles, each label string equal to its name. See
[`docs/agents/triage-labels.md`](docs/agents/triage-labels.md).

### Domain docs

Multi-context: `CONTEXT-MAP.md` is the topology, the root `CONTEXT.md` owns the domain
language, and each app's `CONTEXT.md` adds technical vocabulary only. See
[`docs/agents/domain.md`](docs/agents/domain.md).
