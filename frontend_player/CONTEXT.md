# Raketa Player App — Technical Vocabulary

This file holds **player-app-only technical vocabulary**. It does **not** define domain
language — those terms (User, Authority, Sport, Assessment, Skill rating, statuses,
events) live once in the
shared glossary [`../CONTEXT.md`](../CONTEXT.md), which all three apps obey. See
[`../CONTEXT-MAP.md`](../CONTEXT-MAP.md) for the topology.

> When you name a mobile architecture concept, use the term as defined here. When you
> name a _domain_ concept, use the root glossary. Don't drift to synonyms either avoids.

## Glossary — player-app technical terms

- **Feature** — a vertical slice under `src/features/<name>/` owning a user-facing
  capability, split into the full layer set (`domain/ use-cases/ api/ mappers/
schemas/ components/ hooks/ types.ts`). _Avoid_: module, screen-folder.
- **Screen** — an expo-router route file under `src/app/`. Thin: it composes a feature's
  components and owns navigation, nothing else. _Avoid_: page, view.
- **Wire type** — a raw request/response shape **generated** from the backend's
  `openapi.json` into `src/generated/`. _Avoid_: DTO (a wire type is the _input_ to
  building a DTO).
- **DTO** — the app's **own** transport object, built in a feature's `api/` layer from a
  wire type. Owned here; never imported from `generated/` directly.
- **Domain object** — a feature's entity/value object in `domain/`: the mapped,
  rule-bearing form a use-case and the UI work with. Pure TS, no React Native/Expo.
- **Mapper** — pure function converting wire DTO ⇄ domain object, in `mappers/`. The
  single place the wire shape is allowed to influence domain shape.
- **Use-case** — one function per workflow in `use-cases/`, orchestrating domain +
  ports. The home of business orchestration. _Avoid_: service, controller.
- **Secure store** — the OS keychain (iOS Keychain / Android Keystore) via
  `expo-secure-store`, where access and refresh tokens live. Reached **only** through
  `src/shared/lib/auth`. _Avoid_: local storage, AsyncStorage (that is unencrypted and
  must never hold a credential).
- **Token rotation** — the 401 → refresh → retry cycle implemented once in
  `src/shared/lib/http`. Single-flight: concurrent 401s wait on one refresh rather than
  each firing their own. _Avoid_: refreshing inside a feature's `api/` layer.
- **Query / Mutation** — TanStack Query primitives used in `hooks/` for reads (including
  polling via `refetchInterval`) and writes, always against FastAPI through
  `shared/lib/http`. _Avoid_: calling `fetch` from a component.
- **UI state** — cross-cutting client state (filters, sheet open/close) held in
  **Zustand**. Server data is _not_ UI state — TanStack owns that.
- **Public surface** — a feature's `types.ts`. The only file another feature or a route
  may import from it. _Avoid_: "barrel", "index" — this app has no `index.ts`, and the
  word "barrel" suggests re-exporting everything, which is the opposite of the intent.
- **Public config** — any value in the native config's `extra` or an `EXPO_PUBLIC_*`
  variable. It ships inside the bundle and is readable from a released app. _Avoid_:
  calling these "env secrets" — the word invites someone to put a real one there.
- **Environment** — which deployment of the platform this build talks to:
  `local | development | staging | production`, spelled identically in all three apps.
  `local` is a developer's own machine and is the only one that runs today. _Avoid_:
  `dev`, `prod`, `test` — the first two are the spellings the backend used to accept and
  now refuses, and a test run happens on a laptop or a CI runner, both of which are
  `local`. _Avoid also_: calling a laptop `development`, which is the name that means a
  shared remote deployment.
- **Scheme rule** — the environment fixes the API URL's scheme: `https://` in the three
  deployed environments, either in `local`. Validated across both variables at launch, so
  a laptop URL under a deployed name is a refusal naming both rather than a build pointing
  at nothing. This is the **public-network** form of the platform's rule — the URL is
  reached from a phone over the internet — and `local` is unconstrained because every
  tunnel a physical device needs is `https://`. Defined once for all three apps in
  [`../docs/environments.md`](../docs/environments.md). The rule stays silent when the URL
  itself is malformed: a failed field leaves zod's result _dirty_ rather than aborting it,
  so without that guard one typo produced two complaints.
