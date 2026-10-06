# ADR-0194 — The games test console acts as seed accounts, and writes history, never time

- **Status:** Accepted
- **Date:** 2026-10-06
- **Replaces the dev console's rules** (#256). They were never an ADR: they live in
  `backend/CONTEXT.md` (*Dev console*, *Console gate*), `backend/.claude/rules/surfaces.md` and
  `app/api/dev/`'s docstrings. Three are **reversed** here:
  - *it acts as another player only by signing in as them*: it now acts as a seed account without
    signing in (§2);
  - *the seed-account test is a filter, never a refusal*: it is now a refusal (§2);
  - *it declines the `app/seeds/` import*: situations are built from the seed's building blocks
    (§4).

  **Three are kept**: a second per-environment table that is never `SEEDABLE`, the refusal at the
  top of the routes module, and one page with no build and no timer that acts (§1, §6). The
  per-environment table is **narrowed to `local`** (§1).
- **Extends [ADR-0187](0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §5's** dev surface. It still has **no client**, and it gains a path for every action, situation and
  job (§7).
- **Extends [ADR-0029](0029-seed-data-through-aggregates-never-in-production.md)** to situations:
  they go through the same use cases a request runs, on a backdated clock (§4).
- Decided in the 2026-10-05 grilling that removed Classic play (Q8, Q13–Q16, Q23–Q25), for PRD
  [#570](https://github.com/Raketa02/Raketa/issues/570). Settles
  [#589](https://github.com/Raketa02/Raketa/issues/589). Built by
  [#590](https://github.com/Raketa02/Raketa/issues/590)–[#594](https://github.com/Raketa02/Raketa/issues/594),
  after [#578](https://github.com/Raketa02/Raketa/issues/578) removes the old console.

## Context

Testing the new games by hand means **being several people at once**. Ania's group game fills when
Kuba, Zofia and Marek have said yes and hers is the last. Walking that by hand takes:

- four accounts on four phones, or signing out and in over and over;
- the club website open in another window, to accept a request;
- a card that declines. The local fake payment provider exists, but nothing lets a person steer it;
- real hours of waiting for a cut-off, the club's half hour or a book-by;
- three places to look for who was told what: the phones, the notices list, and the mail catcher.

The Games & Fill in QA plan costs an afternoon of setup per scenario.

**The dev console that exists drives only the removed loop.** It is one HTML page at `/dev`, one
roster route, and three views: roster, search as, answer as. Its rules were written for a tool that
should never be able to do anything a player couldn't. It signs in as one seed account at a time,
through the ordinary login and with the public seed password, so there is no impersonation path at
all. It holds the token in memory, shows the current identity large, and has *not one timer*, so
that nothing answers on its own. Every button but the roster drives code #569 deletes.

A console for the new games needs three things the old rules forbid or never covered:

1. **Many people on one screen.** A fill takes four people, and a rescue or a club answer adds a
   fifth party. One identity at a time, with a sign-in per switch, is the four-phone problem again.
2. **The club and the payment provider.** Neither is a player, so signing in through the player
   login can't reach them.
3. **Time.** A cut-off, a book-by and the club's answer window are real moments. Waiting for them is
   most of the afternoon.

Considered and rejected:

- **Keep signing in, and hold one token per row.** Four sign-ins per group, tokens to refresh, and
  still no way to be a club or a payment provider. It keeps the letter of *no impersonation path*
  while the page holds four people's credentials at once.
- **Move the server's clock**, globally or per game (*"pretend it's later"*). The phone reads the
  real clock, so the phone and the server would disagree about every countdown on screen, and every
  job would read a time no device shows. A per-game offset is a second clock the domain would have
  to consult everywhere it asks *now*.
- **Club settings in minutes**, so a cut-off can be five minutes away. Cut-offs and notice are whole
  hours for every club, and games start on the hour. A setting that exists for testing is a setting
  production carries for ever.
- **Serve it wherever the seed runs** (`local`, `development`, `staging`). The old console was
  harmless there: it was no stronger than the login route, which already accepts the public seed
  password. A console that acts without signing in is a door with no credential at all. On any
  shared host, anybody who reaches the address can be any seeded player, steer payments, and run
  jobs.

## Decision

### 1. It exists only in `local`

The **games test console** is the dev console rebuilt, on the same `dev` surface. #590 rewrites the
backend glossary's *Dev console* and *Console gate* entries for it, and defines its own words there:
*situation*, *Run it now*, the *acting* account.

The dev surface's per-environment table, `CONSOLE_SERVED`, serves it in **`local` only**:
`development`, `staging` and `production` are refused. It stays a **second table, never derived
from `SEEDABLE`**, and now the two answer differently: the seed still runs in three environments,
the console in one. That is the case two tables were kept for. The refusal stays at the top of the
routes module, where `create_app` can read the table in every environment without importing what
it refuses.

### 2. It acts only as seed accounts, without signing in, and shows who is acting on every row

A console route takes **the acting seed account** and runs that person's action under that identity.
There is no impersonation token, no session and no header that a player route would honour.

- **Only seed accounts.** The acting account must be one the seed created, addressed on the
  reserved `.example` TLD. Any other account is **refused**. The old console could treat this as a
  filter, because its only door was the ordinary login. Now the console's route is the door, so the
  check has to refuse.
- **Who is acting is shown on every row.** This replaces *one identity at a time*. The page shows
  many people at once, and every button sits on the row of the person it acts as, with their name
  and photo.
- **The club** acts as the Club account whose court it is. **The payment provider** is the
  in-process fake adapter, given controls: a player's card set to succeed, decline or ask for extra
  verification; a refund delivered; a recorded confirmation replayed, twice or out of order.

### 3. Every action runs the same use case as the player's or club's own route

A *Yes* on Kuba's row runs the use case Kuba's *Yes* runs, with the same inputs, **refusals
included**. A refusal comes back in the domain's own words, never softened or worked around.

- **No logic of its own.** A console route is wiring: it builds the command and calls the use case.
- **A route's work lives in its use case.** If a player or club route does something outside its
  use case, the console would skip it. That work moves into the use case, never into a copy.
- **A replayed confirmation** goes through the same webhook handling a real one does.

### 4. Situations write history, never time

A **situation** is a named builder that sets the stage for one mechanic in one press: *Needs Ania's
yes, Instant club*, *Empty seat at the cut-off*, and so on. **The server clock is never moved**, and
nothing the domain reads as *now* is ever offset.

- **Through the seed's building blocks, and the same use cases.** The cohort, clubs, groups,
  proposals, bookings, rescues, posts and payments are built as `make seed` builds them (ADR-0029).
  So a situation can never produce a state the app couldn't reach. The dev surface therefore imports
  the seed's building blocks, and its own refusal (§1) still runs first.
- **History is written on a backdated clock**, the seed's `FixedClock`. Something that happened
  earlier is recorded as having happened earlier, never by pretending it is later now.
- **A moment fixed to the hour lands on the next whole hour the rules allow.** That covers a cut-off
  and a book-by: games start on the hour, and clubs set these in whole hours. The console says when
  it fires, like *"fires at 15:00 · 40 min"*, and the tester waits.
- **A moment counted from an event is built minutes away by backdating the event.** That covers the
  club's answer window, results and the day close.
- **A situation obeys the rules.** Pressed twice, it can meet *games per week* or one game an hour.
  The answer is the domain's refusal, and a fresh store is `make down-v && make up && make seed`.

### 5. *Run it now* runs only work that is due

Each timed rule has a *Run it now*: the proposer, book-by expiry, the cut-off, the club's answer
timeout, the day close, and every other scheduled job the new games run.

- **It runs the job's own unit of work**, the code the scheduler runs, over what is due at the real
  *now*.
- **It never brings anything forward.** Work that isn't due stays untouched, so a press can do
  nothing the next scheduled tick wouldn't. A countdown on every pending moment tells the tester when
  a press will find something.

### 6. One page, no build, no token, and nothing that acts on its own

The page stays **one file with no build**: no npm, no bundler and no lint lane. It is served by the
dev surface beside its routes.

- **It stores no token anywhere**, because it holds none.
- **Nothing refreshes or acts on its own.** Every press refreshes what it changed, and a refresh
  button covers the rest. A countdown only redraws a number. This keeps the old console's *not one
  timer* where it matters: nothing answers, runs or fetches unless the tester presses.
- **A *Sent* pane per person** reads the in-app notices, the push the recording sender would have
  sent, and the outgoing mail queue, with each email linked into the local mail catcher.

### 7. The dev contract grows its routes, and still has no client

Every console route is on the dev surface and in `openapi.dev.json`. **Nothing generates types from
it**: the only caller is the one page. So it stays outside the client drift check, and contract
freshness covers it as it covers every document.

## Consequences

**Easier**

- **A QA scenario is a press, not an afternoon.** One laptop and the protagonist's phone are enough
  for a fill, a rescue, an On request answer, a declined card or a day close. QA plans can name a
  situation for their setup, instead of steps a person has to run by hand.
- **The phone and the server always agree what time it is**, because neither clock moves.
- **What a console press causes is what a player's press causes.** Each one runs the real use case,
  so a bug found through the console is a bug in the app, not in the console.
- **Running due work by hand needs no new rule.** It is the scheduler's code, called sooner.

**Harder**

- **There is now a way to act as somebody without their credential.** It is fenced by the table
  (`local` only), the refusal on import, and the seed-account refusal. If the table were ever
  wrong, the result would be a door anybody could walk through. The table's exhaustiveness check
  and the route tests that find it absent outside `local` are what stand behind that.
- **The dev surface stops being small.** The old one was a page, one roster route and one query, and
  it said that
  growing a second query meant it had become a product. Now it has a route per action, situation
  and job, and imports many contexts' use cases and the seed. The placement stands: nothing imports
  it, so deleting it changes nothing that ships. But it now takes real code review.
- **Every player and club action has a twin**, and the twins can drift. A console route that builds
  its command differently from the player's route makes a refusal disagree. The equivalence tests
  (the same outcome and the same refusals for each action) are the price, and work that sits in a
  route instead of its use case is now a bug.
- **The tester still waits for the hour.** A cut-off situation pressed at 14:20 fires at 15:00, or
  later if the rules need more notice. That is accepted, because the alternative is a clock that lies.
- **Situations pile up in the local store.** They write on top of the seed, so repeated presses fill
  weeks and hours, and the domain starts refusing. The fix is the reset, never a softer rule.
- **`development` and `staging` lose the console.** Neither runs today, so nobody loses anything
  now. The day one does, testing there means real phones or a new decision.
- **The page has no automated test**, as the old one had none. The routes are tested over HTTP. The
  page is walked by the tester, and a broken button is found by hand.
