# Rakieta Player App — Technical Vocabulary

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
- **Public config** — any value in `app.json` `extra` or an `EXPO_PUBLIC_*` variable.
  It ships inside the bundle and is readable from a released app. _Avoid_: calling these
  "env secrets" — the word invites someone to put a real one there.
- **Environment** — which deployment of the platform this build talks to:
  `local | development | staging | production`, spelled identically in all three apps.
  `local` is a developer's own machine and is the only one that runs today. _Avoid_:
  `dev`, `prod`, `test` — the first two are the spellings the backend used to accept and
  now refuses, and a test run happens on a laptop or a CI runner, both of which are
  `local`. _Avoid also_: calling a laptop `development`, which is the name that means a
  shared remote deployment.
- **Scheme rule** — the environment fixes the API URL's scheme: `http://` in `local`,
  `https://` in the three deployed environments. Validated across both variables at
  launch, so a laptop URL under a deployed name is a refusal naming both rather than a
  build pointing at nothing.
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
- **CNG (Continuous Native Generation)** — native projects generated from `app.json` +
  config plugins + dependencies via `expo prebuild`, rather than maintained by hand.
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
