# The club website's standard

**Server-first**, as [ADR-0187](../../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
§6 decided. It is this app's own. Nothing learned in the player app transfers here, and nothing
here transfers to the public site, which keeps a copy of whatever it borrows. Each part below is
a rule and the reason for it. A change that needs to break one changes this page in the same
pull request.

## 1. Where code lives

```
src/
  app/                 routes and layouts only
    (signed-out)/      sign-in, sign-up, forgot-password/…, reset/[token]
    (signed-in)/       layout (the frame), overview, bookings, courts, money, groups,
                       administrators, details, raketa-settings
    session/           renew and end: the session's own route handlers (§3)
    payments/continue  where Stripe sends a desk whose link is spent: a fresh one, followed
  proxy.ts             renews a lapsing session and stamps each request's path (§3)
  instrumentation.ts   refuses to start without the configuration (§6)
  server/              the only code that reaches the backend; every file `server-only`
  features/<area>/     queries.ts · actions.ts · mappers.ts · schemas.ts · copy.ts · components/
  ui/                  tokens.css and the primitives
  generated/           openapi-typescript output; never edited by hand
e2e/                   the Playwright suite and its stub backend (§7)
```

- **Routes compose; they decide nothing.** A page reads through a feature's `queries.ts` and
  hands a view model to a feature's component. ESLint refuses `@/server/*` in `src/app/` and in
  components, so the backend is only ever reached through a query or an action. The exception is
  `src/app/session/`, whose two route handlers belong to the server layer as the proxy does.
  `/payments/continue` is a route handler too, a door rather than a page, and it goes where
  Overview's action says (`continueWithStripe`).
- **A feature is an area of the site**: `sign-in` (signing in and up, signing out, _Forgot
  password?_, _Set a new password_), `club-details`, `overview` (the setup checklist and
  _Connect with Stripe_, then _Live on Raketa_),
  `bookings` (the day's Raketa bookings, _Move_ and _Cancel_), `courts` (_Courts & prices_: the courts, their weekly hours,
  exceptions and prices), `money` (a month of the club's money, its payouts and its Stripe
  dashboard), `raketa-settings`, `administrators` and `groups` (the Groups table, and a group's page:
  _Want to join_ and _Hand over_). A feature may use another feature's components, schemas, copy and mappers
  (sign-up draws Club details' fields; Overview greets a `Club` and says _Set a new password_ in
  sign-in's words; Raketa settings reads the checklist through Overview's mappers),
  and never another feature's actions or queries: a route reads both features' queries and
  hands each its view model. A feature's queries and actions call the backend only
  through the three doors of §4, and may read the session, the recovery cookie, the marks of
  §2 and the configuration directly.
- **`mappers.ts` is the only file outside `src/server/` that imports a generated type**, besides
  the suite's stub in `e2e/`, which types its replies from the contract on purpose. It
  turns a wire type into a view model and back. A contract change then lands in one file per
  feature, and the compiler finds it: the sports' names are a `Record` over the wire's enum, so a
  fifth sport fails to compile until it has a name.
- **`src/ui/` knows nothing of the club.** Primitives take words and values as props, and never
  import a feature or the server. `src/ui/copy.ts` holds the words that belong to no feature: the
  frame's page names, the error pages, and the refusals every form can meet.

## 2. The cookie session

The browser holds **one cookie**, `raketa_club_session`: the access token, the refresh token and
the moment the access token lapses, sealed by iron-session with `SESSION_SECRET`. It is
`httpOnly`, `SameSite=Lax`, `Path=/`, and `Secure` everywhere but `local`. Its thirty-day life is
longer than any refresh token, so **the backend decides when a session ends**.

- **Nothing a page sends the browser carries a token.** Pages get view models, forms get refusal
  codes, and the suite asserts that no response the browser receives contains either token.
- **Reading works anywhere on the server; writing only where Next allows a `Set-Cookie`**: a
  server action, a route handler, the proxy. That one constraint shapes §3.
- **Sign out** revokes the refresh token at the backend (idempotent), then deletes the cookie,
  whatever the backend answered.
- **What a browser was told once is a third cookie**, `raketa_club_told_live`: Overview says
  _You're live_ once (the screens B2), and a club can go live while nobody is looking (Stripe
  says so later), so no save could carry the news. It holds no token and nothing anybody could
  use, has the session's attributes, and is set and cleared only by Overview's server action
  (`src/server/marks.ts`).
