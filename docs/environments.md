# Environments

**The cross-app reference.** Four environments, named identically by the backend, the player
app, the club website and the public site. This page is the authority on the vocabulary and the
rules that follow from it; [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md) is the
authority on *why*, and [ADR-0029](adr/0029-seed-data-through-aggregates-never-in-production.md)
on how fake data is made.

It lives here, at the repo root, rather than in any app's `CONTEXT.md`, for the reason
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md) gives: an environment name is shared vocabulary, and a
word defined three times drifts three ways.

## The four

| Environment | What it is | Runs today |
| --- | --- | --- |
| `local` | A developer's own machine. Docker Compose, a local Postgres, the mail catcher, an Expo dev server, `next dev` for each web app. | **Yes — the only one.** |
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
| `frontend_club/` | `APP_ENV` | Read by the website's server when it starts, like every variable it has. None is `NEXT_PUBLIC_*`, so nothing is inlined into the browser. |
| `frontend_public/` | `APP_ENV` | The same, for the public site. |

Each app validates its own copy. There is no shared package: the four apps share no code
([ADR-0005](adr/0005-three-app-monorepo-ownership-boundaries.md),
[ADR-0187](adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)),
so the vocabulary is duplicated deliberately and this page is what keeps the copies honest.

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
| backend | **any deployed environment** with no `PUBLIC_SITE_URL`, or one that is not `https://` | Every group link is built from it and posted into a chat, where it stays after the setting is fixed. The default is `frontend_public`'s dev server on a laptop. |
| backend | **any deployed environment** with no `CLUB_WEBSITE_URL`, or one that is not `https://` | A club's reset email links to its *Set a new password* page there. The default is `frontend_club`'s dev server on a laptop. |
| backend | **any deployed environment** with no `SMTP_HOST` or no `MAIL_SENDER` | The defaults are the mail catcher's compose service name and a sender on the reserved `.example` domain. An environment that inherited them would queue every reset and invitation for a relay that does not exist. **This is how the production sender stays off until a domain exists**: by refusing to start, never by quietly not sending ([ADR-0186](adr/0186-email-goes-through-a-port-and-a-purged-queue.md) §1). |
| backend | a deployed environment with `SMTP_SECURITY=none` | Every reset and invitation email carries a code that opens an account, so the connection to the relay is encrypted: `starttls` or `tls`. |
| backend | `production` with a `DB_SSL_MODE` that does not encrypt | Transport security should not be something anyone has to remember. |
| backend | **any deployed environment** with `PAYMENTS_PROVIDER=fake`, or with Stripe and no `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` or `STRIPE_WEBHOOK_SECRET` | The fake saves cards that do not exist and charges nobody, so every game it booked would be one no player paid for; and a webhook nobody can verify is one anybody can forge ([ADR-0190](adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)). A laptop runs on the fake by default, and may run Stripe without a webhook secret. |
| backend | a **live** Stripe key (`sk_live_`, `rk_live_`) anywhere but `production`, or a **test** one (`sk_test_`, `rk_test_`) in `production` | A live key on a laptop is one setting away from a test run charging real cards; a test key in production books games nobody paid for. Whichever provider is selected, and the key is never printed. |
| backend | a deployed environment with `BCRYPT_ROUNDS` below production's 12 | Nothing fails at a weak cost — every login still works — so the stored passwords would just be cheaper to crack, and nobody would notice. The default is 12 everywhere, and only a laptop may lower it; the test suite uses bcrypt's minimum, 4. |
| player | `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_FEATURES_URL` or `EXPO_PUBLIC_ENV` missing or malformed | Validated eagerly in the bootstrap sequence, so it lands on a startup screen naming the variable rather than three screens deep as a failed request. |
| player | a deployed `EXPO_PUBLIC_API_URL` or `EXPO_PUBLIC_FEATURES_URL` that is not `https://` | The scheme rule, below. |
| club | any of `APP_ENV`, `API_URL`, `SESSION_SECRET`, `MAP_TILE_URL`, `MAP_START` or `GEOCODER_URL` missing, blank or malformed | `src/instrumentation.ts` validates them before the server takes a request and **exits** naming each. Next alone would log the error and serve 500s. `SESSION_SECRET` is at least 32 characters, because iron-session refuses a shorter one at the first seal — a refused sign-in instead of a refused start. |
| club | a deployed `MAP_TILE_URL` that is not `https://` | The browser fetches the tiles. The scheme rule, below. |
| public | any of `APP_ENV`, `API_URL`, `PUBLIC_SITE_URL`, `APP_STORE_URL`, `GOOGLE_PLAY_URL`, `APP_SCHEME`, `APPLE_TEAM_ID`, `IOS_BUNDLE_ID`, `ANDROID_PACKAGE` or `ANDROID_CERT_FINGERPRINTS` missing, blank or malformed | The same exit at start, for the same reason. The last four are what the app-link files are made from, so a malformed one would publish an association no phone accepts. |
| public | an `APP_SCHEME` that is a web or script scheme (`http`, `https`, `javascript`, `data`, `vbscript`, `file`, `blob`) | *Open in Raketa* goes to `<APP_SCHEME>://<route>`, and from one of those it would open a page or run a script instead of the app. |
| public | a deployed `PUBLIC_SITE_URL`, `APP_STORE_URL` or `GOOGLE_PLAY_URL` that is not `https://` | A browser or a messenger opens each. The scheme rule, below. |

