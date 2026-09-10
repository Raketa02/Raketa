# ADR-0028 — Four environments, one typed configuration

- **Status:** Accepted
- **Date:** 2026-08-17

## Context

Nothing in this repo named environments consistently, and the two apps that named one
disagreed about what the name meant.

The backend's environment was an unconstrained string defaulting to `dev`, with no
validation. A typo was accepted silently, and because the production predicate matched only
`prod` and `production`, a value of `prd` quietly made a production deployment behave as
non-production. The player app had a genuine validated enum — `development | staging |
production` — with no name for a laptop, so a developer's own machine was called
`development`, which is the name that will mean a shared remote deployment. The club app had
no configuration module at all: four loose variables in a template, read by nothing.

Three consequences a developer felt daily:

- *"It works locally"* and *"it works in dev"* were the same sentence, and neither was
  checkable.
- Configuration was a set of independent knobs — debug mode, log level, log format, database
  SSL, CORS origins, the club's session-cookie `Secure` flag — each of which had to be set
  consistently with the others by hand. That is one setting expressed six times, and the
  failure is silent: nothing goes wrong until the one deployment where somebody flips four
  of them.
- The single most damaging configuration mistake available — the shipped JWT signing key,
  public in this repository's history — was reachable in production by omission.

The temptation was to defer all of this. Deployment is deliberately dormant
([ADR-0010](0010-local-first-development-aws-deferred.md)) and no domain is registered, so
there is nowhere for `staging` to *be*. But every rename still has to happen the day a
server exists, bundled with first-time infrastructure work, with real data and a real
audience for the mistake. The cost never goes down; it only moves.

Two alternatives were considered and rejected:

- **Three names, deferring `local`.** This is what the player app had. It leaves a laptop
  and a shared remote deployment indistinguishable in a log line, which is precisely the
  ambiguity being paid to remove.
- **Reading the framework's build mode.** `NODE_ENV` has two values and describes how the
  app was *compiled*; one production build serves staging and production alike. Reading a
  two-valued build flag to answer a four-valued infrastructure question is the bug, not the
  shortcut.

A fifth name, `test`, was also considered and rejected. A test run happens on somebody's
laptop or on a CI runner, and both are `local`; a `test` environment would name a *test
suite*, whereas these four names describe where software runs.

## Decision

**We will name four environments — `local`, `development`, `staging`, `production` — spelled
identically in all three apps, and give each app one typed, validated configuration module
that refuses to start on configuration that is dangerous rather than merely wrong.**

1. **The four names are a closed enum in every app**, written out rather than derived, so a
   fifth environment fails to compile (both clients) or fails to import (the backend) until
   somebody has decided what it means. The backend reads `APP_ENV`; the club app reads the
   same `APP_ENV`, unprefixed and therefore server-only; the player app reads
   `EXPO_PUBLIC_ENV`, because Expo substitutes only that prefix at build time. The *values*
   are identical, which is the part that matters.

2. **The environment may select configuration defaults; it may never select behaviour a
   domain test could observe.** No business rule, threshold, validation, status code or
   response shape varies by environment, and neither client ever branches on environment to
   decide where its data comes from. On the backend this is an `.importlinter` contract, not
   a convention: `app.core.config` is forbidden to `app/application/`, `app/shared/domain/`,
   and every `app/modules/*/domain` and `app/modules/*/application`.

3. **One value supplies the defaults that always move together** — debug mode, log level,
   log format — each still explicitly overridable, so a legitimate one-off does not require
   abandoning the mechanism.

4. **Dangerous configuration refuses to boot**, checked on the settings object rather than
   in the application factory, so it holds for a worker, a migration or a seed run and not
   only for a process serving HTTP. Every refusal names the offending variable and the
   reason, and **never echoes the offending value** — a database URL carries a password and
   a refusal message goes straight into a log aggregator.

5. **An unprovisioned environment fails loudly rather than falling back.** No placeholder
   hostname is written anywhere, in any app or template, because no domain is registered and
   a config file naming a host that does not exist describes infrastructure that does not
   exist. The backend therefore asks whether somebody *set* a value, not whether it differs
   from a sentinel; the two clients have no defaults at all, so absence is itself the
   refusal.

6. **A URL that crosses a public network is `https://` in every deployed environment.**
   `local` is unconstrained. This rule does **not** apply to a server-to-server address —
   see [`../environments.md`](../environments.md) for the full statement and the reasoning.

7. **Per-environment mobile build variants are deferred.** One bundle identifier, one URL
   scheme, one installable variant, no build profiles, until a second backend exists to
   point a second one at. This is a decision, not an omission: three installable apps that
   all reach the same laptop cost maintenance and buy nothing.

8. **The dev compose file becomes the local compose file** — `docker-compose-local.yml` —
   with every reference following it. [ADR-0010](0010-local-first-development-aws-deferred.md)
   names the old filename and is **not** edited; an accepted ADR records what was decided
   then.

