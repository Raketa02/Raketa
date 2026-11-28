# ADR-0206 — A feature is turned on by a pull request again, and Explore is the first

- **Status:** Accepted
- **Date:** 2026-11-21
- **Restates ADR-0180** (*a feature is turned on by a pull request, and decided on the device*),
  which the Classic play removal deleted with the flag machinery it decided (#576, #583). Its text
  is at `git show 5739ab07^:docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md`.
  §1–§10 below keep that record's numbering, so a `§` in the code still points at the same rule,
  **minus testers**: the tester mark left the backend in #581, and nothing here brings it back.
  ADR-0180's number is not reused, and neither is any other deleted one.
- **Supersedes [ADR-0013](0013-player-app-runtime-architecture.md)'s *Not adopted now* line for
  a feature-flag service**, for the second time. The rest of that list stands, and so does its rule
  that a dependency arrives with the code that needs it: the SDK and its saved datafile arrive with
  `explore`, the flag that needs them (§11).
- **Narrows the enforcement of [ADR-0008](0008-player-mobile-securestore-direct-api.md) again**,
  not its decision. *`AsyncStorage` must never hold a credential* stands. The allow-list
  [ADR-0188](0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
  left at one module is **two modules again** (§12).
- **Amends [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §12**:
  *Play opens on Groups | Explore* now stands **only with `explore` on**. Off, Play is titled
  *Groups*, with no switcher (§11).
- **Leaves standing** [`docs/environments.md`](../environments.md)'s *Feature flags are not
  environment configuration* word for word — a flag may be defaulted per environment, never derived
  from it. Only the page's sentence *There is no flag system today* goes.
- Settles [#826](https://github.com/Rakieta02/Rakieta/issues/826). The flags repository's half is
  `Rakieta02/rakieta-features#3`: the `explore` key, off in every environment, and the dead
  `find_a_game`, `classic_play` and `testers` definitions out. Grilled 2026-11-21 (Q1–Q23).

## Context

**The player app ships with the Groups functionality only, and Play still draws a switch to a
page that is not built.** Since #512 Play has opened on a *Groups | Explore* switcher, and Explore
is `features/find_a_game_next`'s empty screen — the place the rebuilt Find a game will grow. A
player who presses it finds nothing. The product owner wants Explore hidden until it has content,
and turned on later without a release.

**There has been no way to do that since 2026-10-06.** The Classic play removal (#569) took the
flag machinery out with the loop it hid: the Featurevisor SDK, the datafile fetch and its saved
copy, `httpGetFromFeaturesHost`, `appBuild`, the hooks and `EXPO_PUBLIC_FEATURES_URL` (#576), and
the record that decided them (#583). ADR-0013 put *a feature-flag service* back on its *Not adopted
now* list, and `docs/environments.md` said *There is no flag system today*. The flags repository,
`Rakieta02/rakieta-features`, was left unread. Everything removed is recoverable from
`6d8d1388^`, and the code it recovers was built, tested and walked on a phone.

Rejected on the way:

- **A build-time switch** — an `EXPO_PUBLIC_*` variable, or a constant — breaks the environments
  page's rule that a flag can change without a redeploy, and turning Explore on would be a release.
- **Deleting the switch** until Explore exists — Explore will be built *behind* the flag, in place,
  and a deleted switch has to be rebuilt and re-decided the day it is wanted.
- **A different flag system** — a hosted service is a vendor and a bill for one flag, and the
  toggle leaves version control. The workflow ADR-0180 chose, a pull request to a YAML repository,
  is the one the author trusts, and it already exists.
- **A flag client with no flag**, restored first and gated later — ADR-0013's rule is that a
  dependency arrives with the code that needs it, so the client and its first flag land together.

## Decision

**We adopt [Featurevisor](https://featurevisor.com) again, as ADR-0180 decided it, minus the
tester mark, and gate Play's Explore with it.**

1. **Feature flags live in their own repository and change by pull request.** The definitions are
   YAML in **`Rakieta02/rakieta-features`** (private), not in this monorepo. A feature is toggled by a
   pull request there; its CI lints the definitions, runs their test specs and builds one JSON
   **datafile** per environment. **Every feature carries a test spec**, so a pull request states the
   effect it intends and proves it. Featurevisor's state files are committed back by the publish
   run on `main` and never appear in a pull request.

2. **Its environments are ours, spelled as ours** — `local`, `development`, `staging` and
   `production`. A feature's value may differ per environment **in the flags repo**; the app picks
   the datafile for the environment it was built for and never branches on the environment to
   decide a feature.

3. **One target, `player`.** Each environment builds `datafiles/<environment>/featurevisor-player.json`.

4. **The datafile is served from a configured URL.** The player app reads its base from
   `EXPO_PUBLIC_FEATURES_URL`, **required** and validated like `EXPO_PUBLIC_API_URL`, the scheme rule
   included: plain `http` in `local` only. Today it is the developer's own machine, serving the built
   datafiles with the flags repo's `npm run serve` on port 3040; later it is a bucket the publish run
   uploads to, and moving there changes configuration, never code. **Hosting is not part of this
   decision**: the upload step stays skipped while `DATAFILES_BUCKET` and `DATAFILES_ROLE_ARN` are
   unset, and they stay unset until Explore is ready to turn on. Until then, off a developer's
   machine, there is no datafile.

5. **Evaluation happens in the client only.** The player app evaluates every feature locally with
   the Featurevisor SDK, behind one module that holds the instance and answers *is feature X
   enabled?* The backend evaluates nothing and guards nothing: Explore's page has no endpoint, and
   turning a screen off hides it.

6. **Fallback order: fresh datafile, then the saved one, then the code default.** The app fetches
   the datafile through the shared HTTP client — unauthenticated, the background timeout class — at
   cold start and on every return to the foreground, and **nothing waits on it**: never a bootstrap
   step, never a spinner. Each readable datafile is kept raw in AsyncStorage and read back at the
   next launch. Every key is declared **once** in the client beside its **code default**, which is
   what a phone with neither datafile gets.

7. **A gated screen reads its feature flag once, when it mounts** (`useFeatureOnMount`). It does
   not re-render when the value changes underneath it, so nothing appears or vanishes under a
   player's thumb; a merged toggle reaches a running app at its next cold start or foreground and
   takes effect at the gated screen's next mount. ADR-0180's second reader, `useFollowedFeature`,
   which followed a flag for the tab bar's Classic play columns, is **not** restored: no chrome is
   gated.

8. **`bucketBy: playerId`**, so a rollout follows the account, not the device. **The evaluation
   context is `playerId`, `platform` (`ios` / `android`) and `appVersion` (semver)**, and with no
   signed-in player there is no context: every key is its code default.

9. **No datafile names a player, and there is no tester mark.** `playerId` is in the context for
   `bucketBy` alone, and a rule or segment on one is refused by the flags repo's own lint, because
   the file it would land in is public. ADR-0180's `isTester` attribute and `testers` segment do not
   come back. A later need to show a feature to some players first is its own decision.

10. **Versions are pinned together, and an unknown format is refused.** The app pins
    `@featurevisor/sdk` exactly at **3.8.0**, the version paired with the flags repo's CLI
    **3.11.0**, whose datafiles carry `schemaVersion` `'2'`. A datafile with any other
    `schemaVersion` is refused, and the one in use stays in use — the saved one, or failing that the
    code defaults. The CLI's major moves only with the SDK's.

11. **The first feature flag is `explore`, and it is off** — in code and in every environment's
    definition.
    - **Anything unknown counts as off**: no datafile yet, offline, a host that never answers, a
      datafile refused with none saved, no signed-in player. The switcher is drawn only on an
      explicit **on**.
    - **Off, Explore is unreachable.** Play is the Administrator's Groups pattern: a pinned screen
      header titled **Groups** — an h1, with no eyebrow, no sub-line and nothing on the right — over
      the groups list, unchanged, with **+ New** and **Join** where they are. No segment is drawn.
      The remembered Play segment is the only way into Explore, so while off a saved `explore` is
      **read past and never written**: Play shows Groups, and the stored choice stays the player's
      (ADR-0188) for the day the flag comes on.
    - **On is today, unchanged**: the switcher, Groups first, the remembered segment honoured.
    - Play reads it once, when it mounts (§7). The bottom tab stays **Play**.
    - **Its record** — **Owner:** the product owner, with the shell as the gate's code owner.
      **Purpose:** keep Play to Groups while Explore is unbuilt. **Default:** off. **Rollout:**
      decided when Explore has content; a percentage by `playerId`, in the flags repo.
      **Removal:** once it is on for everyone in production, the key, the flags repo's definition
      and spec, the gate and the toggle-off branch go together.

12. **The AsyncStorage allow-list is two modules again**: the feature flags' saved datafile
    (`features/feature_flags/api/datafileCache.ts`), which is public and names no player (§9), and
    ADR-0188's phone-preferences store. The SDK is importable from one module only
    (`features/feature_flags/api/featurevisor.ts`). `scripts/test-import-boundaries.sh` drives the
    linter at code breaking each fence and asserts it goes red.

13. **The word is *feature flag*, never a bare *flag*,** in the player app's code, copy and docs.
    The app already says *flag* for the per-phone marks kept at sign-out
    ([ADR-0200](0200-a-level-is-asked-where-play-begins.md) §8), and the two are different things: a
    phone flag is raised by the phone and kept; a feature flag is decided in another repository and
    only read here.

## Consequences

**Easier**

- Explore is out of a shipping app's way without being deleted, and turning it on is a reviewed
  pull request in the flags repo and a hosted datafile — no release.
- The same seam serves the next unbuilt feature: a key and its default in one file, and a gate.
- Every rule ADR-0180 learned the hard way comes back with it — the refusal of an unknown format,
  the saved datafile, the read-once gate, the unauthenticated background read — tested as it was.

**Harder**

- **Two repositories must agree, and nothing checks it across them.** Both must spell the key
  `explore`. A key declared in the client and missing from the datafile evaluates to its code
  default, silently, so a typo is a feature that never turns on.
- **Nothing is hosted, so no real phone can turn it on yet.** Off a developer's machine every phone
  runs the code default. Turning Explore on for players is a later decision with real work: a
  bucket, a role CI assumes, the two repository variables, and step 4 of the environments
  checklist.
- **Every developer's real `frontend_player/.env.local` needs a new line**, `EXPO_PUBLIC_FEATURES_URL`,
  or the app refuses to start naming it. It is a human step — an agent may not edit a `.env` file —
  and it lands on everyone at once.
- **A toggle is not instant**: next cold start or foreground, then the gated screen's next mount.
- **Client-only evaluation hides, it does not forbid.** Harmless for Explore, which has no
  endpoint; the first flag that must guard behaviour reopens §5.
- **The version pin is a manual discipline.** Nothing compares the flags repo's CLI major with the
  app's SDK major; getting it wrong fails safe but silently.
- **A saved `explore` lingers.** A player who chose Explore before this ships keeps that choice on
  the phone, unread, until the flag comes on or they sign out.
- **This is the second reversal of the same decision within seven weeks.** The record is restated
  rather than undeleted because #569 ruled that deleted records stay deleted; a reader following
  `§` references from the code must read this record, not the deleted one.
- A dependency, the Featurevisor SDK, joins the player app again, and AsyncStorage's fence grows
  back to two.
