# Environments

**The cross-app reference.** Four environments, named identically by the backend, the player
app. This page is the authority on the vocabulary and the rules that follow
from it; [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md) is the
authority on *why*, and [ADR-0029](adr/0029-seed-data-through-aggregates-never-in-production.md)
on how fake data is made.

It lives here, at the repo root, rather than in any app's `CONTEXT.md`, for the reason
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md) gives: an environment name is shared vocabulary, and a
word defined three times drifts three ways.

## The four

| Environment | What it is | Runs today |
| --- | --- | --- |
| `local` | A developer's own machine. Docker Compose, a local Postgres, an Expo dev server, `next dev`. | **Yes — the only one.** |
| `development` | A shared remote deployment: the first place code runs that is not somebody's laptop. | No — defined and validated, not provisioned. |
| `staging` | A rehearsal for production. Same configuration profile, same refusals, different data. | No — defined and validated, not provisioned. |
| `production` | What players use. | No — does not exist yet. |

No domain is registered, so `development` and `staging` have no host and no database.
Selecting one is a startup failure naming the missing variable — never a silent fallback.

**Why three names for things that do not run.** Because the contract each must satisfy is
cheaper to write now than during first-time infrastructure work, with real data and a real
audience for the mistake. `staging` in particular exists to be *the same as production*: the
day it is provisioned, the fact that it already shares production's profile and production's
refusals is what makes it a rehearsal rather than a fourth guess.

## Which variable, in which app

| App | Variable | Notes |
| --- | --- | --- |
| `backend/` | `APP_ENV` | A strict `StrEnum`. `ENV` was renamed away because it collides with an ordinary shell variable. |
| `frontend_player/` | `EXPO_PUBLIC_ENV` | Expo substitutes only `EXPO_PUBLIC_*` at build time, so the *name* cannot match. The **values** are identical, which is the part that matters. |

Each app validates its own copy. There is no shared package: the three apps share no code
([ADR-0005](adr/0005-three-app-monorepo-ownership-boundaries.md)), so the vocabulary is
duplicated deliberately and this page is what keeps the copies honest.

## The backend's derived profile

One value supplies the settings that always move together. Each stays explicitly overridable
by its own environment variable — a legitimate one-off (verbose logging in staging while
chasing a bug) does not require abandoning the mechanism.

| `APP_ENV` | `DEBUG` | `LOG_LEVEL` | `LOG_JSON` |
| --- | --- | --- | --- |
| `local` | `true` | `DEBUG` | `false` |
| `development` | `false` | `DEBUG` | `true` |
| `staging` | `false` | `INFO` | `true` |
| `production` | `false` | `INFO` | `true` |

`local` is a laptop, so it gets readable logs and debug mode. Everything deployed is ingested
by a log aggregator, so it gets JSON. `development` keeps `DEBUG`-*level* verbosity because it
exists to be debugged, but not debug *mode*, which serves verbose errors to callers. `staging`
matches production exactly.

Every structured log record carries its environment, so a `development` crash can never be
read as a production incident.

## Refusing to start

Configuration that is dangerous rather than merely wrong refuses to boot. On the backend the
checks live on the settings object, not in the application factory, so they hold for a worker,
a migration or a seed run — not only for a process serving HTTP.

| App | Refused when | Because |
| --- | --- | --- |
| backend | `APP_ENV` is not one of the four | A typo must not silently change behaviour. `prd` used to make production behave as non-production. |
| backend | **any deployed environment** with no `APP_HOST`, `WRITER_DB_URL` or `REDIS_URL` | Each shipped default is a service name out of `docker-compose-local.yml`. It resolves on a laptop and nowhere else, so falling back points at a database, or an ephemeral store, that does not exist. |
| backend | `production` with the default `JWT_SECRET_KEY` | It is public in this repository's history, so every token it signs is forgeable. |
| backend | `production` with `DEBUG=true` | It serves verbose errors to callers. |
| backend | `production` with wildcard `ALLOW_ORIGINS` **and** `ALLOW_CREDENTIALS` | Browsers reject the combination anyway, so it cannot be mistaken for working configuration. |
| backend | a deployed environment with a non-`https://` entry in `ALLOW_ORIGINS` | A browser origin reached over a public network in the clear is a session cookie in the clear. |
| backend | `production` with a `DB_SSL_MODE` that does not encrypt | Transport security should not be something anyone has to remember. |
| backend | a deployed environment with `BCRYPT_ROUNDS` below production's 12 | Nothing fails at a weak cost — every login still works — so the stored passwords would just be cheaper to crack, and nobody would notice. The default is 12 everywhere, and only a laptop may lower it; the test suite uses bcrypt's minimum, 4. |
| player | `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_FEATURES_URL` or `EXPO_PUBLIC_ENV` missing or malformed | Validated eagerly in the bootstrap sequence, so it lands on a startup screen naming the variable rather than three screens deep as a failed request. |
| player | a deployed `EXPO_PUBLIC_API_URL` or `EXPO_PUBLIC_FEATURES_URL` that is not `https://` | The scheme rule, below. |

