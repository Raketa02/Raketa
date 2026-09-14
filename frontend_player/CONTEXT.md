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
- **Profile surface** — the **one read** the Play screens hold about the player: the
  availability grid, the Search radius and the per-sport Play intent, in one round trip across
  the two aggregates that own them. Deliberately **not the whole profile**, and the two
  absences on it are different absences — gender and the gender preference are a _standing
  refusal_ that never comes back out of this API, and tags, photos and the location area are a
  _deferral_ this same route grows when **You** is built. Its home is `player_profile/`, not
  `play/`, because the three **writes** are: one unkeyed `PUT` per fact, and a read whose
  paired writes live in another feature is a read in the wrong feature. Of the three facts
  only the radius is written from Find a game — a search carries no radius and never will, so
  the profile is the only place a slider there can mean anything. _Avoid_: "the profile" for
  this — it is a surface over one, and calling it the profile is how a fourth field gets added
  to a body scoped to three; also "play screen read", which names a caller rather than the
  facts.

### The Play tab

Nine client-only concepts, one kit of parts, and one gate that is **not** client-only. The
nine do not exist on the backend, and the first four are the shape
[#228](https://github.com/Raketa02/Raketa/issues/228) settled: what Play remembers, for how
long, and what it must never remember. The stores are `features/play/store/`; the rules are
`features/play/domain/`. The **Declaration interstitial** is the exception on both counts — it
is a screen this app draws over a write and a refusal the backend already owns, and it is
listed here because it is a Play surface rather than a profile one.

- **Play session** — **one visit to the Play tab**: the Working copy and the Line-up built on
  it, and nothing else. It begins when the shell lays the Play stack down and **ends exactly
  when [the reset](#routing) runs** — every door out of Play and every door back in goes
  through that one function, which is what makes the ending a definition rather than a line
  each screen must remember. **Backgrounding does not end one**: the process lives and the
  stack is intact, so a line-up really can sit half-built for an hour, which is the state the
  send-time re-check exists for. Process death ends everything; nothing is persisted. _Avoid_:
  "the session" unqualified — that is the auth session, and the two have different lifetimes;
  "Play state", which invites a seventh thing being added to it.
- **Working copy** — **the week Play searches on**: seeded from the player's profile week when
  the tab is entered, edited freely on Find a game, and **never written back**. It travels as
  `availability_override` on the search and nowhere else, so a week improvised for one evening
  is forgotten with the session. Seeded **on navigation, never during a render** — the
  prototype cloned it inside its own render, which is the one inherited defect this concept
  exists to refuse. Whether it _differs from the profile_ is a **comparison made on every tap**,
  not a flag a toggle sets: a slot ticked on and off again is not a changed week. Distinct from
  the search's own `KEEP_THESE_TIMES` prompt, which the backend raises against the post-rung
  grid and which only the backend can compute. _Avoid_: "draft week" — a Profile draft exists
  to be committed and this exists to be discarded; "the grid", which is the control that draws
  it.
- **Origin search** — **the search a Line-up was built off**, held as its id and what it was
  asked for: sport, mode and the week. `POST /forecasts` calls `search_id` the _Origin key_ and
  refuses players who did not appear in that search, so this is the name for what a line-up is
  judged against. It is folded onto the record in `api/` — `SearchEnvelope` carries the id and
  the mode and neither the sport nor the week, because those were the request's. **A line-up's
  invalidity is derived from it and never synchronised**, which is why the two Play stores can
  exist without a write that crosses them. _Avoid_: "the current search" — the whole point is
  that it may no longer be current; "search context".
- **Line-up** — **`{ originSearchId, seats }`**, and the seats are **player ids and nothing
  else**: every name, level and photograph is read back off the origin search's own rows in
  Query. Client-only until it is sent — adding somebody builds it on your screen and reaches
  nobody. It is orphaned when the origin moves, and **three acts move the origin** — changing
  the sport, changing the mode, and leaving Find a game on an edited week — which share **one
  guard with three callers**, so a fourth origin field inherits the confirmation for free.
  _Avoid_: "the court" — that is the drawn object the line-up is shown on; "team", "group".
- **Arrangement** — **one way round a four, with its own forecast**, and there are exactly
  three of them for any four people. **All of them cross**: `LineupResponse` and
  `ForecastResponse` each return every arrangement, which is what makes _Even it out_ a
  **selection** rather than a calculation and what makes a swap cost no round trip. Which one
  is drawn is decided by **who is beside you** — a pairing _is_ that fact — so trading the two
  opponents keeps the same arrangement and the same number, and only crossing the net changes
  either. Which seat is **yours** is `Relationship.SELF`'s answer and never an index's, because
  no route serves a searcher their own player id. _Avoid_: "the pairing" for the object — that
  is the fact it is keyed on; "the forecast" for all three, since each carries its own.
- **Seating** — **where each of them is standing right now**: one entry per seat, in seat
  order, and the one thing that is neither the Line-up's membership nor Query's rows. It is
  **route-local and derived** — absent means _whatever the current arrangement says_ — so an
  answer landing seats people with nothing written down, and a **membership** change resets it
  while a re-arrangement does not. It may put you in the far half, because swap mode is _change
  sides, never seats_ and **a side follows you**. _Avoid_: "seat order" for the value — that is
  the order the wire uses; "the arrangement", which is what a seating selects rather than what
  it is.
- **Ranked list** — the pool, a line-up's shortlist and a deck deal: **one record shape**. The
  first two are minted by a mutation and read by id from `searchKeys.detail(search_id)`; **the
  deal is the exception**, because nothing reads one back by id and a second one is not a second
  copy — `POST /deck` excludes everybody already dealt for a day, so asking twice spends the
  player's own pool. It is held under `searchKeys.deck(sport, week, under)`, keyed by **the
  question rather than the answer**, which is the only key that can be built before the request
  and therefore the only one under which _already asked_ is a fact. `under` is the radius and the
  declaration: they are not on the request, they change the answer, and leaving them out is the
  deck answering _Widen in You_ with the deal that ran before the widening. The entry holds the
  Origin search **and the rows**, which is what lets a Line-up's seats be ids and nothing else:
  every name, level and photograph on a court is read back off them. **Nothing in Play
  background-refetches** — `staleTime: Infinity`, no refetch on focus — because foregrounding
  the app would otherwise reorder the pool under the player's finger. What _does_ refetch on the
  ordinary defaults: the profile and its week, the ratings behind the sport chips, and the Match
  me count. **Re-sorting costs no round trip** and neither does re-arranging four people; only
  changing who is on the court does. _Avoid_: "results", and "the pool" for all three — a deal
  and a shortlist are not pools.
- **Withheld seat** — a seated player the **live gates no longer admit**, found as a **set
  difference** between the line-up's seats and the `player_id`s the origin search's read-back
  still holds. A withheld row carries no id, so the difference is the only way to know; it is
  **derived at the moment somebody asks and never stored**, which is the same discipline that
  lets the two Play stores exist without a sync — a stored mark is a third thing that can be
  stale about staleness. **The seat is marked, not emptied**, and the marked player **stays in
  the forecast**, because dropping them would make the number disagree with the court in front
  of the player and would force a second cause for _provisional_. **The court states the fact
  and never the cause**: four gates reach one sentence. A mark therefore appears only after a
  pool visit, because that is when the read-back happens. _Avoid_: "blocked seat" and "removed
  player" — both name a cause this app may not know and may not say; "stale seat", which is
  about time and this is not.
- **Declaration interstitial** — the one-tap question a searcher meets when they are **rated in
  a sport and have never said what kind of game they want in it**. It is opened off a set
  difference the search screen already holds — rated, and absent from the Profile surface's
  declaration map — so it stands **before** `play_intent_not_declared` refuses rather than
  after it. [ADR-0094](../docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)
  calls it _"permanent, not a migration path"_: it is what makes _every searcher has declared_
  true rather than intended, and it closes a sport rated before the declaration shipped, a
  restored account and a bug in the tail with one screen. **It is not the mode toggle**, and
  the two must never be collapsed — it writes a `PlayIntent` with three values and the toggle
  chooses a `SearchMode` with two, which is the arity gap ADR-0094 spent a type on. _Avoid_:
  "the intent prompt" — a Prompt rides on a search response and offers something; this gates
  one; "onboarding step", which it is not and must not become.
- **No hold state** — the one thing this tab must never remember. A held account is a `403` the
  HTTP layer already maps as terminal, re-checked server-side at every request; **there is no
  cached hold flag anywhere**, because a cached flag is the only mechanism by which a hold
  released on one screen could survive on another. Gating the builder at _navigation_ would
  need exactly that cache, and it is refused. _Avoid_: "hold flag", "blocked user state".
- **Parts kit** — the shared parts the three candidate cards are assembled from:
  `CandidatePhoto` (photo-or-poster in a box, one component at three sizes), `CardHead`,
  `FactRow` and `ReasonLine`, plus the competitive card's own `PhotoPanel`, `IdentityRow`,
  `HeadToHeadBand`, `SocialTagRow`, `OnCourtMark`, `RecordBlocks` and `StakeBoxes` — those last
  two over one `StatBox`. **Three components over one kit, never one component with a `surface`
  prop** — `CandidateCard` is photo-left with a head-to-head row, `CandidateCardSocial` and
  `DeckCard` are media-top with fact rows, and only the deck card floats. The two courts,
  `CourtMini` and `CourtBuild`, are the same pairing over the design system's `Court`: the
  drawn object owns the geometry and knows nothing about players, and the seat owns its label,
  its ring, its badge and its taps. _Avoid_: "the card component" — there are three; "variant"
  and a `surface` prop, which is the sixty-line conditional this split exists to prevent.
- **Drawn set** — the terms a candidate card **renders a value for**, and therefore will not
  restate as a reason line. Three sets, one per card, and each is **exported by the card that
  draws them** rather than held in the selector: the set is a statement about that component,
  and anywhere else it is the one thing that could go stale silently when a row is added or
  removed. The filter over it runs **first and the cap after**, which is what makes a card that
  promised three reasons draw three. _Avoid_: "the filter", which is the rule rather than the
  set; "hidden terms" — a term outside the set is not hidden, it is said in the other register.
  **One term is drawn in half and is deliberately not in any set**: the competitive card draws
  the two tag terms' `matched` ids as chips and leaves their other three registers as sentences,
  so the drop is conditional on what the row actually drew and lives beside the set in
  `candidateFacts` rather than in it. A set entry would take four registers away to stop one
  repeating, and the exported set stays what it says it is — terms this card renders a value for.
- **Head-to-head band** — the competitive card's one block for _how this game would go_: your
  Level on the left, theirs on the right, and the served forecast with its balance word between
  them, over 7.11's bar at `md`. `HeadToHeadBand`, replacing a two-`Side` row, a bare bar and a
  _Predicted balance_ row that said one thing stacked. **The bar takes the level advantage and
  the figure is the forecast** — two facts, and neither is derived from the other. Each half
  hides on its own stood-down term, and the band never vanishes whole while either can be drawn.
  _Avoid_: "balance bar" for the band — that is the design-system primitive inside it; deriving
  the percentage from the two levels, which is forecast arithmetic on the client.
- **Photo panel** — the competitive card's identity: the 74 × 92 box that draws the player's
  photograph (or their generated poster) with the **Level** hugely over it, the **Sport** small
  and capitalised beneath, and the **on-court mark** above. `PhotoPanel`, over 7.16. The Level is
  `player_card.level` — **what they published**, not the level term's μ — so the panel is drawn
  whatever fired; the Sport is the _search's_ and reaches no spoken name. _Avoid_: "avatar" and
  "thumbnail" — the photograph is the ground and the rating is the subject.
- **On-court mark** — the two words the photo panel prints at its top, on a photograph the
  on-court check **passed**: `ON COURT`, `OnCourtMark`, over `domain/onCourtMark`'s one rule.
  **Only a pass is marked.** _Checked and flagged_ and _nobody looked_ draw and announce
  **identically**, because a card must not publish a moderation outcome about a third party, and
  the generated poster draws none because it is not a photograph. It carries **no number in
  either register**: the confidence never crosses on any route. The designs' **✓ ON COURT
  shield** is not what shipped, and the reason is measured rather than judged — Archivo draws no
  U+2713, the app's own tick leaves the words too little room, and the panel's corner leaves a
  chip less still (7.15, `onCourtMarkFit.test.ts`). _Avoid_: "verified", "badge" and "shield" —
  it verifies nothing about a person and it is a label with no ground; "photo review", which is
  the uploader's surface and a different fold of the same code (`player_profile` warns where a
  card marks); a **tick** anywhere in this app that is not `shared/ui/Tick`'s drawn geometry.
- **Social tag row** — a row of up to six of somebody's Social tags, and the **overlap** drawn
  over it. The ones the reader also chose are tinted and carry `· you too` in words; on a
  candidate card the intersection is `matched[]`'s, off the wire, and is never recomputed from a
  profile read. **The rule and the drawing are two layers**: `SocialTagRow` and the four-answer
  `SocialTagOverlap` are `shared/`'s, because the competitive card and the record sheet both draw
  the row, while `play/domain/socialTagOverlap` — the rule that reads one of those answers off a
  **candidate** — is Play's, because a candidate row is. That is why the type and the component do
  not share a name. _Avoid_: "chips" — nothing here is pressable, so they are tags (6.4); tinting
  a `complementary` or `clashing` pair, which is a different relationship and reaches the card as
  prose.
- **Stat box** — the drawn shape the competitive card states a **record block** and an **at
  stake** pair in (both are the root [`CONTEXT.md`](../CONTEXT.md)'s terms, not this file's):
  `StatBox`, a recessed `paper2` box with a name over a figure, three across and then two.
  Recessed rather than plain card text because the card prints a Level twice and a Player Score
  is **not a rating** — 7.13 and 7.14. A box whose fact is absent is **not drawn**, so the ones
  that remain fill the width and no hole marks the gap. _Avoid_: `FactRow` for these — a fact row
  is a fact the card **states**, where these are figures a reader **compares**; a "stat card",
  which is a surface and this is a box inside one.
- **Run of form, drawn** — five squares, one per result, oldest to newest and **never padded**: a
  run of three is three squares and the space after them, because the length is the statement.
  `RunOfForm` is `shared/ui`'s, because the record block and the record sheet both draw it and a
  second copy would be a second thing to keep in step with a **pinned** geometry test. Won is
  `ink` and lost is `muted` — a **lightness** step at 3,24:1, derived from the component's own
  `RUN_OF_FORM_FILL` in `recordSquares.test.ts`, so it reads with no hue perception at all — and
  because a square carries no word, the whole row reaches a listener as **one counted clause**
  against the run's own length (_3 of the last 5 won_) rather than as five elements. An outcome
  this build cannot read takes the **whole field** with it at the mapper, for the same reason:
  half a run cannot be drawn honestly, and _Counted_ beside it goes on printing. _Avoid_: a
  fifth square in a neutral fill, which claims a game nobody played; five spoken states, which
  reads the row as a table.
- **Singles-only stake** — the rule that hides _Win, counted_ / _Lose, counted_ on a doubles seat.
  It is `domain/atStake` rather than the component's, because it is a thing somebody could be
  **wrong** about; the component is handed a pair or nothing. A **refusal to draw** and not an
  absence — the server prices the pairing anyway — where for fun is a genuine absence and never
  reaches the rule. It reads **`isDoubles`**, the feature's one seat-count boundary, which moved
  from `builderPresentation` to `domain/lineup` when this became its second reader: a rule about a
  court's shape is not copy, and a `domain/` file reaching into the copy deck is the wrong
  direction. _Avoid_: a `singles` boolean, and a local `seats === 2` — both are a second answer to
  a settled question.
- **The three spellings of absence on that row** — the distinction it exists to keep. **Compared
  and nothing matched** is the amber _No tags in common_, which stands **in the row's place** and
  is the one claim the row makes; the claim needs **both** tag terms, because a positive match
  needs only one and a claim about everything has to have asked everything. **Not compared** —
  both terms stood down — is the platform not knowing, so the tags draw untinted and nothing is
  said. **Matched beyond this build's vocabulary** is `matchedInFull`: `matched[]` is narrowed at
  the mapper like every other tag list, and that drop is the one place §3's silence would become
  a claim, so it draws as the second and withholds the term's measured zero with it. _Avoid_:
  collapsing the second and third into "no overlap" — one is a gap and the other is a claim.
- **Fact row vs reason line** — the two registers a card states something in. A **fact row** is
  a fact the card states unconditionally — the level row, the meta line, _You overlap_,
  _Predicted balance_ — and a **reason line** answers _why this person_, is selected, ranked
  and capped, and **states its evidence's facts without grading them**. The same term is one or
  the other on a given card and never both, which is the whole of the de-duplication rule. A
  **concern** is a reason line's shape in the opposite tone: the engine's own graded claim
  about a term, and the one thing on a card that is entitled to grade. _Avoid_: calling a fact
  row a reason, and "why-fit row", which is the sheet's.
- **Search envelope** — every fact about **the search** rather than about a candidate, and the
  second argument every card and the why-fit sheet takes: the id, the mode, the pool
  description, the radius clamp, the sort row's offers, the relaxation ladder's and the two
  version stamps. Its `mode` is **null exactly on the
  deck**, and it is passed whole rather than as a mode string precisely so it cannot be
  conflated with the mode the engine priced a row under, which is on the evidence. It is also
  where the searcher's **own** area code would be folded on, so that a card can compute the one
  comparison it is licensed to and still **read no global state** — and it is **absent**,
  because no route serves a player their own coarse area: `area_code` crosses on the candidate
  and on the distance evidence, and both are theirs. The meta line drops its clause and keeps
  its kilometres until the fact exists. _Avoid_: "the search" for the record it describes;
  passing `mode` alone; a sentinel for the missing area, which would silently mean _never in
  your area_.
- **Rung offer** — **what relaxing one of the searcher's own asks would be worth**, priced by a
  genuine re-run and drawn on the pool and **nowhere else**. Two asks — the week and the radius
  — and the letter that identifies the rung is **never printed** in any spelling, because
  letters were chosen over numbers precisely so nobody could line them up against a struck rung.
  Its count is _the total who would clear the floor at this rung_, so **the client never
  subtracts**: the rows on screen and the people above the floor are two populations, and one of
  them is not even a superset. `null` and `[]` are different answers — _nobody needed offers_
  against _there is nothing left to offer_. **The radius clamp gates the sentence, not the
  offers**: the bit says a widening _hit_ the slider's ceiling rather than that the searcher is
  at it, and the engine clamps such a rung down to the maximum and offers it anyway — so what
  the bit decides is the copy written when nothing is left, which is the reach as a fact rather
  than an instruction nobody can carry out. A rung priced at nobody is a **sentence rather than
  a button**. _Avoid_: "widening" for the offer (the widening is the engine's and never crosses
  on the request); "+3 more"; "the ladder" for one rung; reading the clamp as _the searcher is
  at the ceiling_, which deletes real offers from the one screen built to make them.
- **Standing statement** — what replaces _back_ once a rung has been taken: one sentence naming
  the widening this list ran under and the profile it did **not** touch. There is no way back to
  the strict list, because a player holding both would be diffing them to find the people that
  differ, which is the engine's job — so the way out is changing the ask again. _Avoid_:
  "undo" and "reset the search", neither of which exists.
- **Sort row** — the pool's chips, **rendered from `sorts_available` verbatim and omitted
  entirely when it is empty**. Re-sorting costs no round trip, so a sort is in no query key at
  all. The row gains **the way back** the moment the player leaves the order they arrived in:
  _Best fit_ is withheld precisely when the returned order already is best-fit order, so a row
  drawn from the server's list alone would make _Closest_ a one-way door. _Avoid_: a hardcoded
  row of four, which is three-quarters a lie today; deriving offerability from the rows.
- **The pin** — the pool's one reordering that is **not** a comparator: somebody with a live yes
  towards the searcher (`inclusion_reason == INTEREST_LIFT`) sits first **in the served order
  only**, whatever they scored, and drops into their honest place the moment any chip is tapped.
  It is **not** the `+12` #231 struck, and the falsifier is the printed number — a bonus is
  arithmetic on a published figure, changes what _best_ means silently and survives every
  re-sort, where a pin changes a **position**, prints the number the wire served, names itself
  on the card it moved, and releases. _Avoid_: calling it a boost or a bonus; adding anything to
  `fit` on this side.
- **Best match tag** — the coral tag on the row with the **highest ✦ on screen** — one card or
  none, the server-first row on a tie. It is keyed to **the ordering in force** rather than to a
  tapped chip, because _Best fit_ is withheld exactly when the served order already is fit
  order; it is hidden under _Closest_, _Evenest_ and _Most reliable_; and where it and the
  **[interest tag](#glossary--design-system-terms)** fall on one card the interest tag replaces
  it. It is the competitive card's alone, because that is the card with a tag slot beside the
  handle. _Avoid_: handing it to the runner-up when the top row is taken; reading _Best fit_ as
  a threshold — it is a **sort**, and it hides nobody.
- **Pending seat replacement** — **the seat the pool was opened against**, held route-locally
  and discharged by the first add: where that seat is occupied the add is a **replacement**, and
  the screen names whom it replaces before it happens. It **needs no clearing rule**, because
  the court pops rather than pushes and the route unmounts with it. _Avoid_: holding it in a
  store, which reintroduces exactly the bug the pop already prevents.
- **Play segment** — the **two ways through the Play tab** as one control, drawn on both
  screens and never on the tab bar: _Find a game_ and _Match me_. The halves move in opposite
  directions, and that is the whole of it — _Find a game_ is an **arrival**, so it calls [the
  reset](#routing) and ends the Play session, where _Match me_ is an ordinary push with Find a
  game left underneath. It is design-system 6.3, specified since the document was locked and
  built for this. _Avoid_: "the play tabs" — the bar has the tabs, and this is inside one of
  them; `router.back()` for the left half, which lands correctly on most paths and silently
  wrongly on the rest.
- **Outstanding yeses** — your **own** _Let's play_ yeses still standing in the sport on
  screen, read from `GET /interest` and **filtered by sport**, so that the number is about the
  deck it is drawn under. It is the one figure in the tab that background-refetches, because
  the rule against that is about **orderings** — a pool reordering under a finger — and a count
  has no order to lose. The prototype counted people who had waved at _you_, and that number
  **cannot exist**: an incoming yes never crosses the wire in either direction, which is what
  makes saying yes low-stakes. It moves on a tap's **own response** rather than on a refetch.
  It is drawn as a **sentence on the deck's ending** and nowhere else: it was `Match me · 3` on
  the segment until that was struck, because a number in that position reads as _how many cards
  are waiting_, which is the count the deck refuses to publish anywhere.
  _Avoid_: "Match me count" — the segment carries no number; "unread", "inbox" and "badge" —
  there is no inbox and the bar carries no badge;
  counting the outgoing list, which is this app answering a question the response answers.

### The result argument

Five client-only concepts, all of them in `features/games/`. The domain terms — Game, Result,
Score, Proposal, Correction, Counter, Acceptance, Standing — are the **root glossary's** and are
not restated here; what follows is only what this client had to invent to draw them.

- **Result argument** — **the seven screen states** a game can be in for the player reading
  it, folded in `domain/resultArgument.ts` from the standing, the standing proposal and which
  seat is theirs: awaiting an entry · never played · our score stands · their score stands ·
  both stand · confirmed · unscored, plus _not yours_ for a link that has gone stale. It is what
  decides whether a screen offers a **correction** or a **counter** — the same request and
  completely different news — so nothing outside that file reads a `GameStanding` directly.
  _Avoid_: "the result **conversation**", which this client used until
  [ADR-0146](../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) gave the
  glossary word to the Conversation context — two things called _conversation_ in one codebase
  is how somebody eventually subscribes the wrong one, and this one's own terms are Proposal,
  Correction, Counter and Acceptance. Also avoid "the result state" (there are two
  clocks and neither is a state machine), and naming a screen after the act, since one route
  takes three.
- **The score draft** — the grid as it is being typed: one entry per row it draws, each cell
  holding what somebody put there as characters. Characters rather than numbers because `''` and
  `'0'` are different facts — losing a set to love is a result and an unfilled cell is not — and
  **absolute**, `a` and `b`, exactly as the wire is. _Avoid_: holding it from the reader's point
  of view, which is one flip away from publishing a loss as a win.
- **The pad** — the entry instrument, brought across from `prototype/result-confirmation`
  unchanged: **the sport's own values**, `0…padTo`, plus a **`+` key** and a rub-out. A pad and
  not a stepper and not the system keyboard, because a score is typed standing on a court,
  one-handed. The `+` key is what makes the range a statement about the common format rather
  than a ruling — a padel third set is often a ten-point tie-break and a badminton game goes to
  thirty — so it is the sentence _we know the shape, not the rulebook_ built into the instrument
  and not only into the validator. _Avoid_: "the keyboard" (the system one is what this exists
  instead of) and treating `padTo` as a maximum.
- **Side labels** — _You / Them_ in singles, _Your side / Their side_ in doubles. **Sides even
  though a seat carries a handle**, and that is the decision rather than a leftover: a score is a
  **side's** claim — one per side, and either of the two who played it may agree with the other's
  — so a column headed with a name would charge a doubles score to one of them, and a listener
  reading a set cell by cell would hear the wrong person's six
  ([ADR-0141](../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). _Avoid_:
  heading a score column with a handle.
- **The court's handles** — what a seat says about the person in it, and **the whole of it**: no
  Level, no band, no area, no run of form, because those are what a _searcher_ reads to decide
  about a game that might happen. They are drawn in the eyebrow — _Padel · with kasia_w, tomek.p
  and marekb_, which is what tells two padel games in a week apart — and in the two sentences
  about something a **person** did: putting a score up, and agreeing with one. Always the
  **whole** handle
  ([ADR-0107](../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4), and the
  unknown player's `?` for a seat `users` can no longer answer for. _Avoid_: shortening one, and
  dropping a seat that has no handle — the court keeps its shape and loses a word.
- **The plan slot** — the one `ReactNode` `GameScreen` grew when it stopped being only the result
  argument ([#368](https://github.com/Raketa02/Raketa/issues/368)): a child the screen renders on
  its **entry arm** and knows nothing about, filled by `features/plans`
  ([ADR-0149](../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
  §2). **Three slots since [#414](https://github.com/Raketa02/Raketa/issues/414)** — `card`, the
  Now card without its doors; `court`, the pairing #415 fills; `plan` — drawn in that order on the
  plan lead, all opaque. **Neither type crosses** — there is no Plan, no ladder and no rung in
  this feature, and `eslint.config.mjs` refuses the import. _Avoid_: a second screen for a game
  that is being planned (a hand-off mid-standing gives a player two screens for one game depending
  which day they tap it), and passing the screen anything that says which of its two routes
  mounted it.
- **The entry lead** — which of two things an `AWAITING_ENTRY` arm leads with: **the plan** while
  the moment is still ahead, **the score** once it is here — and **the plan** while a seat is
  open, whatever the clock says. One standing over two landings, which is what §5.2 means by
  _Planning_ arriving at the Planning arm and _Needs result_ arriving at the score grid. It is folded in
  `features/plans` — the ladder reads a plan, and now the court — and **derived from the card's
  own door**, so the two cannot disagree: _the verb names what you arrive at_. It changes **what
  leads and never what is offered**: _We played_ is available on every arm with a full court, one
  press away on the ones that do not lead with it, and **withheld while a seat is open** — which
  is the domain's answer (`actsOffered`), not the lead's. _Avoid_: a rung crossing into
  `features/games`, a second table mapping rungs to landings, and reading it as a permission —
  entry is gated on the window and the court, and nothing else.
- **The court acts** — the fourth `ReactNode` slot on `GameScreen`, drawn **last** on the plan
  lead under _We played_: the acts on the court itself — _Leave this game_
  ([ADR-0162](../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)), and #419's
  fill and call-off beside it. Every one is a **challenge** act reached from a game — the seat
  that reopens is the challenge's — so the control, its sheet and its words are
  `features/challenges`', exported through its `types.ts` and composed by `features/plans`, which
  also decides whether one is drawn at all (the agreed moment). _Avoid_: the screen reading the
  slot, a leave control on the card or in the chat, and `features/games` learning what a
  challenge is.
- **The read instant** — `read_at`, the moment every standing and deadline in the list was
  folded against. **Every duration on these screens is measured from it and never from the
  device clock**, so a countdown cannot drift out of agreement with the word printed beside it.
  There is no date and no clock time anywhere in the feature: this platform has no calendar to
  print one against. _Avoid_: "now" — the phone's now is exactly the value that must not be
  used.

### The room

Eight client-only concepts, in `features/conversations/`, `shared/lib/platform/`, `shared/ui/`
and — for the one of them two features now read — `shared/date/`. **The quick chip is not among them**: the
questions are about the plan's slots and the words are §22.4's, so both are `features/plans`' and
only the row that draws them is the room's. The domain terms — Conversation, Message,
System line, Member — are the **root glossary's** and are not restated here; what follows is only
what this client had to invent to draw the room
([#364](https://github.com/Raketa02/Raketa/issues/364)) and to keep it current
([#365](https://github.com/Raketa02/Raketa/issues/365)).

- **Stream entry** — what one row of the room draws: a recorded **Entry** the server has
  answered for, or a **Sending message**, which is a message this phone has posted and the server
  has not answered for yet. `streamOf` puts what is going out after what has landed and drops a
  send the moment its message arrives, matched on `client_message_id` — so a resumed send can
  never draw twice. A sending message carries **no moment**: the instant something happened is the
  server's, and the phone's clock is the value the whole feature refuses. _Avoid_: "pending
  message" (the send is the one act here that is _not_ pending), and giving one a `seq` — the
  sequence is the server's and inventing a place in it is a claim, not a placeholder.
- **The platform day** — which calendar day an instant falls on **in `Europe/Warsaw`**, the one
  zone this platform arranges in. It is what the **day separator** is computed from, and the
  reason is one sentence: a device zone would put two people in one room on two different days.
  The same zone the plan's day and hour are recorded in, which is what lets a separator and a
  `DAY_RECORDED` line agree about which day Saturday is — and it is why the conversion is
  `shared/date/platformZone.ts`' rather than a feature's: the plan's day row is its third caller,
  and two implementations would put two surfaces of one screen on two different days. _Avoid_: the
  device's zone anywhere, a per-message clock — there is none, on purpose — and `Intl` with a
  `timeZone`, which can silently fall back to exactly the device day this exists to refuse.
- **The day separator** — the only time-shaped thing the stream draws, between entries on
  different platform days. A room lives at most a few days, so the fact worth having is _was this
  today_. _Avoid_: "timestamp".
- **The chat door** — the way into a room from somewhere that is not the Chats list, drawn as
  _Open the chat_. It is a **client join over `GET /conversations`** and it **fails soft**: no
  route serves a challenge or a game its conversation, so the surface finds the row whose id
  matches and draws nothing when there is none. The words live in `features/conversations` so the
  three surfaces that draw one cannot say three different things. _Avoid_: a `conversation_id` on
  anything but a conversation, and a disabled door — no door is the answer.
- **The live channel** — the one long-lived connection this app opens: `LiveStreamPort` over
  Server-Sent Events, held for as long as a room is on screen in the foreground, and **never one
  per row of a list**. It is a **platform port** like the position and the photo library, on the
  same second argument: a transport cannot be driven from a test either. _Avoid_: "socket" or
  "websocket" in this app's prose — the channel is unidirectional by construction and that is a
  decision, not an implementation detail.
- **The nudge** — one frame off that channel, and the whole of what it says is _this room moved_.
  The wire carries `{ v, conversation_id, last_seq }`; **the number stops at the port**, because
  the answer to a nudge is a re-read from the client's **own** high-water mark and a number handed
  up is a number somebody eventually pages from. _Avoid_: "event" or "push" for one, treating a
  missing frame as a gap to detect, and any arithmetic on `last_seq` above the port.
- **Live state** — the three-way _live · not live · held_ a room draws about itself, folded in
  `domain/liveState.ts` from the channel's standing and the account's. **Live is the absence of a
  claim** rather than a claim: an open channel, one still connecting and one deliberately closed
  behind a backgrounded app are one answer, because in all three the honest thing to draw is
  nothing. _Avoid_: a _Live_ badge, a connection indicator, and reading the port's status directly
  in a component — _only in the foreground, and only after a connect attempt has failed_ is the
  pair of conditions that gets dropped there.
- **Held** — the account cannot write anywhere another player sees it, and can always read. On this
  screen that greys the composer and every chip behind **one** pre-emptive note. It reaches the
  client only as the `account_held` refusal — no read serves it — and **nothing in this build can
  open a case**, which is a named exception recorded in `domain/liveState.ts`. _Avoid_: "suspended"
  or "banned", a note per control, and hiding the room.
- **The swipe row** — a list row that slides left to **reveal** one control behind it, and the
  control's act is never the swipe's: `shared/ui/SwipeRow`, on React Native's own `PanResponder`,
  claiming a touch only on a move that has travelled the **intent distance** across and further
  across than down, and never on the press — so a tap stays a tap on the door and a drift stays the
  list's scroll. A row rests **closed** or **revealed** and never in between. The Chats
  conversation row reveals _Leave the game_, which is the departure's door (`DepartureDoor`,
  `features/challenges`', **composed in by the shell** because neither feature may import the
  other); the organiser's challenge row, **while nobody has joined**, reveals _Remove the
  challenge_ (`RemovalDoor`, the same feature's own, so nothing is composed); every other row
  reveals nothing and does not move. Both doors are one shape — an `ActDoor` a surface draws
  however a door looks there, on `useActDoor`, which holds when the sheet is up and that a
  refusal's re-read is paid on dismissal — and the same act is the card's **accessibility
  action**, because a swipe is a gesture a screen reader consumes. _Avoid_: "swipe to delete" or
  "swipe to leave" — the swipe reveals a word and the sheet behind it acts; a row that slides to
  show nothing; a gesture library.

### The yes screen

One client-only concept, in `features/challenges/`
([ADR-0167](../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)).
_Yes_ is what the app already calls both acts — _I'm in_ is a yes, _Let's play_ is a yes that met
another — and this is the screen a yes lands on.

- **The yes screen** — the one-shot, full-phone screen a yes lands on the instant it is
  answered: the faces on the court reader first, one lime word, two pills, on the app's one
  dark ground, with the tab bar stood down. Keyed by the challenge and by **which yes** it is —
  a challenge's, whose word is _Challenge!_, whose picture is the court in two sides with a `vs`,
  and whose _Later_ is the Chats list; a mutual's, whose word is _Matched!_, whose picture is you
  and them with no `vs` and no empty seat in every sport, and whose _Later_ is a pop
  ([#434](https://github.com/Raketa02/Raketa/issues/434)) — and it reads everything it draws
  from the challenge the query cache holds, fetching it on open where the deck never held it. Its
  two doors are the only ways out: _Open the chat_ waits on the button for the room and lands as
  `[Chats list, the room]`; _Later_ goes back. **A tile** is the face the app draws everywhere,
  with two initials over a poster and an outlined empty seat as its two additions; **the spoken
  sentence** is the picture as one header, built from whole handles. _Avoid_: "the celebration"
  or "the moment" (not terms), "the match screen" (the word is copy on one face of it and never a
  noun for a game), pushing it from anywhere but a yes, and re-showing it — every exit removes it.

### The plan

Eleven client-only concepts, all of them in `features/plans/`. The domain terms — Plan, Slot, the
three recordings — are [ADR-0144](../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)'s,
re-keyed on the **challenge** and given an **anchor** by
[ADR-0164](../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md),
and are owed to the root glossary by [#332](https://github.com/Raketa02/Raketa/issues/332); what
follows is only what this client had to invent to let a room fill one in
([#366](https://github.com/Raketa02/Raketa/issues/366)).

- **The slot order** — `where · day · hour`, spelled once in `domain/slots.ts` and read by the
  card, by the quick chips one feature over and by the game screen's checklist. It is the order
  people discuss them in and of **decreasing negotiability**, and it is what _in slot order_ means
  everywhere that phrase appears. _Avoid_: a second spelling of it, and _part of day_ — that was
  the source's second slot and it is not one.
- **The day row** — the days a plan may still name: **today + 6, clamped to the row's
  `anchor + PLAN_HORIZON`**, so it shrinks as the week runs out and is **empty** inside the entry
  grace. _Today_ is the surface's own `read_at` — the room's in the chat, the games list's on the
  game screen — and the anchor rides on the plan row: the challenge's send until the game exists,
  then `planned_at`, only ever later, so the row **widens** when the court fills. _Avoid_: a
  calendar, a date picker, "expired" — the row shrinking is not a deadline passing — and deriving
  the anchor from a game, which a room without one does not have.
- **The hour row** — the thirty-five half hours between 06:00 and 23:00. _Bounded chips the
  platform offered, never a free instant_: the grid is a convention and
  `the_hour_is_not_offered` is what makes it true. _Avoid_: a wheel, a free-text time, and
  narrowing the row once an hour is set — a plan is never unmade.
- **The slot chip** — a pressable pill reading **its value or its name**, and the only surface in
  the app that edits a plan. `Chip` here because the plan is edited; `Tag` on the game screen
  because it is read. It goes **busy with the value it already had** while its write is going out.
  _Avoid_: "lock", a locked border, a `locked by everybody` pill and a complete state — filling the
  third slot **is** the lock and there is nothing left to draw about one.
- **The count line** — `2 of 4 in — you can plan now, lock when everyone's here`, drawn **where
  the lock button will be, exactly while the room has no game** (ADR-0164 §5): the room's members
  over the sport's seats. It is the note #324 owes an absent control — the button is **absent,
  never greyed** — and it becomes the button on the nudge that brings the game. A singles room
  never draws it, because two yeses is the whole court and the room opens with its game. _Avoid_:
  a disabled lock with a reason on it, counting seats from the plan, and drawing it on a game with
  a seat left open — that court has its game and the button, and the server's
  `the_court_is_not_whole` is a sentence.
- **The line-up, as the card reads it** — `LineUp`: `{ complete: true }`, or
  `{ complete: false, members, seats }`. **Complete means the court has become a game** (ADR-0165
  §1: the line-up having completed), never that the count is full — three of four with a game is
  a seat left open on a complete line-up. Folded by the room (`lineUpOf`, handed the sport's seat
  count), handed to the card, and read by `lockControl` as its `waiting` state before the slot
  count; the game screen hands `LINE_UP_COMPLETE`. _Avoid_: an optional count standing in for the
  fact, and deriving completeness from `members === seats`.
- **The quick chip** — one of at most three questions above the room's composer, **one per
  unfilled plan slot in slot order plus _On my way_ when the agreed day is today**. A chip **posts
  words and changes nothing**: filling the slot it asks about would record an agreement nobody had
  yet. The conditional fallback is what caps the row at three; unconditional it would be exactly
  four. The rule and the words are this feature's because both read the slot order; the **row** is
  the room's, because a chip is a message and the send is the composer's. _Avoid_: naming a
  weekday, a part of a day or a venue in one — a chip naming Saturday is wrong six days a week.
- **The plan tags** — the same three slots **read** rather than edited, on the game screen's
  **score lead**: `Tag`s and never `Chip`s, because _a control that cannot be operated must not
  offer the affordance of one_ (ADR-0149 §4 as amended by #414), and **one accessibility element**,
  because they are one fact in three parts with no action. The way to change one is the chat door
  beneath them. On the **plan lead** the plan is the chat's editable card, reused as it is, with
  the panel inside it through its `note` slot. _Avoid_: an `editable` prop on the card — the two
  drawings share a slot vocabulary and no behaviour — and a dot on one of these, which is the
  sport's and only the sport's.
- **The checklist** — three lines, capped, in one order on the game screen's **score lead**
  (both entry arms until #414): **what is true now**, **what is still to agree** (the whole list,
  in slot order), and **what it moves**, which is **cited rather than written**: `features/games`'
  own `worthLine`. On the plan lead the card's bars and the counter carry the first two and the
  eyebrow's kind word the third. _Avoid_: a fourth line, a second sentence about what a game is
  worth, and a branch per rung.
- **The composed game screen** — `GameScreenWithPlan`, the thing both of the game screen's routes
  mount: the join over games, plans and the player's rooms, the fold that says which act the entry
  arm leads with, and the three children that fill the screen's slots — the Now card with its
  doors off, the court's pairing, and the plan (`GameScreenPlan`, editable, on the plan lead;
  `GamePlan`, read-only, on the score lead). It is here rather than in `features/games` because
  every half of it reads a plan, and it is **one component rather than two lines in each route
  file** because a composition spelled twice drifts at one of them. _Avoid_: composing it at a
  call site, and giving it anything that says which of the two addresses mounted it.
- **The past combination** — a day and an hour that together name a moment that has gone. It is
  refused **in written copy rather than by a disabled control**, because the two are filled in
  either order and either can be the second, so the sentence names **both** remedies and no value.
  _Avoid_: pre-empting it on the client — the platform has one opinion about _now_ and it is the
  server's.

### Now

Eight client-only concepts, all of them in `features/plans/` — the rail and its card are this
feature's because a card needs a **plan** beside a **game** and ADR-0149 §1's arrow runs one way
([`the-loop-components.md`](../docs/specs/the-loop/the-loop-components.md) §3.4). What follows is
only what this client had to invent to draw what is happening today and next
([#367](https://github.com/Raketa02/Raketa/issues/367),
[#413](https://github.com/Raketa02/Raketa/issues/413)).

- **The ladder** — the four rungs a game's card is named by, **read in order**, in
  `domain/ladder.ts`: _a seat is open_ → **Needs a player**, _the agreed point has passed_ →
  **Needs result**, _all three slots filled_ → **Game on**, otherwise **Planning**. The
  conditions overlap on purpose and the order is what resolves them: **the clock outranks the
  checklist**
  ([ADR-0145](../docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md) §3),
  so rungs 3 and 4 are reached only while the point is still ahead — **the calendar is not a
  rung** ([ADR-0166](../docs/adr/0166-the-day-row-says-today-and-no-card-does.md)): a game on its
  own day is _Game on_ or _Planning_ by its slots, and the day row says _Today_ — and
  **the open seat outranks the clock**
  ([ADR-0162](../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md), #411 rule
  5): a court somebody left cannot be played or recorded until somebody is in that seat, so the
  rung is read off the court before the plan is asked anything. _Avoid_: restating _and the moment
  still ahead_ as a condition of its own — the order already says it — a _Today_ rung or any
  card named after the calendar, reading a rung anywhere but here, and asking the wire for the
  rung: nothing on it names one, and `player_id: null` is the whole of what it says.
- **The open seat** — a seat somebody has **left** and nobody has filled: `player_id: null` on
  the wire, `playerId` absent here, and **still a seat** — it keeps its place and its side, the
  court keeps its size, and every surface that draws the court draws it empty: the builder's
  dashed outline on the card, an **Open seat** row on the players card, `An open seat` in the
  card's spoken name. It stays open until it is filled, the game is called off, or the window
  closes into _Never played_. _We played_ is withheld while one is open. _Avoid_: dropping the
  seat (a three-person doubles game), drawing `?` in it (that is a person `users` cannot name),
  and a plus (nothing on these courts is pressable).
- **The agreed moment** — whether the plan's agreed point is behind the games list's instant:
  `momentHasPassed`, the first clock rung's own test, exported for the one control that is drawn
  only while it is ahead — _Leave this game_. The rung alone cannot say it, because _Needs a
  player_ outranks _Needs result_. _Avoid_: reading it against the phone's clock, and a second
  comparison beside the ladder's.
- **The agreed point** — the moment a plan names: the agreed **instant** when the day and the hour
  are both recorded, the **start of the following local day** when only the day is, and **nothing**
  when no day is. **Later rather than earlier**, so nobody is asked for a result before they could
  have played. It is the server's field and is never recomputed on this side. _Avoid_: deriving one
  from the day and the hour here — that is a zone conversion, and a second answer to _when is this
  game_ on one screen.
- **The rail** — `YOUR GAMES · n`, **one card, swipe**. A rail rather than a list, because
  _a game awaiting an entry, one awaiting an answer and one that never happened are one thing at
  three moments of its life_ and a rail keeps that refusal by not being a list at all: there is
  nowhere to put a shelf. The order is **the server's, newest arrangement first**, and it is
  **stable** where a clock sort silently re-orders a player's cards between sessions. _Avoid_:
  shelves, a re-sort, and calling it a list.
- **The card name** — which of eleven cards a game draws, folded at read time from the standing,
  the court, the slot count and the clock: the five rungs, **Confirm the result** (one name over
  four `AWAITING_ANSWER` arms), **Counted**, **Uncounted**, **Never played**, **Called off** (the
  fourth end, [ADR-0163](../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md) — shelved a
  day from `calledOffAt`, read before the window and the entry, and drawn as _Never played_ is),
  and the named gap for a standing this build cannot read. It is the
  **tag**, and every slot on the card that differs by name is a **table lookup on it** — the stage
  dot, the accent, the door's word — so a twelfth name fails `pnpm typecheck` in one file.
  _Avoid_: a status column, a client state machine, a switch over the names, and a twelfth card.
- **The shell** — one dark card for all eleven names: **header · slots + court · footer**. The
  Planning card is the first drawn for real; every other name is the same shell on **soft
  defaults** until its own design arrives, so the rail does not mix two visual languages and a
  card flipping under a thumb does not jump layouts. _Avoid_: a second card component, and a
  layout that changes shape rather than content between two names.
- **The stage dot** — the tag's dot on this card is **the stage's, not the sport's**: `arranging`
  while the game is still in the players' hands (Planning, Needs a player, Needs result, Confirm
  the result), `mint` where it is settled (Game on, Counted), the quiet hairline on the three
  endings nobody scored. It is legal because **the sport is the word beside it** — `PADEL`,
  `PADEL · FRIENDLY` — and nothing writes _singles_ or _doubles_: the court says the format.
  _Avoid_: a sport dot here, urgency as the pill's variant, and a dot on a card that names no
  sport.
- **The slot rows** — three, in the app's own order (**where · day · hour**, read from `slots.ts`),
  each a **settled bar**, a label (`WHERE` · `DAY` · `TIME`) and a value. **Bright is agreed, dim is
  not**: a settled slot draws its value big and white — the place without its court, `Sunday`
  `9 Aug`, the hour in mono — and an unsettled one draws _Not agreed yet_ small and grey. The card
  fills with brightness as the plan does. `TIME` is the card's word for the `hour` slot; the
  chat's chip keeps `Hour`. **On the day of the game the day row reads `Today` `14 Sep`**
  ([ADR-0166](../docs/adr/0166-the-day-row-says-today-and-no-card-does.md)) — `dayIsToday` in
  `slots.ts`, the plan's day against the platform day of the games list's `read_at`, the one
  definition the quick chips' _On my way_ also reads; the card is the only surface that says it,
  and _Today_ is the only word it says. _Avoid_: a figure, a line, a gloss, a countdown on any of
  them, a row that shrinks when its slot is empty, _Tomorrow_ or _Yesterday_, and _Today_ on the
  chat's chip or the game screen's tag.
- **The accent** — one table by name for the settled bar's colour **and** the wide door's variant:
  `volt` on Planning (_the plan is settled here_ — a meaning volt has on this card and nowhere
  else), mint on everything else as the soft default. _Avoid_: a volt bar over a mint door, and
  volt on `primary`.
- **The line under the slots** — the one fact the shell keeps from before: **Needs result's
  window** (`{duration} left`, folded against `read_at`, obeying nothing) and **the endings'
  standing** (`gameStandingLine`, cited). Nothing on the three plan-led rungs. _Avoid_: the gloss
  coming back under another name, and a checklist on the card.
- **The two doors** — **the wide door** is the next thing to do and its word changes with the
  stage: `Finish the plan` · `Open` · `Fill the seat` · `We played` · `Confirm the result`, one per
  name and none on an ending; it **navigates and never writes**. `Fill the seat` is the one door
  that runs something first — the challenge screen's fill, a search that reaches nobody — and it
  is `features/challenges`' `FillTheSeat` drawn in the door's place, only while the agreed moment
  is ahead. **The bubble** beside it is the icon door to the room, drawn only where there is one.
  **The body is not a door.** _Avoid_: a pressable body, a disabled control where a card offers
  nothing, a door that writes, and a third door.
- **The court's acts** — the game screen's fourth slot, `courtActs`, drawn last on the plan lead:
  every one a **challenge** act reached from a game, composed by `plans` through
  `challenges/types.ts` and handed its one rule as `offered`. `Fill the seat` (primary, where
  _We played_ would be, while the moment is ahead), `Call it off` (secondary, while a seat is open,
  for **any player on the court** — an accepted seat, a fact `CallOff` joins off the challenge
  list itself; ADR-0165 §5), `Leave this game` (last, while the moment is ahead). _Avoid_: `plans`
  learning what a seat's answer is, an act mounted and unmounted by its rule rather than handed
  it, and any of these on the card or in the chat.

### The sportsmanship card

Three client-only concepts, all in `features/sportsmanship/`. The domain terms — the card,
stars, blank, settled court — are the **root glossary's** and are not restated here; the word
**rating** is Skill rating's everywhere in this app, so nothing in this feature is spelled with
it.

- **The star draft** — what the player has said so far on one card, held as a player id to
  their stars for exactly as long as the card is on screen. **Absence is blank**, which is what
  makes _leave anybody blank_ representable without a sixth value on a five-point scale, and a
  map keyed by person is what makes _two answers about one player_ unrepresentable rather than
  validated. Pressing the star that already stands **clears the row** — a rule about what an
  answer is, in `domain/stars.ts` and never in the drawing, because sending is final and a
  finger that slipped is the one person _leave anybody blank_ has to be true for. _Avoid_:
  spelling a blank as `0` or as a null, and "the ratings" for what is typed — nothing is a
  rating until it is sent, and not even then by this app's vocabulary.
- **The rated court** — the evening a card is about, as **this feature declares it**: a game
  id, its sport, and who was on the court. `GET /sportsmanship` answers ids and nothing else on
  purpose, so the words come from the games list the card is drawn beside, and `Game` satisfies
  the shape structurally rather than the feature adopting another feature's entity. A card
  whose court is not in the list is **dropped**, because there would be nobody to name.
  _Avoid_: reading the games cache from this feature, and re-deriving the seven-day window on
  this side — which cards are open is the server's answer and this client holds no clock it
  could be right with.
- **The star row, drawn** — five 44pt targets, flush, with a drawn 24pt pentagram inside each
  ([6.13](docs/design-system.md#613-the-star-row)). `StarRow` is `shared/ui`'s: it has a touch
  rule, a press state, a fill pair and three pinned ratios, which is a design-system object
  whether or not a second feature draws it. Given is `ink` and blank a `muted` outline — the
  run of form's own pair at 3,24:1, so it reads with no hue perception, plus a **shape**
  difference the squares could not have — and each star is **its own accessibility element**
  with only the standing one `selected`, because a listener has no row to count along. _Avoid_:
  a zero star, half stars, and marking every filled star selected, which reads the row out as a
  table.

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
- **Presentation module** — a `*Presentation.ts` holding the words this app gives a closed
  server vocabulary, chosen **by the stable code**: localization goes _code → message_, never
  _message → message_. Two shapes, and the split is whether the sentence quotes a value — a
  `Readonly<Record<Code, string>>` where the code has no payload, so a code with no words does
  not compile, and one function per variant where it does. Feature-local, one per **vocabulary
  owner** rather than per screen. _Avoid_: a template inlined in a component, and rendering the
  backend's `message`, which ships English into every locale.
- **Copy deck** — the document a feature's presentation modules are written against and
  **cited by section, never restated**:
  [`the-words.md`](../docs/specs/matchmaking/the-words.md) for Play. It is where a later copy
  edit is argued, so that one voice can be checked against itself in one place.
- **Out-of-date gap** — what a build says about a code it has never seen:
  `shared/vocabulary/outOfDate.ts`'s one sentence, drawn wherever the screen states a count or
  a total the unreadable row belongs to, and a **drop** everywhere else. It names neither the
  code nor the vocabulary — a wire token in a player's face is not an explanation.
- **Recovery category** — which of _auto-retry · user-retry · re-auth · user correction ·
  conflict · terminal_ an error is. Assigned when the endpoint is mapped.
- **Paused, not failed** — a query or mutation the online manager is **holding** because there
  is no connection. It attempted nothing, so it produces no `AppError` at all and no `code`
  table or recovery category can reach it; what it gets instead is `offlineMessage()`, beside
  `recoveryMessage` and with **exactly two values, split on whether the act resumes by itself**.
  It is rendered **inline at the paused control**, never as a screen-level banner: a banner
  assumes being offline makes what is on screen wrong, and over a record pinned at
  `staleTime: Infinity` it is not. The split is **not** the HTTP verb — the line-up forecast is
  a `POST` that pauses and takes the first sentence. _Avoid_: "offline error" and
  "`OfflineBanner`", declined by name in `docs/architecture.md` Part 11.
- **Retry target** — which of two acts a _Try again_ re-runs, on the one wait where it is
  ambiguous: `POST /searches` **mints** a record and `GET /searches/{id}` **re-reads** one. No
  record id, re-fire the `POST`; a record id exists, re-read — because re-running the search
  mints a new id and orphans the line-up bound to the old one. The control is the failed act's
  own, never the screen's. _Avoid_: "refresh", which names neither act.
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
  capability the app cannot run in a test, with exactly two implementations: the real one that
  imports the module, and a fake in `src/test-support/platform.ts`. Three exist —
  `LocationPort`, `ImagePickingPort` and `LiveStreamPort` — and each is **the only importer of
  its module**, the way `shared/lib/auth` is the only importer of the keychain. The reason is
  not tidiness: a native module has no JS underneath it, so a feature that imports one is a
  feature no test can drive — and **the third one is a socket rather than a native module**,
  here on that argument alone, which is why _platform_ and not _native_ is the word. _Avoid_:
  "device module", "native service" — a module holding several capabilities is the utils bucket
  this app bans, and a capability is one file.
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
- **Returned to** — a screen coming back to the top of its stack, as `useOnReturn` reports
  it: the navigator's focus **after a blur**. A stack keeps the screen under the top one
  mounted, so a pop is neither a mount nor a foreground and nothing re-reads on it unless the
  screen says so. _Avoid_: "focused" for this — `useFocusEffect` fires on the way in as well,
  and a mount is not a return; and teaching `focusManager` to mean it, which would refetch
  every query in the app on every pop.

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
- **Marked card** — the pressable card's third border, and the one that is **not about the
  control**: pressed (`coral`) and selected (`ink`) are things the reader has done to the card,
  where **marked** (`voltStroke`, 1pt) is a standing fact about whoever is drawn on it. The
  press still wins over it, it announces nothing, and it is **never the only cue** — a caller
  that draws it also draws the word. Today its one caller is the competitive candidate card,
  bound to the tag being drawn rather than to the code beneath it.
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
- **Meter vs bar** — 7.3's two rows, and opposite objects. A **bar** states a fraction to a
  screen that names its denominator and reports one through `accessibilityValue`; a **meter**
  visualises a number the row beside it has already printed and is **hidden from assistive
  technology**. _Avoid_: using either word for the other, or calling a meter a progress bar.
- **A meter's tone** — which of three fills it draws in, `good` · `neutral` · `poor`. It is
  the **caller's** reading of the figure and never the meter's own: where a number turns poor
  is a fact about what the number means, so one ladder is read by every surface drawing it and
  a bar can never disagree with a pill above it about one ratio. _Avoid_: "the meter's
  threshold", which puts the ladder in the primitive, and treating the tone as the carrier of
  a value — it is always the third cue, behind the bar's length and the figure printed beside
  it.
- **Accessible name** — what a control announces. It is **copy**, not a component detail: it
  is localisable, it quotes formatted numbers, and it is composed from codes in a
  `*Presentation.ts`, never written as a template in the component that draws the control.
  _Avoid_: "aria-label", which is the web's spelling and not React Native's.
- **Live region** — a value that announces itself when it changes because focus is elsewhere.
  There are three in Play and no fourth. _Avoid_: `accessibilityLiveRegion`, which is Android
  only and fires on re-render rather than on arrival.
- **Collapsed presentation** — an animation skipped to its end state. **One condition, two
  causes**: the OS asking for reduced motion, or a screen reader running. They are not
  synonyms and a surface honours both.
- **Balance word** — the plain word beside an evenness figure — _Very even_, _Fairly even_,
  _One side favoured_, _Lopsided_. It breaks in four where the bar's tone breaks in three,
  deliberately: the word is what satisfies _never colour alone_, and a fourth tone would be a
  fourth meaning.

> The rating, band, confidence, match-fit and hold concepts these surfaces render are
> **interface** names only. Their domain terms are unmodelled — Bookings, Courts and
> Matches are Part 2 of the shared glossary. Settle those there first, then rename here.

Add player-app-only technical terms here as they are resolved. Anything describing the
_domain_ belongs in the shared glossary instead.
