# Raketa — Player app (iOS + Android)

The native app players use to find courts, book slots and organise matches.
React Native + Expo + TypeScript, rendering with real platform components — not a
website in a WebView.

One of three independently deployable apps in this monorepo — see the root
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md).

## First run

```bash
cd frontend_player
pnpm install
cp .env.example .env.local   # both values are required — see Environment below
npx expo-doctor              # verifies the dependency versions agree with the SDK
pnpm start                   # then press i (iOS sim) / a (Android emulator)
```

The app boots to a placeholder screen. `src/app/_layout.tsx` composes the root providers
and gates the splash screen on the **bootstrap sequence** — the ordered startup path in
[`docs/architecture.md` Part 3](docs/architecture.md#part-3--bootstrap-and-the-session-state-machine),
implemented in `src/shared/lib/bootstrap/`. It validates config, then loads Archivo and
IBM Plex Mono with `expo-font` and awaits them before the splash hides. Routing, sessions
and features arrive in later slices; build them outward from the folder contract in
[`src/features/_template/README.md`](src/features/_template/README.md). The design system
is already locked — see below.

`.npmrc` pins pnpm to `node-linker=hoisted`, because Metro and jest-expo resolve what to
transform through `node_modules/(?!…)` allowlists that pnpm's symlinked layout defeats.

> Deliberately **not** scaffolded with `create-expo-app`: its default template
> contradicts the feature-first structure recorded in
> [ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md).
>
> The dependency versions in `package.json` target **Expo SDK 52**. Expo pins RN and
> its own packages tightly, so run `npx expo install --check` after the first install
> and let Expo correct anything that drifted — trust its resolution over the pins here.

## Commands

```bash
pnpm start        # Expo dev server
pnpm ios          # build & run on the iOS simulator
pnpm android      # build & run on an Android emulator
pnpm lint         # ESLint (also enforces the import boundaries)
pnpm typecheck    # tsc --noEmit, strict
pnpm test         # Jest (jest-expo)
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm check        # lint + format check + typecheck + test — the local gate
```

## Environment

Copy `.env.example` → `.env.local`. `EXPO_PUBLIC_API_URL` and `EXPO_PUBLIC_ENV` are both
**required**: `src/shared/config/env.ts` validates them once at launch and the app stops
on a startup screen naming whichever is missing or malformed, rather than failing later
inside a feature. On a **physical device**, `EXPO_PUBLIC_API_URL` must be a LAN IP or
tunnel — `localhost` on a phone means the phone.

`EXPO_PUBLIC_ENV` is one of `local`, `development`, `staging`, `production` — the same
four names the backend and the club app use. **Only `local` runs today**; the other three
are validated but not provisioned. The environment decides the URL scheme, and that is
validated too: the three deployed ones must be `https://`, because this URL is reached
from a phone over the internet. `local` takes either — a tunnel is how a physical device
reaches a laptop, and every tunnel hands back `https://`. A laptop URL under a deployed
name is a startup failure naming both variables. See [`../docs/environments.md`](../docs/environments.md).

The environment also decides what the app calls itself. `app.config.ts` is a **function**
of it — not a static `app.json` — and delegates the one decision to
`src/shared/config/appIdentity.ts`: outside `production` the app is named for its
environment (`Raketa local`) and wears an amber badge over every screen; `production` is
`Raketa`, unbadged. There is one installable variant — one bundle identifier, one URL
scheme — so today all four resolve to the same app pointed at the same laptop. That is
the point: the machinery is exercised in the only environment that runs, so it will not
be wrong the first time it matters.

Every `EXPO_PUBLIC_*` value ships inside the bundle and is readable from a released
app. Config only, never secrets.

## Architecture in one paragraph

Screens live in `src/app/` (expo-router, file-based, route groups `(public)` `(auth)`
`(app)`). Each user-facing capability is a vertical slice in `src/features/<name>/` with
the full layer set (`domain/ use-cases/ api/ mappers/ schemas/ components/ hooks/`),
dependencies pointing inward. Cross-cutting infrastructure — the HTTP client, auth, the
Query client, bootstrap, platform adapters, observability — lives in `src/shared/lib/`.
The `api/` layer calls FastAPI **directly** — there is no BFF, because a native app has
no cookie jar; tokens live in the OS keychain via `expo-secure-store`, reached only
through `src/shared/lib/auth`. TanStack Query owns every backend-derived value; Zustand
owns UI state only.

The full contract — state ownership, the session state machine, single-flight token
refresh, the error taxonomy, Query defaults, native and delivery policy — is
[`docs/architecture.md`](docs/architecture.md), recorded as
[ADR-0013](../docs/adr/0013-player-app-runtime-architecture.md). **Read it before writing
a feature.**

## The home screen

`/` is **Now**: offers, the matches you are in, and five shelves of suggestions, under a
five-chip sport bar. It is a status surface before a search box, and it is the first
screen after onboarding.

It refreshes on **four occasions and no others** — the app coming to the foreground, a
pull, an action, and a countdown reaching zero
([ADR-0054](../docs/adr/0054-now-refreshes-when-asked-never-on-a-timer.md)). There is no
interval in this app. The phone derives one thing: how long is left until a moment the
server named ([ADR-0053](../docs/adr/0053-the-phone-holds-no-rules-and-only-subtracts.md)).
Those rules are walked over the feature's own source, because each is a rule about what the
code does _not_ do.

A match card ends in **one action row of three optional slots** — a countdown, the card's
one act, and the exit — with no variants between them
([ADR-0088](../docs/adr/0088-the-action-row-is-three-slots-and-the-clock-takes-the-first.md)).
Twenty-six of the thirty-six situations name no act at all, so most cards end in an empty
row, and that is the honest shape of a v1 with no match-detail screen rather than an
oversight. The countdown **repaints** every second inside ten minutes and every minute
above, from one screen-wide clock; repainting is drawing and is never a fifth occasion to
fetch.

A suggestion carries a **fit badge** — `✦ 93`, dark, and coral on at most **one card on the
whole screen** ([ADR-0037](../docs/adr/0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)).
The number is always printed and always between 20 and 99: below 20 every score means _no_,
and nothing reaches 100 because certainty is never warranted. Up to three lines under it say
_why this one_, in this app's words rather than the server's, and where a confidence
percentage would go there is **a warning instead** — the app says _early days for this match_
rather than printing a second number nobody can act on. Which card shouts is the **server's**
decision, because it depends on the other cards; the phone never compares a score against
anything.

Every shelf **ends in a card into Find**, carrying that shelf's own claim and the sport you
are filtered to, so a row running out is a door and not a wall. A shelf card has no button:
where it has something to offer, the whole card is the control, and where it has not, it is
inert rather than a control that swallows a press.

Tapping a chip for a sport you have no level at does not answer _nothing open in Squash_. It
opens a **door**: the honest sentence, a way into that sport's questionnaire, and the new
clubs and new players beneath it, so you can see there is squash here before spending two
minutes ([ADR-0084](../docs/adr/0084-the-sport-bar-is-five-fixed-chips-and-an-unrated-sport-is-a-door.md)).
Finishing lands you back on Now, filtered to the sport you just took up. A questionnaire left
half-answered **parks** rather than taking the screen at launch — it will never stand between
you and the match you have paid for — and the door picks it up where you left it, however long
ago that was.

## Racing for a seat

A seat that frees is offered to everybody it fits at once, and the card says so: **a seat
just opened — first to take it**. Nothing on it claims the seat is reserved, because nothing
holds it ([ADR-0061](../docs/adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md)).
The offers sit at the very top of Now, above the matches you are in: the thing with a clock
is first.

Taking one is a single tap and no dialog. What comes back is the card itself: if you were
fastest it now counts down **five minutes to pay** and its button says _finish paying_, and
the match has moved out of the offers and into your own matches
([ADR-0081](../docs/adr/0081-a-seat-is-never-taken-until-it-is-paid.md)). While that payment
is running there is **no exit control** — abandoning a payment is not the same thing as
leaving a match, and it is not dressed as one.

**If somebody was faster you find out from the screen rather than from an error.** The card
you tapped redraws in place, saying what the match is actually doing and offering nothing,
and one plain line appears at the top of Now — _that seat has gone_ — which fades on its own
([ADR-0062](../docs/adr/0062-a-notification-is-a-prompt-to-look-not-a-record.md)). No dialog,
no toast, and no card left saying _first to take it_ an hour after it was taken.

**Turning notifications down costs you the message and never the card.** The offers are on
this screen whether or not your phone ever buzzed.

## Leaving standby

Asking to be told when a seat frees on a match costs nothing, and getting off that queue
costs nothing either — so it is **one tap and no confirmation**
([ADR-0087](../docs/adr/0087-leaving-standby-is-the-seventh-act.md)). There is no position to
lose: standby confers priority rather than a place, and rejoining costs what joining cost. A
warning here would tell you that you were giving something up, which is not true.

The card leaves your screen and nothing announces it — you are looking at the answer. The one
time the app says anything is when the tap did not reach us, and then it says what is still
true: _that did not go through — you are still on standby_.

## What you owe

If you owe money there is **one line on Now** saying the amount, and saying plainly that until
it is settled you cannot create a match or book a court — so you meet that as something you
were told rather than as a refusal with no explanation
([ADR-0070](../docs/adr/0070-now-is-three-regions-and-a-card-has-two-halves.md)).

**Taking a seat in somebody else's match still works**, and the line says so. Nothing on the
screen is greyed out, dropped or dimmed: being cut off must not make you less likely to pay.

## Leaving a match

The exit on a card opens a screen, never a dialog
([ADR-0086](../docs/adr/0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)).
It states what leaving is worth **right now**, and beside that its reasons — the commitment
deadline, what your seat cost, and how full the match is. Under it are **all four outcomes**
with a marker on each, so you can see what you have passed and what is ahead; a table that
quietly drops _nothing comes back_ once it is unreachable is also a table that never showed
it while it was.

**The screen is the confirmation.** One button, carrying the quote, and no third step: a
dialog over a screen whose whole job is to state the consequence asks the same question
twice. If the outcome has worsened between opening the screen and pressing, the server
refuses and hands back the new one — so you never get less than you were quoted, silently,
and you _see_ the correction rather than being told about it.

Afterwards your card comes back on Now **in place**, rendered for a leaver and still showing
the match's progress, because somebody taking your seat is the only thing that decides
whether your money comes back. Nothing vanishes. A player who had paid nothing yet sees a
card naming **no amount** rather than a blank to interpret. Past the point of departure the
exit is simply **not there** — no door is offered that will not open.

## Entering a score, and answering one

A match you played asks for a score, and the card's act opens a screen
([ADR-0060](../docs/adr/0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md)).
It is **one screen for the whole conversation** — entering, being asked whether the other
side's score is right, proposing a different one, the settled result and the evening nobody
scored — because the route renders the same situation the card resolved rather than a screen
of its own.

**Both sides are named, yours first**, everywhere a score appears: with four people and two
sides, `6-4, 3-6, 6-2` says nothing about whose 6 it was.

**The clock is the biggest thing on it**, next to the sentence saying what happens if nobody
does anything — because silence is what settles a result. One proposal nobody answers
**stands**; two that never agree leave the match counting for nothing. While the half-hour
acceptance window is running the screen says so, so it never reads _settled_ thirty minutes
early.

**Disagreeing costs a statement.** There is no _reject_ button anywhere, and there is nowhere
to send one: a modification carries a score, which is what makes the objection specific and
settles it by the other side's silence in turn.

A settled result prints its score and **moves nobody's level** — no engine produces one, and
the app does not invent a number nothing computed. A player who left before the match opens
the screen and is offered nothing, because she played half an evening and paid for it; she is
never told her match did not exist.

The pad is **one pad for every sport**, and that is a gap rather than a preference: the sport
is not on the player contract at all, so it ships as the widest of the four
([#120](https://github.com/Raketa02/Raketa/issues/120)).

Under all of it is the **tab bar** — five destinations, five Feather glyphs, and a flat
coral circle in the middle for creating a match
([ADR-0082](../docs/adr/0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md)).
Three of the five are placeholder screens their own feature will replace; the fifth is the
account screen, which nothing could reach until the bar landed. **Which tab you are on is
carried by colour alone**, which does not meet WCAG 1.4.1 — a knowing, sighted-only failure
with its remedy already costed in the ADR, and every tab announces its selected state to a
screen reader regardless.

## Design system

The visual language was designed and audited before the app existed, and is **locked**:

- [`docs/design-system.md`](docs/design-system.md) — the rules. **Start at Part 0**, which
  separates the prototype's harness from the product and tabulates every web→native
  translation.
- [`src/shared/ui/theme.ts`](src/shared/ui/theme.ts) — every colour, type role, spacing
  step, radius, metric, shadow and duration. **A literal in a component is a bug.**
- [`docs/design-system-v34-prototype-audit.md`](docs/design-system-v34-prototype-audit.md)
  — the archived measurement of the v34 web prototype. Descriptive, superseded by the rules.

The prototype's phone frame, dark stage, scenario rail and time bar are **harness and do
not ship** — the app _is_ the phone. Styling is a typed theme plus `StyleSheet.create`; no
NativeWind, no styling library — [ADR-0012](../docs/adr/0012-player-app-design-system.md).

Full rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary: [`CONTEXT.md`](CONTEXT.md).