**Two constraints on every refusal message, in all three apps.** It **names the offending
variable and the reason**; it **never contains the offending value**. A URL carries
credentials and a refusal goes straight into a log aggregator or a crash report. The
environment name may appear where it is the *reason* — it is not a secret and is already on
every log record — but it is never the offending value of the refusal that prints it.

## How each app refuses to fall back

The mechanism differs, because what each app *could* fall back to differs. The outcome is the
same for the three addresses the backend cannot run without: **a deployed environment is asked
for its own host, database and ephemeral store, and may inherit none of them.**

That is stated over *deployed* rather than over *unprovisioned*, and it once was not (#341).
The three refusals were written for `development` and `staging` — the environments nobody had
built — on the reading that being unbuilt is what makes an address dangerous. It is not. What
makes it dangerous is that the default is a compose service name, and that is equally true of
`production`, which was the one environment left able to inherit one. The committed ECS task
definition did: it selected `production`, supplied no `REDIS_URL`, and would have booted
against `redis://redis:6379/0` for ever.

**Three compose service names are still inheritable, and are not refused today.**
`PHOTO_STORAGE_ENDPOINT_URL` defaults to `http://minio:9000`, `PHOTO_REVIEW_ENDPOINT_URL` to
`http://photo-review:8000`, and `PHOTO_STORAGE_ACCESS_KEY` to the shipped MinIO key — whose
*secret* half is refused in production while the key itself is not. A production process
today resolves all three to a laptop's dev stack. `app/core/config.py` says of the first pair
that "both are `None` in a deployed environment"; they are not, because the default is the
local one rather than `None`. This is the same failure as #341 in a context that has not been
argued out yet — the photo sidecar has no container in the task definition at all — so it is
named here rather than quietly fixed. **Do not read the rule above as covering it.**

- **The backend has defaults that would be wrong**, so it asks whether somebody actually *set*
  a value — `model_fields_set`, not "differs from a sentinel". That is forced by the
  no-placeholder-hostname rule: with no domain registered there is nothing to compare a host
  against, so the only honest question is whether a human supplied one.
- **Both clients have no defaults at all.** Every variable is required, so absence is itself
  the refusal, naming the variable.

## The scheme rule

A URL that **crosses a public network** must be `https://` in every deployed environment.
`local` is unconstrained beyond being an absolute `http(s)` URL.

A URL that is **server-to-server** — one tier calling another, never crossing a public
network — carries no scheme rule. Whether that hop is encrypted is a deployment-topology
question no application can answer for its operator.

| App | Variable | Reached by | Rule |
| --- | --- | --- | --- |
| player | `EXPO_PUBLIC_API_URL` | a phone, over the internet | `https://` when deployed |
| player | `EXPO_PUBLIC_FEATURES_URL` | a phone, over the internet | `https://` when deployed |
| backend | `ALLOW_ORIGINS` entries | a browser (they *are* browser origins) | `https://` when deployed; the `*` wildcard is not an origin and is exempt |

**Why the datafile host is on the list though it serves nothing secret.** The feature-flag
datafile is public-read by design
([ADR-0180](adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md) §9),
so the rule is not protecting its contents from being read. It is protecting them from being
*rewritten*: a datafile fetched in the clear is a file anybody on the same café Wi-Fi can
replace, turning a screen on or off. The rule is for integrity here, not confidentiality, and the
client enforces both URLs in one loop so neither can be forgotten.

**Why `local` is unconstrained.** The rule used to require `http://` there. That refused an
`https://` tunnel — and `expo start --tunnel`, `cloudflared` and `tailscale funnel` all hand
back `https://`, so the single case a tunnel exists for (a physical phone that cannot reach
the laptop's LAN IP) was refused at launch. Nothing about a laptop is protected by forbidding
TLS on it.

**Why a server-to-server URL is exempt.** `http://backend.svc.cluster.local:8000` is a
legitimate and common deployed address that never leaves the cluster. Refusing it would push
an operator into either terminating TLS they do not need or editing a schema — and a rule that
is routinely edited around is not a rule.

The rule is checked across a URL *and* the environment together, so it lives on the object
rather than on either field. It **stays silent when the field itself already refused the
value**: a failed `.url()` leaves zod's result *dirty* rather than aborting it, so without
that guard `localhost:8000` produced two complaints, the second blaming the environment for a
URL that simply has no scheme. One typo, one complaint.

## The rules, condensed

1. **The environment may select configuration defaults; it may never select behaviour a
   domain test could observe.** No business rule, threshold, validation, status code or
   response shape varies by environment. Enforced on the backend by an `.importlinter`
   contract, not by memory.
2. **Dangerous configuration refuses to boot**, checked where every construction path sees it.
3. **A refusal names the variable and the reason, and never the value.**
4. **A deployed environment fails loudly rather than falling back.** It is asked for its own
   host, database and ephemeral store; none of the three may be inherited from the local
   defaults. [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md)'s rule 5
   stated this of *unprovisioned* environments, and its
   [2026-09-10 amendment](adr/0028-four-environment-model-and-typed-configuration.md#amendment--2026-09-10-rule-5-binds-every-deployed-environment-not-only-the-unbuilt-ones)
   restates it over every deployed one — with the three photo settings named there as still
   uncovered.
5. **No placeholder hostname is written anywhere**, in any app or template. A config file
   naming a host that does not exist describes infrastructure that does not exist.
6. **A public-network URL is `https://` in every deployed environment**; a server-to-server URL
   carries no scheme rule.
7. **A production build cannot switch environment.** The environment is fixed when the artefact
   is built, not chosen when it starts: the player app's is inlined by Expo's build-time
   substitution. Nothing in the client reads a runtime switch, offers a picker, or
   lets a deep link, a query parameter or a debug menu repoint the app at another backend. A
   build that could be repointed is a build whose test results say nothing about where it will
   run. (The developer-facing environment switcher is deferred for the same reason it is
   currently pointless — there is nothing to switch to.)
8. **The OpenAPI documents remain the source of truth for client types, in every environment.**
   `backend/openapi.player.json` is generated by the backend and the client generates its wire
   types from it ([ADR-0006](adr/0006-backend-owns-api-contract.md)). No client hand-writes a DTO mirroring a
   backend response, and **no environment is an excuse to**: a type that is "just for local" is
   a type nothing regenerates. CI regenerates and diffs, so a contract change shipped without
   its client types fails the build.
9. **External services use sandbox credentials outside production.** Payments, mail, SMS, push,
   object storage, maps — every third party gets its test/sandbox key in `local`,
   `development` and `staging`, and its live key only in `production`. The rule is one-way and
   has no exceptions: a live key in a non-production environment charges a real card, mails a
   real person, or writes to a real bucket, and it does so from an environment nobody is
   watching. (Nothing here is integrated yet. The rule is written before the first integration
   on purpose — it is much harder to introduce afterwards.)
10. **`NODE_ENV` is the build mode, not the environment.** It has two values and describes how
    the app was compiled; one production build serves staging and production alike. A client
    that could read it to decide behaviour should ban it outright, with a lint rule.

## Feature flags are not environment configuration

**A flag answers *is this feature active*. An environment answers *which infrastructure am I
using*. The two are never mixed.** This is a durable rule, not a scoping note.

The failure it prevents is specific and common: a feature turned on "in staging" by an
`if environment === 'staging'` branch. That branch is behaviour selected by environment, which
rule 1 forbids — and it means the feature has never been exercised in the environment it will
ship to. The environment and the flag then have to be changed together, by memory, which is
the class of failure this whole page exists to remove.

Concretely:

- A flag is a value the *application* reads and can change without a redeploy. An environment
  is fixed when the artefact is built.
- A flag may be *defaulted* per environment, once a flag system exists. It is never *derived*
  from the environment, and no code branches on the environment to decide whether a feature is
  on.
- A feature that is not ready is off everywhere, including production, and is turned on by
  flipping the flag — not by promoting it through environments.

The flag system is Featurevisor, adopted by
[ADR-0180](adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md). Its
definitions live in a separate repository, `Raketa02/raketa-features`, whose environments are
these four names; each builds its own datafile, and the player app reads the one for the
environment it was built for. That is where a flag's per-environment default lives — in the
flags repo's YAML, never in a branch in either app. The rule above was recorded before any flag
system existed so that the first one would not arrive as an environment branch, and it holds
for this one unchanged.

**Where the app finds its datafile.** `EXPO_PUBLIC_FEATURES_URL` is the base, and the path under
it is the environment's name: the app fetches
`$EXPO_PUBLIC_FEATURES_URL/<environment>/featurevisor-player.json`, for the environment it was
built for. In `local` the base is the Mac itself: `npm run serve` in the flags repo serves the
built datafiles on port 3040, on all interfaces, so a physical phone is given the Mac's LAN IP,
never `localhost`, just as for the API. Later it is the bucket the flags repo's publish run
uploads to, and moving there changes this value and no code.

The variable is required and validated at launch like any other, but **the datafile is never
waited on.** It is fetched once at launch and again on each return to the foreground, and when it
cannot be had the app answers from the last good datafile it saved, or failing that from each
feature's code default (ADR-0180 §6). So a host that is down or wrong shows up as flags holding
their old or default values, never as a startup failure. That is the reason step 4 of the
checklist below says to publish the datafile before a build points at it.

## Testing

Which tier runs against which environment, and the one line that is not crossed.

| Tier | Runs against | Notes |
| --- | --- | --- |
| Backend unit (`backend/tests/unit/`) | Nothing. Pure objects, in-memory SQLite for adapter tests. | `conftest.py` sets `APP_ENV=local`. There is no `test` environment: a test run happens on a laptop or a CI runner, and both are `local`. |
| Backend API (`backend/tests/api/`) | An in-memory SQLite database and an ASGI transport. No network. | The shared `client` fixture. Reuse it rather than standing up a second app or database. |
| Client unit (Jest / Vitest) | Nothing. Pure functions, mocked ports. | Config parsers are pure functions from a raw record to a validated object, which is why they are tested exhaustively. |
| Client component | A renderer, no network. | Asserts what a user can observe. |
| Backend demands (`backend/tests/demands/`) | An in-memory SQLite database, for the one port with a real provider. | ADR-0098's consumer-driven **contract suite**, parameterised over every implementation registered in `app/bootstrap/matcher_demands.py`. Not in the *Contract* row below, and not named for it: that word means `openapi.player.json` here. |
| Contract | `backend/openapi.player.json`. | CI regenerates the client's types and diffs. |
| End-to-end (Playwright) | `local` today. `development` or `staging` once either is provisioned. | Each test owns its data. |
| Manual exploratory | `local`; `development` or `staging` once provisioned. | |

**How the suite runs.** The merge gate runs every test of every app a push changes, never a
subset. It runs them in parallel, across tiered jobs per app and split into shards, behind
one `ci-ok` check. The full suite at the end of a ticket runs in parallel too, across the
laptop's cores. Coverage is never measured on a pull request: it runs nightly, on every push
to `main`, and on demand with `make coverage`, and nothing gates on it. Running only the tests
a change can affect (`make test-affected`, `pnpm test:affected`) is for iterating on a ticket.
It is never what lets a change merge, because the selector cannot see the tests that read the
source tree as text. Decided by
[ADR-0181](adr/0181-the-merge-gate-runs-every-test-and-choosing-tests-is-the-inner-loops-job.md).
The backend's suite runs as balanced groups, one per runner and each in parallel across that
runner's two cores, and the run fails when the groups' reports do not add up to the suite —
a test that no group ran, or that two did (#489).

**Production is never where a destructive automated test runs.** No test suite, load
generator, fixture teardown, database reset or seed run targets production — not gated behind a
flag, not "carefully", not with a confirmation prompt. The guarantee is structural rather than
procedural: the seed system refuses a production configuration on import
([ADR-0029](adr/0029-seed-data-through-aggregates-never-in-production.md)), and every automated
suite runs against an ephemeral database it created.

The only automated things that may touch production are **read-only and idempotent** — health
checks, synthetic `GET` probes, uptime monitoring. Anything that writes is a deploy or an
operator action, and both are somebody's decision rather than a job's.

## Schema change: expand and contract

**Prefer additive changes** is the rule of thumb. **Expand and contract** is the practice that
makes it work, and it is written down here because the constraint that forces it is not
obvious from any one app: **old mobile builds stay installed on real phones for months.** There
is no way to force everyone to update, so at any moment several client versions are talking to
one backend. A field removed today is removed from a client shipped in March that is still
running.

Three phases, and the middle one is the one people skip:

1. **Expand.** Add the new column, field or endpoint alongside the old one. Both are populated
   and both are served. Nothing reads the new one yet. This deploys on its own and is
   reversible.
2. **Migrate.** Clients move to the new shape at their own pace, and backfill runs. The
   backend writes both and reads whichever is present. **This phase lasts as long as the
   oldest client version anybody still supports** — for mobile, months, not days.
3. **Contract.** Only once nothing reads the old shape: stop writing it, then remove it. This
   is a separate deploy from step 1, and it is the one that breaks things if the second phase
   was cut short.

Concretely:

- Adding an optional field is phase 1 alone, which is why additive change is cheap.
- Renaming a field is all three phases — it is an add, a migration and a delete, never one
  commit. A rename shipped as a rename breaks every client that has not updated.
- Making an optional field required is a contract, not an expansion: it breaks every client
  still sending the old payload.
- Dropping a database column follows the same three phases even when no client sees it,
  because a rollback to the previous image must still find the column there.
- An already-applied Alembic migration is never edited. Add a new one.

The API-contract half of this is [ADR-0006](adr/0006-backend-owns-api-contract.md) and
`backend/.claude/skills/api-contract-change`; this section is the database and rollout half,
and the two are the same discipline applied on either side of the wire.

## Seed data

Fake data is created by executing the same use cases a request executes
([ADR-0029](adr/0029-seed-data-through-aggregates-never-in-production.md)), so a seeded
aggregate has a real event stream and replays correctly.

```bash
cd backend && make seed        # inside the API container
cd backend && make seed-host   # the same module, on the host
```

`local`, `development` and `staging` are seedable. **`production` is refused**, checked on
import of `app/seeds/` rather than in the make target — an image runs `python -m app.seeds`,
not `make`. Accounts are named for the state they represent and addressed on the reserved
`.example` TLD, so a seeded address can never resolve or receive mail.

## Turning on a remote environment

The day a domain is registered, this is a configuration task rather than a redesign. In order:

1. **Register the domain and provision the infrastructure** — a database and a host for the
   API. Reactivating the deployment path supersedes
   [ADR-0010](adr/0010-local-first-development-aws-deferred.md) and needs its own ADR; the
   dormant pipeline's own reactivation steps are in the header of
   [`.github/workflows/deploy-ecs.yml`](../.github/workflows/deploy-ecs.yml) and in
   `backend/docs/deployment/aws-ecs.md`.
2. **Issue a TLS certificate** for every public-network host. Rule 6 is not satisfiable
   without one, which is the intended ordering.
3. **Set the backend's variables**: `APP_ENV`, and — because nothing deployed may inherit the
   local defaults — `APP_HOST`, `WRITER_DB_URL` and `REDIS_URL` explicitly. Then
   `JWT_SECRET_KEY` (`openssl rand -hex 32`), `PHOTO_STORAGE_SECRET_KEY`, `DB_SSL_MODE` (one of
   `require`, `verify-ca`, `verify-full`), and `ALLOW_ORIGINS` as an explicit `https://` list
   rather than a wildcard — or an explicit empty list, which is what it is today, because no
   browser client exists and the mobile app sends no `Origin` header.

   **Do not maintain this list by reading it.** `make taskdef` builds the settings object
   out of `backend/deploy/ecs/taskdef.json` and names whatever it does not supply — and
   checks the container's stop deadline against the application's own drain while it is
   there; that check, and not this paragraph, is what CI enforces. The paragraph is
   here because a checklist a human follows should say what is coming — it went eleven days
   out of date once, and the check is what makes that recoverable rather than invisible.
4. **Set the player app's variables**: `EXPO_PUBLIC_ENV`, `EXPO_PUBLIC_API_URL` (`https://`)
   and `EXPO_PUBLIC_FEATURES_URL` (`https://`, the flags host). Before a build points at the
   flags host, the flags repo's publish run must have uploaded that environment's datafile
   there: until it does, every feature silently takes its code default, and nothing refuses.
   At this point the per-environment bundle-identifier question deferred by
   [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md) becomes live for the
   first time, because there is finally a second backend to point a second variant at.
5. **Point every external service at its sandbox credentials**, per rule 9. Live keys go to
   `production` and nowhere else.
6. **Seed it** — `development` and `staging` are seedable, and the accounts are the same edges
   a laptop gets.
7. **Delete this list's assumptions as they stop being true.** The three "not provisioned"
   rows in the table at the top of this page, and the sentences in each app's `.env.example`
   saying only `local` runs, are the first things that become false.

## Where to look next

| Question | File |
| --- | --- |
| Why four environments, and why typed | [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md) |
| Why seeds go through aggregates | [ADR-0029](adr/0029-seed-data-through-aggregates-never-in-production.md) |
| The backend's settings, profile and refusals in detail | `backend/README.md`, `backend/CONTEXT.md` |
| The player app's config, app identity and badge | `frontend_player/README.md`, `frontend_player/docs/architecture.md` Part 14 |
| What each variable is, per app | each app's `.env.example` |
| Whether the deployment artifact supplies them | `make taskdef` — [`check-taskdef.sh`](../.github/scripts/check-taskdef.sh) |