**Two constraints on every refusal message, in all four apps.** It **names the offending
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
- **The three clients default nothing they need.** Every variable a client cannot run without
  is required, so absence is itself the refusal, naming the variable. A variable set to
  nothing counts as missing in the two web apps, because `SESSION_SECRET=` is a template line
  nobody filled in. The one optional variable is the player app's `EXPO_PUBLIC_LINK_DOMAIN`,
  whose absence is a real state: no web domain claimed yet (below).

The backend asks the same question of four more settings, each added with a web app or with
email: the two sites every link is printed under (`PUBLIC_SITE_URL`, `CLUB_WEBSITE_URL`) and the
mail relay and sender (`SMTP_HOST`, `MAIL_SENDER`). Each default resolves on a laptop and
nowhere else, so a deployed environment names its own or does not start.

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
| backend | `PUBLIC_SITE_URL` | whoever taps a group link in a chat, or opens an invitation or a reset email | `https://` when deployed |
| backend | `CLUB_WEBSITE_URL` | a club opening its reset email | `https://` when deployed |
| backend | `SMTP_SECURITY` | the mail relay, over a public network | not `none` when deployed — the scheme rule's mail-shaped instance |
| club | `MAP_TILE_URL` | the browser, fetching the map's tiles | `https://` when deployed |
| club | `API_URL` | the website's own server | none: server to server |
| public | `PUBLIC_SITE_URL`, `APP_STORE_URL`, `GOOGLE_PLAY_URL` | a browser, or a messenger fetching a preview | `https://` when deployed |
| public | `API_URL` | the site's own server | none: server to server |

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

## The addresses links are built from

