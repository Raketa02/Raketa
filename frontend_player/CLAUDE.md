# Raketa Player App (iOS + Android)

React Native + Expo + TypeScript. The native app players use to find courts, book slots and
organise matches. It renders with **real platform components** — this is not a website in a
WebView. Feature-first Clean Architecture
([ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)), talking to
FastAPI over HTTPS and generating its wire types from `backend/openapi.player.json`
(the player half of the two-document contract). pnpm.

> The `frontend_player/` app of a three-app monorepo — see the root
> [`CLAUDE.md`](../CLAUDE.md). Run every command from this directory. Never import from
> `../backend/`; a hook blocks writes outside this app. Shared docs:
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
rotation, the `AppError` family, `shared/lib/auth` over the keychain, and three features —
`auth` (sign up — including the **adult attestation**, the one question on that form that is
not about the account — sign in, session restore), `onboarding` (the entry gate, welcome, the
sports picker, the adaptive question loop, the explained result, and the summary and data
screens a player leaves through) and `player_profile` (onboarding's **second part**, complete: six
steps over a client-held draft, and the one write that ends them — the Social tags picker,
2 to 6 chips from a served vocabulary, the photos step, up to three court photos or none,
the availability grid, seven days by three parts of the day, blank on arrival and requiring
one ticked cell of the twenty-one before it continues
([ADR-0102](../docs/adr/0102-silence-is-never-scored.md)), the location step, one foreground fix coarsened to about a kilometre before it is
held, the radius step, a slider over the served bounds that opens at the served default, the
Proposals opt-in, never pre-ticked and with a finish that stays closed until the player
answers either way, and the **profile commit**: every answer in one idempotent
`POST /players/me/profile`, after which the player walks the data screen into the app).