- **_Forgot password?_ keeps its own sealed cookie**, `raketa_club_recovery`, for an hour at most:
  the email asked with, and once a right code is claimed, the ticket. The ticket is a credential,
  so it never reaches the browser either. The reset link's token is the exception that proves the
  rule: the browser arrived with it in the address bar, the page binds it to its action, and
  `/reset/*` sends `Referrer-Policy: no-referrer` so it goes nowhere else.

## 3. Keeping the pair fresh

The backend rotates a refresh token on every use and refuses a spent one. Three places meet an
access token, and each does what it can:

- **`src/proxy.ts`, before every page and action (it can set a cookie).** Renews a pair within
  30 s of lapsing, and hands the new cookie to the browser **and to the render behind it**. A
  pair the backend refuses to renew clears the cookie; silence changes nothing. It also stamps
  every request with its own path, in `x-club-path`, always overwriting what the browser sent.
- **`readAsClub`, while a server component renders (it cannot).** A 401 hands the page to
  **`/session/renew?to=<its path>`**, a route handler that renews through the single flight and
  sends the browser back. Refused, the cookie goes and sign-in says the session ended; no answer,
  sign-in says so and the cookie stays. A pair refused while under five seconds old goes to
  `/session/end` instead, so a renewal never goes round, and `/session/renew` only ever returns
  to a path of this site.
- **`writeAsClub`, in a server action (it can).** **401 → renew → retry** in place, once. A
  refused renewal, or a second 401, ends the session the same way.

**Every renewal is a single flight** (`src/server/refresh.ts`). One refresh token is exchanged
once, and every request holding it shares that exchange: a page and the links it prefetches
arrive together carrying the same cookie, and a second exchange would be refused and would end a
session that was fine. The renewed pair is also kept for twenty seconds, so a request that left
before the new cookie landed gets the same pair.

The flights live in memory, per process and per bundle: Next builds the proxy apart from the
pages, and advises against sharing state between them. That is enough for one server. **More
than one instance behind a balancer needs sticky sessions or a shared flight**, which is a
deploy-time question for the day there is a deployment.

## 4. Calling the backend

`src/server/club.ts` is the only way in, through three doors:

- **`anonymously(call)`**: sign-up, sign-in, _Forgot password?_.
- **`readAsClub(call)`**: a render's read. No session redirects to sign-in; a 401 renews by §3.
- **`writeAsClub(call)`**: a server action's write, with the retry of §3.

**A read with no render to read in is a server action too**, in `actions.ts`, through
`writeAsClub`: a dialog that opens on a click, such as Bookings' _Move_, which reads the free
courts as it opens (`readFreeCourts`). It writes nothing; the door is the one that can renew in
place.

Each call is `openapi-fetch` over the generated `paths`, with a ten-second timeout, and each
settles into an **outcome**: `{ ok: true, data }` or `{ ok: false, error: { status, code,
field?, details? } }`, where `details` keeps the envelope's words, such as the group a
`club_sport_declared_by_group` names. `code` is the backend's, or one of three of the website's
own: `backend_unreachable` (no answer), `backend_failed` (an answer with no envelope) and
`request_invalid` (any `422`, whose envelope reads `validation_error` and names no field). A
`422` is this site's bug, said over the form, except on the three forms whose one box the
contract checks by format is an email (sign-in, _Forgot password?_ and the code): there the
backend's email check disagreed with this site's, and the action turns it into `email_invalid`
under the box. Failures that are nobody's typing are logged by code and trace id, never with a
payload.

**Decisions branch on `code`, never on `message`.** The backend's message is a diagnostic; the
sentence the desk reads is this site's, chosen by code.

## 5. Forms

- **A server action checks what it can, then asks the backend, then answers with codes.** The
  local checks restate the backend's rules, which is the accepted cost of independent apps, and
  refuse with the backend's own codes, so one sentence serves a refusal from either side. A form
  the site refuses never reaches the backend.
- **A refusal goes under the field it names** (`details.field`), or over the form when it names
  none. A code the site has no sentence for still lands under its field, with the fallback
  sentence, so a new backend refusal is never lost.
- **`copy.ts` holds every sentence**, keyed by code, in each feature, and `src/ui/copy.ts` the
  words that belong to none. The wording follows the
  player app's where the two do the same thing (the password rule, a wrong code), by copying it.
