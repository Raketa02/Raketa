# Rakieta for Clubs — the club website

Next.js 16 (App Router) + React 19 + TypeScript, pnpm. A club signs up, signs in, keeps its
details, sets up what it sells through Rakieta (courts, weekly hours, exceptions, prices and its
Rakieta settings, followed by Overview's four-step setup checklist), runs its Rakieta bookings
(moving a game to another court of its kind, or indoor for an outdoor game; cancelling one, which
moves it instead when another of the club's courts takes it, as the dialog says first), connects
Stripe and sees its money and payouts, invites its Administrators and watches its official
groups
([ADR-0187](../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)).
Every club works one way, Only Rakieta: there is nothing to choose, and no club confirms a game,
so nothing here waits for the desk's answer
([ADR-0196](../docs/adr/0196-only-rakieta-until-rakieta-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)).
It talks to the backend's **club surface** (`backend/openapi.club.json`) **from its server
only**: the browser never holds a token.

> One app of the monorepo — see the root [`CLAUDE.md`](../CLAUDE.md). Run every command from this
> directory. It imports nothing from another app; a hook blocks writes outside it.

**Read [`docs/architecture.md`](docs/architecture.md) before adding a page, a form or a call to
the backend.** It is this app's standard, with the reason for each rule. The words this app uses
for its own machinery are in [`CONTEXT.md`](CONTEXT.md); domain words are the root glossary's.

## The standard, in one screen

- **`src/app/`** holds routes and layouts. `(signed-out)` and `(signed-in)` make the session
  boundary visible; the signed-in layout reads the club, which redirects to sign-in without a
  session. **Every signed-in page reads through the same guard too**, because a layout does not
  re-run on every navigation. `src/app/session/` holds the session's own two route handlers, and
  `src/app/payments/continue/` the door Stripe sends a desk back through.
- **`src/server/`** is the only code that reaches the backend, and every file in it imports
  `server-only`: the sealed cookie session, the single-flight refresh, and the typed client
  (openapi-fetch over the generated `paths`). **A feature calls the backend through three doors**
  in `src/server/club.ts`: `anonymously`, `readAsClub` (a render: a 401 hops to
  `/session/renew` and back) and `writeAsClub` (a server action: 401 → refresh → retry in
  place). Beside them, a feature's queries and actions may read the session, the recovery cookie
  and the configuration directly.
- **`src/proxy.ts`** renews a pair that is about to lapse before a page or an action reads it,
  because a render cannot set a cookie, and stamps each request with its own path.
- **`src/features/<area>/`**: `queries.ts` reads, `actions.ts` writes (and makes the reads
  that have no render to read in, such as a dialog opening), `mappers.ts` turns wire into view
  model (**the only file outside `src/server/` and `e2e/` that imports a generated type**),
  `schemas.ts` checks a form, `copy.ts` holds every sentence, and `components/` are
  server components unless a page needs interaction. A feature may use another feature's
  components, schemas, copy and mappers, never its actions or queries.
- **Decisions branch on the backend's error `code`, never its message.** An action answers a
  form with codes; the form turns a code into its sentence from `copy.ts`. The words that belong
  to no feature (the frame, the error pages, the common refusals) are `src/ui/copy.ts`'s.
- **`src/ui/`** holds the design tokens (`tokens.css`, sampled from the club mocks) and the
  primitives, which take their words as props. **No literal colour or size appears anywhere
  else**, and no inline `style`.
- **Every form with a box in it is `src/ui/Form`**, never a bare `<form action>`: React resets a
  form after an action with `form.reset()`, which unticks a controlled checkbox its state still
  holds. A form that is only a button, like _Sign out_, stays a plain `<form>`.

ESLint enforces the import rules and `pnpm test:tokens` the token rule. Both name the rule
they enforce when they fail.

## Commands

```bash
pnpm dev          # next dev on :3000, reading .env.local
pnpm check        # lint + format:check + typecheck + tokens + test: the local gate
pnpm test         # Playwright: builds the site, starts it on :3100 against the stub on :4010
pnpm exec playwright test e2e/<file>.spec.ts   # one spec while iterating
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.club.json
```

`pnpm test` builds first, and **`next build` type-checks `e2e/` too**: a type error in a spec
fails the web server, reported as _"Process from config.webServer was not able to start"_.

## Environment

**Copy `.env.example` → `.env.local` before `pnpm dev`, and fill in `SESSION_SECRET`.** Every
variable is required and has no default. `src/instrumentation.ts` validates them when the server
starts and **exits** naming each bad one. Next alone would log the error and serve 500s, so the
exit is deliberate. `APP_ENV` is one of the four names and only `local` runs today.

## The test seam

Playwright drives the built pages while `API_URL` points at **the stub backend** in `e2e/stub/`,
which answers with payloads typed from the generated contract and records every request. The
fixtures reset it before each test and install **the fake club** (`e2e/stub/club.ts`): one
club whose tokens rotate, whose reset signs everyone out, and whose administrators and official
groups keep the backend's rules (a test seats them in `club.administrators` and `club.groups`;
a group is run only while its administrator is active), and whose Rakieta offer, `club.rakieta`,
keeps the courts, prices and settings and reads the setup checklist off them (nothing set until
a test says; `club.rakieta.ready()` makes the club live), and whose bookings, `club.bookings`,
fold their status off the clock as the backend does (a test seats them with
`club.bookings.add(booking(…))`) and hold each share until the game's `cut_off`, taken after it
(`club.bookings.passTheCutOff(game)` takes them). Move puts a game only on a court of its kind,
or indoor for an outdoor game; a cancel, unless _anyway_, moves it to the court that takes it,
deciding afresh whatever the preview said. The fake club's money, `club.money`, answers a
month's rows and the payouts a test seats (`moneyRow(…)`, `payout(…)`; a fee Stripe hasn't
given is `null`, _not yet known_). Stripe's hosted pages are the stub's
too, so a redirect to one lands, and `stub.stripePages` says which opened. A test about one reply overrides
that operation with `stub.on`, naming it by the contract's path, `{administrator_id}` and all.
One worker, because the one server talks to the one stub.

- **A token in a test comes from the fake**: `club.accessToken(n)`, `club.refreshToken(n)`.
  They are unique across the run, because the website keeps a renewed pair for a few seconds per
  refresh token, and a reused `refresh-1` would find the previous test's.
- **After clicking a link, wait for the new page's heading before filling a box.** The old page
  stays on screen while the next one loads, and its boxes may share a label.
- Reading `node_modules/`, `.next/`, `test-results/` and `playwright-report/` is denied here.
  Fetch a library's source or docs from GitHub at the pinned tag.

## Safety — never without an explicit request

- Create or edit a real `.env*` file. Edit `.env.example`, and let a human copy it.
- Send a session token or a ticket to the browser in any form: a prop, a hidden field, a
  response body, a log line. A reset link's token is the one the browser arrived holding, and
  the page binds only that one to its action.
- Name a production tile provider or turn on a deployed environment. Both are deploy-time items
  (ADR-0187 §3 and §7).