**Sign-up asks whether the player is an adult, and it is an attestation.** The platform is
adults only, and that is a precondition of _holding an account_ rather than a rule about who
is shown to whom ([ADR-0124](../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
What the form collects is **one boolean — never a date of birth**, and it is **not age
verification**: there is no date picker anywhere in this app and this is not where the first
one arrives. The box is never pre-ticked, _Create account_ is never disabled by it, and the
refusal is a sentence under the box rather than a closed control
([ADR-0089](../docs/adr/0089-player-profile-context-event-sourced.md)). The same sentence
renders when the server refuses by `adult_attestation_required` — an older build or a
replayed request can carry a body this form would not have sent, and _try again_ would then
be the one thing that is not true.

**Onboarding is two parts, and the part is the checkpoint unit**
([ADR-0090](../docs/adr/0090-onboarding-per-player-checkpoint.md)). Part one is the Skill
rating and resumes mid-run; part two writes nothing until one commit at the end, so leaving
it restarts at step one. The entry gate reads three facts and has four destinations — resume
· welcome · the social steps · the app — and the second part's screens live in
`player_profile/` rather than in `onboarding/` because the profile screen will later edit the
same values against the same rules
([ADR-0089](../docs/adr/0089-player-profile-context-event-sourced.md)).

**The consent step's copy is frozen and versioned.** `optInPresentation.ts` owns every
sentence the Proposals opt-in card shows, together with the `copy_version` stamped beside
the answer in the draft — consent gathered against one sentence is not consent to a
different one, so re-wording that card is a **new version with the old one retained**,
never an edit. It is the only file in this app whose strings are evidence. It stands at
**`proposals-opt-in.v2`**, which dropped the line under the title; `v1` is retired and kept
in the same file, because a version identifier with no record of what it named evidences
nothing.

**The ratings summary ends the first part, and it is the door into the second.** The order
is result → **done** → the six steps → the commit → data → the app. The _pass_ routes as far
as the summary and no further (`nextDestination`: _is there anything to account for_), and
the **done screen** reads whether a Player profile is still owed and either enters the second
part or continues to the data screen — one fact, read once, on the screen that acts on it. A
player who is already set up — one resuming a run they left behind — passes straight through.
The summary comes before the six steps rather than after the commit, because it is what a
player just earned and the second part was otherwise standing between them and it; a Skill
rating is written when the questionnaire completes, not when a profile is committed, so
nothing on that screen was ever waiting on the commit to be true. Entered with no pass
running, it has nothing of its own to show and says so.

**The commit is the one mutation in this app a retry may repeat.** Its **commit key** is
minted when the part is entered and lives exactly as long as the draft, so a double tap and a
retry after a failure both carry the key the first attempt carried — the disabled control is
the courtesy, the key is the defence. `Idempotency-Key` is set by `shared/lib/http` for any
request that names one, including the replay a 401 rotation makes. A failed commit keeps the
draft, keeps the player on the step, offers the control that failed as the retry, and claims
nothing. `commitStanding` and `mayFinish` own when the finish opens — a rule, not a
`disabled={…}` expression — and `readyToCommit` under them is what makes a partial commit
unrepresentable. Three things hold the finish shut. **No Location area**: location is a core
requirement for discovery, `CommitPlayerProfileRequest` requires it, and the last step asks
once more with the way back one press away rather than trapping a player on step four behind
an OS prompt. **A blank availability grid**: the week has a floor of one cell since
ADR-0102, so silence about when somebody plays is asked for rather than scored as a zero —
step three already refuses to continue on one, and this is the same rule read at the end.
**A photo still going up**: uploads outlive the step that started them, and the
body names photos by the ids the server gave back, so committing mid-upload would silently
drop a picture the player watched arrive. That one asks for nothing and opens itself.

A failed commit whose `code` names an answer — `availability_grid_empty` today — is drawn as
that answer rather than as _try again_, with the control back to the step that takes it: the
commit re-validates every rule a picker enforced, and re-sending the identical body would
fail identically.

`src/shared/lib/platform/` owns everything the app knows about the device: the Query
focus and online wirings, and two **platform ports** — `LocationPort` over `expo-location`
and `ImagePickingPort` over `expo-image-picker`. Each is the only importer of its native
module, for the reason `shared/lib/auth` is the only importer of the keychain, plus one
more: a native module has no JS implementation underneath it, so a feature that imports
one cannot be tested at all. Hand-written fakes live in `src/test-support/platform.ts`, and
a screen reaches either through `useLocation()` / `useImagePicking()` — contexts whose
default is the device, so only a test ever supplies anything else. Beside them sit the two
lifecycle wirings and `useOnForeground`, the app's one answer to _did we just come back_.
**Location is foreground only** — nothing asks for, checks or starts a background one — and
a fix is **coarsened to about a kilometre the moment it is read**, so the precise reading
never reaches a store, a screen or a crash report.

`shared/lib/http` has **two verbs**: `httpRequest` for JSON and `httpUpload` for one file.
They share the correlation id, the `Authorization` header, the timeout policy, the error
mapping and the single-flight 401 rotation — a second copy of any of those is the second
networking path the module exists to prevent. `httpUpload` also reads the local `file://`
URI a picker hands back, because `fetch` is what this module is allowed to touch, and it
reports **stages rather than bytes**: React Native's `fetch` cannot say how much of a body
has gone out, and buying that would mean a second transport.

`src/shared/ui/` holds the design-system primitives built so far — the cards, note, row,
hairline, button, tag, chip, bar, header, the overlays and drawn objects the result screen
needed (bottom sheet, popover, level bar, confidence ring), the photo tile with its
generated court poster, the availability grid and the radius slider, and the tick box with
the tick both it and the grid draw; the rest arrive with the features that need them. **Build outward from the structure below** rather than reaching
for `create-expo-app` — its default template contradicts ADR-0009 — and copy the shape of
`src/features/auth/` or `src/features/onboarding/` rather than inventing a second one.

**Copy `.env.example` → `.env.local` before the first run.** `EXPO_PUBLIC_API_URL` and
`EXPO_PUBLIC_ENV` are both required and validated once at launch by
`src/shared/config/env.ts`. A missing or malformed value stops the app on a startup screen
naming it — that is the guardrail working, not a bug.

`EXPO_PUBLIC_ENV` is `local | development | staging | production`, the same four the
backend uses, and **only `local` runs today.** The environment fixes the
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
architectural, and this app shares no packages with any other app — a rule that outlives
the club console it was written against.

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
pnpm test:boundaries   # drive ESLint at code breaking each module ban; it must go red
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.player.json
pnpm doctor       # npx expo-doctor — checks dependency/SDK agreement
pnpm check        # lint + format + typecheck + test + boundaries — the local gate
```

**You cannot see the screen.** If a change is visual, say so and ask for a look rather than
asserting it renders correctly.

## Safety — never without an explicit request

- **Ask for a background location.** Foreground only, permanently: a stream of positions
  collected while the player is elsewhere is a movement trail, which is not what anybody
  agreed to. `app.config.ts` disables it on both platforms and two tests assert the
  absence.
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
- **Each platform port is the single chokepoint for its native capability.** Only
  `platform/location.ts` may import `expo-location` and only `platform/imagePicking.ts`
  may import `expo-image-picker` — one file each, not the platform directory, so a module
  of ports cannot become a device bucket. Nothing else: not a feature, not a screen, not a
  test. Depend on `LocationPort` / `ImagePickingPort` and drive the fakes in
  `src/test-support/platform.ts`. ESLint enforces it and `pnpm test:boundaries` proves the
  rule still fires.
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

A browser client would route everything through a server-side BFF with httpOnly cookies —
the club console did, before it was removed in the 2026-08-25 reset. This app
does not, and that is deliberate: a native app has no cookie jar and no shared-origin
browser context, so the equivalent protection is the **OS keychain**
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry by adding a proxy, and don't reach for a cookie session here.

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
