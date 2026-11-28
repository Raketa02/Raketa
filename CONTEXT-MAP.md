# Rakieta — Context Map

A **polyglot monorepo** of **four independently deployable apps** that realize the
**same** bounded contexts
([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)).
The two web apps are the newest, each built on its own scaffold:

- **`backend/`** — async FastAPI service. Clean/hexagonal, DDD, event sourcing,
  transactional outbox. Python 3.11 + Poetry. **Source of truth for the API contract.**
- **`frontend_player/`** — React Native + Expo, TypeScript. The native iOS/Android app
  for players — and for **Administrators**, as a second profile inside it, never a separate
  app. Talks to FastAPI directly; tokens live in the OS keychain.
- **`frontend_club/`** — the **club website**, Next.js. A club signs up, invites its
  Administrators and watches its official groups. Its server keeps the session in an encrypted
  httpOnly cookie; the browser never holds a token. *Scaffolded by
  [#522](https://github.com/Rakieta02/Rakieta/issues/522).*
- **`frontend_public/`** — the **public site**, Next.js, server-rendered: the pages a group link,
  an invitation or a password reset opens when the app is not installed, and the app-link files.
  No sign-in, no session. *Scaffolded by [#525](https://github.com/Rakieta02/Rakieta/issues/525).*

Outside the monorepo, **`Rakieta02/rakieta-features`** holds the feature flags as Featurevisor
YAML, and **the player app reads it again** ([#826](https://github.com/Rakieta02/Rakieta/issues/826)). It
is not an app and holds no domain code: its CI builds one datafile per environment, and the
player app fetches its own over HTTP and decides each feature flag on the device
([ADR-0206](docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)).
Nothing checks the two repositories against each other; a key they spell differently is a
feature at its code default. The backend reads nothing from it.

```
                          ┌──────────────────┐
                          │   backend/       │  owns the domain + the contract
                          │   FastAPI        │  one document per surface
                          └───┬─────┬─────┬──┘
              player surface  │     │     │  public surface (no auth)
         ┌────────────────────┘     │     └─────────────────────┐
┌────────▼──────────┐   club surface│              ┌────────────▼────────┐
│ frontend_player/  │  ┌────────────▼──────┐       │ frontend_public/    │
│ Expo · direct API │  │ frontend_club/    │       │ Next.js · SSR       │
│ token in keychain │  │ Next.js · server  │       │ holds nothing       │
│ player + admin    │  │ cookie session    │       │ group/invite/reset  │
└───────────────────┘  └───────────────────┘       └─────────────────────┘
```

The dev console's `openapi.dev.json` is a fourth surface with no client.

> **The club console that the 2026-08-25 reset removed returns as a different app.** It was
> a Next.js console with a BFF; what arrives is the **club website** of PRD
> [#500](https://github.com/Rakieta02/Rakieta/issues/500) — sign-up, Administrators, official
> groups — at the same path, `frontend_club/`, whose fence the guardrail hooks kept for exactly
> this day. `frontend_public/` is new and gets a fence of its own
> ([#502](https://github.com/Rakieta02/Rakieta/issues/502)).

> **Courts, bookings and money came back without a new app**
> ([ADR-0189](docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md), built under
> PRD [#530](https://github.com/Rakieta02/Rakieta/issues/530)). The backend grew new contexts —
> Proposals, Bookings, Payments, Notifications, and courts in Clubs — the player app got the group deck, Fill in and an Account group on You, and
> the club website got Bookings, Check in (its removal decided by
> [ADR-0195](docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)),
> Courts & prices, Money and Rakieta settings (*On request*'s answers and *Instant* removed by
> [ADR-0196](docs/adr/0196-only-rakieta-until-rakieta-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md),
> which leaves *Only Rakieta* until Rakieta is the club's booking software). Stripe is an
> outside service behind a port, not a deployable, and its webhooks are on no client's contract
> ([ADR-0190](docs/adr/0190-money-goes-through-one-port-and-a-notice-is-read-once.md)). The terms
> are in `CONTEXT.md` under those contexts; the spec set is `docs/specs/games-and-fill-in/`.
>
> **Friends comes without a new app either**
> ([ADR-0202](docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md),
> PRD [#743](https://github.com/Rakieta02/Rakieta/issues/743); built). The backend
> grows a **Friends** context, a friends game is a further birth in Bookings and its Cover a Seat
> charge in Payments; the player app grows a friends feature; the public site grows a page for
> `/f/<code>` beside its group, invitation and password-reset pages; and the club website only reads its
> other-clubs setting as on by default. The terms are in `CONTEXT.md` under **Friends**, **Bookings**,
> **Payments** and **Proposals**; the spec set is `docs/specs/friends/`.
>
> **Rankings comes without a new app either**
> ([ADR-0203](docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md),
> PRD [#766](https://github.com/Rakieta02/Rakieta/issues/766); built). The backend
> grows a **Rankings** context: a stored projection of every player's level per sport and its
> history, fed by the rating's events through the outbox, and reaching Friends, Blocks, Users and
> the Player profile only through ports it declares. The record gains a strand and a block gate,
> and a friend request its daily limit. The player app grows a rankings feature, a trophy on Home and
> a switch on You. The club website and the public site don't change. The terms are in `CONTEXT.md`
> under **Rankings**, **Player record**, **Blocks** and **Friends**; the spec set is
> `docs/specs/rankings/`.
>
> **Discovery comes without a new app either**
> ([ADR-0204](docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md),
> PRD [#789](https://github.com/Rakieta02/Rakieta/issues/789); built). Home gains five
> rows below *Your games*. The backend grows a **Discovery** context for the three people rows — *Same
> competitive level*, *New in Rakieta* and *Same vibe* — with three stored tables, the stated exceptions
> to *derived, never stored*: a player directory fed by the profile's and the user's events, every
> player's current level per sport fed by the rating's, and a per-viewer rest count, reaching Friends,
> Blocks, the Forecast, the profile, the user
> and the rating only through ports it declares. **Groups** gains the Hottest groups read and Withdraw
> on a Join request, **Rankings** the Top 10 read, and loses its switch and its block filtering; the
> record opens to any reader but across a block or *Show me to new people*'s rule, and a friend
> request loses its daily limit. The player app grows a discovery feature, a Hottest groups row in
> groups, a Top 10 row in rankings and the round friend button in friends. The club website only drops
> a withdrawn request from its list; the public site doesn't change. The terms are in `CONTEXT.md`
> under **Discovery**, **Groups**, **Rankings**, **Player profile**, **Player record**, **Blocks** and
> **Friends**; the spec set is `docs/specs/home-rows/`.
>
> **The Home refactor comes without a new context**
> ([ADR-0205](docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md),
> PRD [#810](https://github.com/Rakieta02/Rakieta/issues/810); decided, not yet built). The four cards
> that wait on the player move behind an envelope in Home's header, into **Needs your answer**, and
> Home's five rows fold into FOR YOU's lines, with counts. **Proposals** keeps the envelope's *new*: a
> visit per player, counted on `GET /home`. **Groups** gains a paged Groups heating up read, and the
> four row reads, Groups' and Discovery's, a capped `total`. Every contract change is additive, and
> only the backend and the player app change. The terms are in `CONTEXT.md` under **Proposals**
> (*Home*, *Needs your answer*) and **Friends**; the brief, the decision log and the mocks are
> `docs/specs/home-refactor/`.
>
> **For fun is built by shared social tags, without a new context**
> ([ADR-0207](docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md),
> PRD [#827](https://github.com/Rakieta02/Rakieta/issues/827); decided, not yet built). **Proposals**
> builds and ranks For-fun tables by their **Social vibe**, then new faces, with skill only a guard,
> and opens the For-fun deck on the best company; competitive building is untouched. **Match Fit**
> gains the Social vibe as one pure function, which Proposals and **Games** both call. The **Player
> profile**'s vocabulary grows to 27 tags, held 2 to 8. No new table: Proposals and Games read
> Discovery's tag rows through ports of their own. Only the backend and the player app change. The
> terms are in `CONTEXT.md` under **Matchmaking** (*Social vibe*) and **Player profile** (*Social
> tag*); the brief, the decision log and the mocks are `docs/specs/for-fun/`.
>
> **You’re in becomes its own tab, without a new context**
> ([ADR-0208](docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md),
> PRD [#844](https://github.com/Rakieta02/Rakieta/issues/844); decided, not yet built). A group page
> has four tabs, Games · Fill in · You’re in · Friends: **Fill in** keeps the rescues, the player's
> live yeses move to **You’re in**, and Post a game floats there. The badges count what the player
> hasn't seen, and the phone remembers which rows were seen, per account (ADR-0208). The one
> contract change is additive: **Proposals**' group deck read carries the ids of the cards with
> somebody In. Only the backend and the player app change. The terms are in `CONTEXT.md` under
> **Bookings** (*Fill in*, *You’re in*); the decision log and the mocks are
> `docs/specs/fill-in-split/`, and the specs it amends are `docs/specs/games-and-fill-in/`.
>
> **The drawn splash touches no context**
> ([ADR-0209](docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md),
> PRD [#852](https://github.com/Rakieta02/Rakieta/issues/852); decided, not yet built). On every cold
> open a volt ball bounces into the **Rakieta** wordmark, and startup runs behind it instead of
> holding the native splash. A launch that already knows it has no internet doesn't send the launch
> check. Only the player app changes: no backend change and no contract change. Since ADR-0211 the
> splash's drawn wordmark, the launcher's name and every string spell the brand alike: **Rakieta**.
> The brief, the decision log and the mock are `docs/specs/splash-screen/`.
>
> **The tab menu touches no context** (PRD [#859](https://github.com/Rakieta02/Rakieta/issues/859);
> decided, not yet built). A group page's *Competitive / For fun* switch leaves the page for a menu on
> the selected **Games** or **Friends** tab, with today's counts and **Play intent**'s door on Games
> and neither on Friends, and the deck card's player tiles take a fixed shape. It is a change of
> layout with no new record: ADR-0201 §2 and the fill-in split's override 2 carry dated notes. Only
> the player app changes: no backend change and no contract change. The brief, the decision log and
> the mocks, which are illustrations only, are `docs/specs/tab-menu/`; the specs it amends are
> `docs/specs/games-and-fill-in/` and `docs/specs/friends/`.
>
> **The tab bar dock touches no context**
> ([ADR-0210](docs/adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md), PRD
> [#878](https://github.com/Rakieta02/Rakieta/issues/878); decided, not yet built). The player app's
> tab bar floats over every main screen as a glass dock, Home · Play · You, and a coral **selection
> marker** travels to the lit tab. What each tab opens doesn't change. Only the player app changes:
> no backend change and no contract change. The brief, the decision log and the mocks, which lead
> on design but give no number, are `docs/specs/tab-bar-dock/`.
>
> **The brand's new name touches no context**
> ([ADR-0211](docs/adr/0211-the-brand-is-rakieta-everywhere.md), PRD
> [#889](https://github.com/Rakieta02/Rakieta/issues/889); decided, being built). The brand is
> **Rakieta**, everywhere. The glossary's terms that carry it (*Rakieta hours*, *Rakieta settings*,
> *Only Rakieta*, *Rakieta sells them alone*, *New in Rakieta*) change their brand word and nothing
> else, and no concept, context or fence changes. Every app changes, and so
> does the contract: its paths, schemas, operation ids and titles say Rakieta.
>
> **The older way of making a game went on 2026-10-06** — *Classic play*: the Players deck and
> radar, Chats, challenges and plans, Find a game, the searches, the candidate index and the
> ranking, with the feature flag that hid them
> ([#569](https://github.com/Rakieta02/Rakieta/issues/569)). No app or fence changed; the
> `challenges` and `plans` contexts left the backend, `play`, `challenges`, `plans` and
> `feature_flags` left the player app, and the records and specs that described only them were
> deleted ([ADR index](docs/adr/README.md#the-2026-10-06-classic-play-removal--the-second-gap)).

> **The matchmaking engine did not add an app, and that was a decision rather than an
> omission** — the two web apps above arrived later, for a different reason: they are new
> surfaces with their own users, not a slice of the backend's own work. Its input document
> recommended a deployable in Go at `matcher/`;
> [ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) puts it in the
> backend instead — the stateful half as a module, the scorer as the **second engine** beside
> RacketSkill. So there is no `matcher/CLAUDE.md`, no `matcher/` ownership fence and no matcher CI
> lane. The two engines may not import each other, which is why `.importlinter` carries two
> `forbidden` contracts rather than one: two engines that can reach each other develop two
> opinions about a level. Since 2026-10-06 the second engine scores nothing — it is the balance
> forecast and group availability the new games read — and its spec set is gone.

## How the domain language is split

An `Assessment` means the same thing in both apps. To stop the ubiquitous language
drifting, the **domain** glossary lives in exactly one place and each app adds only its
own **technical** vocabulary:

| File | Scope | Owns |
| --- | --- | --- |
| **`CONTEXT.md`** (root) | **Shared domain language — source of truth** | User, Player, Authority, Email, Sport, SportSpec, Assessment, Skill rating, Level, Band, Confidence, statuses, domain events, Audience, Signing out everywhere, Player profile, Social tag, Weekly hours, Gender preference, Play intent, Block, Mode, Ruleset, Level window, Newcomer window, Forecast, Split, Game, Line-up, Departure, Result, Score, Played · no score, Disputed, Isn't here yet, Arrival, On time · Came late · Didn't come, I was there, Standing, Counted game, Conversation, Member, System line, Typing, Player Score, Points, Played through, Reliability band, New, Results left in dispute, Reliability filter, Run of form, At stake, On-court check, Sportsmanship, Stars, The card, Club, Club account, Home club, Club courts, Court, Kind of court, Rakieta hours, Exception, Price, Share, Court hour, Only Rakieta, Rakieta settings, Cut-off, Book-by, Paused, Setup checklist, Group, Player group, Official group, Owner, Group member, Join policy, Join request, Group link, WhatsApp group size, Handover, Administrator, Invitation, Booking, Leaver, Rescue, Fill in, Move by cancel, Payment method, Setup, Payment terms, Payment provider, Seat charge, Pool, Proposal, Version, Yes, In, Withdraw, Live yes, Post, Fills, Group deck, Owed card, Games & money, Home, It's a game!, Ranking, General, Friends (the view), Place, Listed, the chip, Top 10, Show me to new people, Hottest groups, Heat, HOTTEST, GROWING, People rows, Same competitive level players, % even, New in Rakieta, Same vibe players, Vibe %, Good match, Fresh, Gap, Rest, On screen… |
| **`backend/CONTEXT.md`** | Backend technical vocab only | event-sourced aggregate, outbox, event store, port/adapter, UoW… |
| **`frontend_player/CONTEXT.md`** | Player-app technical vocab only | feature, use-case, mapper, wire type vs DTO, screen, secure store, query/mutation, presentation module, copy deck… |
| **`frontend_club/CONTEXT.md`** | Club-website technical vocab only | server layer, cookie session, recovery cookie, single flight, server action, view model, stub backend… |
| **`frontend_public/CONTEXT.md`** | Public-site technical vocab only | dead link, untrusted route input, preview tags, preview image, tile, link state, setting by link, the way in, Open in Rakieta, app-link files, stub backend… |

An app `CONTEXT.md` must **never redefine** a domain term — it points back to the root
glossary. Three words collide across that line and are settled at the root: the app's
switcher says *profile* (UI vocabulary — *Player profile* is an aggregate), a Members list
says **admin** (copy for *runs this group* — not the `ADMIN` Authority), and a conversation's
**Member** is not a **Group member**.

## Design systems are per-app and never shared

Each client owns its own visual language, tokens and vocabulary, and shares no code with
any other ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)). It is
stated as a rule rather than as a description because the moment a second client exists,
the tempting move is a shared design package, and that is the thing this forbids — and the
moment is here: the public site **borrows the club website's look** (paper, the coral square
wordmark, a white card) by **copying its values into its own tokens**, never by importing them
([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §6).

| File | Owns |
| --- | --- |
| **`frontend_player/docs/design-system.md`** | The player app's rules: colour meanings, the primitives, the level bar, overlays, touch and accessibility. **Locked** — [ADR-0012](docs/adr/0012-player-app-design-system.md). |
| **`frontend_player/src/shared/ui/theme.ts`** | The player app's values, as a typed object. Same rule: no literal in a component. |
| **`frontend_club/src/ui/`** | The club website's tokens, as CSS custom properties taken from the club mocks, and its primitives. |
| **`frontend_public/src/ui/`** | The public site's own copy of that look, laid out for phones first, plus the colours of a group's tile and sport dots, copied from the player app's; `tokens.ts` repeats the few its preview image needs. |

Design-system *terms* (token, soft/ink, eyebrow, hairline, severity rail, band ink, sheet
vs drawer) are technical vocabulary and live in that app's `CONTEXT.md`. A design system
never settles a **domain** term — that happens in the root `CONTEXT.md` first.

**Two things sit between the apps and are shared.**

[`docs/environments.md`](docs/environments.md) — the four environment names, what each is,
which variable carries it in each app, the refusals, the scheme rule, the test taxonomy, and
the checklist for turning on a remote environment. Not domain language (no nouns a player
would recognise) and not a design system: a **deployment contract**. It lives at the root
because an environment name is the one piece of vocabulary every app must spell
identically — `local`, `development`, `staging`, `production` — and a word defined once per
app drifts once per app. Decided by
[ADR-0028](docs/adr/0028-four-environment-model-and-typed-configuration.md) and
[ADR-0029](docs/adr/0029-seed-data-through-aggregates-never-in-production.md). Each app's
`CONTEXT.md` may add how *it* reads the value; none of them redefines the names.

[`docs/value-formatting.md`](docs/value-formatting.md) — the exact string a price, a level, a
time or a duration becomes. Not a design system (no colour, no size), not domain language (no
nouns): a rendering contract. The backend sends numbers and machine codes and never display
text ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), so the client
formats, and this is the table it implements. Enforced by the cross-application
contract suite of [ADR-0021](docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md),
not by hoping.

## Decisions (ADRs)

**`docs/adr/`** (root) holds every decision affecting the system or the contract
between apps, numbered sequentially across the whole repo. There are no per-app ADR
directories: a decision that only affects one app still tends to constrain the others,
and one numbered sequence is easier to reason about than several. **The sequence has gaps**
— see the [index](docs/adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps).

## Claude Code instructions

`CLAUDE.md` files load from the working directory **and every ancestor**, so a session in
`backend/` gets the root file plus the backend's. Files in sibling apps never load. Work
from inside the app you are changing:

- **`CLAUDE.md`** (root) — monorepo orientation and the repo-wide safety list.
- **`backend/CLAUDE.md`** — Python/FastAPI rules (TDD, hexagonal, events, Poetry).
- **`frontend_player/CLAUDE.md`** — Expo/RN rules (feature layering, secure store, codegen).
- **`frontend_club/CLAUDE.md`** and **`frontend_public/CLAUDE.md`** — each web app's own
  standard ([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §6), written by its scaffold. A rule learned in one client does not transfer to another.

**Settings and hooks do not work that way.** Claude Code reads `.claude/settings.json`
**only from the directory the session started in** — it is not inherited from ancestors.
So each app carries its own `.claude/settings.json` that registers the same two hooks and
adds that app's permissions. Registering them only at the root would leave every scoped
session — the ones the ownership boundary exists for — running with no guardrails.

Each app also carries:

- **`.claude/rules/`** — conventions with `paths:` frontmatter, loaded only when Claude
  opens a matching file (the design system on UI files, the HTTP rules on API clients).
- **`.claude/skills/`** — procedures, loaded only when invoked or judged relevant.

The always-loaded `CLAUDE.md` holds what is true in *every* session in that app; everything
else lives one layer down. See
[`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).

## Where things live

```
/
├── CLAUDE.md                 ← monorepo orientation + safety list
├── CONTEXT-MAP.md            ← you are here
├── CONTEXT.md                ← SHARED domain glossary (source of truth)
├── Makefile                  ← thin root helpers (gen-api, check, afk)
├── .claude/
│   ├── settings.json         ← root-session permissions + hook registration
│   ├── hooks/                ← enforce-ownership.sh, guard-bash.sh, test-hooks.sh
│   └── skills/               ← cross-app procedures (write-adr, guardrails)
├── docs/
│   ├── adr/                  ← system-wide decisions (0001…)
│   ├── agents/               ← ownership boundaries, domain-doc consumption
│   ├── environments.md       ← THE four environment names + deployment contract
│   ├── specs/player-app/     ← the player app's product + architecture specifications
│   ├── specs/matchmaking/    ← only the-words.md, the WHOLE app's copy deck, here for history;
│   │                            the engine's spec set went with Classic play (#569)
│   ├── specs/player-record/  ← the player record: the plan it was built from + the decisions
│   ├── specs/you/            ← the You tab, row by row (ADR-0179)
│   ├── specs/play-groups/    ← Play › Groups, the club website and the Administrator:
│   │                            the product owner's mocks and which area each one draws
│   ├── specs/games-and-fill-in/ ← a group's Games deck and Fill in, courts and money (ADR-0189):
│   │                            the mechanics, the screens and the mocks — the one way a game is made
│   ├── specs/rankings/       ← a ranking per sport, sorted by the level (ADR-0203): the mechanics,
│   │                            the screens, the brief and its mocks
│   ├── specs/friends/        ← friends, the friend link and friends games (ADR-0202)
│   ├── specs/home-rows/      ← Home's five rows and who sees whom (ADR-0204): the mechanics,
│   │                            the screens, the brief and its mocks
│   ├── specs/home-refactor/  ← Needs your answer and FOR YOU (ADR-0205): the brief, the
│   │                            decision log and the mocks, which lead on design
│   ├── specs/for-fun/        ← For fun built by shared tags, the Social vibe (ADR-0207): the
│   │                            brief, the decision log and the mocks, which lead on design
│   ├── specs/fill-in-split/  ← Fill in and You’re in as two tabs, unseen badges (ADR-0208):
│   │                            the decision log and the mocks, which lead on design
│   ├── specs/splash-screen/  ← the drawn splash, startup behind it (ADR-0209): the brief, the
│   │                            decision log and the mock, which lead on design
│   ├── specs/tab-menu/       ← Competitive / For fun in the tab's menu, the deck tiles' shape
│   │                            (PRD #859): the brief, the decision log and the mocks, illustrations only
│   ├── specs/tab-bar-dock/   ← the tab bar as a floating glass dock and its selection marker
│   │                            (ADR-0210): the brief, the decision log and the mocks, which lead on design
│   └── value-formatting.md   ← the rendering table the client implements
├── backend/                  ← FastAPI  (CLAUDE.md + CONTEXT.md + its own docs/)
├── frontend_player/          ← Expo     (CLAUDE.md + CONTEXT.md)
│   ├── docs/architecture.md          ← the player app's runtime contract (ADR-0013)
│   ├── docs/design-system.md         ← the player app's LOCKED visual contract
│   └── src/shared/ui/theme.ts        ← its values; components read the theme only
├── frontend_club/            ← Next.js  the club website  (CLAUDE.md + CONTEXT.md + docs/architecture.md)
├── frontend_public/          ← Next.js  the public site   (CLAUDE.md + CONTEXT.md + docs/architecture.md)
└── tools/afk/ + .sandbuket/  ← the AFK agent execution loop and its sandbox image
```
