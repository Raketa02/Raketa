# ADR-0187 — Four deployables: the club website and the public site live in this repo

- **Status:** Accepted — **§8 amended 2026-11-23 by
  [ADR-0209](0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)** (PRD
  [#852](https://github.com/Raketa02/Raketa/issues/852)), with one exception to *"The brand is
  Raketa, everywhere"*: the player app's drawn splash spells its wordmark **Rakieta**. The
  launcher's name and every string stay *Raketa*, and the mocks' *Rakieta* is still read as Raketa
  everywhere else.
- **Date:** 2026-09-25
- **Amends [ADR-0005](0005-three-app-monorepo-ownership-boundaries.md): four deployables.** Its
  decision is unchanged: fully independent apps, HTTP only, no shared source and no workspace, and
  one session per app, enforced. What changes is the app list, which becomes `backend/`,
  `frontend_player/`, `frontend_club/` and `frontend_public/`. The hook's `frontend_club/` arm,
  kept after the reset *"so that a second client is fenced on the day it lands"*, is used for what
  it was kept for. `frontend_public/` gets a tier of its own
  ([#502](https://github.com/Raketa02/Raketa/issues/502)).
- **Amends [ADR-0006](0006-backend-owns-api-contract.md): one document per surface, and there are
  four.** They are `player`, `dev`, `club` and `public` (§5). The decision is unchanged: the backend
  owns the contract, and no client hand-writes a type that mirrors a response.
- **Confirms [ADR-0009](0009-feature-first-clean-architecture-frontends.md) player-only.** It
  governs `frontend_player/` only, as its reset note already reads. **Each web app gets its own standard**
  (§6), and nothing learned in one client transfers to another.
- **Distinguishes [ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)'s**
  rejection of a fourth deployable. That was a slice of the backend's own work proposed as a
  service. These are two new **surfaces with their own users**: a club at a desk, and a stranger
  who tapped a link.
- **Leaves standing [ADR-0008](0008-player-mobile-securestore-direct-api.md)'s** deliberate
  asymmetry. The club website returns with a server-side cookie session, which is the shape its
  *Neutral* section described, and the player app keeps its keychain and its direct calls.
- **Gives way on one copy rule.** [`the-words.md`](../specs/matchmaking/the-words.md)'s voice rule
  *no Rakieta*, which bars naming the app inside a sentence, yields **wherever a mock sentence names
  the app** (§8).
- Settles [#501](https://github.com/Raketa02/Raketa/issues/501) for the PRD
  [#500](https://github.com/Raketa02/Raketa/issues/500). Fenced by
  [#502](https://github.com/Raketa02/Raketa/issues/502). Scaffolded by
  [#522](https://github.com/Raketa02/Raketa/issues/522) (club website) and
  [#525](https://github.com/Raketa02/Raketa/issues/525) (public site). Gated in CI by
  [#527](https://github.com/Raketa02/Raketa/issues/527).

## Context

PRD #500 needs three new places a person can stand:

- **A club at its desk.** It signs up, invites administrators, watches its official groups and hands
  them over. That is a website, used on whatever device is at the desk, from a monitor to a phone.
- **An administrator.** They create official groups and post their links into WhatsApp. That happens
  on a phone, next to WhatsApp.
- **A stranger who tapped a link without the app installed.** It may be a group link in WhatsApp, an
  invitation email opened on a laptop, or a password reset opened on a phone that doesn't have
  Raketa. They need a page that shows the group, or lets them set a password, and hands them to the
  stores. WhatsApp needs server-rendered preview tags to draw a card for the link.

The product owner's document proposed two folders, `frontend_club` and
`frontend_club_administrator`, and invited a better split.

Rejected on the way:

- **A `frontend_club_administrator` app.** An administrator is a person with an account
  ([ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)),
  and many of them already play. A second app would mean a second sign-in, a second install and a
  second copy of the design system, the court drawing and the auth concurrency rules. It would also
  leave nowhere for the switcher to switch.
- **The public pages in a separate repository**, beside a future marketing site. These pages aren't
  marketing. The invitation page **sets a password**, the reset page resets one, and the group page
  resolves a link the backend minted. Each is a step in a product flow and reads a backend surface.
  Outside this repo, the contract gates would stop at the repo boundary, and a backend change could
  break a password page with CI green.
- **The public pages inside the club website.** One Next.js app would then serve both an
  authenticated desk and anonymous strangers. Its cookie session, its tokens and its preview tags
  would share one origin, one deploy and one blast radius.
- **Client-side rendering for the public pages.** Messengers don't run JavaScript. A preview card
  needs its tags in the HTML the server sends.

## Decision

### 1. Four deployables, sharing nothing but HTTP

| App | Path | Stack | Talks to |
| --- | --- | --- | --- |
| Backend API | `backend/` | FastAPI | — |
| Player app | `frontend_player/` | React Native + Expo | the player surface |
| Club website | `frontend_club/` | Next.js, TypeScript | the club surface, from its server |
| Public site | `frontend_public/` | Next.js, TypeScript, server-rendered | the public surface, from its server |

Each app has its own lockfile, config, generated types, `CLAUDE.md`, `CONTEXT.md` and
`.claude/settings.json`. ADR-0005 holds: no shared source, no root workspace, no cross-app import, one
session per app.

### 2. The administrator is a profile in the player app, not an app

The administrator side lives in `frontend_player/` as **its own feature slices**
(`features/administrator*`) and **its own group of screens, outside the player's tab shell**, with a
**Groups · You** bar of its own. It reuses the shared pieces: sign-in, the design system and the court
drawing. There is **no `frontend_club_administrator/`**.

### 3. `frontend_club`: the browser never holds a token

The club website is **Next.js with the App Router and TypeScript**. **A server-side layer keeps the
club's session in an encrypted, httpOnly cookie** and calls the club surface itself. No token, and no
generated wire type, ever reaches the browser. Every page works at every width, down to a phone with
no sideways scrolling.

The map pin uses **OpenStreetMap tiles, with attribution**. OpenStreetMap's own tile servers aren't
for production traffic, so **a tile provider that allows it is a deploy-time item**. The tile URL is a
setting (§7).

### 4. `frontend_public`: server-rendered, and holds nothing

The public site is **Next.js with every page server-rendered**, so messengers read each group's
preview tags (title, description, image) without running JavaScript. It serves:

- **`/join/<code>`**: the group page. It shows the monogram, name, club and district, sport dots and
  member count. It **never says who the members are**.
- **`/invite/<token>`**: the invitation page. It greets the person, offers the store buttons, shows
  the code with *after you install, open Raketa and enter this code*, and has **Set your password
  here**.
- **`/reset/<token>`**: *Set a new password* for players and administrators.
- **Apple's association file and Android's asset links** at their well-known paths, generated from
  settings.
- **Open in Raketa** on every page, using the app's scheme, for phones where the tap-to-open link
  didn't fire.

**The clubs' *Set a new password* page lives on the club website**, not here, because clubs already
use that site. This corrects #500, as [#522](https://github.com/Raketa02/Raketa/issues/522) records.

It has **no sign-in, no session and no cookies**. A future marketing site may live anywhere, because
it isn't this.

### 5. One contract document per surface, four in all

| Document | Consumer | Generated into |
| --- | --- | --- |
| `backend/openapi.player.json` | the player app | `frontend_player/src/generated/` |
| `backend/openapi.dev.json` | the dev console | nothing: no client |
| `backend/openapi.club.json` | the club website | `frontend_club`'s generated types |
| `backend/openapi.public.json` | the public site; **no authentication** | `frontend_public`'s generated types |

A client never reads another client's document, which is ADR-0006's reason for splitting them.
**Every document is emitted and freshness-checked, and every client's types are drift-checked**, each
with its still-fires proof. `make gen-api` regenerates all three clients
([#527](https://github.com/Raketa02/Raketa/issues/527)).

**The public surface discloses the least a page needs.** A group gives its name, monogram, club,
district, sports and member count. An invitation gives the first name, the club and its state, and
its code while it's valid. A reset gives its state. Nothing on it names a member.

Between a backend contract ticket and the client ticket that regenerates from it, the drift check is
red. The branch goes green at the end, not per ticket.

### 6. Each web app has its own architecture standard and its own design tokens

ADR-0009's uniform layer set (domain, use cases and so on) is the player app's alone. A website whose
rules are all the backend's would carry hollow `domain/` folders, which is exactly what ADR-0009's own
escape hatch warns about. Each scaffold writes its standard into the app's own `CLAUDE.md` and docs,
from this section.

**`frontend_club`: server-first.**

- **`src/app/`** holds routes and layouts and nothing else. Route groups `(signed-out)` and
  `(signed-in)` make the session boundary visible in the tree, and the signed-in layout redirects
  when there is no session.
- **`src/server/` is the only code that reaches the backend**, and it's marked `server-only` so it
  can't be bundled for the browser. It holds:
  - **the cookie session**: tokens sealed with a server-only secret, `httpOnly`, `SameSite=Lax`, and
    `Secure` outside `local`
  - **the refresh**: 401 → refresh → retry, single-flight per session
  - **the typed client** over the generated types
- **`src/features/<area>/`**, one per area of the site (sign-in, overview, groups, administrators,
  club details), each with:
  - `queries.ts` for server-side reads
  - `actions.ts` for server actions that write
  - `mappers.ts` from wire to view model: **the only place outside `src/server/` that imports a
    generated type**
  - `schemas.ts` for form validation
  - `components/`: **server components by default**, with `'use client'` only where a page needs
    interaction (a form, the map, a dropdown, a dialog)
- **Decisions branch on the backend's error `code`, never on its message.**
- **Tokens**: its design tokens are CSS custom properties taken from the club mocks, in `src/ui/`,
  beside its primitives. No literal colour or size appears in a component.

**`frontend_public`: server-rendered pages that hold nothing.**

- It has the same `src/app/`, `src/server/` (typed client over `openapi.public.json`, `server-only`),
  `src/features/<page>/` and `src/ui/` shape as the club website, **minus the session**.
- **A token in a URL is read and posted back on the server.** The pages load **no third-party script**
  and send **`Referrer-Policy: no-referrer`**, so an invitation or reset token never leaves in a
  `Referer` or in someone else's analytics.
- **Preview tags come from `generateMetadata`**, per group, in the HTML the server sends.
- **Tokens**: it borrows the club website's look (paper, the coral square wordmark, a white card) and
  is laid out for phones first. It borrows by **copying values into its own `src/ui/`**, never by
  importing from `frontend_club/`.

**The test seam is the same shape in both, and each owns its copy.** Playwright drives the pages. The
app's server layer points at a small **stub backend** that answers with payloads typed from that app's
generated contract and records the requests it receives. **No automated test crosses apps.** The
end-to-end journey is a QA plan walked by hand
([#528](https://github.com/Raketa02/Raketa/issues/528)).

### 7. Every address is a setting, never a literal

These are all configuration, read under the four environment names with
[ADR-0028](0028-four-environment-model-and-typed-configuration.md)'s refusals:

- the public site's domain, which every group link, invitation link and reset link is built from
- the club website's URL
- the store URLs
- the app scheme
- the tile URL
- the Apple team and bundle identifiers
- the Android signing fingerprints

**Both web apps refuse to start without their configuration.**

**Only `local` runs.** Universal links and app links are built and configured from settings, and go
live only once a domain exists. Locally, links use the app's own scheme. Links that arrive in the app
(`join/<code>`, `invite/<token>`, `reset/<token>`) are **untrusted route input** and can never repoint
the backend.

### 8. The brand is Raketa, everywhere

"Raketa for Clubs", every email, every page and every line of copy say **Raketa**. The mocks'
*Rakieta* is read as Raketa. The copy deck's rule against naming the app inside a sentence gives way
**wherever a mock sentence names the app**, as in *"Join Ogrody 33 Club on Raketa: <link>"* and
*"Open Raketa and sign in with your email and password"*. Everywhere else the rule stands.

## Consequences

**Easier**

- The public pages sit under the same contract gates as every other client. A backend change that
  breaks a password page fails CI.
- Each client's session fits its own threat model: a sealed cookie on a website that desks share, a
  keychain on a phone, and nothing at all on a page for strangers.
- An administrator is one install and one sign-in, and the switch between their two sides costs
  nothing.
- A domain, a store listing or a tile provider arriving later is configuration, not code.

**Harder**

- **Four lockfiles, four CI lanes, and Playwright browsers in CI.** The path filters, the bootstrap
  check and `ci-ok`'s needs all grow, and a web app's lane is slower than a unit suite.
- **Two Next.js apps to keep up to date**, separately, by the rule that they share nothing. A framework
  upgrade happens twice.
- **Three design systems, and two that look alike on purpose.** The public site copies the club
  website's values, and a change to one doesn't reach the other. Divergence has to be caught by eye.
- **More duplication between clients.** The same payload shapes are generated three times, and the
  same password rule is re-stated on two websites and in the app. ADR-0005 called this the real cost
  of independent apps, and it grows by two.
- **The public surface is unauthenticated.** It answers anybody who guesses a code, and the invitation
  lookup answers anybody holding a token. Rate limiting belongs to the deployed environment, which
  doesn't exist yet.
- **Tap-to-open links can't be tested until a domain exists.** Everything before then is exercised
  through the app's own scheme, which is a different path through the operating system.
- **A tile provider is a production dependency that nobody has chosen yet.**