- **App identity** — what the app calls itself in a given environment: the display name
  under the icon, and the badge, as one pure function (`shared/config/appIdentity.ts`).
  One decision, because it is one sentence — _this build is not production_ — said in the
  two places a person looks. `production` is the only unbadged one and the only one whose
  name is bare. _Avoid_: reading it from `expo-constants`; it is derived from the
  environment, never stored.
- **Environment badge** — the amber pill over every screen naming the environment,
  absent entirely in `production`. It is a developer aid, so it never intercepts a touch
  and it is never the thing a rule keys on. _Avoid_: treating its absence as proof of
  production — the badge reads the environment, not the other way round.
- **Installable variant** — one bundle identifier, one package name, one URL scheme, at
  every environment. Per-environment identifiers wait until there is a second backend to
  point them at; until then three installable apps would all reach the same laptop.
- **Prebuild output** — the generated `android/` and `ios/` directories from
  `expo prebuild`. Build artifacts, not source; not committed.

## Glossary — runtime architecture terms

The rules are in [`docs/architecture.md`](docs/architecture.md). Named here so a hook, a
review comment and a test description all use the same word.

### Session and startup

- **Session status** — the tri-state the whole app branches on:
  `bootstrapping | authenticated | unauthenticated`. _Avoid_: `user === undefined`,
  `isLoggedIn`, a bare `isLoading` — none can express "still restoring", which is what
  causes a login screen to flash over a valid session.
- **Bootstrap sequence** — the one ordered startup path in `shared/lib/bootstrap`
  (reporting → config → focus/online wiring → keychain → session → splash → tree).
  _Avoid_: "init", "app setup" — those name a place, not an order, and the order is the
  point.
- **Splash gate** — holding `expo-splash-screen` until bootstrap resolves _and_ the fonts
  are loaded. The mechanism that makes the tri-state visible-free.
- **Token manager** — the module in `shared/lib/auth` owning raw token values and their
  **in-memory mirror** (read from the keychain once at bootstrap; written back atomically
  on every change). _Avoid_: "token store" — it is not a Zustand store and never will be.
- **Refresh coordinator** — the single-flight `refreshPromise` holder. **Single-flight**
  means concurrent 401s await one refresh. _Avoid_: "refresh interceptor", "retry queue".
- **Atomic rotation** — persisting a new access + refresh pair as **one** session update.
  Half a rotation is an unrecoverable session.
- **Refresh rejection vs refresh unreachable** — the distinction that decides whether a
  failed refresh destroys the session (rejected) or preserves it (network). Never
  collapse the two into "refresh failed".

### Routing

- **Route group** — a parenthesised directory in `src/app/` — `(public)`, `(auth)`,
  `(app)`, `(onboarding)` — making the authorization boundary visible in the file tree.
