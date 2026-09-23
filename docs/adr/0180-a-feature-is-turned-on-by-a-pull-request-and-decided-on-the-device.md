# ADR-0180 — A feature is turned on by a pull request, and decided on the device

- **Status:** Accepted
- **Date:** 2026-09-23
- **Supersedes** [ADR-0013](0013-player-app-runtime-architecture.md)'s *Not adopted now* line
  for **a feature-flag service** only. The rest of that list — `openapi-fetch`, Sentry,
  Maestro, React Hook Form, `expo-network`/netinfo — stands, and so does its rule that a
  dependency arrives with the code that needs it: the SDK and AsyncStorage arrive with
  [#479](https://github.com/Raketa02/Raketa/issues/479).
- **Leaves standing** [`docs/environments.md`](../environments.md)'s *Feature flags are not
  environment configuration* word for word — **a flag may be defaulted per environment, never
  derived from it.** This record is the flag system that rule was written for; only the page's
  sentence *there is no flag system today, and none is in scope* goes.
- **Narrows the enforcement of** [ADR-0008](0008-player-mobile-securestore-direct-api.md),
  not its decision. *`AsyncStorage` must never hold a credential* stands; a datafile is not one.
  But the player app's lint bans `@react-native-async-storage/async-storage` everywhere under
  `src/`, and `scripts/test-import-boundaries.sh` proves the ban. #479 lets **one** module, the
  flag wrapper's own cache, import it, and the boundary test keeps asserting the ban everywhere
  else.
- **Amends** the root glossary: **Feature flag** is defined, and **Tester** joins the Users
  context as a mark on the account, **not an `Authority`**.
- Settles [#476](https://github.com/Raketa02/Raketa/issues/476) (PRD) and
  [#477](https://github.com/Raketa02/Raketa/issues/477). The backend's half is
  [#478](https://github.com/Raketa02/Raketa/issues/478), the client's
  [#479](https://github.com/Raketa02/Raketa/issues/479). Grilled 2026-09-23.

## Context

**There is no way to turn a part of the player app off without shipping a build.** The Play
tab's **Find a game** is about to be rebuilt, and the rebuild needs somewhere to live while
the current version keeps working — then a way to reach players gradually: the testers first,
then a share of players, then everyone.

The repo has twice said no to this. ADR-0013 lists *a feature-flag service* under *Not adopted
now*, and `docs/environments.md` says *There is no flag system today, and none is in scope*.
The same page recorded, ahead of time, the rule the first flag system must obey — **a flag may
be defaulted per environment, never derived from it** — precisely so it would not arrive as an
`if environment === 'staging'` branch. That trigger has now fired: a feature needs to be
replaced in place.

Four forces shaped the answer:

- **The author's past projects toggled features by pull request to a separate YAML
  repository.** That workflow is the one they trust: the diff is the change, a review is the
  approval, and history is `git log`.
- **There is no CDN and no AWS work yet.** Only `local` runs. Whatever is chosen has to work
  from the developer's Mac on the LAN today and from S3 later, without code changing between
  the two.
- **The splash screen must not wait on it.** ADR-0013 spent real care on the first 400 ms of
  launch; a network call on that path to decide a flag would undo it.
- **The datafile is public-read.** Anything written into it — a list of tester ids, a
  segment on one `playerId` — is published to anyone who can guess the URL.

Rejected on the way: a hosted flag service (a vendor and a bill for one flag, and the toggle
leaves version control); an environment variable per feature (a redeploy per toggle, which is
the thing being removed); OTA updates via `expo-updates` (a build pipeline to change one
boolean); and a datafile snapshot bundled into the app as a last fallback (a committed
snapshot drifts silently — nobody regenerates it, and the day it is read it says something
nobody decided).

## Decision

**We adopt [Featurevisor](https://featurevisor.com), following its own workflow.**

1. **Flags live in their own repository and change by pull request.** The definitions are
   YAML in **`Raketa02/raketa-features`** (private), not in this monorepo. A feature is
   toggled by a pull request there; its CI lints the definitions, runs their test specs and
   builds one JSON **datafile** per environment. **Every feature carries a test spec**, so a
   pull request states the effect it intends and proves it. Featurevisor's state files —
   what keeps a rollout's buckets stable as its percentage rises — are committed back by the
   publish run on `main` and never appear in a pull request. The repository has no PRD or
   tickets of its own; this record is its decision.

2. **Its environments are ours, spelled as ours.** Exactly `local`, `development`, `staging`
   and `production` ([`docs/environments.md`](../environments.md)). A feature's value may
   differ per environment **in the flags repo**; the app picks the datafile for the
   environment it was built for and never branches on the environment to decide a feature.
   That is *defaulted per environment, never derived from it*, made structural. A feature
   that is not ready is off everywhere, production included, and ships by being turned on.

3. **One target, `player`.** Each environment builds a single datafile for the player app,
   `datafiles/<environment>/featurevisor-player.json`. A backend target would be added beside
   it, the day §5 is reopened.

4. **The datafile is served from a configured URL.** The client reads its base from
   `EXPO_PUBLIC_FEATURES_URL`, validated like `EXPO_PUBLIC_API_URL`, scheme rule included:
   plain `http` in `local` only. Today it is the Mac's LAN address, served by the flags repo's
   own serve script; later it is an S3 bucket the publish run uploads to. **No CDN is
   required**, and moving from the Mac to S3 changes configuration, never code. The upload
   step is written and stays skipped until two repository variables are set: the bucket
   (`DATAFILES_BUCKET`) and the role CI assumes to write to it (`DATAFILES_ROLE_ARN`).

5. **Evaluation happens in the client only.** The player app evaluates every feature locally
   with the Featurevisor SDK, behind one module of its own that holds the instance, sets the
   context and answers one question: *is feature X enabled?* The backend evaluates nothing
   and does not guard the endpoints behind a gated screen — turning a screen off hides it, it
   does not close the door behind it. Adding a backend SDK is its own later decision, made the
   first time a flag has to guard backend behaviour.

6. **Fallback order: fresh datafile, then cache, then code default.** The app fetches the
   datafile through the shared HTTP client in one non-blocking query, at launch and again when
   it returns to the foreground — **never a bootstrap step**, so the splash never waits on it.
   Each good datafile is kept raw in AsyncStorage and read back on the next launch; SecureStore
   stays for credentials only. Every feature key is declared **once** in the client beside its
   **code default**, which is what a first launch with no network gets. `find_a_game` defaults
   to enabled.

7. **A gated screen reads its flag once, when it mounts.** It does not re-render when the value
   changes underneath it. A merged toggle reaches a running app at its next cold start or
   foreground and takes effect the next time the gated screen mounts, so nobody has a screen
   pulled out from under them mid-task. The first gate is **`find_a_game`** on the Play root;
   its builder and pool routes redirect to the Play root while it is off, and fill-the-seat and
   the Players tab are untouched.

8. **`bucketBy: playerId`.** A player's rollout bucket follows their account, not their
   device, so they see the same thing on every device, and raising a percentage keeps everyone
   already in. The context the app sends is `playerId`, `platform` (`ios` / `android`),
   `appVersion` (semver) and `isTester`.

9. **Testers are a backend-owned mark, and no datafile names a player.** A **Tester** is a
   player whose account carries the tester mark — two idempotent events on the `User`
   aggregate, set and cleared by an admin command through a use case, and read as a required
   `is_tester` on `GET /api/v1/users/me`. It is **not a role**: `Authority` stays `USER` or
   `ADMIN`, because being shown a feature early grants no power over anyone. The app sends the
   mark as `isTester`, and the flags repo targets it through a `testers` segment. `playerId`
   exists in the context for `bucketBy` alone; **a segment or rule on a `playerId` is refused
   by the flags repo's own lint**, because the file it would land in is public.

10. **Versions are pinned together, and an unknown format is refused.** The flags repo pins
    its Featurevisor CLI exactly, and **its major moves only with the player app's SDK major**.
    A datafile carries a `schemaVersion` (today `"2"`); the app refuses one it does not know
    and keeps using the last good datafile it has — the cache, or failing that the code
    defaults. An upgrade in the flags repo that changes the format therefore stops installed
    apps from *updating*, never from *working*.

## Consequences

**Easier**

- Find a game can be replaced in place: the placeholder ships behind `find_a_game`, and the
  new version arrives behind the same key, testers first.
- A toggle is a reviewed diff with a spec beside it and a history in `git log`, not a click in
  a dashboard nobody audits.
- The environment rule stops being a promise. Per-environment values live in one YAML file in
  another repository, where no app code can reach them to branch on.
- Launch is untouched: the fetch is a background query, and the splash waits on nothing new.
- Going from the Mac to S3 is a changed URL and a set repository variable.

**Harder**

- **Two repositories must agree, and nothing checks it across them.** A feature key declared
  in the client and missing from the datafile evaluates to its code default, silently. The
  client's declaration of every key with its default is the only list, and a typo there is a
  feature that never turns off.
- **A toggle is not instant.** It reaches a running app at the next cold start or foreground,
  and a gated screen at its next mount. There is no push and no kill switch that acts inside a
  second, and anyone who needs one has to reopen §6 and §7.
- **Client-only evaluation hides, it does not forbid.** With `find_a_game` off, the builder and
  pool endpoints still answer anyone who calls them. That is acceptable for replacing a screen
  and wrong for anything that must not happen; the first such flag reopens §5.
- **The version pin is a manual discipline.** Nothing in either CI compares the flags repo's
  CLI major with the app's SDK major. Getting it wrong fails safe — installed apps keep their
  last good datafile — but it fails *silently*: nobody's toggles arrive, and nothing says so.
- **Only `local` has a consumer.** The other three datafiles are built with no app reading
  them, so a mistake in them is found the day an environment is turned on.
- **The flags repo cannot enforce review.** `Raketa02` is a free account, and a private
  repository there has no branch protection; *one review before merge* is a convention only.
- **AsyncStorage stops being banned outright.** One module may import it, and the lint
  message that says *never* becomes *only here, and never a credential*. The fence against a
  token landing in plaintext is now an allow-list of one, which a later module can ask to join.
- A new dependency pair, the Featurevisor SDK and AsyncStorage, joins the player app, and the
  tester mark adds two events to the `User` stream that will be replayed forever.
