# feature_flags — the datafile, the gate, and the code defaults

> The design record for `src/features/feature_flags/` — what the feature does and the reasons the
> shape is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**A feature is turned on by a pull request to another repository and decided on the device, and
this feature is the device's half**
([#479](https://github.com/Raketa02/Raketa/issues/479),
[ADR-0180](../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).
Flags are YAML in `Raketa02/raketa-features`, built into one JSON datafile per environment and
served from `EXPO_PUBLIC_FEATURES_URL`. The app fetches `<it>/<environment>/featurevisor-player.json`,
evaluates locally with the Featurevisor SDK (3.8.0, pinned exactly), and answers one question: _is
this feature enabled for this player?_ The public surface is two hooks and a name —
`useFeatureDatafile`, `useFeatureOnMount`, `FeatureKey` — plus the key factory the router harness
waits on.

**Every key is declared once, beside its code default, in `domain/featureFlags.ts`.** That list
is the only one there is: nothing checks the client against the flags repo, so a key missing from
the datafile evaluates to its code default, silently. The code default is the app _as it ships_ —
`find_a_game: true` — and is what a first launch with no network gets. `FeatureKey` is the list's
own key type, so a gate naming an undeclared key does not compile.

**Fresh, then cached, then code default — and nobody waits for any of them** (§6). Two queries,
both started by `useFeatureDatafile` from the `(app)` layout on the same moment as the location
refresh (`entry.kind === 'app'`): the saved datafile read back from AsyncStorage, and a fresh one
fetched through `shared/lib/http`'s third verb. The fresh query is `staleTime: Infinity` with
`refetchOnWindowFocus: 'always'` — nothing refetches it but a return to the front, and every return
does — and **`retry: false`**, against the app default: a failed read already has its answer in hand
and its next attempt already scheduled, and a retry on a timer spends data on a read nobody is
waiting for. The saved query is `networkMode: 'always'`, because under the app default it would be
paused offline, which is exactly when it is the only datafile there is. Neither is a bootstrap step.

**A datafile is checked before the SDK sees it, and a refusal keeps the one in use** (§10).
`schemas/datafileSchema.ts` checks the envelope `createFeaturevisor` requires and the
`schemaVersion` against `READABLE_SCHEMA_VERSIONS` (`'2'` today). The SDK's own answer to a bad
datafile is to report it and carry on with an empty one — every feature at its default, a good
datafile pushed out — so the check is ours. A refused fetch fails the query with a terminal
`AppError`; Query keeps the last good `data`, so a datafile refused mid-session leaves the one
fetched earlier in use, and the saved copy is never overwritten with one the next launch could not
read. The same check runs on the saved copy on the way out: an older build may have written it.

**The SDK is one file, and so is AsyncStorage** — `api/featurevisor.ts` and `api/datafileCache.ts`,
each the only importer of its module, both enforced by the lint and proved by
`pnpm test:boundaries`. The wrapper holds one instance and replaces its datafile when handed a new
one; the context travels with each question rather than being set on the instance, so nothing about
a signed-out player stays behind in it. **A feature the datafile does not name is `undefined`, not
`false`** — the SDK says `false`, which would switch a screen off for everybody over a key the two
repositories disagree about — and the use case answers `undefined` with the code default. The
SDK's diagnostics are routed nowhere: its console reporter prints the evaluation context, a player
id in a device log, and there is no observability module yet. The cache never throws: a failed
read is no cache and a failed write loses only the next launch's copy.

**The context is `playerId`, `isTester`, `platform`, `appVersion`** (§8), spelled as the flags
repo spells them. The first two come off the signed-in player auth already holds —
`AuthenticatedUser.isTester` is the tester mark from `/users/me` — and the last two off
`shared/lib/platform`'s `appBuild()`, each absent rather than guessed when the build cannot say.
With no signed-in player every feature is at its default: a rollout buckets by player, and there is
nobody to bucket.

**A gate reads once, when its screen mounts, from the cache, and subscribes to nothing** (§7).
`useFeatureOnMount` evaluates inside a `useState` initialiser against whatever the two queries
hold at that moment. A subscription could only deliver an answer the gate has promised to ignore,
and an observer on `/users/me` would refetch it on every mount of every gated screen. The first
gates are Play's three routes — see [`play.md`](play.md).

**The walks** are `components/theFindAGameGate.test.tsx`: the real route tree, the real SDK, the
datafile stubbed at the socket (`stubDatafile`, `datafileFor`), and every walk waiting on
`datafileSettled` before it mounts the screen it asks about, because a gate that mounted first
would be — correctly — answering from the rung below. `stubGate` serves no datafile, so every other
suite runs on the code defaults, and jest's setup empties AsyncStorage after every test so a saved
datafile never leaks into the next one. The toggle arriving mid-search is walked in
`play/components/pool.test.tsx`, and fill-the-seat's two walks are in
`challenges/components/challengeFill.test.tsx`. **Seen on a device on 2026-09-23**: the `local`
rule turned off and on through the flags repo's serve script, each change showing at the next Play
mount after a return to the foreground.

**`find_a_game` defaults to off since [#512](https://github.com/Raketa02/Raketa/issues/512)**, and
off is Play › Groups (PRD #500): the app as it ships is the _Groups | Explore_ segment, and on
restores Find a game whole (story 141). The code default was _the app as it ships_ and still is —
what ships changed. Two consequences for the walks. **Every suite about Find a game switches the
flag on** through `launchIntoFindAGame` in `test-support/onboardingRouter.tsx`, which serves the
datafile and waits on it before Play is pressed, because a gate reads once on mount and a press
that raced the datafile would — correctly — land on Groups. And **every walk that proves a cached
or refused datafile is still in use now saves _on_**: with the default off, a walk that saved off
would pass with the cache broken. `isFeatureEnabled`'s _nothing to say_ walks raise the default to
on for their length (`jest.replaceProperty`), for the same reason — the SDK's own `false` and an
off default would otherwise agree. The flags repo's local datafile is the other half of PRD #500's
ruling and is [#521](https://github.com/Raketa02/Raketa/issues/521)'s, a human ticket.

**`classic_play` replaced `find_a_game`, and the bar follows it**
([#550](https://github.com/Raketa02/Raketa/issues/550),
[ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6). The
grilling ruled **one flag for the old loop** (Q42) — the Players deck, the Chats tab, challenges
with their plan and Find a game come back together — so `find_a_game` is gone from
`FEATURE_DEFAULTS` rather than kept beside it, and `classic_play` is the only key, **off by
default**. Play's three routes read it where they read `find_a_game`, unchanged in shape. The new
reader is the tab bar, and it could not be a gate: it mounts with the signed-in app before either
datafile has been read and stays up for the session, so a read at mount would answer the code
default every launch. **`useFollowedFeature` answers again whenever a datafile lands** — two disabled
observers on the reads `useFeatureDatafile` owns, so it adds no request and no refetch on focus —
and **the player observed**, so a tester mark that changes mid-session reaches the bar on its own
(one more observer on `/users/me` in a component mounted once; `flagContextFor` is shared with the
gate, which still reads the player from the cache). The shell also stops reading `GET /challenges`
for Chats' badge while the flag is off (`useChallengesWaiting(active)`). That is still §7's
_next cold start or foreground_; what changes is chrome, never the screen under it, and a screen
still uses `useFeatureOnMount`. The walks moved to `components/theClassicPlayGate.test.tsx`, which
adds the bar's side of every case, and `launchIntoFindAGame` is `launchIntoClassicPlay`. **The flags
repo is [#532](https://github.com/Raketa02/Raketa/issues/532)'s** (a human ticket): until it
declares `classic_play`, every environment gets the code default — off — and its `find_a_game`
definition is read by nothing and can be retired there.
