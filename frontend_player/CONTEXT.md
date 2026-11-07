# Raketa Player App — Technical Vocabulary

This file holds **player-app-only technical vocabulary**. It does **not** define domain
language — those terms (User, Authority, Sport, Assessment, Skill rating, statuses,
events) live once in the
shared glossary [`../CONTEXT.md`](../CONTEXT.md), which all three apps obey. See
[`../CONTEXT-MAP.md`](../CONTEXT-MAP.md) for the topology.

> When you name a mobile architecture concept, use the term as defined here. When you
> name a _domain_ concept, use the root glossary. Don't drift to synonyms either avoids.
>
> **Cut back on 2026-10-06** with the Classic play removal
> ([#569](https://github.com/Raketa02/Raketa/issues/569)): the Players deck and its radar, the
> Chats tab, Find a game, challenges, plans and the old game card, the `/games/[id]` route, the
> feature flags and sign-up's radius and opt-in steps left the code, and every term that named
> only them went with them.

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
- **Scheme rule** — the environment fixes the scheme of the API URL: `https://` in the three
  deployed environments, either in `local`. Validated across the URL and the environment at
  launch, so a laptop URL under a deployed name is a refusal naming both rather than a build
  pointing at nothing. This is the **public-network** form of the platform's rule — the URL is
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
  lands from **one read**, the authenticated player the app already asks for. Its order is the
  rule: the account's profiles, then the naming for an account that is not **named** — that holds
  no nickname ([ADR-0199](../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3) — then
  the social steps for one with no Player profile, then the app
  ([ADR-0200](../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1). **A rating and an
  unfinished run route nowhere** ([#730](https://github.com/Raketa02/Raketa/issues/730)): a
  level is asked where play begins, by the **level door**, and a run left halfway is offered
  there. Until #730 the gate read three facts in parallel and had two more destinations,
  _resume_ and _welcome_. Distinct from the guard, and deliberately **not** part of session
  status — a profile check inside bootstrap would block every cold launch on a network request.
  _Avoid_: "onboarded flag" — there is no such thing, because a rating is per sport. Whether a
  _Player profile_ exists is not that flag: it is a per-player question with a per-player
  answer, which is the distinction [ADR-0090](../docs/adr/0090-onboarding-per-player-checkpoint.md)
  draws and the shared glossary now carries.
- **Profile (the switcher's)** — which hat the app is wearing for an account: **Player**, or the
  **Administrator** of one club ([ADR-0185](../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §1). UI vocabulary, never a domain term — a _Player profile_ is an aggregate, and this is not it.
  In code it is `ProfileChoice` (auth's) and the switcher's rows `ProfileOption`. The **last
  profile** is the one the phone remembers per account and the entry gate opens in
  ([ADR-0188](../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
  §2). Switching is client state, never a token. _Avoid_: "role" — `authority` on the wire is a
  different thing — and "account type".
- **Untrusted route input** — any param from a deep link, push payload, universal link,
  App Link or QR code. Zod-validated in the feature's `schemas/` before use.
- **Push token** — the address Expo's push service reaches this phone by, minted per Expo
  project and read through the push port; registered for the signed-in player and let go at
  sign-out, in a request's body and never a path or a log line (#559). _Avoid_: device token, which
  is the platform's own (APNs / FCM) under it.
- **Notice banner** — a notice pushed while the app is open, drawn by the app at the top because the
  phone presents nothing then; a press opens its game (#559). _Avoid_: toast — a toast is not a
  control and is never pressed.
- **`GAME_MOVED` notice kind** — the wire spelling of _Game moved_, the root term; always on and
  opened on the booked game (#677). `domain/vocabulary.ts` spells it.
- **`indoor` on the wire** — `true`, `false` or `null`. The mappers drop a `null` to an absent
  `indoor?`, and `courtKindWords` is the one place the phone spells it (#677).
- **Incoming link** — an address the operating system opens the app with, read by
  `+native-intent` before anything is routed. Only four are links — `join/<code>` (a **Group
  link**), `invite/<token>`, `reset/<token>` and `f/<code>` (a **Friend link**, #756) — by the
  app's scheme or the **link domain** (`EXPO_PUBLIC_LINK_DOMAIN`, unset today) — plus the bare
  `raketa://`, the existing-account invitation email's button; anything else is ignored (#520).
  _Avoid_: deep link for these four — any path is a deep link, and these are the only ones the
  app answers.
- **Held link** — an incoming link not answered yet, kept in memory (one at a time) through
  sign-in and onboarding until a place that can answer it is reached: Join a group, the
  invitation sheet, a sheet asking to sign out first, or a friend link's opening and Home. Dies
  with the process.
- **Install referrer** — the text Google Play keeps from the store page that installed the app,
  which the public site's Play button sets to its page's link (#755). Read **once, on an Android
  phone's first launch**, by a launch step (`readTheInstallReferrerOnce`), and a `join/` or `f/`
  link in it is held as if it had been tapped (#756). An iPhone has none. _Avoid_: "deferred deep
  link" — nothing is deferred by a service; Play keeps one string, read once.
- **The shell** — the tabs a signed-in player is inside, and the **one stack** under them:
  `Home · ⚡Play · You`, three fixed columns drawn by `TabBar` and mounted once by `TabShell`.
  Deliberately **not** `<Tabs>`: that keeps a history per tab and restores it, which is the
  whole of what [#227](https://github.com/Raketa02/Raketa/issues/227) forbids. _Avoid_: "the
  tab navigator" — there isn't one.
- **Home** — the first tab, route `/`: the booked-games rail under the tab's own words —
  `features/proposals`' `HomeRail` over `GET /home`, with the payments to confirm above it. It
  was **Now** until [#550](https://github.com/Raketa02/Raketa/issues/550), and the rename is
  whole — key `home`, label _Home_, `HomeScreen`, `HOME_COPY`, `landOnHome`. **Home's badge** is
  `useHomeBadge()`, the read's `needing_you` — the cards that need you and every payment you have
  to confirm — and nothing at nought; the shell reads it on every screen, so it holds `GET /home`
  for the session, and since [#576](https://github.com/Raketa02/Raketa/issues/576) that is the
  only list it holds. _Avoid_: "Now" for the tab.
- **The reset** — `resetShellStack`, the shell's only navigation move: throw the stack away
  and lay a new one down. Home and You lay down one screen and ⚡Play lays down two — Home
  under Play's root — which is why back from Play's entry leaves Play rather than walking it;
  and a game that has just filled lays down Home before its details are pushed over it, so
  back from the game is Home. _Avoid_: "switching tabs" as though it were a push.
- **A placeholder tab** — a tab with no screen behind it yet, and **there is none now**. For
  as long as one existed it stated what its tab would be and that it was not built, in one
  sentence, so a player could tell it from a bug; the sentence was a **citation** of a decision
  taken elsewhere. Every tab that held one was built or retired — **You**, the last, by being
  built as onboarding laid out flat (ADR-0179) — and the union and the table went with them,
  because a shape kept for a case that cannot recur is not a fact. What survives is the rule
  the placeholders were written under: **no sentence the shell writes says nothing is
  happening**, and `shellCopy.test.ts` still holds every line to it. Play's _Explore_ keeps it
  by saying nothing at all — a blank page in `features/find_a_game_next` until the rebuilt Find
  a game lands. _Avoid_: "empty state" (that is a screen with a real answer of nothing) and
  "coming soon" — a screen that lands with its contract says in one line what it is, never that.

### The onboarding flow

Client-only concepts. **None exists on the backend and none should:** an Assessment is per
sport, and nothing on the server records the sequence of them, which door a walk began at, or a
half-answered second part. The pass and the door are modelled in `features/onboarding/domain/`
(`onboardingPass.ts`, `levelDoor.ts`) and the pass is held in that feature's store; the steps
belong to `features/player_profile/`, which owns the second part and the You tab that edits
the same values. **Onboarding is a nickname and the six steps** (ADR-0200 §1): sign-up, the
naming, the steps, Home — eight screens, and no questionnaire.

- **Onboarding pass** — **one walk through the questionnaire**: the sports the player chose,
  in the order they chose them, and which of those produced a Skill rating. It is what the
  eyebrow counts (_Padel · Rating 1 of 2_), what decides which sport comes next, and which sport
  the way back stands on. Client-only, in-memory, never persisted. It **begins** explicitly —
  at the picker with the queue that was chosen, at a card or chip with its one sport, at the
  level door's _Carry on_ with the run's sport, or at the question route for a run reached by
  a link with no pass running, which is a genuine pass of one sport — and it **ends** in one
  place, when the player reaches the app. Between passes there is **no pass**, and that absence
  is load-bearing: it is what lets a run reached by a link begin one without adopting a
  finished walk's queue. **Every pass begins inside the app, and a pass has an origin**
  (ADR-0200 §5): **Home** (`FROM_HOME` — the picker opened with no group, and a run reached by
  a link), which ends there with _Back to Home_; the Skill passport's _Add a sport_, which
  begins a pass of exactly one sport and ends back on the passport with _See your ratings_
  ([ADR-0179](../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §3); or **a group's tab** — the level door, an official group's card, _Post a game_'s or
  Members' — which ends back on that group, on that tab, standing on the sport rated last, and
  whose last result says _Back to {group name}_. _Done for now_, _continue later_ and _abandon_
  end it at its origin too, and so does **turning back** from the picker — a pass over no sport,
  begun and over at once. A link naming a sport outside the running pass is sent out to `/`
  rather than into the middle of a flow — a second door is not a shortcut. Onboarding's own
  origin, _welcome_, went with the questionnaire leaving onboarding (#730). _Avoid_: **"run"**
  — that is one Assessment, and a pass is a sequence of them; **"session"** — that is the auth
  session, and the two have different lifetimes; also "onboarding state", "wizard".
- **Level door** — the one dark card a player rated in nothing meets **in a player group**, in
  place of Games, Fill in and Friends, _Post a game_ and Members (`LevelDoor`, onboarding's;
  `needsALevel`, groups') — ADR-0200 §2. It offers one of two things, by `levelDoor`'s rule:
  **_Get your level_** — _pick the sports you play, a few questions each_ — opening the picker
  over every sport with nothing ticked; or, with a run left halfway, **_Carry on with your padel
  questions_** — _you're on question 5_, counted off the run's own transcript — opening that run
  where it stands, and never offering to start again. Nothing is drawn until it knows which.
  **An official group never draws it**: its own card offers its sports (ADR-0200 §3). It is
  the only thing that offers a run left halfway — the **Deferred run** of #730's predecessors,
  held on the phone so the gate's _resume_ would leave it alone, went with that branch. _Avoid_:
  "gate" — the entry gate routes launches, and this routes nothing; "rating wall".
- **Social step** — one of the **six** profile steps, onboarding's **second part** — all of it
  after the naming since the questionnaire left onboarding (#730): tags, intro,
  photos, availability, location, gender, in that order (`SOCIAL_STEPS`). The step names are
  the route segments, so `/location` is the screen that asks for a Location area and there is
  no second spelling of the six. The order is not arbitrary at three points: **the intro
  straight after the tags**, because the tags ask what kind of player somebody is in the
  platform's words and the line is the same question in their own
  ([ADR-0170](../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
  §5); **gender with the matching constraints rather than with the tags**, because a preference
  over who you play with narrows who is put in front of you rather than describing you; and
  **gender last** — _Who you play with_ carries the finish (`ProfileFinish`), and the radius and
  the opt-in that used to follow it left with the old loop's ranking
  ([#582](https://github.com/Raketa02/Raketa/issues/582)). **The part is the unit, not the
  step** — back and forward move freely between steps and never cross out of the part, the
  first step has no back control, and the last is followed by the profile commit rather than
  by a seventh screen
  ([ADR-0090](../docs/adr/0090-onboarding-per-player-checkpoint.md)). _Avoid_: "wizard
  step", "page"; also "onboarding step" for a question in the questionnaire — that is a
  **position** in a run, and the two move by different rules.
- **Intro shape refusal** — the two of `intro_not_admitted`'s three reasons that are facts
  about the string itself, `too_long` and `multiline`, which the intro step reads off the
  Profile draft and shuts _Next_ on before anything is sent — and the You tab's _Intro_ reads
  off its draft and shuts _Save_ on — in the **same three-member vocabulary** the wire's
  refusal carries, so one sentence table serves the refusal a screen pre-empts and the one
  the commit or the intro write brings back. The third, `contains_contact`, is **the
  server's pattern and never this app's**: a copy of it would be a staler one on every phone
  the day it is tuned from a refusal, so it lands at the write — four screens later on the
  step, one press later on the tab, drawn in the same place under the box — and the step
  says the rule up front instead. Counted in **code points**, as the server's `len`
  counts, and trimmed first, as the server trims. The [Intro](../CONTEXT.md) itself is the
  root glossary's. _Avoid_: "validation" — the client validates nothing, it pre-empts two
  refusals whose authority stays on the server; "content filter" — nothing here reads what
  the line says.
- **Profile draft** — every answer the second part has collected, held **on the client**
  until the one commit that ends the part. It is the part's and only the part's: the You tab
  edits the same facts against the same rules and holds **no draft of this kind** — each
  screen there holds a draft of one fact beside the profile read until its _Save_, and the
  photos hold none at all. Three of its fields start **empty** because empty
  is a real answer — no photo, a blank week, and the intro box with nothing in it — and the
  intro is held **as typed**, untrimmed, so a round trip finds the box as it was left; what
  the commit carries is the trimmed line, or no field at all. In memory, never persisted, and never sent
  anywhere before that commit — which is what makes moving between steps free and what makes
  leaving mid-part restart at step one. Its absence is a state: no draft means the player is
  not in the part, which is how a link naming a step in the middle is told from a player who
  walked there. _Avoid_: "form state" — it outlives every screen in the part; "saved draft"
  and "resume" — nothing is saved, and the asymmetry with a run left halfway, which the level
  door carries on from where it stands, is deliberate.
- **Profile commit** — the Profile draft with **every answer present**, and the one request
  that carries it. A distinct type from the draft on purpose: three answers can be missing
  while a player is walking the part — the week, the area and the gender (`MissingAnswer`) —
  and none of them may be missing in what is sent, so a partial commit is unrepresentable
  rather than merely avoided. It is built in one place (`readyToCommit`), which also names
  what is still wanted so the last step can ask for it rather than only refuse: the gender is
  the one the last step asks itself (`ASKED_ON_THE_LAST_STEP`), and the other two are an
  `AnswerAskedBehind` the finish sends the player back for. **Where the part stands**
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
  filter what a player sees — it hides them from every man, including men who would play
  anybody, and that is the half nobody would guess. The rule decides _whether there is a
  cost_; this app's copy says it **at the moment of the press, on every surface that takes
  the value** — the step, and since [#472](https://github.com/Raketa02/Raketa/issues/472)
  the You tab's _Who you play with_, which draws the same group (`GenderControls`) under a
  _Save_ of its own. Learning it from an empty deck is not acceptable
  ([ADR-0096](../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
  _Avoid_: "filter" — a filter is one-directional and this deliberately is not; "privacy
  setting" — it changes who is matched, not what is shown, and neither value is ever drawn
  to anybody but its owner, on the two screens that take it and on the row's line only as
  _Matched with …_, never the gender (ADR-0179 §4).
- **Photo workbench** — the pictures a photos screen is holding, each with the upload it is
  in the middle of. **It has two homes** (ADR-0179 §2). On the step it sits beside the
  Profile draft in the same store, and it is not an answer: a local `file://` URI is
  worthless to the server and an upload in flight has nothing to commit, so what reaches the
  draft is **derived** from it — the ids of the photos that arrived, in the player's order.
  One store because the two share one lifetime and that derivation is the invariant; two
  would be two things to reset and a sync somebody forgets. On the You tab it sits beside
  the Profile surface, **seeded once** from the profile's photos — each restored tile drawn
  from the signed address `GET /photos/{id}` answers, because a restored photo has no device
  copy — and the same derivation is a `PUT /players/me/photos` on every change that moves
  the ids: the step has no _Save_, so the tab has none, and the row is the state. Either way
  the hook that picks and uploads is one and reads the bench _as it is now_, because the
  queue runs between renders. _Avoid_: "photo state", "upload queue" — the queue is one
  promise chain inside the hook, and it is not what this holds; "draft" for the tab's bench —
  nothing on it waits for a button.
- **Profile options** — the **one read** the six steps are drawn from: the Social tag
  vocabulary with its grouping and how many tags a profile must hold. Reference data owned
  by TanStack Query, fetched once for the whole part, and the
  reason no client restates a vocabulary or a bound the commit re-validates against. Ids and
  grouping cross the wire; **every label a player reads is this app's copy**, so a served id
  this build has no words for is dropped rather than drawn — the answer `toSport` gives an
  unknown sport. _Avoid_: "config" and "settings"; neither is about this player, and both
  invite something per-player being added to it.
- **Profile surface** — the **one read** this app holds about the player's declared facts:
  the weekly hours and the per-sport Play intent, in one round trip across the two aggregates
  that own them — and, since the route **grew** the day **You** was built
  ([#466](https://github.com/Raketa02/Raketa/issues/466), ADR-0179 §4, §8), the Social tags,
  the photos with their verdicts and the intro, read on #471, and the **owner's own** gender
  and preference — the one shape that carries them — read on #472. The Search radius and the
  standing Proposals opt-in left it with the old loop
  ([#581](https://github.com/Raketa02/Raketa/issues/581)). There is no `has_location`, because a
  profile cannot be committed without an area and a flag that cannot be false is a branch
  nobody tests. Its home is `player_profile/` because the **writes** are: one unkeyed `PUT` per
  fact, and a read whose paired writes live in another feature is a read in the wrong feature.
  **The You tab draws it**, every one of them as a fact with a door, and its screens write the
  week, the tags, the intro and each of the two gender groups on a **button** and never on
  release, and the photos on every change to the row. _Avoid_: "the profile" for this — it is
  a surface over one, and calling it the profile is how a field gets added to a body scoped to
  what the tab draws.

### The Play tab

- **Play segment** — _Groups_ or _Explore_, the two pages the Play tab opens on (#512): Groups
  is the player's groups, Explore the blank page the rebuilt Find a game grows in
  (`features/find_a_game_next`). The shell's, remembered per account by the phone-preferences
  store, and **Groups** whenever nothing — or nothing this build recognises — was saved.
  _Avoid_: "tab" — Play is the tab and these are its segments.

A group's page is Play's too (`/play/group/[groupId]`), and its **Games** tab is the deck
`features/proposals` deals ([#553](https://github.com/Raketa02/Raketa/issues/553)). Two of that
deck's client-only concepts are listed here; the yes that fills a game is
[the fill](#the-fill)'s.

- **Declaration interstitial** — the one-tap question a player meets in front of a group's
  Games deck when they have **never said what kind of game they want in its sport**: the
  deck's read comes back with no segments, and the question replaces the deck until it is
  answered, then the deck is read again (`DeclarationInterstitial`, reporting `DECK`).
  [ADR-0094](../docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)
  calls it _"permanent, not a migration path"_: it is what makes _every player dealt a game
  has declared_ true rather than intended, and it closes a sport rated before the declaration
  shipped, a restored account and a bug in the tail with one screen. **It is not a mode
  toggle**, and the two must never be collapsed — it writes a `PlayIntent` with three values,
  where the old Find a game's toggle chose a search mode with two, which is the arity gap
  ADR-0094 spent a type on. It began on Find a game and came to `features/proposals` with the
  deck in #574. _Avoid_: "the intent prompt" — it gates the deck rather than offering
  something beside it; "onboarding step", which it is not and must not become.
- **The stamps** — the yes stamp and _NOT THIS TIME_, two outlined words a Games card wears under
  the thumb, one volt and one white, tilted, **invisible at rest**, fading in with the drag and
  full at the threshold (95pt) where a release commits the answer in the drag's direction
  ([ADR-0169](../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §3). The
  drawing is `DeckStage`'s and the words are the caller's (`stampsFor`): the yes reads _PAY_ where
  it charges at once and _I'M IN_ on a vote, the card's share after `STAMP_JOIN` either way —
  _PAY · 32 zł_ (Q124) — while the ball under the stage stays _I'm in_ (`ANSWER_LABELS`). They are
  **feedback and never controls**: hidden from assistive technology and unspoken. The three
  round buttons under the stage — ✕, i and a drawn tennis ball (`DeckAnswers`) — are the path
  that is never removed. _Avoid_: "swipe buttons"; a stamp that is pressable; a stamp without
  its button.

### The record's drawn parts

Five drawn parts in `shared/ui/`, with the vocabulary under them in `shared/vocabulary/`, built
for Play's candidate cards and brought below every feature when the record sheet became their
second caller. The cards left with Find a game
([#576](https://github.com/Raketa02/Raketa/issues/576)); the parts stayed with the record sheet
(`features/player_record/`), the You tab's header card, a game's forecast and the post-a-game
slot sheet. _At stake_, _Run of form_, _Social tag_ and the _On-court check_ are the root
glossary's terms; what follows is only how this client draws them.

- **Photo panel** — the box that draws a player's photograph (or their generated poster) with
  the **Level** hugely over it, the **Sport** small and capitalised beneath, and the **on-court
  mark** above. `PhotoPanel`, over 7.16, at two sizes that each **re-derive** from the panel's
  own width rather than scale: `card` (74 × 92), on the You tab's header and the post-a-game
  slot sheet, and `record`, the record sheet's header. The Level and the Sport are optional:
  somebody rated in nothing draws their poster with nothing over it, never a nought. _Avoid_:
  "avatar" and "thumbnail" — the photograph is the ground and the rating is the subject.
- **On-court mark** — the two words the photo panel prints at its top, after a drawn tick, on a
  photograph the on-court check **passed**: `ON COURT`, `OnCourtMark`, over one boolean the
  record's mapper folds — a photograph, and the check's `allowed` (`onCourt`). **Only a pass is
  marked.** _Checked and flagged_ and _nobody looked_ draw and announce **identically**,
  because a surface must not publish a moderation outcome about a third party, and the
  generated poster draws none because it is not a photograph. It carries **no number in
  either register**: the confidence never crosses on any route. The tick is `shared/ui/Tick`'s
  path sized to the words, because Archivo draws no U+2713 (7.15, `onCourtMarkFit.test.ts`).
  _Avoid_: "verified", "badge" and "shield" — it verifies nothing about a person and it is a
  label with no ground; "photo review", which is the uploader's surface and a different fold
  of the same code (`player_profile` warns where the record marks); a **tick** anywhere in this
  app that is not `shared/ui/Tick`'s drawn geometry.
- **Social tag row** — a row of up to six of somebody's Social tags, and the **overlap** drawn
  over it: the ones the reader also chose are tinted and carry `· you too` in words — but only
  an overlap the engine published, never one recomputed from a profile read. **The rule and
  the drawing are two layers**: `SocialTagRow` and the four-answer `SocialTagOverlap` are
  `shared/`'s, and the record's rule over them is `player_record/domain/tagRow`'s
  (`recordTagRow`). The overlap's only source was the candidate card's `matched[]`, so since
  the cards left no caller hands the record sheet one and the row draws its tags untinted.
  _Avoid_: "chips" — nothing here is pressable, so they are tags (6.4).
- **Stat box** — the recessed box a figure is **compared** in: `StatBox`, a `paper2` box with a
  name over a figure. The record sheet's three blocks (`RecordBlocks` — the Player Score, the
  last five, the count) and a game's two _at stake_ tiles (`games`' `StakeTiles`) are its two
  placers, and **what is shared is the box and never which boxes**. Recessed rather than plain
  text because a Player Score is **not a rating** and must not read as a second one beside the
  Level — 7.13 and 7.14. A box whose fact is absent is **not drawn**, so the ones that remain
  fill the width and no hole marks the gap. _Avoid_: a "stat card", which is a surface, and
  this is a box inside one.
- **Run of form, drawn** — five squares, one per result, oldest to newest and **never padded**: a
  run of three is three squares and the space after them, because the length is the statement.
  `RunOfForm` is `shared/ui`'s, drawn in the record sheet's blocks against a **pinned** geometry
  test. Won is `mint` and lost is `muted`, off the component's own `RUN_OF_FORM_FILL` in
  `recordSquares.test.ts` — a hue step, where it was a lightness step (`ink`, 3,24:1) — and
  because a square carries no word, the whole row reaches a listener as **one counted clause**
  against the run's own length (_3 of the last 5 won_) rather than as five elements. An outcome
  this build cannot read takes the **whole field** with it at the mapper, for the same reason:
  half a run cannot be drawn honestly, and _Counted_ beside it goes on printing. _Avoid_: a
  fifth square in a neutral fill, which claims a game nobody played; five spoken states, which
  reads the row as a table.

### The result argument

Nine client-only concepts, all of them in `features/games/`. The domain terms — Game, Result,
Score, Proposal, Correction, Counter, Acceptance, Standing, and attendance's Isn't here yet,
Arrival, Came late, Didn't come and I was there — are the **root glossary's** and are not restated
here; what follows is only what this client had to invent to draw them.

- **Result argument** — **the screen states** a game can be in for the player reading it,
  folded in `domain/resultArgument.ts` from the standing, the scores on the table, the game's
  kind and which seat is theirs: awaiting an entry (_How did it go?_) · our score stands ·
  their score stands (_Is that right?_) · both stand · confirmed · disputed · played · no score ·
  for fun (_Played_, which asks nothing), the endings a booked game adds (called off, started
  short) and its two at the court (not here yet, didn't come —
  [#658](https://github.com/Raketa02/Raketa/issues/658)), plus _not yours_ for a link that has
  gone stale.
  **An agreement is not one of them** since #654: _That's right_ settles at once, so the next
  read is confirmed ([#656](https://github.com/Raketa02/Raketa/issues/656)). It is what
  decides whether a screen offers a **correction** or a **counter** — the same request and
  completely different news — so nothing outside that file reads a `GameStanding` directly.
  _Avoid_: "the result **conversation**", which this client used until
  [ADR-0146](../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) gave the
  glossary word to the Conversation context — two things called _conversation_ in one codebase
  is how somebody eventually subscribes the wrong one, and this one's own terms are Proposal,
  Correction, Counter and Acceptance. Also avoid "the result state" (there are two
  clocks and neither is a state machine), and naming a screen after the act, since one route
  takes three.
- **The attendance block** — _Who's here_, then _Who was there_: the rows `attendanceBlock` folds
  in `domain/attendance.ts` for a booked game's reader
  ([#658](https://github.com/Raketa02/Raketa/issues/658)) — a tap about each other player in the
  first half hour (_isn't here yet_, or _is here_ about somebody awaited), a late claim to confirm
  afterwards, and _came late_ said beside whoever did. **The reader's own act is not a row**: _I'm
  here_ and _I was there_ are pinned, as the score's send is. The **first half hour** is the one
  window measured on this side — the booking's `startsAt` plus 30 minutes against `read_at`
  (`tapsAreOpen`), because nothing on the wire carries it before somebody is tapped; every outcome
  is the backend's fold. _Avoid_: "check-in" (removed, ADR-0195 §4), and "marking" or "reporting"
  somebody — #560's no-show report, which this replaced: nobody marks anybody, a tap only says they
  aren't here yet, and their arrival lifts it.
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
  Level, no band, no area, no run of form, because those are what a player reads to decide
  about a game that might happen. They are drawn in the eyebrow — _Padel · with Kasia Wójcik,
  Tomek Przybylski and Marek Baran_, which is what tells two padel games in a week apart — and in
  the sentences about something a **person** did: putting a score up, and leaving a game that was
  then called off.
  Always the **whole** nickname, never with an @
  ([ADR-0107](../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4, read on
  the nickname again by [ADR-0199](../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1:
  the nickname is a handle, so the term's word is right again), and the unknown player's `?` for
  a seat `users` can no longer answer for. _Avoid_: shortening one, and dropping a seat
  that has no name — the court keeps its shape and loses a word.
- **A person's `name`** — the field a read model carries for what a person is called: **their
  nickname**, mapped from the wire's `nickname` at `mappers/`, whole and never with an @
  ([ADR-0199](../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). It keeps the word
  for the reason `playerName()` does (ADR-0199, _Neutral_): _name_ there means _what a player is
  called_. Where a shape once held a Name **and** a nickname — the authenticated player, the
  record — it holds `nickname` alone. The one such value that is not always a nickname is a
  group's `administratorName`: _… runs this group_ names an Administrator who has never played by
  the name their club typed (§4). _Avoid_: reading it as the retired **Name**, and drawing an @.
- **The open seat** — a seat somebody has **left** and nobody has filled: `player_id: null` on
  the wire, `playerId` absent here (`openSeats`), and **still a seat** — it keeps its place and
  its side, and the court keeps its size. _We played_ is withheld while one is open
  (`actsOffered`), until it is filled or the game is called off; a booked game whose hour comes
  with one open started short. _Avoid_: dropping the seat (a three-person doubles game), and
  drawing `?` in it (that is a person `users` cannot name).
- **The slots** — the four `ReactNode`s `GameScreen` grew when it stopped being only the result
  argument ([#368](https://github.com/Raketa02/Raketa/issues/368)) — `card`, `court`, `plan` and
  `fill` — and `entryLead`, which of two things an `AWAITING_ENTRY` arm leads with, the plan or
  the score. The screen draws each and reads none
  ([ADR-0149](../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
  §2): they were how the old loop's card, pairing, plan and _Fill the seat_ were composed onto
  it without `features/games` learning what a plan was. That loop is gone
  ([#576](https://github.com/Raketa02/Raketa/issues/576)), and the one route that mounts the
  screen now — a booked game's result, `BookedGameResult` — leads with the score and hands every
  slot `null`, each for a reason of its own: the booking is the plan, the details are the card
  and drew the forecast, and a seat open on a booking is a rescue. The props stay until a
  ticket folds the screen to the one lead it has. _Avoid_: reading the plan lead as a live
  arm — no caller reaches it.
- **The read instant** — `read_at`, the moment every standing and deadline in the list was
  folded against. **Every duration on these screens is measured from it and never from the
  device clock**, so a countdown cannot drift out of agreement with the word printed beside it.
  There is no date and no clock time anywhere in the feature: this platform has no calendar to
  print one against. _Avoid_: "now" — the phone's now is exactly the value that must not be
  used.

### The room

Eight client-only concepts, in `features/conversations/`, `shared/lib/platform/` and — for the
one of them several features now read — `shared/date/`. The room is a booked game's: opened with
the booking and reached from the game's details, with no plan card, quick chips or details door
in it since the old loop left ([#576](https://github.com/Raketa02/Raketa/issues/576)). The spec's
Q100 (2026-10-09) makes the bubble on the game's Home card a second door: it opens the room
straight over Home, and Back returns to whichever screen opened it ([#619](https://github.com/Raketa02/Raketa/issues/619)). The
domain terms — Conversation, Message, System line, Member — are the **root glossary's** and are
not restated here; what follows is only what this client had to invent to draw the room
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
  It is `shared/date/platformZone.ts`' rather than a feature's because the room, the notices,
  the receipts and every club day and hour a Games card, Home and posting name all read it, and
  two implementations would put two surfaces on two different days. _Avoid_: the device's zone
  anywhere, a per-message clock — there is none, on purpose — and `Intl` with a `timeZone`,
  which can silently fall back to exactly the device day this exists to refuse.
- **The day separator** — the only time-shaped thing the stream draws, between entries on
  different platform days. A room lives at most a few days, so the fact worth having is _was this
  today_. _Avoid_: "timestamp".
- **The chat door** — the way into a booked game's room: from its details, drawn as _Open the
  chat_ (`OPEN_THE_CHAT`, in `features/conversations` so every door says the same words), and
  the bubble on its Home card (Q100), named the same. It is
  a **client join over `GET /conversations`** by the row's `booking_id` (`useBookingRoom`, and
  `useBookingRooms` for Home's cards) and it **fails soft**: no read serves a booking its
  conversation, so the surface finds the row whose booking matches and draws nothing when there
  is none. _Avoid_: a `conversation_id` on anything but a conversation, and a disabled door — no
  door is the answer.
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
  screen that greys the composer behind **one** pre-emptive note. It reaches the
  client only as the `account_held` refusal — no read serves it — and **nothing in this build can
  open a case**, which is a named exception recorded in `domain/liveState.ts`. _Avoid_: "suspended"
  or "banned", a note per control, and hiding the room.

### The yes screen

One client-only concept, in `features/proposals/`
([ADR-0167](../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)):
the screen a yes lands on. Its first two faces — a challenge's _Challenge!_ and a mutual's
_Matched!_ — left with the old loop ([#576](https://github.com/Raketa02/Raketa/issues/576)); the
ground, the entrance and the tile came to `features/proposals` with the face that stays (#574).

- **It's a game!** — the full-phone screen a yes lands on when it **filled a game** dealt in a
  group's deck (#555) — booked, or waiting for one payment, with one line under the word for what
  is still missing then (#630, Q110; no club confirms a game since ADR-0196, #676): your side and
  theirs sliding in to meet with a `vs`
  between, one lime word, two pills, on the app's one dark ground (`YesGround`), moved once by
  `YesEntrance`. The faces are drawn off **the card the yes was said on**, and the doors are
  _Open game_ (Home laid down, the game pushed over it) and _Later_. Raised by the fill over the
  whole phone, the bar included, on `ModalStage`'s top layer rather than pushed as a route,
  because it answers wherever the player is by then. **A tile** (`YesTile`) is the face the app draws everywhere,
  with two initials over a poster and an outlined empty seat as its two additions; **the spoken
  sentence** is the picture as one header, built from whole nicknames (ADR-0199 §1). Since the mechanics' Q113 (in
  the root glossary, the share is **held** at the fill and taken at the club's **Cut-off**) its
  lines and the
  notices beside it say _held_, never _you paid_, before the cut-off
  ([#642](https://github.com/Raketa02/Raketa/issues/642)). _Avoid_: "the celebration" or "the moment"
  (not terms); showing it to anybody but the player whose yes filled the game — the others are
  told by a notice — and re-showing it, which nothing does.

### The fill

One client-only concept, in `features/proposals/` (#555; the Games & Fill in mechanics §6.5, §11,
§12.2): what happens on the phone around the yes that may fill a game.

- **The fill** — `FillProvider`, mounted by the shell around the tabs for the session, because a
  yes said on the deck or a game's details outlives both. It holds the **Undo window**, the
  **payment setup sheet** a first yes needs, **It's a game!** and the **confirmation** of a refused
  share; the screens reach it through `useFill`. _Avoid_: "the booking flow" (a Booking is the
  backend's aggregate), "checkout".
- **A yes that waits** (`waitsForUndo`) — a yes on _Book it now_ or on any rescue: it books and
  commits money — the share held, or taken after the cut-off (the root glossary's **Fills**) — so
  it waits ten seconds behind **Undo** (the toast _Booking in 10 s · Undo_, a draining ring) and
  is sent at zero; its card stays in the deck's read, **hidden**, so Undo deals it back where it
  was. Every other yes is a free vote, sent at once.
- **A payment to confirm** — this player's share refused (the bank wants them present, or a
  decline): nobody paid, their seat is kept for them alone for the window the server names, and
  confirming it on the phone — on the club's account, the same payment — books it. The window is
  the root glossary's **Time to pay**, or since Q113 its **Time to fix the card**, named by the
  read (`timeTo`: `FIX_THE_CARD` or `PAY`) and drawn by it — _Fix your card by 14:40_ where it would
  say _Confirm your payment by 14:40_
  ([#643](https://github.com/Raketa02/Raketa/issues/643),
  [#645](https://github.com/Raketa02/Raketa/issues/645)). On a rescue the seat is kept for them
  to take: _… to take the seat_. _Avoid_: "retry the payment" (the server never retries it; the
  player confirms it); "pay" for the time to fix the card (nothing is paid in it).

### Home

One client-only concept, in `features/proposals/` since
[#576](https://github.com/Raketa02/Raketa/issues/576): Home is booked games only, so the rail is
that feature's whole, and the old loop's card — its ladder, its slot rows, its doors and its
dismissal — left with `features/plans`. What follows is only what this client had to invent to
draw a player's games ([#556](https://github.com/Raketa02/Raketa/issues/556)).

- **The rail** — `YOUR GAMES · n`, **one card, swipe**: the booked games and the ones waiting
  for a club, on `HomeRail`. A rail rather than a list, because _a game awaiting its club, one
  that is booked and one that needs a result are one thing at three moments of its life_ and a
  rail keeps that by not being a list at all: there is nowhere to put a shelf. The order is
  **the read's, soonest first**, and nothing re-sorts it. _Avoid_: shelves, a re-sort, and
  calling it a list.

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
  assumes being offline makes what is on screen wrong, and a read already held is not — what
  breaks offline is the act. The split is **not** the HTTP verb — a score put up is a `POST`
  that pauses and takes the first sentence, and a yes that books a game is a `POST` that takes
  the second. _Avoid_: "offline error" and "`OfflineBanner`", declined by name in
  `docs/architecture.md` Part 11.
- **No hold state** — the one thing this app must never remember. A held account is a `403` the
  HTTP layer already maps as terminal, re-checked server-side at every request; **there is no
  cached hold flag anywhere**, because a cached flag is the only mechanism by which a hold
  released on one screen could survive on another. Gating a screen at _navigation_ would need
  exactly that cache, and it is refused. _Avoid_: "hold flag", "blocked user state".
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
  imports the module, and a fake in `src/test-support/platform.ts`. Among them
  `LocationPort`, `ImagePickingPort`, `LiveStreamPort`, `HapticsPort`, `ClipboardPort` (#512, for
  Join a group's Paste) and `InstallReferrerPort` (#756) — and each is **the only importer of its module**, the way `shared/lib/auth` is the only importer of the keychain. The reason is
  not tidiness: a native module has no JS underneath it, so a feature that imports one is a
  feature no test can drive — and **the third one is a socket rather than a native module**,
  here on that argument alone, which is why _platform_ and not _native_ is the word. _Avoid_:
  "device module", "native service" — a module holding several capabilities is the utils bucket
  this app bans, and a capability is one file.
- **Phone-preferences store** — `shared/lib/preferences`, the **choices a player made that the
  phone keeps for them**: one key per account per value, the only AsyncStorage importer, and
  **emptied at every sign-out** as a step of `endSession`
  ([ADR-0188](../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)).
  Four values — the **Play segment** since #512, the last sport, the last profile and the booked
  games this phone has opened — and a stale or unreadable one is its default, judged by the
  feature that owns it. **And two flags kept at sign-out**: _the guide on Your rating was shown_,
  per account (ADR-0200 §8, #732), and _the install referrer was read_, the phone's own, under no
  account (#756).
  _Avoid_: "settings", "local storage", "cache" — it holds a choice, never a copy of the server,
  and never a credential.
- **Permission state** — the four answers a platform port gives about a capability:
  `undetermined | granted | denied | blocked`. **Denied and blocked are different
  refusals** — denied can be asked again at the moment the player understands why; blocked
  is settled in the OS settings app and re-asking resolves instantly and negatively, so a
  screen must say so and offer the settings page instead of a control that would prompt. _Avoid_: a boolean, "permission denied" for
  both — collapsing them either re-prompts forever or sends an unasked player to Settings.
- **Location fix** — one position from the device: latitude, longitude, and the accuracy
  the device itself reports, `null` where it reports none. Read **in the foreground, one
  fix at a time, for two uses and no third** — the permission text names both (ADR-0195 §3).
  _Avoid_: "tracking", "background location" — a stream of positions collected
  while the player is elsewhere is a movement trail, a different privacy class from the
  one anybody agreed to, and nothing in this app asks for it. **The area**: a fix is
  **coarsened the moment it is read** — the Location area is what the app keeps, and the
  fix itself does not outlive the function that asked for it. **An attendance tap**
  ([#658](https://github.com/Raketa02/Raketa/issues/658)): when a player says who's at a
  game, one **precise** fix (`readPreciseFix`) is read at that tap and sent with it, so the
  backend can tell whether they are at the club — never coarsened, because 300 m is the
  question, and never kept: it is read inside the write and handed to the request, the
  backend keeps only _at the club_, and neither the phone nor the server stores the
  position. **Read again on a cold start**, and on a return
  from the background when the last read is more than a day old, through the same port and
  with the same accuracy, by `useLocationRefresh` — never merely on foreground, and never
  with a prompt: the refresh checks the permission and asks nobody, so a revoked one leaves
  the stored area where it is
  ([ADR-0174](../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §6).
  The location **step**'s own re-read on foreground is a different thing and stands: the
  player is on the screen that shows the area, and what is on it should be near where they
  are. _Avoid_: a silent read on every foreground — outside that screen a read on every
  return is a movement trail taken one foreground at a time, which is what the day was
  chosen against.
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
  that draws it also draws the word. Its callers were the two list cards, bound to the _Wants to
  play you_ tag; both left with Find a game ([#576](https://github.com/Raketa02/Raketa/issues/576)),
  and `Card`'s `marked` has no caller today.
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