- **Guard** — the redirect in `(app)/_layout.tsx` keyed on session status. On SDK 52 this
  is a redirect, not a declarative protected route; those landed later. _Avoid_:
  "middleware" (that is a web server's word, and it runs on a server).
- **Entry gate** — the _second_ redirect in `(app)/_layout.tsx`, deciding where a launch
  lands from **three parallel reads**: is a run unfinished, does a rating exist, and does a
  Player profile exist. Four destinations, and the order between them is the rule: resume ·
  welcome · the social steps · the app. Distinct from the guard, and deliberately **not**
  part of session status — a rating check inside bootstrap would block every cold launch on
  a network request. The third read is the authenticated player the app already asks for,
  never a fourth endpoint. _Avoid_: "onboarded flag" — there is no such thing, because a
  rating is per sport. Whether a _Player profile_ exists is not that flag: it is a
  per-player question with a per-player answer, which is the distinction
  [ADR-0090](../docs/adr/0090-onboarding-per-player-checkpoint.md) draws and the shared
  glossary now carries.
- **Untrusted route input** — any param from a deep link, push payload, universal link,
  App Link or QR code. Zod-validated in the feature's `schemas/` before use.
- **The shell** — the five tabs a signed-in player is inside, and the **one stack** under
  them. `Now · Around · ⚡Play · Chats · You`, drawn by `TabBar` and mounted once by
  `TabShell`. Deliberately **not** `<Tabs>`: that keeps a history per tab and restores it,
  which is the whole of what
  [#227](https://github.com/Raketa02/Raketa/issues/227) forbids. _Avoid_: "the tab
  navigator" — there isn't one.
- **The reset** — `resetShellStack`, the shell's only navigation move: throw the stack away
  and lay a new one down. Four tabs lay down one screen and ⚡Play lays down two, which is
  why back from Play's entry leaves Play rather than walking it. **A Play session ends
  exactly when it runs.** _Avoid_: "switching tabs" as though it were a push.
- **A placeholder tab** — one of the four with no screen behind it yet. It states what its
  tab will be and that it is not built, in one sentence, so a player can tell it from a
  bug. Three of the four are **citations** of decisions taken elsewhere, and **Now never
  says nothing is happening** — it is where a send lands. _Avoid_: "empty state" (that is a
  screen with a real answer of nothing) and "coming soon".

### The onboarding flow

Four client-only concepts. **None exists on the backend and none should:** an Assessment is
per sport, and nothing on the server records the sequence of them, a player's decision to
come back later, or a half-answered second part. The first two are modelled in
`features/onboarding/domain/onboardingPass.ts` and held in that feature's stores; the last
two belong to `features/player_profile/`, which owns the second part and will own the
profile editor that later edits the same values.

- **Onboarding pass** — **one walk through onboarding**: the sports the player chose, in
  the order they chose them, and which of those produced a Skill rating. It is what the
  progress bar measures, what decides which sport comes next, and what the closing screens
  account for. Client-only, in-memory, never persisted. It **begins** explicitly — at the
  picker with the queue that was chosen, or at the question route for a run resumed
  straight from the entry gate, which is a genuine pass of one sport — and it **ends** in
  one place, when the player reaches the app. Between passes there is **no pass**, and
  that absence is load-bearing: it is what lets a resumed run begin one without adopting a
  finished walk's queue. **Onboarding happens once, at the beginning** — there is no
  re-take from inside the app — so a link naming a sport outside the running pass is sent
  to welcome rather than into the middle of a flow. _Avoid_: **"run"** — that is one
  Assessment, and a pass is a
  sequence of them; **"session"** — that is the auth session, and the two have different
  lifetimes; also "onboarding state", "wizard".
- **Deferred run** — an Assessment the player asked to **continue later**. Unfinished on
  the server with every answer intact, and held on the client only so the entry gate stops
  resuming it. It lasts the **app session**, deliberately outliving the pass: a pass ends
  when the player reaches the app, and that is the exact moment the gate re-evaluates, so
  a deferral folded into a pass would send the player back into the run they set aside.
  _Avoid_: "paused run", "saved run" — both suggest a server-side state, and there is
  none; "abandoned run" — that **is** a server-side transition and is the permanent way
  out, where this is the temporary one.
- **Social step** — one of the **seven** screens of onboarding's **second part**: tags,
  photos, availability, location, radius, gender, opt-in, in that order. The step names are
  the route segments, so `/radius` is the screen that asks for a Search radius and there is
  no second spelling of the seven. The order is not arbitrary at two points: **location
  before radius**, because a distance is a distance _from_ somewhere, and **gender with the
  matching constraints rather than with the tags**, because a preference over who you play
  with narrows who is put in front of you rather than describing you. **The opt-in is
  always last** — it is the consent that ends the part and the step that carries the finish.
  **The part is the unit, not the step** — back and forward move freely between steps and
  never cross out of the part, the first step has no back control, and the last is followed
  by the profile commit rather than by an eighth screen
  ([ADR-0090](../docs/adr/0090-onboarding-per-player-checkpoint.md)). _Avoid_: "wizard
  step", "page"; also "onboarding step" for a question in the questionnaire — that is a
  **position** in a run, and the two move by different rules.
- **Profile draft** — every answer the second part has collected, held **on the client**
  until the one commit that ends the part. In memory, never persisted, and never sent
  anywhere before that commit — which is what makes moving between steps free and what makes
  leaving mid-part restart at step one. Its absence is a state: no draft means the player is
  not in the part, which is how a link naming a step in the middle is told from a player who
  walked there. _Avoid_: "form state" — it outlives every screen in the part; "saved draft"
  and "resume" — nothing is saved, and the asymmetry with part one's resumable run is
  deliberate.
- **Profile commit** — the Profile draft with **every answer present**, and the one request
  that carries it. A distinct type from the draft on purpose: three of the draft's fields
  are legitimately absent while a player is walking the part — four, since the gender step
  — and none of them may be absent in what is sent — so a partial commit is unrepresentable rather than merely
  avoided. It is built in one place (`readyToCommit`), which also names what is still
  wanted so the last step can ask for it rather than only refuse. **Where the part stands**
  folds that together with how the one request is going — outstanding · waiting on an upload
  · ready · sending · failed · landed — and _when the finish opens_ is read off it, so the
  rule has a name and a test rather than living in a `disabled` prop. _Avoid_: "submit",
  "save" — this happens once and creates the profile; "payload" — that is the body, and the
  commit is the answers.
- **Commit key** — the Idempotency key the profile commit is sent under, minted when the
  part is entered and living exactly as long as the Profile draft. It belongs to the
  **part**, never to a press: a double tap and a retry after a failure both carry the key
  the first attempt carried, so the server serves one profile whatever the finger and the
  connection do. A disabled control is the courtesy; this is the defence. _Avoid_:
  "request id" — that is the per-request correlation id `shared/lib/http` sets, and it is
  deliberately different on every attempt.
- **Gender preference reach** — what narrowing the preference costs its holder, as a
  **reason code** rather than a sentence. The gate is mutual, so `WOMEN_ONLY` does not only
  filter what a player sees — it hides them from every man, including men who searched for
  anybody, and that is the half nobody would guess. The rule decides _whether there is a
  cost_; this app's copy says it, on the step, **at the moment of the press**. Learning it
  from an empty inbox is not acceptable
  ([ADR-0096](../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
  _Avoid_: "filter" — a filter is one-directional and this deliberately is not; "privacy
  setting" — it changes who is matched, not what is shown, and neither value is ever drawn
  on any surface but the step that takes it.
- **Photo workbench** — the pictures the photos step is holding, each with the upload it is
  in the middle of, beside the Profile draft and in the same store. Not an answer: a local
  `file://` URI is worthless to the server and an upload in flight has nothing to commit, so
  what reaches the draft is **derived** from it — the ids of the photos that arrived, in the
  player's order. One store because the two share one lifetime and that derivation is the
  invariant; two would be two things to reset and a sync somebody forgets. _Avoid_: "photo
  state", "upload queue" — the queue is one promise chain inside the step's hook, and it is
  not what this holds.
- **Profile options** — the **one read** the seven steps are drawn from: the Social tag
  vocabulary with its grouping, how many tags a profile must hold, and the Search radius
  bounds. Reference data owned by TanStack Query, fetched once for the whole part, and the
  reason no client restates a vocabulary or a bound the commit re-validates against. Ids and
  grouping cross the wire; **every label a player reads is this app's copy**, so a served id
  this build has no words for is dropped rather than drawn — the answer `toSport` gives an
  unknown sport. _Avoid_: "config" and "settings"; neither is about this player, and both
  invite something per-player being added to it.

### Data and errors

- **Query key factory** — the per-feature object in `hooks/` defining every key, with
  every response-affecting parameter included. _Avoid_: inline string keys.
- **Cache effect** — what a mutation does to the cache: the `setQueryData` write of the
  canonical response, plus the invalidations. Declared per mutation, never implicit.
- **Cache isolation** — clearing the Query cache on logout/account switch so one user's
  data cannot be read by the next. A privacy control, not housekeeping.
- **Focus manager / online manager** — TanStack Query's hooks into app foreground and
  connectivity, wired to `AppState` and native network state in `shared/lib/platform`.
  Without them the browser assumptions underneath Query are simply wrong.
- **Error envelope** — the backend's `{ code, message, details, field_errors, trace_id }`.
  The **error code** is the machine-readable, stable half — the only half a client branches
  on. The message is copy.
- **`AppError`** — the normalized client-side error family in `shared/errors`. Nothing
  above `shared/lib/http` ever sees a raw `fetch` rejection or backend JSON.
- **Recovery category** — which of _auto-retry · user-retry · re-auth · user correction ·
  conflict · terminal_ an error is. Assigned when the endpoint is mapped.
- **Idempotency key** — the client-supplied token that makes a repeated mutation safe to
  send. The actual duplicate-booking defence; a disabled button is only UX.
- **Correlation ID / trace ID** — the per-request identifier that ties a mobile failure to
  a backend log without logging any payload.
- **Feature store vs app-wide store** — a small Zustand store at
  `features/<f>/store/`, versus `src/shared/store/`. Reach for the feature one first; the
  app-wide one needs a reason. _Avoid_: "global store", "app state" — both invite the
  hundred-property object this structure exists to prevent.

### Platform and delivery

- **Platform port** — a narrow TypeScript interface in `shared/lib/platform/` over one
  native capability, with exactly two implementations: the real one that imports the
  native module, and a fake in `src/test-support/platform.ts`. Two exist —
  `LocationPort` and `ImagePickingPort` — and each is **the only importer of its module**,
  the way `shared/lib/auth` is the only importer of the keychain. The reason is not
  tidiness: a native module has no JS underneath it, so a feature that imports one is a
  feature no test can drive. _Avoid_: "device module", "native service" — a module holding
  both capabilities is the utils bucket this app bans, and a capability is one file.
- **Permission state** — the four answers a platform port gives about a capability:
  `undetermined | granted | denied | blocked`. **Denied and blocked are different
  refusals** — denied can be asked again at the moment the player understands why; blocked
  is settled in the OS settings app and re-asking resolves instantly and negatively, so a
  screen must say so and offer the settings page instead of a control that would prompt. _Avoid_: a boolean, "permission denied" for
  both — collapsing them either re-prompts forever or sends an unasked player to Settings.
- **Location fix** — one position from the device: latitude, longitude, and the accuracy
  the device itself reports, `null` where it reports none. Read **in the foreground,
  once**. _Avoid_: "tracking", "background location" — a stream of positions collected
  while the player is elsewhere is a movement trail, a different privacy class from the
  one anybody agreed to, and nothing in this app asks for it. A fix is **coarsened the
  moment it is read** — the Location area is what the app keeps, and the fix itself does
  not outlive the function that asked for it.
- **Foregrounded** — the app coming back to the front, as `useOnForeground` reports it:
  `AppState` becoming `active`, read through the focus manager `wireFocusManager` already
  feeds. One listener for the whole app (docs/architecture.md Part 13), so _foreground_ has
  one meaning rather than one per screen. _Avoid_: a second `AppState` listener in a
  feature — that is the one that disagrees about what `inactive` means.

- **New Architecture** — React Native's Fabric/TurboModules runtime, enabled
  (`newArchEnabled`). A dependency blocking it is technical debt with a plan, not an
  exemption.
- **CNG (Continuous Native Generation)** — native projects generated from `app.config.ts`
  - config plugins + dependencies via `expo prebuild`, rather than maintained by hand.
- **Native config document** — `app.config.ts`, a **function of the environment** rather
  than a static file. Expo evaluates it in Node before Metro exists, so it reads
  `process.env` directly and refuses an unknown `EXPO_PUBLIC_ENV` rather than defaulting.
  It holds no logic: the one decision is [app identity](#glossary--player-app-technical-terms).
  _Avoid_: `app.json` — it was replaced, not supplemented.
- **Config plugin** — the sanctioned way to express native configuration. _Avoid_: editing
  `android/`/`ios/`, which is [prebuild output](#glossary--player-app-technical-terms).
- **Development build** — a real native build containing this app's native dependencies,
  and the normal development environment. **Expo Go** is for quick experiments only and
  cannot contain them.
- **Runtime version** — the identifier tying a JS bundle to a compatible native binary.
  A JS-only change ships as an **OTA update**; a native change needs a new build.
- **Client capability headers** — app version, build number and platform, sent explicitly
  so the backend can observe and adapt. _Avoid_: user-agent parsing.
- **Redaction** — the logger's structural stripping of tokens, `Authorization` headers,
  passwords and payloads. Structural, so it does not depend on each call site remembering.
- **Event catalog** — the register of analytics events, each with a name, owner, trigger,
  typed properties, PII classification and business meaning. Ad-hoc event names are how
  analytics data becomes useless within a quarter.

## Glossary — design-system terms

The rules are in [`docs/design-system.md`](docs/design-system.md); the values are in
[`src/shared/ui/theme.ts`](src/shared/ui/theme.ts). Named here so a component, a review
comment and a commit message all use the same word.

- **Token** — a value in `theme.ts`, the only legitimate source of a colour, type role,
  spacing step, radius, metric, shadow or duration. _Avoid_: constant, variable (a token
  is a _design_ decision, not just a value).
- **Harness** — the prototype's phone frame, dark stage, scenario rail and time bar. **Not
  product.** _Avoid_: calling any of it a "shell" or "chrome" — those words imply it ships.
- **Paper / surface** — `paper` is the app background; `surface` is white, and everything
  raised off it (cards, sheets, popovers).
- **Line vs line2** — `line` **bounds a thing** (card border, chip border); `line2` is a
  **fold inside one thing** (the hairline, tag backgrounds, inactive tracks). Load-bearing,
  not stylistic.
- **Soft / ink / line companion** — a semantic colour's family. `Soft` is the tinted
  background, `Ink` is the darkened form that carries text on that soft _and_ the fill
  whenever white text sits on top (**Rule C**), `Line` is the soft's border.
- **Rule C** — white text never sits on `coral` or `mint`; it needs `coralInk` or
  `mintInk`. `ink` is the only dark permitted on `coral`.
- **Card / dark card** — the light workhorse and the `night`-filled variant that **repaints
  its children**. _Avoid_: "inverted card".
- **Hairline** — the 1pt `line2` divider inside a card, with a 9pt top margin.
- **Note** — a message block with a 3pt left bar carrying the semantic. Five tones. The one
  place a paragraph is acceptable.
- **Row** — the key-value line. Separated from the row above by a `line2` top border,
  applied from the second row onward.
- **Tag vs chip** — a **tag** is a 9.5pt state pill and is **never pressable**; a **chip**
  is a pressable filter pill and the only true pill in the app. A pressable tag is a chip.
- **Eyebrow vs form label** — an **eyebrow** labels a region you are _reading_; a **form
  label** labels a control you are about to _operate_. Not interchangeable.
- **Slot square** — the day / time / hour / range selectors, sharing a four-state
  vocabulary: **free**, **off** (taken), **selected**, **end** (the hollow square marking
  where a booking finishes).
- **Fit badge** — the match-fit score pill; dark, and coral at 90 or above.
- **Band tint / deep / ink** — the level bar's three values per band. `tint` and `deep` draw
  the bar; **`ink` is for text and the band card's rail.** Distinct from the **model band
  edges**, which are what any printed range must use.
- **Level bar** — the drawn object: band segments, the coral mark, the likely-range bracket
  below, and the band names. **The separation of the two rows is the whole design.**
- **Seat pip / empty seat** — an avatar per seat; the dashed one is the only dashed element
  in the app and means _a place that could be filled_.
- **Square row vs strip** — a free-scrolling row of content-sized children, versus a
  snapping carousel of full-width children that bleeds to the screen edge.
- **Sheet · toast · popover** — the three overlays. Three distinct surfaces, not synonyms,
  and all three render from the root overlay host.

> The rating, band, confidence, match-fit and hold concepts these surfaces render are
> **interface** names only. Their domain terms are unmodelled — Bookings, Courts and
> Matches are Part 2 of the shared glossary. Settle those there first, then rename here.

Add player-app-only technical terms here as they are resolved. Anything describing the
_domain_ belongs in the shared glossary instead.
