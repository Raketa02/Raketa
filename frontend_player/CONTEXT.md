# Raketa Player App — Technical Vocabulary

This file holds **player-app-only technical vocabulary**. It does **not** define domain
language — those terms (User, Club, Court, Booking, statuses, events) live once in the
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
  "middleware" (that is the club app's word, and it runs on a server).
- **Entry gate** — the _second_ redirect in `(app)/_layout.tsx`, deciding between the app
  and onboarding from two parallel reads: is a run unfinished, and does a rating exist.
  Distinct from the guard, and deliberately **not** part of session status — a rating
  check inside bootstrap would block every cold launch on a network request. _Avoid_:
  "onboarded flag" — there is no such thing, because a rating is per sport.
- **Untrusted route input** — any param from a deep link, push payload, universal link,
  App Link or QR code. Zod-validated in the feature's `schemas/` before use.
- **Tab key** — one of `now` · `find` · `create` · `msg` · `you`, the bar's own five names,
  taken from `UI` §B13. **Not** a route: `(app)/(tabs)/_layout.tsx` holds the one mapping
  from a key to a route file, which is why `you` reaches `account`. _Avoid_: treating the
  key and the route name as interchangeable — two of them differ.
- **Placeholder route** — a route file that exists because the tab bar reaches it and its
  feature does not exist yet (`find`, `create`, `inbox`). It says what it is and what it is
  not, and the ticket that builds the feature deletes it. Distinct from a **stub**: nothing
  here pretends to work.
- **Who spends the inset** — the tab bar takes the bottom safe-area inset, so every screen
  under `(tabs)` declares `edges={['top']}`. `BottomTabView` hands the bar its own insets
  and leaves the screens' inset context untouched, so both claiming it is both padding it.

### The onboarding flow

Two client-only concepts. **Neither exists on the backend and neither should:** an
Assessment is per sport, and nothing on the server records the sequence of them or a
player's decision to come back later. Both are modelled in
`features/onboarding/domain/onboardingPass.ts` and held in that feature's stores.

- **Onboarding pass** — **one walk through onboarding**: the sports the player chose, in
  the order they chose them, and which of those produced a Skill rating. It is what the
  progress bar measures, what decides which sport comes next, and what the closing screens
  account for. Client-only, in-memory, never persisted. It **begins** explicitly — at the
  picker with the queue that was chosen, or at the question route for a run resumed
  straight from the entry gate, which is a genuine pass of one sport, or at the door's
  route for a sport taken up from Now — and it **ends** in one place, when the player
  reaches the app. Between passes there is **no pass**, and
  that absence is load-bearing: it is what lets a resumed run begin one without adopting a
  finished walk's queue. **Onboarding happens once, at the beginning** — there is no
  re-take from inside the app, and Now's door is the one exception, which is why it begins
  its own pass — so a link naming a sport outside the running pass is sent
  to welcome rather than into the middle of a flow. _Avoid_: **"run"** — that is one
  Assessment, and a pass is a
  sequence of them; **"session"** — that is the auth session, and the two have different
  lifetimes; also "onboarding state", "wizard".
- **Pass origin** — where a walk **began**, which is the only thing that decides where it
  **ends** (`onboarding` · `door`). A walk begun at the picker, or at a run resumed on
  launch, closes with the account of itself — the done screen, then the data screen. A walk
  begun at Now's **door** goes back to Now filtered to the sport it produced, and passes
  neither
  ([ADR-0084](../docs/adr/0084-the-sport-bar-is-five-fixed-chips-and-an-unrated-sport-is-a-door.md)).
  **Never derived from whether the player already holds a rating**: she holds one by the
  second result screen of an ordinary two-sport walk, and is owed the account of that walk.
  Where she started is a fact; how many ratings she has is a coincidence.
- **A parked run** — an Assessment left unfinished by a player who **already holds a
  rating**. It is not a state anything stores: it is what an unfinished run _is_ now that
  the entry gate no longer resumes one for her. Nothing is stranded, because the door is the
  way back in, and it continues where it stopped **however old** — the server replays the
  transcript, so no client reads an age. _Avoid_: "deferred run" — that is her explicit
  _later_, lasts one app session, and exists for the player who has no other way out.
- **Deferred run** — an Assessment the player asked to **continue later**. Unfinished on
  the server with every answer intact, and held on the client only so the entry gate stops
  resuming it. It lasts the **app session**, deliberately outliving the pass: a pass ends
  when the player reaches the app, and that is the exact moment the gate re-evaluates, so
  a deferral folded into a pass would send the player back into the run they set aside.
  _Avoid_: "paused run", "saved run" — both suggest a server-side state, and there is
  none; "abandoned run" — that **is** a server-side transition and is the permanent way
  out, where this is the temporary one.

### The Now vocabulary

Four copy tables and three lookups, colocated under `features/now/` and **not** promoted to
`shared/`. The result route imports them; a third reader is the signal to promote
([ADR-0075](../docs/adr/0075-the-second-table-is-unpaid-and-the-first-ships-in-english.md)).

- **Copy table** — a `Record` over a union **generated** from `openapi.player.json`, whose
  entry is a **function** of the payload rather than a template string. There are four:
  36 situations, 10 term codes, 5 hold reasons, 7 acts. They are **three copy tables plus
  the acts**, kept separate rather than merged over a union of unions — that key type would
  be assembled by hand, which is the one thing the completeness rule exists to avoid.
  _Avoid_: "i18n catalogue", "strings file" — the unit here is a payload and a function,
  not a string with placeholders, which is why no i18n library ships.
- **Completeness** — a **typecheck**, never a test. A contract value added without its
  sentence fails `pnpm typecheck`, riding `make gen-api` and the drift check that already
  exist. This departs from the app's precedent deliberately: `theme.ts` hand-writes its key
  unions, so nothing else in this client can currently fail to build when the contract grows.
- **Closed-union pin** — `AssertTrue<IsClosedUnion<T>>` beside each table. Completeness is
  only a mechanism while the key is a closed union: a code crossing as a bare `string` turns
  the `Record` into an index signature that never fires, and the missing sentence ships as a
  blank line. The pin is what makes that a build error rather than a silent stop.
- **Count pin** — the enumeration written out in `copyTables.test.ts`. The `Record` forces a
  thirty-seventh row to be **written**; it cannot force anybody to **notice**. _Avoid_:
  treating the two as one guard — they catch different edits.
- **Tolerance** — the runtime fallback beside the typecheck, and a different mechanism for a
  different moment. Every lookup takes a `string`, so a phone meeting a name this build has
  never heard of loses **one sentence** and draws the spine. Typing the parameter as the
  union would make that branch unreachable in the one place it has to work.
- **Tag · tone · alert** — the three columns of the situation table that cross **no wire**.
  All three are total functions of the situation, so a flag would let the server and the
  phone disagree about whether a card is urgent. Nineteen tags, where the state-table
  research counted seventeen: the two offer situations are facts about _this viewer_ and
  none of the seventeen says one.
- **Audience** — which of the three a card is drawn for: in the match, looking in, or the
  **leaver**. Named vocabulary with **no reader yet** — nothing on the wire distinguishes
  them until the departure payload lands, which is why `SituationContext` is an object and
  not a positional argument list: the field reaches the rows that read it and leaves the
  rest untouched.
- **Find pre-filter** — a shelf's own claim (`seats`, `order`, `kind`) plus the sport the
  client holds. What the tail card opens Find with; a shelf running out is a door and not a
  wall. Held as a value object, because Find does not exist yet and a URL shape decided here
  would be decided in the wrong place.

### The Now screen

The player app's home. `features/now/` grew from a vocabulary into a screen with
[#86](https://github.com/Raketa02/Raketa/issues/86) and gained the match card's action row
with [#87](https://github.com/Raketa02/Raketa/issues/87); the tab bar under it landed with
[#93](https://github.com/Raketa02/Raketa/issues/93), and the shelves — the tail card, the fit
badge and emphasis — with [#88](https://github.com/Raketa02/Raketa/issues/88).

- **Composed screen** — the whole answer to one `GET /api/v1/now`: three regions and one
  fact about the viewer. The client's own domain object, in `domain/ComposedScreen.ts`.
  _Avoid_: "the feed" — the feed is one region of three.
- **Present and empty** — what a region with nothing is, never absent
  ([ADR-0070](../docs/adr/0070-now-is-three-regions-and-a-card-has-two-halves.md)). One
  code path instead of two, and the reason a player with nothing gets a shape she
  recognises. A **shelf** with nothing is the opposite: absent, because a shelf makes a
  claim and a region does not.
- **The four asks** — arrival · pull · an action · a countdown reaching zero
  ([ADR-0054](../docs/adr/0054-now-refreshes-when-asked-never-on-a-timer.md)). The only
  four things that refresh Now, expressed as Query options on `useNow` rather than as
  machinery: `refetchOnWindowFocus: 'always'` is arrival, and `staleTime: Infinity` with
  `refetchOnMount: false` is what stops a screen becoming visible being a fifth.
  **Arrival is the app foregrounding**, never a screen mounting.
- **The one derivation** — subtracting a card's moment from the current time,
  `domain/countdown.ts` and nowhere else
  ([ADR-0053](../docs/adr/0053-the-phone-holds-no-rules-and-only-subtracts.md)). No kernel
  on the phone, nothing provisional, nothing to reconcile. `nowDiscipline.test.ts` walks
  the feature's source for `Date.parse` and finds one file.
- **The deadline ask** — one `setTimeout`, at a moment the **server** named, re-armed when
  the screen changes. Not a timer: there is no interval anywhere in the feature, and
  `refetchInterval` is walked for by name because it is the poll most likely to grow back.
- **Repaint, against ask** — the distinction
  [ADR-0088](../docs/adr/0088-the-action-row-is-three-slots-and-the-clock-takes-the-first.md)
  states and says is stated nowhere else. A countdown **repainting** is drawing; a countdown
  **reaching zero** is one of the four asks. So the feature holds two `setTimeout`s doing
  two jobs, and the walk names both and asserts that only one of them can see Query at all.
  Conflating them is how Now ends up on a sixty-second poll.
- **The action row** — one row on a state card, three optional slots, **zero variants**:
  the clock leftmost, the act at `flex: 1`, the exit rightmost (ADR-0088). Each appears
  exactly when its own field is present, a vacant slot does not stretch, and the empty row
  still renders as a zero-height spacer — because `marginTop: auto` needs something to push.
  _Avoid_: "the CTA row" — twenty-six of the thirty-six situations name no act at all.
- **State card, against shelf card** — the two card shapes ADR-0088 distinguishes. A state
  card (the strip, the offers region) reaches its act through a **labelled button** and
  takes the handler that answers it; a shelf card reaches the same act through its **whole
  body** and gains no button, and **only when it names an act** — the converse of ADR-0083's
  rule, so an inert card does not swallow a press. The inconsistency is deliberate and is the
  sharpest thing in that ADR. A whole-card control is **one accessibility element**, so such a
  card announces its act and nothing else ([#116](https://github.com/Raketa02/Raketa/issues/116));
  no shelf card names an act until [#89](https://github.com/Raketa02/Raketa/issues/89).
- **The clock slot** — the card's _one_ moment, and a **live seat claim wins it**: the
  claim's five minutes override the card's own clock, exactly as `finishPaying` overrides
  the situation's act. Which of the two can _run out_ is not a choice and the deadline ask
  watches both; which of the two is _shown_ is this rule.
- **A shelf card's clock is a claim's clock** — and nothing else (ADR-0088). The card's own
  moment is _the next thing that happens to a viewer with a stake in the match_, and a
  suggestion is a match she has none in; her own claim is about her. **The server sends the
  match's boundary on a shelf card anyway**, which is the ADR's one factual slip
  ([#114](https://github.com/Raketa02/Raketa/issues/114)) and costs the client nothing,
  because the shelf card reads the claim and never the card's clock. When the claim is
  there the countdown **replaces** the tone tag rather than joining it: while a player holds
  1:30 to pay, _Forming_ is not the news.
- **The seconds band** — ten minutes, and it decides two things that must agree: inside it
  the screen repaints every second and the label draws a clock face (`4:37`); outside it the
  screen repaints once a minute and the label draws a duration (`42 min`, `2 h 14 min`,
  `3 d 4 h`). **The format never prints a digit the cadence cannot keep true**, which is why
  it is one constant and not two.
- **The dropped icons** — `✉` and `⌘`, removed from the action row by ADR-0088 as a
  **genuine override of a UI authority** rather than as a forced consequence: one duplicated
  a tab-bar button once per card, the other opened a sheet showing four dots everywhere it
  survived. `nowDiscipline.test.ts` walks the feature so neither returns.
- **Shimmer vs pull indicator** — the two ways loading is shown, and neither is a staleness
  marker. A shimmer says _there is nothing here yet_ and belongs to a **cold open**; the
  pull indicator says _this is real and I am checking_ and keeps the screen where it is.
- **Staleness** — what this screen never admits. No marker, no dot, no banner, no
  _"can't reach Raketa"_. A failed refresh over a populated screen changes nothing on it.
  The word `stale` is still legitimate about a **hold** — a court the club has capped — and
  the walk is written to allow exactly that.
- **Visit** — how long a sport-bar selection lasts: until thirty minutes **away**, measured
  from the app backgrounding
  ([ADR-0084](../docs/adr/0084-the-sport-bar-is-five-fixed-chips-and-an-unrated-sport-is-a-door.md)).
  A cold start is not the boundary, because phones do not close apps.
- **The door** — the block Now composes where a sport's **ranked shelves** would be, for a
  chip the viewer holds no rating at. It is **in the shelves list, in order**, never a flag
  and never an inference the phone draws from shelves that are missing — that inference is
  wrong on any day the city genuinely has nothing in a sport she _is_ rated at, and the
  phone holds no rules
  ([ADR-0084](../docs/adr/0084-the-sport-bar-is-five-fixed-chips-and-an-unrated-sport-is-a-door.md),
  [ADR-0053](../docs/adr/0053-the-phone-holds-no-rules-and-only-subtracts.md)). _New on
  Raketa_ and _New clubs_ draw **beneath** it, which is the argument for spending the two
  minutes rather than a leftover.
- **Two sentences, one behaviour** — the door's two codes (`noRunYet` · `runParked`) differ
  in their **words** and in nothing else. The tap is one `POST /assessments`, which is
  idempotent per player and sport and hands back a parked run's outstanding question, so the
  phone never learns which case it is in and holds no rule about resuming.
- **The fit badge** — `✦ 93`, and the client's three obligations to it
  ([ADR-0037](../docs/adr/0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)). The
  score is **clamped 20–99 at display time**, in the mapper, so the engine's true 0–100 value
  never enters the app; **up to three reasons** stand under it, resolved from a term code and
  a typed payload to this app's own sentence; and an **unsure** estimate becomes a warning
  line. _Avoid_: printing coverage in any form — it ranks and it gates emphasis, and a
  type-level assertion in `nowMappers.ts` fails the build the day it crosses the wire.
- **Emphasis** — the one card on the whole screen that shouts, as a **flag the server ships**
  and never a comparison the phone makes. Its three gates are fit ≥ 90, coverage ≥ 80 % and a
  seat open, all of which are about the _other_ cards, and an offer on screen silences it
  entirely — so it is a property of the composed screen
  ([ADR-0032](../docs/adr/0032-order-is-a-property-of-the-composed-screen.md)). The drawn cue
  is a colour and no word, which is `UI` §B9's _"two bands only"_; the **announced** label
  carries the state, because a cue with no non-visual half is one nobody using a screen
  reader can have. `nowDiscipline.test.ts` walks the feature for a score compared against
  anything.
- **The tail card** — the card every shelf ends in, opening Find pre-filtered by the shelf's
  own claim plus the sport the screen holds. **Not in the contract**: the client appends it,
  and a shelf whose code this build cannot address gets none — the same answer its missing
  title is. A shelf running out is a door and not a wall. Find cannot yet receive the
  pre-filter ([#115](https://github.com/Raketa02/Raketa/issues/115)), so the tap opens the
  destination and the claim stops at the screen.
- **Block** — what the shelves list holds: a shelf, or a door. The domain calls the field
  `blocks` where the wire keeps `shelves`; the wire keeps its name because renaming it
  breaks every shipped client reading a region that has not otherwise changed.
- **The strip** — the enrolled region's `.hstrip`: one card at a time, the full content
  width, bled to the screen edge, peeking by `gutter − gap`. **Not the rail**, whose
  `railCardRatio` belongs to a shelf and would show a quarter of the next card's contents
  here. See `docs/design-system.md` Part 8.

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
- **Text against non-text** — the distinction Rule C turns on, and the reason the tab bar's
  plus is white on `coral` while its badge numeral is `ink`. A glyph is non-text content
  under WCAG 1.4.11 and needs 3:1; a numeral is read, so 1.4.3 applies and needs 4.5:1.
  White on `coral` is 3.89:1 — it clears one and not the other. _Avoid_: reading the plus
  as a Rule C exception; it is the same rule answering a different question.
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
