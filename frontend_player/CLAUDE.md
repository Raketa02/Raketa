# Raketa Player App (iOS + Android)

React Native + Expo + TypeScript. The native app players use to find courts, book slots and
organise matches. It renders with **real platform components** — this is not a website in a
WebView. Feature-first Clean Architecture
([ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)), talking to
FastAPI over HTTPS and generating its wire types from `backend/openapi.player.json`
(the player half of the two-document contract). pnpm.

> The `frontend_player/` app of a three-app monorepo — see the root
> [`CLAUDE.md`](../CLAUDE.md). Run every command from this directory. Never import from
> `../backend/` or `../frontend_club/`; a hook blocks writes there. Shared docs:
> [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

Two contracts predate the code and are **already settled** — read them before writing a
feature, not after:

| Doc                                              | Settles                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| [`docs/architecture.md`](docs/architecture.md)   | Where code lives, who owns which state, how auth/errors/Query/native behave in production. |
| [`docs/design-system.md`](docs/design-system.md) | Every colour, type role, spacing step and interaction rule. **Locked.**                    |

## What exists

`src/app/_layout.tsx` composes the providers and `src/shared/lib/bootstrap` runs the one
ordered startup sequence. Above that: the HTTP client with its 401 → refresh → retry
rotation, the `AppError` family, `shared/lib/auth` over the keychain, and two features —
`auth` (sign up, sign in, session restore) and `onboarding` (the entry gate, welcome, the
sports picker, the adaptive question loop, the explained result, and the summary and data
screens a player leaves through).

`features/now/` is **Now, the app's home** — the screen `(app)/(tabs)/index` renders and the
one onboarding lands on. Three regions (offers · the enrolled strip · the shelves), the sport
bar, `ADR-0054`'s four asks, the match card's **action row**, and the shelves' **fit badge,
reasons, emphasis and tail card**.

`features/departure/` is **the route the card's exit opens** — what leaving a match is worth
right now, and the one control that takes it.

**A chip for a sport she holds no rating at draws a door, and the door is a route**
([ADR-0084](../docs/adr/0084-the-sport-bar-is-five-fixed-chips-and-an-unrated-sport-is-a-door.md)).
The block arrives **in the shelves list, in order** — where the ranked shelves would be, with
_New on Raketa_ and _New clubs_ beneath it — and the phone never concludes one from shelves
that are missing, because that inference is wrong on any day the city genuinely has nothing in
a sport she _is_ rated at. Its two codes differ in their **words and in nothing else**: the tap
is `/rate/[sport]`, one `POST /assessments`, which is idempotent per player and sport and hands
back a parked run's outstanding question — so **Now imports nothing from onboarding**, and no
rule about resuming lives on the phone. `entryDestination` no longer resumes a run for a player
who already holds a rating: it **parks**, and the door is the way back into it, however old.
A walk begun at the door carries `origin: 'door'` and ends **back on Now filtered to that
sport**, passing neither closing screen — never derived from _does she already hold a rating_,
which is true of every ordinary two-sport walk by its second result screen.

**`(app)/(tabs)/` is a real tab navigator now, with five destinations**
([ADR-0082](../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md)):
Now · Find · create · Inbox · You. `shared/ui/TabBar` draws it — five Feather glyphs at
`size.tabIcon`, a flat coral circle for create, an `ink` numeral on the Inbox pill — and holds
**no navigation**: it takes the active key and hands back the pressed one, so
`(app)/(tabs)/_layout.tsx` is the only file that knows a tab key is a route. Three of the five
are placeholder route files that their own feature deletes; `account` is reachable at last.
**Selection is coral alone and knowingly fails WCAG 1.4.1** — sighted-only, remedy priced in
the ADR (a 3pt coral dot under the selected label). Do not add a _different_ second cue without
amending it. **The bar spends the bottom safe-area inset**, so every screen under `(tabs)` takes
`edges={['top']}` — a screen claiming `bottom` too puts a band of dead paper above the bar.

**Leaving a match is a route, and the screen is the confirmation**
([ADR-0086](../docs/adr/0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)).
The exit on a card pushes `/matches/[matchId]/departure`, which states the live **quote**, its
three reasons — the commitment deadline, her seat's amount, how full the match is — and **all
four outcomes** with a server-composed marker on each. One primary button carrying the quote
and **no third step**: a dialog over a screen whose whole job is to state the consequence asks
the same question twice. **A refusal is not a second shape**: all five ways the act can stop
applying come back as what a success returns, and `applied` — not `mayDepart` still being true
— is what tells the two apart. Past the point of departure the button is **absent rather than
refusing**, with no sentence in its place: the situation line already says why.

**An action off Now writes Now's update; it never invalidates it**
([ADR-0074](../docs/adr/0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md)).
The write's answer carries the one card that changed **in one of two forms**, and
`writeNowUpdate` applies it across every sport's cached screen — nothing added, no region
reordered, and the shelves never touched at all. The second form is _this card is gone_
([ADR-0091](../docs/adr/0091-a-queue-place-is-a-card-and-leaving-one-is-the-first-card-that-goes.md)):
leaving standby removes a card, because a queue place is the whole of what put that match on
the strip. It is the **one** operation here that shortens a region, the surviving cards keep
the order they arrived in, and the two forms are told apart by the wire's own discriminator —
never by a card being absent, which would read an old server's answer as _gone_. Popping back off a route is deliberately none
of the four asks, so without this the player would return from leaving a match to a card still
offering her the way out. The **leaver's own line** is the audience made visible: it sits
beside the match's situation and never instead of it, because a refill is the only thing that
decides her money, and a player who paid nothing sees a sentence naming **no amount** rather
than a blank.

**A shelf card carries the fit badge, its reasons, and no button**
([ADR-0037](../docs/adr/0037-the-fit-badge-shouts-once-and-only-about-a-seat.md),
[ADR-0088](../docs/adr/0088-the-action-row-is-three-slots-and-the-clock-takes-the-first.md)).
The badge's score is **clamped 20–99 in the mapper**, so the engine's true 0–100 value never
enters the app; up to **three reasons** stand under it, resolved from a term code and a typed
payload into this app's own sentence, and an **unsure** estimate becomes a warning line rather
than a percentage. **Coverage is never shown in any form** — a type-level assertion in
`nowMappers.ts` fails the build the day it crosses the wire. **Emphasis is the server's flag**:
its three gates are all about the _other_ cards, so the phone reads it and never computes it,
and the walk bans comparing a score against anything. A shelf card's **body** is the control,
exactly when it names an act, and its **clock is a claim's clock and nothing else** — the
server sends the match's own boundary there anyway ([#114](https://github.com/Raketa02/Raketa/issues/114))
and the card ignores it. Every shelf ends in a **tail card** the client appends from the shelf
code plus the held sport; Find cannot yet receive that pre-filter
([#115](https://github.com/Raketa02/Raketa/issues/115)).

**The action row is one row of three optional slots and has zero variants**
([ADR-0088](../docs/adr/0088-the-action-row-is-three-slots-and-the-clock-takes-the-first.md)):
a clock, an act, an exit — each drawn exactly when its own spine field is present, the act the
only flexible element, and the **empty row still rendered** as a zero-height spacer so
`marginTop: auto` has something to push. A **live seat claim wins the card**: the claim's five
minutes take the clock slot and `finishPaying` takes the act. `ADR-0088` is also where the
distinction between a **repaint** and an **ask** is stated — the countdown redraws every second
inside ten minutes and every minute above, from **one screen-wide clock**, and that is drawing
rather than a fifth occasion to fetch.

**Eight rules on that feature are walked over its own source** in
`components/nowDiscipline.test.ts`, because each is a rule about what the code does _not_ do
and no green assertion can carry one. **The phone holds no rules** ([ADR-0053](../docs/adr/0053-the-phone-holds-no-rules-and-only-subtracts.md)):
`Date.parse` appears in `domain/countdown.ts` and nowhere else, so the only derivation is
subtracting a card's moment from now. **Nothing refreshes on a timer**
([ADR-0054](../docs/adr/0054-now-refreshes-when-asked-never-on-a-timer.md)): no interval, no
`refetchInterval`, and **two** `setTimeout`s — the wake at a moment the _server_ named, and the
repaint clock — with the walk asserting that the repaint module cannot reach Query at all.
**Neither of the prototype's two action-row icons comes back** (`✉`, `⌘`). **The screen never
admits staleness**: no marker, no banner, no _"can't reach Raketa"_. **The door is never
inferred**: a door is _constructed_ in `mappers/nowMappers.ts` and nowhere else, and its copy
table is read only where a code is resolved — so a component cannot decide to draw one.
**Order is the composed screen's** ([ADR-0032](../docs/adr/0032-order-is-a-property-of-the-composed-screen.md)):
nothing sorts, and a **shelf** is constructed in that same one module — so an action's update
cannot grow one, and a match she joined cannot move under her thumb. **Emphasis is never
computed**: no module compares a score against anything. **An update is narrowed on what the
wire says it is**: `toNowUpdate` switches on `update_type`, never on a missing card, and both
forms are constructed in that one module — so a component cannot decide a card has gone. Each
guard carries a negative control; do not add an exemption to a walk, **narrow the rule
instead** — which is what the second one did when the repaint clock landed.

**The departure feature is walked too**, in `components/departureDiscipline.test.ts`, and its
four rules are the ones that could only go wrong there. **Nothing mentions transferring a
seat** — it is the leaver's best outcome and it belongs to a flow that does not exist, so a
rendered test can only prove today's screen is silent while the walk proves the words are not
in the build. **No second `Date.parse`**: this screen subtracts through Now's `countdown` or
it does not subtract, or the same deadline would eventually read two ways on two screens.
**No second situation table**: the wire embeds the match's spine and situation half verbatim,
so both screens read one table. **The write is never retried on the app's own initiative** —
the request key makes a retry _she_ makes safe, and is not a licence to make one for her.

It also holds the section's **vocabulary**: six copy tables (36 situations · 10 term codes ·
5 hold reasons · 7 acts · 2 door codes · a leaver's line over 4 outcomes), the shelf-code →
Find pre-filter map and the caption codes, all keyed
on unions generated from `openapi.player.json`. **Completeness is a typecheck, not a test**
([ADR-0075](../docs/adr/0075-the-second-table-is-unpaid-and-the-first-ships-in-english.md)): a
contract value added without its sentence fails `pnpm typecheck`. That only holds while the key
is a closed union — a code crossing as a bare `string` turns the `Record` into an index
signature that never fires — so each table carries an `AssertTrue<IsClosedUnion<…>>` pin, and
`copyTables.test.ts` writes the enumeration out so that _growth_ is a decision somebody makes in
a diff. The three guards catch three different edits; do not collapse them.

**The tables live in `mappers/`.** They key on `@/generated`, which only `api/` and `mappers/`
may read, and mapping a wire code to a value object `domain/` owns is what a mapper is. The half
of each entry the wire has no opinion about — tone, tag, the act's surface — is in
`domain/presentation.ts`. **The mapper resolves a code to its copy**, so a component never
holds a table and never sees a wire union.

**How a value becomes a string is `shared/lib/formatting/`,** implementing the repo-wide
[`docs/value-formatting.md`](../docs/value-formatting.md) so that `38,00 zł` is the same
characters here and in the club console. Neither `Intl.NumberFormat` nor `toFixed` — both are
refusals that file states, with reasons.

`src/shared/ui/` holds the design-system primitives built so far — the cards, note, row,
hairline, button, tag, bar, header, and the overlays and drawn objects the result screen
needed (bottom sheet, popover, level bar, confidence ring); the rest arrive with the
features that need them. **Build outward from the structure below** rather than reaching
for `create-expo-app` — its default template contradicts ADR-0009 — and copy the shape of
`src/features/auth/` or `src/features/onboarding/` rather than inventing a second one.

**Copy `.env.example` → `.env.local` before the first run.** `EXPO_PUBLIC_API_URL` and
`EXPO_PUBLIC_ENV` are both required and validated once at launch by
`src/shared/config/env.ts`. A missing or malformed value stops the app on a startup screen
naming it — that is the guardrail working, not a bug.

`EXPO_PUBLIC_ENV` is `local | development | staging | production`, the same four the
backend and the club app use, and **only `local` runs today.** The environment fixes the
API URL's scheme — `https://` for the three deployed ones, either for `local` — so a
laptop URL under a deployed name fails at launch naming both variables rather than
shipping a build that points at nothing.

**`app.config.ts` is a function of that environment**, not a static document — it replaced
`app.json`. It holds no logic of its own: `src/shared/config/appIdentity.ts` is a pure
table mapping each environment to the app's display name and its badge, and the config
document calls it. Outside `production` the app is named for its environment and wears an
amber badge over every screen; `production` is bare and unbadged. There is **one**
installable variant — one bundle identifier, one URL scheme, no build profiles — until a
second backend exists to point a second one at.

Expo evaluates that document in **Node**, before Metro, so it reads `process.env`
directly and refuses an unknown environment rather than defaulting to one. It registers
sucrase's TS require hook first, because Node cannot otherwise `require` the `.ts`
identity module — delete that line and `npx expo start` fails on a missing module.

**Dependency versions target Expo SDK 52.** Expo pins React Native and its own packages
tightly, so after changing dependencies run `npx expo install --check` and trust Expo's
resolution over the pins in `package.json`. That pin is why `eslint.config.mjs` reaches
`eslint-config-expo` through `FlatCompat`: its flat config ships from v9, which belongs to
SDK 53.

**`.npmrc` sets `node-linker=hoisted`.** Metro and jest-expo decide what still needs
transforming with `node_modules/(?!…)` allowlists, and pnpm's default symlinked layout
defeats them — React Native ships untranspiled Flow, so the first casualty is `jest`
failing to parse `error-guard.js`. Hoisting is Expo's documented answer; it changes nothing
architectural, and this app still shares no packages with `frontend_club`.

Archivo (400–800) and IBM Plex Mono (400–600) are loaded with `expo-font` and **awaited
before the splash screen hides** — a font that arrives late reflows every number on screen.
They are imported **file by file**: each `@expo-google-fonts` index `require`s every weight
and italic it ships, and Metro does not tree-shake, so importing one name costs 4,2 MB
instead of 1,0 MB.

## Commands

```bash
pnpm start        # Expo dev server (press i / a for simulator)
pnpm ios / android
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Jest (jest-expo)
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.player.json
pnpm doctor       # npx expo-doctor — checks dependency/SDK agreement
pnpm check        # lint + format check + typecheck + test — the local gate
```

**You cannot see the screen.** If a change is visual, say so and ask for a look rather than
asserting it renders correctly.

## Safety — never without an explicit request

- **Store credentials anywhere but the OS keychain.** Tokens live in `expo-secure-store`,
  reached only through `src/shared/lib/auth`. **Never** `AsyncStorage` (unencrypted
  plaintext on device), never a module variable that outlives a session, never a log line.
  _(ESLint blocks the AsyncStorage import.)_
- **Put a secret in `app.config.ts` `extra`, or in any `EXPO_PUBLIC_*` variable.** Everything in
  the bundle is readable from a shipped app. Those are **config**, not secrets. A secret a
  mobile client "needs" is a design error — it belongs behind the backend.
- **Run a build or release** (`eas build|submit|update`, `expo publish`). _(hook-enforced)_
- **Create or edit a real `.env*` file.** Edit `.env.example`. _(hook-enforced)_
- **Import from `src/generated/` outside a feature's `api/` or `mappers/` layer.**
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put business rules in screens or hooks.** Rules live in `domain/` + `use-cases/`.
- **Call `fetch` outside `src/shared/lib/http`,** or add a second networking path.
- **Copy server data into Zustand.** TanStack Query owns every backend-derived value.
- **Retry a mutation** unless the endpoint is idempotent, takes an idempotency key, or is
  explicitly safe to repeat. Booking and payment calls are exactly where a silent retry
  charges someone twice.
- **Trust a deep-link, push or route param.** Validate with Zod before use.
- **Write a literal colour, font size, spacing or radius in a component.** Every value comes
  from `src/shared/ui/theme.ts`.
- **Add a dependency that owns styling** — NativeWind, styled-components, Unistyles,
  Restyle, a component kit. The system is a typed theme + `StyleSheet.create`
  ([ADR-0012](../docs/adr/0012-player-app-design-system.md)).
- **Commit `android/` or `ios/`.** They are `expo prebuild` output, not source.

## Architecture

Full contract: [`docs/architecture.md`](docs/architecture.md). **Every feature carries the
full layer set**, so an agent applies one rule rather than judging per feature.

```
src/
  app/                      expo-router screens (thin). File-based routing.
    _layout.tsx             root providers + the bootstrap gate
    (public)/ (auth)/ (app)/(tabs)/
  features/<feature>/
    domain/                 entities + value objects + rules (pure TS, no RN/fetch)
    use-cases/              one fn per workflow; orchestrates domain + ports
    api/                    calls FastAPI directly; speaks wire types
    mappers/                wire DTO <-> domain object
    schemas/  components/  hooks/  store/ (optional)
    types.ts                the feature's public surface
  shared/
    ui/                     theme.ts (THE source of every value) + primitives
    lib/  http/ auth/ query-client/ bootstrap/ platform/ observability/
    config/ errors/ store/
  generated/                openapi-typescript output — raw wire types ONLY
```

The per-layer contract is in [`src/features/_template/README.md`](src/features/_template/README.md).
Copy that folder to start a feature.

Rules to preserve:

- **Dependencies point inward:** `app/ → components/ → hooks/ → use-cases/ → domain/`.
  `domain/` imports nothing from React Native, Expo, `fetch` or `generated/`.
- **The wire boundary is `api/` + `mappers/`.** ESLint enforces it.
- **`src/shared/lib/auth` is the single chokepoint for credentials.** No feature, screen or
  hook imports `expo-secure-store`. One module owning the keychain is what makes token
  lifetime auditable.
- **`src/shared/lib/http` is the only place `fetch` is configured** — and the only place the
  401 → refresh → retry rotation lives.
- **`shared/` never imports a feature,** and a feature never deep-imports another — go
  through its `types.ts`. But **do not move code to `shared/` because two files use it**;
  keep it local until cross-feature ownership is proven.
- **No global `services/`, `utils/`, `types/` or `hooks/` bucket.** A capability is one
  directory; utilities get semantic homes (`formatting/`, `date/`, `currency/`).
- **Uniform-strict escape hatch:** where a feature genuinely has no business rule, its
  `use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the folders
  for predictability, but **do not invent fake invariants to fill them.**

### One owner per kind of state

| State                     | Owner                                                                |
| ------------------------- | -------------------------------------------------------------------- |
| Anything from the backend | **TanStack Query** — never mirrored into a store                     |
| Access + refresh tokens   | `shared/lib/auth` → `expo-secure-store` (+ in-memory mirror)         |
| Logged-in / out           | `SessionStatus`: `bootstrapping \| authenticated \| unauthenticated` |
| Local component state     | `useState` / `useReducer`                                            |
| Shared ephemeral UI state | Zustand, **feature-scoped first**                                    |
| Form input                | The form + one Zod schema                                            |
| Navigation                | expo-router — a route param is not app state                         |
| Config                    | `shared/config/env.ts`, Zod-validated at startup                     |

Reach for Zustand last: component-local → feature store → app-wide store, and only with a
reason. Zustand never holds API entities, tokens, a backend cache, or a global loading flag.

### Session, bootstrap and routing

Model bootstrap as a **state**, never as `user === undefined` — that ambiguity is what
produces a login-screen flash while valid credentials are still being read out of the
keychain, and an authenticated-tree flash before a redirect.

`shared/lib/bootstrap` runs one ordered sequence: error reporting → validate config → wire
focus/online managers → read SecureStore → restore/validate session → hide splash → render.
Nothing renders a route tree before it resolves.

Expo Router's declarative protected routes landed **after SDK 52**, so the guard is a
redirect in `(app)/_layout.tsx` keyed on `SessionStatus`. Route groups exist so the
authorization boundary is visible in the file tree.

iOS Keychain data can survive a reinstall, so **a token existing is not proof a session
exists** — bootstrap validates it.

### Why there is no BFF here

The club app routes everything through a server-side BFF with httpOnly cookies. This app
does not, and that is deliberate: a native app has no cookie jar and no shared-origin
browser context, so the equivalent protection is the **OS keychain**
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry by adding a proxy, and don't copy the club app's cookie code here.

## Mobile gotchas that bite once

- **`localhost` on a device is the device.** A physical phone needs a LAN IP or tunnel in
  `EXPO_PUBLIC_API_URL`.
- **Old app versions live on real phones for months.** Treat backend contract changes as
  breaking unless additive — you cannot force everyone to update.
- **`fetch` has no default timeout.** Timeouts are centralized in `shared/lib/http` as
  classes (request/upload/download/background) — no millisecond literal in a feature.
- **`android/` and `ios/` are `expo prebuild` output.** Native config goes through
  `app.config.ts` and config plugins; a hand edit is lost on the next prebuild.
- **Never log a token, an `Authorization` header, a password or a full payload.**

## Git & domain language

Conventional Commits scoped `player`: `feat(player): court search filters`. Run `pnpm check`
before pushing. **Contract drift fails the build:** this app's CI job regenerates from
`backend/openapi.player.json` with the `openapi-typescript` its own lockfile pins, and diffs
— commit the regenerated `src/generated/`. It is **not** part of `pnpm check`, so a local
gate can be green while CI is not. The job also runs on a backend-only pull request, because
its paths filter watches that document alongside `frontend_player/**`. Before opening a
PR, walk the Definition of Done in
[`docs/architecture.md` Part 20](docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).

Player-app technical vocabulary: [`CONTEXT.md`](CONTEXT.md). New domain concepts use the
shared glossary's vocabulary ([`../CONTEXT.md`](../CONTEXT.md)) — a `Court` is a `Court`, not
a Venue or Facility.