**Every address is a setting, never a literal**
([ADR-0187](adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
§7). The backend prints links into emails and group screens, and the sites they open must be
where it says they are, so three settings have to agree across apps.

| Setting | Set in | What is built from it | Locally |
| --- | --- | --- | --- |
| `PUBLIC_SITE_URL` | backend **and** `frontend_public`, the same value in both | every group link, `<PUBLIC_SITE_URL>/join/<code>`; the invitation link, `/invite/<token>`; a player's or an administrator's reset link, `/reset/<token>`. The public site makes its preview's image and address absolute from its own copy, so a messenger fetches from the address people reach. | `http://localhost:3001`, the public site's `pnpm dev` |
| `CLUB_WEBSITE_URL` | backend | a club's reset link, `<CLUB_WEBSITE_URL>/reset/<token>`: the club website's own *Set a new password* page | `http://localhost:3000`, the club website's `pnpm dev` |
| `APP_SCHEME` | backend **and** `frontend_public`, equal to the scheme `frontend_player`'s `app.config.ts` declares | the button in the email an existing account is invited by, `<APP_SCHEME>://`; the public site's *Open in Raketa*, `<APP_SCHEME>://<route>` | `raketa`, at every environment |

**Changing `PUBLIC_SITE_URL` re-addresses every link served from then on, and none already
posted.** A group link pasted into WhatsApp keeps the domain it was printed with, which is why
the value is set once per environment. The app recognises `/join/<code>` inside any text, so a
link printed under one environment's domain still names its group in another.

Until a domain exists, a phone opens these links as the public site's pages, and reaches the
app through the scheme. `EXPO_PUBLIC_LINK_DOMAIN` in the player app is empty for that reason: it
is set, with a native rebuild, the day the public site answers on a real `https://` domain
(step 7 of the checklist below).

## Email in `local`: the mail catcher

**No email leaves a laptop.** The dev stack (`backend/docker-compose-local.yml`) runs
**Mailpit**, a mail catcher: the backend's SMTP adapter sends to it, and every email appears
in its **inbox at [`http://localhost:8025`](http://localhost:8025)**. That includes the
invitations, the resets and their codes, which a person reads there exactly as they would in a
real mailbox ([ADR-0186](adr/0186-email-goes-through-a-port-and-a-purged-queue.md) §1).

| | Inside the compose stack | uvicorn on the host |
| --- | --- | --- |
| `SMTP_HOST` | `mailpit`, the default | `localhost` (`backend/.env.example`) |
| `SMTP_PORT` | `1025` | `1025`, published by the stack |
| `SMTP_SECURITY` | `none` — refused anywhere deployed | `none` |

A use case never sends. It writes a row to the mail queue in its own transaction, and the mail
worker sends it within a couple of seconds (`MAIL_DELIVERY_INTERVAL_SECONDS`) and then **purges
the link and the code from the row**. So a code is read in the inbox, never in the database.
Seeded accounts live on the reserved `.example` domain, and the catcher shows their mail as
well.

## The rules, condensed

1. **The environment may select configuration defaults; it may never select behaviour a
   domain test could observe.** No business rule, threshold, validation, status code or
   response shape varies by environment. Enforced on the backend by an `.importlinter`
   contract, not by memory.
2. **Dangerous configuration refuses to boot**, checked where every construction path sees it.
3. **A refusal names the variable and the reason, and never the value.**
4. **A deployed environment fails loudly rather than falling back.** It is asked for its own
   host, database and ephemeral store; none of the three may be inherited from the local
   defaults. Nor may the two site addresses links are printed under, or the mail relay and
   sender. [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md)'s rule 5
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
   currently pointless — there is nothing to switch to.) **The two web apps are servers, like
   the backend**: they read their environment when the server starts, not when it is built.
   None of it is inlined into the browser's bundle — a page is handed only the addresses it
   links to, such as the tile URL or a store's — and nothing a browser sends is read as
   configuration, so no link, query parameter or form can repoint them either.
8. **The OpenAPI documents remain the source of truth for client types, in every environment.**
   The backend emits one document per surface, and each client generates its wire types from
   its own: `openapi.player.json` for the player app, `openapi.club.json` for the club website,
   `openapi.public.json` for the public site ([ADR-0006](adr/0006-backend-owns-api-contract.md),
   [ADR-0187](adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
   §5). No client hand-writes a DTO mirroring a backend response, and **no environment is an
   excuse to**: a type that is "just for local" is a type nothing regenerates. CI re-emits every
   document and regenerates every client, and diffs both, so a contract change shipped without
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
| Contract | Every document the backend emits: `openapi.{player,dev,club,public}.json`. | Two checks. **Freshness** re-emits every document and diffs the JSON (`make contract-freshness`, proven to still fire by `make test-contract-freshness`). **Drift** regenerates one client's types from its own document and diffs them (`check-contract-drift.sh <client>`, proven by `make test-drift`). |
| Web app pages (Playwright, `frontend_club/e2e/`, `frontend_public/e2e/`) | The built site, started with a configuration made for the suite, its server pointed at a **stub backend** typed from that app's generated contract. No real backend and no database. | One worker, because one server talks to one stub. Each app owns its stub. |
| End-to-end | Nothing automated. **No test crosses apps** ([ADR-0187](adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §6). | The journey across the apps is a QA plan walked by hand in `local` ([#528](https://github.com/Raketa02/Raketa/issues/528)), and in `development` or `staging` once either is provisioned. |
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
a test that no group ran, or that two did (#489). Each web app has two jobs of its own: its
static checks with its contract drift, and its Playwright suite, whose one browser (Chromium's
headless shell) is cached on the Playwright version (#527).

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
   API, and a host for each web app. **The public site answers on the domain**, since every
   group, invitation and reset link is printed under it. The club website needs an address of
   its own. Reactivating the deployment path supersedes
   [ADR-0010](adr/0010-local-first-development-aws-deferred.md) and needs its own ADR; the
   dormant pipeline's own reactivation steps are in the header of
   [`.github/workflows/deploy-ecs.yml`](../.github/workflows/deploy-ecs.yml) and in
   `backend/docs/deployment/aws-ecs.md`.
2. **Issue a TLS certificate** for every public-network host. Rule 6 is not satisfiable
   without one, which is the intended ordering.
3. **Set the backend's variables**: `APP_ENV`, and — because nothing deployed may inherit the
   local defaults — `APP_HOST`, `WRITER_DB_URL`, `REDIS_URL`, `PUBLIC_SITE_URL`,
   `CLUB_WEBSITE_URL`, `SMTP_HOST` and `MAIL_SENDER` explicitly. Then `JWT_SECRET_KEY`
   (`openssl rand -hex 32`), `PHOTO_STORAGE_SECRET_KEY`, `DB_SSL_MODE` (one of `require`,
   `verify-ca`, `verify-full`), `SMTP_SECURITY` (`starttls` or `tls`) with the relay's
   `SMTP_PORT`, `SMTP_USERNAME` and `SMTP_PASSWORD`, `PAYMENTS_PROVIDER=stripe` with
   `STRIPE_SECRET_KEY` (live in production, test everywhere else), `STRIPE_PUBLISHABLE_KEY`
   and `STRIPE_WEBHOOK_SECRET`, and `ALLOW_ORIGINS` as an explicit
   `https://` list rather than a wildcard — or an explicit empty list, which is what it is
   today. No browser calls the backend: both web apps call it from their servers, and the
   mobile app sends no `Origin` header.

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
5. **Set the club website's variables**: `APP_ENV`, `API_URL` (server to server, so any scheme
   the topology needs), `SESSION_SECRET` (`openssl rand -hex 32`; changing it later signs every
   club out), `MAP_TILE_URL` (`https://`, from the tile provider in step 7), `MAP_START` and
   `GEOCODER_URL` (server to server, from the geocoder in step 7).
6. **Set the public site's variables**: `APP_ENV`, `API_URL`, `PUBLIC_SITE_URL` (`https://`, the
   backend's own value), `APP_STORE_URL` and `GOOGLE_PLAY_URL` (`https://`), `APP_SCHEME` (the
   app's), and the four the app-link files are made from: `APPLE_TEAM_ID`, `IOS_BUNDLE_ID`,
   `ANDROID_PACKAGE` and `ANDROID_CERT_FINGERPRINTS`. Every value in its `.env.example` that
   names a store listing, a team or a signing key is a placeholder that is nobody's.
7. **Bring in what nobody has chosen yet.** Each of these is configuration the day it exists,
   and each one blocks something real until then:
   - **A domain**, from step 1. Nothing below it works without one.
   - **App links.** The public site serves `/.well-known/apple-app-site-association` and
     `/.well-known/assetlinks.json`, made from the four settings in step 6. iOS and Android read
     them only from a real `https://` domain, so tap-to-open cannot be tested before one
     exists. The player app then claims the domain: set `EXPO_PUBLIC_LINK_DOMAIN` and rebuild
     natively, since it becomes iOS's associated domain and Android's verified intent filter.
     The Android fingerprints are the release key's, plus the store's re-signing key once there
     is one.
   - **Store URLs.** `APP_STORE_URL` and `GOOGLE_PLAY_URL` are Raketa's listings, which exist
     only once the app is published.
   - **A production email sender**: a relay that sends from an address on the domain, set in
     step 3. Deliverability arrives with it: SPF, DKIM, DMARC, bounces, complaints and a
     suppression list, none of which exists today
     ([ADR-0186](adr/0186-email-goes-through-a-port-and-a-purged-queue.md)). `development` and
     `staging` get a sandbox relay, per rule 9.
   - **A map-tile provider** for `MAP_TILE_URL`. OpenStreetMap's own tile servers are for
     development only, so production needs a provider that allows its traffic, and the map
     keeps that provider's attribution
     ([ADR-0187](adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
     §3).
   - **A geocoder** for `GEOCODER_URL`, the club website's address search over the map: anything
     answering Nominatim's `/search` in its `jsonv2` shape. Nominatim's own server allows light
     use only — one request a second, the caller identified, which the website keeps — so
     production needs a provider that allows its traffic, chosen with the tile provider.
8. **Point every external service at its sandbox credentials**, per rule 9. Live keys go to
   `production` and nowhere else.
9. **Seed it** — `development` and `staging` are seedable, and the accounts are the same edges
   a laptop gets.
10. **Delete this list's assumptions as they stop being true.** The three "not provisioned"
    rows in the table at the top of this page, and the sentences in each app's `.env.example`
    saying only `local` runs, are the first things that become false.

## Where to look next

| Question | File |
| --- | --- |
| Why four environments, and why typed | [ADR-0028](adr/0028-four-environment-model-and-typed-configuration.md) |
| Why seeds go through aggregates | [ADR-0029](adr/0029-seed-data-through-aggregates-never-in-production.md) |
| The backend's settings, profile and refusals in detail | `backend/README.md`, `backend/CONTEXT.md` |
| The player app's config, app identity and badge | `frontend_player/README.md`, `frontend_player/docs/architecture.md` Part 14 |
| The web apps' configuration and its refusals | `frontend_club/src/server/config.ts`, `frontend_public/src/server/config.ts`, each app's `CLAUDE.md` |
| How email is sent, queued and purged | [ADR-0186](adr/0186-email-goes-through-a-port-and-a-purged-queue.md), the `mailpit` service in `backend/docker-compose-local.yml` |
| What each variable is, per app | each app's `.env.example` |
| Whether the deployment artifact supplies them | `make taskdef` — [`check-taskdef.sh`](../.github/scripts/check-taskdef.sh) |