The cross-app reference is [`docs/environments.md`](../environments.md). It is the
authority on the vocabulary; this ADR is the authority on why it exists.

## Consequences

**Easier.**

- A word means the same thing in every conversation, every config file and every log line.
- Turning on a remote environment the day a domain is registered is setting variables, not
  restructuring anything. The checklist is in the reference.
- One value replaces six that had to be kept in agreement by memory, and the mechanism is
  exercised in the only environment that runs — so it will not be wrong the first time it
  matters.
- The most damaging production misconfigurations are unreachable rather than discouraged.
  The escape hatch that re-enabled interactive API docs in production when debug was on is
  **removed**, not adjusted: an unreachable escape hatch is still one a reader has to reason
  about.

**Harder, and worth naming.**

- **Reading the configuration module is now required to know what the log level actually
  is** in a given environment. The old independent knobs were dumber and more obvious. The
  trade was made because six settings that must agree, kept in agreement by memory, fail
  silently and only once.
- **Three of the four names describe nothing that runs.** A reader will reasonably ask why
  `staging` exists. The refusal messages and the reference carry that explanation, and both
  will need revisiting the moment it stops being true.
- **A fifth environment is deliberately expensive.** Adding one means editing an exhaustive
  table in each of three apps. That is the point — the alternative is a new name silently
  inheriting production's answers, which is the one wrong answer that is invisible.
- **The player app's config document is evaluated by a runtime the app never otherwise
  meets.** Expo transpiles `app.config.ts` and `require`s it in Node, before Metro exists,
  so the environment decision lives in a pure table with zero runtime imports that both
  runtimes can load.

**Neutral.**

- No API contract change. No endpoint, request shape, response shape or status code moves,
  so no client type regeneration is involved.
- The dormant deployment path stays dormant behind all three of its existing layers — the
  workflow trigger, the `vars.AWS_REGION` configuration gate, and the agent guardrail. This
  ADR does not reactivate it, and doing so would supersede
  [ADR-0010](0010-local-first-development-aws-deferred.md).
- Two manual steps remain that only a human can perform, because the guardrails block agents
  from real env files on purpose: re-copying the working env files from the updated
  templates, and deleting the backend `.env.local` that is read by nothing and whose name is
  about to mean an official environment.

## Amendment — 2026-09-10: rule 5 binds every deployed environment, not only the unbuilt ones

Rule 5 said **an unprovisioned environment fails loudly rather than falling back**, and the
code said it exactly that narrowly: the three presence refusals sat behind
`UNPROVISIONED = {development, staging}`. `production` was exempt from all three.

**That exemption was the wrong half of the set, and it cost a bootable deployment.**
`backend/deploy/ecs/taskdef.json` selects `production` and supplied no `REDIS_URL`, so the
one environment nobody had exempted deliberately would have inherited
`redis://redis:6379/0` — the service name in `docker-compose-local.yml` — and run
permanently degraded, which is the state `app/infrastructure/redis_client.py` says must not
be reachable. Two more variables were missing outright, and the committed artifact could not
have started a container at all ([#341](https://github.com/Raketa02/Raketa/issues/341)).

**The rule is restated over `DEPLOYED`.** What makes an address dangerous is not that the
environment is unbuilt; it is that the shipped default is a compose service name, which
resolves on a laptop and nowhere else. That is as true of `production` as of the two nobody
has built — more so, because it is the one where inheriting a laptop costs most. So
`APP_HOST`, `WRITER_DB_URL` and `REDIS_URL` must each be set explicitly in `development`,
`staging` **and** `production`. `local` is untouched and still needs nothing.

**Nothing else in this record moves.** Rule 5's mechanism is unchanged — the backend still
asks whether somebody *set* a value rather than whether it differs from a sentinel, for the
reason rule 5 gives: with no domain registered there is nothing to compare a host against.
Rule 6's scheme rule was already stated over `DEPLOYED` and is where the name came from.

**And the disagreement is now checkable, which is the part rule 4 could not reach.** Rule 4
put the refusals on the settings object so every construction path sees them; nothing
constructed the *production* settings object, because only `local` runs. `make taskdef`
(`.github/scripts/check-taskdef.sh`) boots the committed task definition through the
real `Settings` and fails naming whatever it does not supply — deriving the required set by
executing this rule rather than by restating it, so the next refusal added here is enforced
against the deployment artifact without anybody remembering to.

**One gap is named rather than closed.** `PHOTO_STORAGE_ENDPOINT_URL`,
`PHOTO_REVIEW_ENDPOINT_URL` and `PHOTO_STORAGE_ACCESS_KEY` also default to the local dev
stack and are refused nowhere, so a deployed process still resolves all three to a laptop —
and `config.py`'s claim that the first pair is `None` in a deployed environment is not true
of the defaults as written. That is the same failure in a context this record cannot settle
alone: the photo sidecar has no container in the task definition at all. See
[`../environments.md`](../environments.md) under *How each app refuses to fall back*.
