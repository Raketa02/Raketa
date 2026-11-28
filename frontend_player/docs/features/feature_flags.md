# feature_flags — the datafile, the gate, and the code defaults

> The design record for `src/features/feature_flags/` — what the feature does and the reasons the
> shape is what it is, one paragraph per decision. **Append here** when a ticket changes what this
> feature does. Index: [`README.md`](README.md).

**A feature is turned on by a pull request to another repository and decided on the device, and
this feature is the device's half**
([#826](https://github.com/Rakieta02/Rakieta/issues/826),
[ADR-0206](../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)).
Feature flags are YAML in `Rakieta02/rakieta-features`, built into one JSON datafile per environment
and served from `EXPO_PUBLIC_FEATURES_URL`. The app fetches
`<it>/<environment>/featurevisor-player.json`, evaluates locally with the Featurevisor SDK (3.8.0,
pinned exactly, paired with the flags repo's CLI 3.11.0), and answers one question: _is this feature
enabled for this player?_ The public surface is two hooks and a name — `useFeatureDatafile`,
`useFeatureOnMount`, `FeatureKey` — plus the key factory the router harness waits on.

**It came back from git** ([#826](https://github.com/Rakieta02/Rakieta/issues/826)). The slice was
first built for `find_a_game` (#479), became `classic_play`'s (#550), and was removed with the loop
that key hid (#576), its record ADR-0180 deleted with it (#583). It is restored as it was at
`6d8d1388^` — the fetch, the saved copy, the SDK wrapper, the schema, the queries, the gate and
their unit tests — **minus two things**: the tester mark (the account carries none since #581, so
the context has no `isTester` and the flags repo no `testers` segment), and `useFollowedFeature`,
which followed a feature flag for the tab bar's Classic play columns and has no chrome to serve.
ADR-0206 restates ADR-0180 with the same section numbers, so every `§` below and in the code reads
there. **The word is _feature flag_, never a bare _flag_**: the app already says _flag_ for the two
marks the phone keeps at sign-out (ADR-0200 §8, `readPhoneFlag`).

**Every key is declared once, beside its code default and its record, in
`domain/featureFlags.ts`.** That list is the only one there is: nothing checks the client against
the flags repo, so a key missing from the datafile evaluates to its code default, silently. The code
default is the app _as it ships_ and is what a first launch with no network gets. `FeatureKey` is
the list's own key type, so a gate naming an undeclared key does not compile. **The one key is
`explore`, off** — Play's Explore segment, gated in the shell ([`shell.md`](shell.md)). Its record
sits on the key: owned by the product owner, with the shell as the gate's code owner; there to keep
Play to Groups while Explore is unbuilt; off; rolled out, when Explore has content, as a percentage
by `playerId` in the flags repo; and removed — key, the flags repo's definition and spec, the gate
and its toggle-off branch together — once it is on for everyone in production.

**Fresh, then cached, then code default — and nobody waits for any of them** (§6). Two queries,
both started by `useFeatureDatafile` from the `(app)` layout on the same moment as the location
refresh (`entry.kind === 'app'`): the saved datafile read back from AsyncStorage, and a fresh one
fetched through `shared/lib/http`'s third verb, `httpGetFromFeaturesHost`. The fresh query is
`staleTime: Infinity` with `refetchOnWindowFocus: 'always'` — nothing refetches it but a return to
the front, and every return does — and **`retry: false`**, against the app default: a failed read
already has its answer in hand and its next attempt already scheduled, and a retry on a timer spends
data on a read nobody is waiting for. The saved query is `networkMode: 'always'`, because under the
app default it would be paused offline, which is exactly when it is the only datafile there is.
Neither is a bootstrap step.

**A datafile is checked before the SDK sees it, and a refusal keeps the one in use** (§10).
`schemas/datafileSchema.ts` checks the envelope `createFeaturevisor` requires and the
`schemaVersion` against `READABLE_SCHEMA_VERSIONS` (`'2'` today). The SDK's own answer to a bad
datafile is to report it and carry on with an empty one — every feature at its default, a good
datafile pushed out — so the check is ours. A refused fetch fails the query with a terminal
`AppError`; Query keeps the last good `data`, so a datafile refused mid-session leaves the one
fetched earlier in use, and the saved copy is never overwritten with one the next launch could not
read. The same check runs on the saved copy on the way out: an older build may have written it.

**The SDK is one file, and so is this feature's AsyncStorage** — `api/featurevisor.ts` and
`api/datafileCache.ts`. The wrapper is the SDK's only importer; the cache is one of two AsyncStorage
importers, beside the phone-preferences store (ADR-0188), and both fences are enforced by the lint
and proved by `pnpm test:boundaries`. The wrapper holds one instance and replaces its datafile when
handed a new one; the context travels with each question rather than being set on the instance, so
nothing about a signed-out player stays behind in it. **A feature the datafile does not name is
`undefined`, not `false`** — the SDK says `false`, which would switch a screen off for everybody over
a key the two repositories disagree about — and the use case answers `undefined` with the code
default. The SDK's diagnostics are routed nowhere: its console reporter prints the evaluation
context, a player id in a device log, and there is no observability module yet. The cache never
throws: a failed read is no cache and a failed write loses only the next launch's copy. It is keyed
`rakieta.feature-flags.datafile.<environment>`, outside the preferences store's prefix, so sign-out
does not empty it: it is public and names no player.

**The context is `playerId`, `platform`, `appVersion`** (§8, `EvaluationContext`), spelled as the
flags repo spells them. The first comes off the signed-in player auth already holds, and the other
two off `shared/lib/platform`'s `appBuild()`, each absent rather than guessed when the build cannot
say. **No tester mark** (§9). With no signed-in player every feature is at its default: a rollout
buckets by player, and there is nobody to bucket.

**A gate reads once, when its screen mounts, from the cache, and subscribes to nothing** (§7).
`useFeatureOnMount` evaluates inside a `useState` initialiser against whatever the two queries
hold at that moment. A subscription could only deliver an answer the gate has promised to ignore,
and an observer on `/users/me` would refetch it on every mount of every gated screen. The one gate
is Play's, on `explore`.

**The walks.** The pure rungs are unit-tested here — `domain/featureFlags.test.ts`,
`schemas/datafileSchema.test.ts` and `use-cases/isFeatureEnabled.test.ts`, the last against the real
SDK with the plainest _on_ and _off_ datafiles. The gate's walks are the shell's
`components/theExploreGate.test.tsx`: the real route tree, the real SDK, the datafile stubbed at the
socket (`stubDatafile`, `datafileFor`), and every walk waiting on `datafileSettled` before it mounts
the screen it asks about, because a gate that mounted first would be — correctly — answering from
the rung below. **Every walk that proves a saved or refused datafile is still in force saves _on_**:
with the default off, a walk that saved off would pass with the cache broken, and
`isFeatureEnabled`'s _nothing to say_ walks raise the default to on for their length
(`jest.replaceProperty`) for the same reason. `stubGate` serves no datafile (a 404), so every other
suite runs on the code defaults; a suite that walks the switcher calls `launchWithExplore`, and
jest's setup empties AsyncStorage after every test so a saved datafile never switches Explore on in
the next one.

**Nothing is hosted yet** (ADR-0206 §4). The flags repo's publish run skips its upload while
`DATAFILES_BUCKET` and `DATAFILES_ROLE_ARN` are unset, and they stay unset until Explore is ready.
So the only datafile any phone can read is one a developer serves with the flags repo's
`npm run serve`, at `http://<machine LAN IP>:3040` in `EXPO_PUBLIC_FEATURES_URL`; everywhere else,
`explore` is its code default, off. The variable is required anyway, under the scheme rule, so a
build with no flags host fails at launch naming it rather than running on defaults forever with
nothing saying so.