- **Every form with a box in it is `src/ui/Form`.** React resets a form after an `action` submission with the
  native `form.reset()`, which restores a controlled text box but unticks a controlled checkbox:
  a refused sign-up lost its sports. `Form` submits through `onSubmit` in a transition, which
  keeps `useActionState`'s pending flag and resets nothing. Its `action` stays on the element for
  a browser without JavaScript. A form that is only a button, like _Sign out_, has nothing to lose
  and stays a plain `<form>`.
- **Boxes are controlled**, and `useFormFeedback` takes a field's refusal away as soon as that
  field changes, because the refusal was about what the box held then.
- **`noValidate` everywhere**: every refusal is this site's sentence under its field, never a
  browser bubble.

## 6. Configuration

Six variables, all required, none with a default, none `NEXT_PUBLIC_*`: `APP_ENV`, `API_URL`,
`SESSION_SECRET`, `MAP_TILE_URL`, `MAP_START` and `GEOCODER_URL` (`.env.example` says what each
is for).
`src/server/config.ts` parses them purely and names every bad one and why, never its value, and
a variable set to nothing counts as missing.

**`src/instrumentation.ts` calls it before the server takes a request, and exits.** Next alone
would log a failed `register()` and go on serving 500s. `APP_ENV` selects defaults only: `Secure`
cookies outside `local`, and `https://` tiles in every deployed environment, because the browser
fetches them over the public network. `API_URL` is server-to-server and carries no scheme rule
(`docs/environments.md`).

The map's tiles are OpenStreetMap's, with its attribution, and **the tile URL is a setting**:
OpenStreetMap's own servers are not for production traffic, and choosing a provider that allows
it is a deploy-time item (ADR-0187 §3).

