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
datafile never leaks into the next one. Fill-the-seat's two walks are in
`challenges/components/challengeFill.test.tsx`. **Not seen on a device.**