**The address over the map is found by this server**, never the browser
(`src/server/geocoder.ts`, behind Club details' `findAddress` action): the desk types where the
club is, and the geocoder at `GEOCODER_URL` — Nominatim's `/search` for development — answers the
best match, which the map takes the pin to. Nominatim's usage policy asks a caller to name itself
and to ask at most once a second; a browser cannot set the `User-Agent`, and this server queues its
searches a second apart. The search prefers places around `MAP_START` without being bounded to
them. It answers with an outcome and its own codes (`place_query_invalid`, `place_not_found`,
`geocoder_unreachable`), and logs a failure by kind, never with the address. A geocoder for
production traffic is a deploy-time item, as the tiles' provider is.

**A render reads the configuration per request, never at build time.** A page that reads the
configuration and nothing else about the request — no cookie, no header — is one Next prerenders
when it builds, and the build's values are frozen into its HTML. `mapSettings()` awaits
`connection()` before it reads, so a page that draws the map renders per request: a site built by
the suite and started with a real `.env.local` once drew a blank sign-up map, every tile sent to
the stub's port. Anything else a render reads from the configuration takes the same step.

## 7. The test seam

**A real browser in front, a stand-in backend behind**, and nothing in between replaced
(ADR-0187 §6). `pnpm test` builds the site and starts it on port 3100 with a configuration made
for the suite. Each Playwright worker starts the **stub backend** on port 4010, where `API_URL`
points.

- The stub answers each operation with a handler whose reply the compiler checks against that
  operation's declared responses in the generated contract. It also accepts the envelope-bearing
  statuses the backend sends without declaring per route (a `401`, a `5xx`), and `drop`, which
  closes the connection unanswered. It records every request, it serves the map's tiles and
  answers the address search (`stub.places`, `stub.geocoderStatus`, `stub.searches`), and it
  serves **Stripe's hosted pages**: a link the fake club hands out points at the stub, so _Connect with
  Stripe_ and `/payments/continue` really redirect there (Playwright's `page.route` never sees a
  redirect's target), the page offers Stripe's way back to Overview, and `stub.stripePages` lists
  what the browser opened.
  An operation is named by its path as the contract writes it,
  `/api/v1/club/administrators/{administrator_id}`, and its handler and `stub.requests` read
  the ids in `params`.
- **The fake club** installs the default handlers: one club, whose tokens rotate, whose spent
  refresh tokens are refused, whose reset signs every session out, whose administrators keep
  ADR-0184's rules, and whose official groups are run only by an active administrator, so a
  removal leaves them needing one until a handover, and each keeps its queue of join requests,
  which the club answers whoever runs it. Its Raketa offer, `club.raketa`
  (`e2e/stub/courts.ts`), keeps #535's rules for courts, hours, exceptions, prices and settings
  and reads the setup checklist off them; it starts with nothing set, and `club.raketa.ready()`
  makes the club live. Its setup checklist has four steps, and its settings are the release
  lead, the cut-off, other clubs' courts and the pause: every club works Only Raketa (Q121). Its bookings, `club.bookings`
  (`e2e/stub/bookings.ts`), keep #547's, #637's and #669's rules: every game the club sees is
  booked (no club confirms one), each status folded from where the booking stands and the clock,
  as the backend folds it (booked or with a seat open, called off, played once its hour is over),
  and a booking still to be played holds its court for Courts & prices. Each booking keeps the
  cut-off it was booked with (a day before it unless the test says), which the read never sends:
  before it a booked game's shares are held and nothing is collected, after it they are taken; a
  cancel lets every hold go and refunds what was taken, and
  `club.bookings.passTheCutOff(game)` takes the held shares where a test needs the clock to pass
  it. Its money, `club.money` (`e2e/stub/money.ts`), answers a month's rows soonest first with
  their totals, deriving what is the club's on every read, _not yet known_ while a fee or a
  refund a row needs is `null` (#641), and its payouts newest first. A test seats its people in `club.administrators`, its groups in
  `club.groups` (`officialGroup(…)`, with `requests: [joinRequest(…)]` or just a
  `waiting_count`), its courts in `club.raketa.courts` (`court(…)`), its games
  with `club.bookings.add(booking(…))` and its money with `club.money.add(moneyRow(…))` and
  `club.money.payouts` (`payout(…)`), and a test about one reply overrides that operation; a handler reads the query string in
  `query`. Its tokens are unique across the run (`club.accessToken(n)`),
  because the single flight's grace window would hand one test the pair it renewed for another.
- **Tests assert what the desk or the backend would see**: text on the page, the URL, the
  cookie's attributes, and the requests that arrived at the stub. They never read the cookie's
  contents or a module's state.
- **One worker**, because the one server talks to the one stub, which each test resets.
- **Start-up refusal is tested at the process**: `e2e/config.spec.ts` spawns `next start` with a
  bad configuration and reads its exit code and output. It also starts the suite's build with a
  **different** tile URL and start point and reads them back off `/sign-up`, which is what
  catches a page that froze the build's configuration (§6).
- **Every page is checked at 360 px** for sideways scrolling.

No automated test crosses apps. The journey through the backend, the app and this site is a QA
plan walked by hand ([#528](https://github.com/Raketa02/Raketa/issues/528)).

## 8. Tokens and primitives

`src/ui/tokens.css` is the only file that writes a colour or a size. The colours were sampled
from the club mocks (`docs/specs/play-groups/mocks/club`, 1–4 and 14–16) and the sizes measured
from them on the four-point grid. The type is Archivo and IBM Plex Mono, self-hosted from
`@fontsource`, so a build fetches no font from the network. `pnpm test:tokens` fails on a
literal anywhere else, and ESLint refuses an inline `style`. A media query's width is the one
literal CSS allows no variable for.

Money is written by `src/ui/format.ts` as the player app writes a share: `140 zł`, `142,50 zł`
(the decimal comma, a space before the unit, and the grosze only when there are some), from the
wire's integer grosze and never through `Intl.NumberFormat` or `toFixed`
(`docs/value-formatting.md`, which left the rendering to the first client to draw a price). A
sum of five figures or more is set in threes with a no-break space, `12 840 zł`, as Polish sets
it, and a sum below nought takes U+2212, `−6 zł`: the Money page's totals and payouts are the
first to need either. A sum Stripe has not given yet (a card fee, a refund less the fee kept, and
the net that needs both) is the words _Not yet known_, from bookings' `knownZloty`, and never an
estimate (#641).

**A page works at every width, down to a phone with no sideways scrolling.** On a phone the top
bar becomes three rows: the wordmark and _Sign out_, the club, then the pages. Every table is
drawn by `src/ui/Table.module.css`: on a phone its rows become blocks, one cell under another,
and its column heads are left to a screen reader. A cell that would be a bare figure there
(Groups' _Players_, _From original group_ and _Games_, Money's sums) takes the table's `labelled` and
prints its column's name before it, for the eye only. Bookings' day and Money's month are one
`PeriodBar`, _‹ its name ›_ with a `PeriodPicker` box beside it.
