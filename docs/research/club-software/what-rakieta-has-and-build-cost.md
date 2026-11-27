# What Rakieta has, and what becoming the club's booking software would cost

Research for the club-software grilling that follows the founder's decision of 2026-10-12: **Rakieta
becomes the club's whole booking software** — one calendar for the desk, the phone, walk-ins, season
bookings, players booking online and the Games deck — replacing tenis4U, Playmore and kluby.org
([#609 decisions](https://github.com/Raketa02/Raketa/issues/609#issuecomment-6120454776),
[#667](https://github.com/Raketa02/Raketa/issues/667)). For each of eighteen feature areas it says what
the code **has today** and what Rakieta's version would **cost**, so a product owner can weigh *Build
at launch / Build later / Leave out*.

**Companion to** [`integration.md`](integration.md), which holds the market (how tenis4U, Playmore,
Playtomic and the rest do each thing). Market facts below are carried from there and keep its dates.

**This file decides nothing.**

**Sources.** The working tree of `feat/RKTA-06_games_fill_in` at `c7aa8a73`, read as it stands
2026-10-12 (its uncommitted changes are the player app's attendance work, and touch none of the areas
below); the root glossary [`CONTEXT.md`](../../../CONTEXT.md); the specs in
[`docs/specs/games-and-fill-in/`](../../specs/games-and-fill-in/); the ADRs; the four emitted contract
documents (`backend/openapi.*.json`); and GitHub issues on `Raketa02/Raketa`. Nothing was run, built or
changed. Code paths are from the repository root; `:n` is a line.

**Kinds:** `[CODE]` what the code does · `[DOC]` what an ADR, spec or the glossary says · `[ISSUE]` a
GitHub issue · `[ABSENT]` looked for and not found, saying where. Lines marked *reading* are inferences,
**including every size**.

**Sizes**, at this repo's ticket grain (one ticket = one app's slice of one feature): **S** ≈ one
ticket, **M** ≈ 2–4, **L** ≈ 5–10, **XL** > 10.

## Read this first

- **What exists is a Rakieta-only slice of club software, not a calendar.** A club has courts, a weekly
  *allotment* of one-hour cells it hands Rakieta, exceptions, per-sport prices, a few settings, a day
  *list* of Rakieta bookings with Move and Cancel, and money for Rakieta shares with payouts. Nothing a
  desk makes itself — a guest, a phone call, a walk-in, a season slot — has anywhere to live.
- **Two assumptions sit under almost every area, and each is a prerequisite of its own.** (1) **A
  Booking is a filled proposal**: its id is the card's, and it cannot exist without a pool, two full
  sides, a per-seat share and a Game. (2) **Every court hour is exactly one hour on a 07:00–23:00
  hourly grid**: hardcoded in 15 backend module files, the club's grid and the phone, and guarded
  against double booking by a unique index on *(court, start)* that cannot see an overlap.
- **Club hours are the player's own Weekly hours type.** The club's Rakieta hours reuse
  `WeeklyHours` from the player profile, so the club's grid cannot get finer without the two being
  pulled apart.
- **The five prerequisites together** — court time that is not a filled proposal, court time of any
  length, a customer who is not a User, staff logins, money that is not a seat's share — come to
  about **20 tickets** before any calendar screen is drawn (*reading*).
- *Reading:* a desk-first launch (the desk calendar, the deck inside it, blocks, prices, customers,
  staff, and the prerequisites) is roughly **35–45 tickets**, plus production. For scale, the whole of
  Games & Fill in was cut into 34 tickets ([#531](https://github.com/Raketa02/Raketa/issues/531)–[#564](https://github.com/Raketa02/Raketa/issues/564)).
- **Cheapest:** migrating today's clubs (S — there are no real ones), blocks and closures (M),
  the deck inside one calendar (M, once the prerequisites exist), a per-booking fee to the club (M),
  reports (M).
- **Dearest:** coaches, lessons and classes (XL), leagues and tournaments (XL), the desk calendar
  itself (XL with its prerequisites), players booking a court directly (L), money at the desk with
  invoices and fiscal receipts (L), unmanned hours (L, with hardware), production (L, mostly human).
- **Rakieta has no revenue line, by decision.** ADR-0189 §4 says Rakieta takes no fee; the code charges
  none. Becoming the club's whole software adds production, support and on-call cost against that.
- **Only `local` has ever run.** No domain, a dormant deploy pipeline, no Stripe test account, no mail
  relay, no push credentials. A desk whose whole day runs on Rakieta stops when Rakieta does.
- **Sequencing:** [#668](https://github.com/Raketa02/Raketa/issues/668)–[#677](https://github.com/Raketa02/Raketa/issues/677)
  are all open. [#670](https://github.com/Raketa02/Raketa/issues/670) deletes the *minimum notice*
  (a book-by close to the start); a deck inside one calendar would likely want that rule back,
  because the desk then writes into the same calendar.

## The yardstick: what one ticket is here

- **[ISSUE]** [#535](https://github.com/Raketa02/Raketa/issues/535) built the whole Club courts
  aggregate — courts, hours, exceptions, prices, ways of working, settings, the sellable-hours port and
  the setup checklist — as **one backend ticket**. [#547](https://github.com/Raketa02/Raketa/issues/547)
  built the club's day list, Move, Cancel, check-in and the no-show report as one;
  [#563](https://github.com/Raketa02/Raketa/issues/563) the club's Bookings page as one;
  [#672](https://github.com/Raketa02/Raketa/issues/672) is one rule (a cancel absorbed by a free court).
- **[ISSUE]** The club side as it stands took **eight tickets**: backend #535, #537, #547, #548 and
  club website #561–#564.
- **[ISSUE]** One spec, [#667](https://github.com/Raketa02/Raketa/issues/667), is ten tickets: root 1,
  backend 5, club website 2, player app 2.
- **[ISSUE]** After #530's 34 build tickets, walking its stories raised **58 more agent tickets** under
  later PRDs and story findings ([#612](https://github.com/Raketa02/Raketa/issues/612)–[#677](https://github.com/Raketa02/Raketa/issues/677),
  less the PRDs, the stories and one human ticket).
  - *Reading:* every size below is a first build; on this record the story walk adds as much again.
- **[CODE]** Every registered job must have a console press, or `backend/tests/api/test_games_test_console_time.py`
  fails; every port has a fake held to a demand suite (`backend/tests/demands/`, ADR-0190 §1).
  - *Reading:* so a new third-party integration is never S: a port, a real adapter, a fake, its demands,
    and usually a press.

## The cross-cutting prerequisites

### P1. Court time that is not a filled proposal — M (≈4)

- **[DOC]** *"A booking is the game a full card became, and its id is the card's"*; a Booking is *"a
  filled proposal"* (`CONTEXT.md:1527-1536`); `_Avoid_: reservation`.
- **[CODE]** `Booking` requires a `pool_id`, a `kind`, a `share_grosze` and two sides
  (`backend/app/modules/bookings/domain/booking.py:198-208`); `Booking.confirmed` checks every side is
  full and takes the `game_id` it opens (`booking.py:263-300`).
- **[CODE]** The projection makes `pool_id` and `share_grosze` `NOT NULL`
  (`backend/app/modules/bookings/infrastructure/booking_models.py:65,70`); the court's price is read back
  as share × seats (`backend/app/modules/proposals/domain/club_bookings.py:124-127`).
- **[CODE]** The club's bookings routes are **signed by Proposals**, *"because the answer is the
  fill's"* (`backend/app/modules/proposals/presentation/club_routes.py:1-16`).
- **[CODE]** What a club can no longer sell is `CourtBookings.taken`, read from the bookings table
  (`backend/app/modules/bookings/infrastructure/club_courts.py`; `event_sourced_booking_repository.py:341-358`).
- **Cost** (*reading*): a new event-sourced aggregate that owns a stretch of court time — the glossary
  has to name it, since *Booking* is taken and *reservation* is avoided — with Rakieta's Booking becoming
  one kind of occupant. The occupancy read becomes the union of all occupants, and the club's day read
  follows. Root 1 (ADR, glossary), backend 3. New streams and tables, through a migration; re-keying
  Rakieta bookings onto it means a local store reset (the precedent is #667's *clean cut*). Contract:
  the club document.

### P2. Court time of any length, on a finer grid — M (≈4), L if Rakieta games change length too

- **[DOC]** *"Every game is one hour"* (ADR-0189 §3, `docs/adr/0189-…md:109`; glossary *Court hour*,
  `CONTEXT.md:1343`). Rakieta hours are *"seven days by sixteen one-hour cells from 07:00 to 23:00"*
  (`CONTEXT.md:1327-1330`); *"a club whose own grid runs in 90-minute slots publishes 1-hour slots for
  Rakieta"* (the mechanics §16.5, line 1155-1157).
- **[CODE]** The club's hours are the **player's** type: `WeeklyHours` imported from
  `player_profile` (`backend/app/modules/clubs/domain/courts.py:26`, `club_courts.py:60`), whose cells
  start 07–22 (`backend/app/modules/player_profile/domain/weekly_hours.py:91,95`). The club day is
  07:00–23:00 (`backend/app/modules/clubs/domain/court_hours.py:39-40`); sellable hours walk those cells
  (`backend/app/modules/clubs/domain/sellable.py:124`); exceptions and price bands are whole hours inside
  the day (`hours_exceptions.py`'s `ClosedHours`, `prices.py`'s `within_the_day`).
- **[CODE]** One hour is a constant under five names (`GAME_LENGTH`, `_A_GAME`, `A_BOOKED_GAME`,
  `_AN_HOUR`, `whole_hours(1)`) in 15 backend module files: `bookings/application/request_emails.py`,
  `bookings/infrastructure/club_courts.py`, `clubs/application/club_courts.py`, `clubs/domain/sellable.py`,
  `games/domain/windows.py`, `payments/application/seat_charge_emails.py`,
  `player_profile/domain/weekly_hours.py`, `proposals/application/propose_games.py`,
  `proposals/domain/club_bookings.py`, `deck.py`, `home.py`, `proposer.py`,
  `proposals/infrastructure/club_court_hours.py`, `proposals/presentation/club_routes.py`, `schemas.py` —
  plus the seed and the console. The phone has `GAME_LENGTH_MS = 3_600_000`
  (`frontend_player/src/features/proposals/domain/when.ts:28`); the club's grid is 7 to 23
  (`frontend_club/src/features/courts/mappers.ts:25-26`).
- **[CODE]** **The double-booking guard assumes aligned hours.** A unique index on *(court_id, start)*
  over bookings not called off (`booking_models.py:46-52`) turns a second claim into `CourtTaken`
  (`event_sourced_booking_repository.py:114-116`); the taken read asks `start >= window start`
  (`:346`), so a booking that began earlier is not seen.
  - *Reading:* a 17:30–19:00 desk booking would collide with neither an 18:00 game's index row nor the
    read.
- **[CODE]** The test suite runs on in-memory SQLite (`backend/tests/conftest.py:10,70-73`) while
  `local` runs Postgres (`docs/environments.md:17`).
  - *Reading:* a Postgres-only overlap constraint would never be exercised by the tests. A ledger with
    one row per court per 15- or 30-minute cell under a unique index works on both.
- **[CODE]** Dormant: the sport registry already lists durations — padel 60/90/120, tennis 60/90,
  squash 45/60/90, badminton 60/90 (`backend/app/kernel/sports.py:46-49`), served by `/sports`. Nothing
  that books reads them.
- **Cost** (*reading*): **keep Rakieta games one hour** and make only the calendar minute-based:
  occupancy, opening hours, blocks and desk bookings, with the club's hours pulled apart from the
  player's `WeeklyHours`. Root 1, backend 2, club website 1 → M. Making Rakieta's own games 90 minutes as
  well is L: Games' windows (the attendance tap window is *"the first half of a one-hour game"*,
  `games/domain/windows.py:55-60`), the deck's *one game per hour*, the emails, the player's
  Weekly-hours grid and the phone. `RakietaHoursSet` stores hour codes, so either an upcaster or a
  store reset.

### P3. A customer who is not a User — M (≈3)

- **[DOC]** The club sees *"each player's **name**, and whether their share is **held** or
  **taken**. No email, no phone, no level, no record, no attendance and no score … The club cannot
  message players"* (the mechanics §16.14, lines 1329-1332).
- **[CODE]** The club's booking row carries `player_id, name, paid, held` and nothing else
  (`ClubBookingPlayerSchema`, `backend/openapi.club.json`).
- **[CODE]** A User has an email, a password, a name and a nickname, and **no phone**
  (`backend/app/modules/users/domain/user.py:46-59`).
- **[ABSENT]** Any person the club holds itself — a guest, a regular, a note, a ban — in
  `backend/app/modules/` and `frontend_club/src/features/`.
- **Cost** (*reading*): a club-scoped aggregate (name, phone, email, notes, and an optional link to a
  User the person consents to), searchable from the desk. Root 1 (an ADR amending §16.14, and the club
  as data controller — tenis4U's privacy terms say so of its clubs, [`integration.md`](integration.md)
  §5), backend 1–2, club website 1.

### P4. Staff identities and roles — M (≈4)

- **[DOC]** The Club account is *"one email and one password, shared by the desk"* (`CONTEXT.md:1307-1311`;
  ADR-0182 §3); *"Separate staff logins (desk staff, managers) come later"* (the mechanics §16.14,
  line 1327).
- **[CODE]** `ClubAccount` holds an id, the club, one email and one password hash
  (`backend/app/modules/clubs/domain/club_account.py`).
- **[DOC]** Administrators are Users who run Official groups **in the player app** and *"never see
  bookings, money or court settings"* (the mechanics §16.13; `CONTEXT.md:1474-1487`).
- **Cost** (*reading*): a staff member per (club, email) with a role (desk, manager, later coach or
  maintenance), invited with the one-time credentials Administrators already use (ADR-0184); the club
  token carrying the person and the role; every club route asking the role; events recording who
  acted. Root 1 (amending ADR-0182 §3), backend 2, club website 1.

### P5. Money that is not a seat's share — M to L (≈5)

- **[CODE]** A Seat charge is one player's share of one booking: `player_id`, `game_id`, `club_id`,
  `amount_grosze`, `starts_at` (`backend/app/modules/payments/domain/seat_charge.py:205-241`).
- **[CODE]** Payouts are decided per club per closed day, game by game, from the Seat charges' net
  (`backend/app/modules/payments/domain/club_payout.py:1-30`).
- **[DOC]** *"The club never refunds anybody by hand"* (the mechanics §16.11, line 1281); receipts and
  invoices are open item O5 (§21, line 1601).
- **[ABSENT]** A whole-court charge, a payment recorded at the desk (cash, card terminal), a payment
  link, a refund by hand — in `backend/app/modules/payments/` and the club document's 36 paths.
- **Cost** (*reading*): a charge for a stretch of court time — the whole price by one payer, or split
  among named payers; a desk payment recorded where no money moves through Rakieta; a refund by hand;
  payouts and the Money page over all of it. Backend 3, club website 1–2. Stripe stays behind the
  port (ADR-0190); a payment link would be a new port call.

### P6. Production — L, mostly human

See area 17.

## The areas

### Root — revenue and billing to the club

**Exists today**
- **[DOC]** *"Rakieta takes no fee and pays none"* (ADR-0189 §4, `docs/adr/0189-…md:116`); out of
  scope: *"Any Rakieta revenue: no fee, no subscription"*, Playtomic's player fee read as Rakieta's
  advantage (the mechanics §20, line 1569); [#667](https://github.com/Raketa02/Raketa/issues/667)
  repeats it under *Out of Scope*.
- **[CODE]** Charges are direct charges on the club's account, which pays Stripe's fees while Stripe
  covers losses — `fees_collector: stripe`, `losses_collector: stripe`
  (`backend/app/modules/payments/infrastructure/stripe_payments.py:331-334`).
- **[ABSENT]** An application fee, a plan, a subscription or an invoice to a club, in `backend/app/`
  and `frontend_club/src/`.
- **[DOC]** What rivals charge: tenis4U 49–149 zł a month; Playmore from 299 zł and 1.79 % of online
  payments; kluby.org 50–79 zł and 2 % ([`integration.md`](integration.md) §4).
- **Assumption it breaks:** Rakieta takes no fee.

**Cost to build** (*reading*)
- **A fee on each online payment** — backend and club website, M (≈3): an ADR amending ADR-0189 §4 and
  ADR-0190; the port's charge carries the fee; a Seat charge's net and the payouts subtract it; Money
  shows it. Whether Stripe takes an application fee on accounts set up this way is unverified (Gaps).
- **A monthly subscription** — backend and club website, M (≈3–4): a billing record per club, a billing
  integration (not researched), a billing page, and Rakieta's own VAT invoices to its clubs.
- No migration. The club document grows; the player document doesn't.

**What it changes in the player app**
- Nothing, unless players pay a service fee — which the spec counts as Rakieta's advantage not to.

### 1. The desk calendar

**Exists today**
- **[CODE]** The club's **Bookings** is one day at a time, a *table* of Rakieta bookings only: an empty
  day reads *"No Rakieta bookings on this day."* (`frontend_club/src/features/bookings/copy.ts:107`,
  `components/BookingsTable.tsx`), read by `GET /api/v1/club/bookings`
  (`backend/app/modules/proposals/application/club_bookings.py`).
- **[CODE]** **Move** goes to another free court of the sport at the same hour; **Cancel** takes a
  reason (weather, repair, double booking, other); neither once the game has started
  (`club_bookings.py:1-25`; `CancelReason`, `booking.py`).
- **[CODE]** The only live refresh is the requests badge, re-read every 30 seconds
  (`frontend_club/src/features/bookings/components/RequestsWatch.tsx:9`).
- **[ABSENT]** A court × time grid, a week view, a booking the desk makes (guest, phone, walk-in),
  payment at the desk, a move to another hour, a refund by hand, any length but one hour — in
  `frontend_club/src/features/` and the club document's 36 paths.
- **Assumptions it breaks:** a Booking is a filled proposal (P1); one aligned hour (P2); the club sees
  only names (P3); one shared login, so nobody is *who booked it* (P4); refunds are automatic only (P5).

**Cost to build** (*reading*)
- Apps: backend, club website.
- On top of P1, P2, P3 and P5:
  - backend 2 — desk acts (book for a customer or a typed name, any length, the table's price or a typed
    one, paid at the desk, unpaid, or by link; move to any free court and time; cancel with or without
    a refund) and a calendar read (every occupant of a day or a week, per court);
  - club website 3 — the grid, by day per court and by week per court, a new interactive component
    under the token rule; the booking dialog with customer search; move, cancel and payment marking;
    a live re-read, with the 30-second watch as the precedent;
  - root 1.
- **L (≈6)**; with its prerequisites **XL (≈15–20)**. New tables through a migration; the club
  document grows a calendar family.

**What it changes in the player app**
- Nothing is required. A desk's Move or Cancel of a Rakieta game is told as *Game moved* or a cancel
  notice ([#677](https://github.com/Raketa02/Raketa/issues/677), open).

### 2. Players booking a court directly, in the app and without it

**Exists today**
- **[CODE]** **Post a game**: a member picks the hour and court on a posting grid and slot sheet
  (`frontend_player/src/features/proposals/components/PostAGameScreen.tsx`, `PostingGrid.tsx`,
  `SlotSheet.tsx`). It books only when every seat says yes (`CONTEXT.md:1755-1758`), and a player may
  have two live (`backend/app/modules/proposals/domain/limits.py:27`).
- **[DOC]** A yes means *"if everybody is in, book it"* (`CONTEXT.md:1736-1740`). The player's limits
  are their own **Games & money** — 1–7 games a week, *Most I'll pay* (`CONTEXT.md:1812-1816`); the deck
  looks 14 days ahead (`backend/app/modules/proposals/domain/deck.py:71`).
- **[CODE]** *Play › Explore* is an empty screen (`frontend_player/src/features/find_a_game_next/types.ts`).
- **[ABSENT]** A club page with its free courts in the player app (`frontend_player/src/app/`).
- **[DOC] [CODE]** The public site serves a group link, an invitation, a password reset and the
  app-link files, with **no sign-in and no session** (`CONTEXT-MAP.md`; `frontend_public/src/app/`;
  five paths in `backend/openapi.public.json`).
- **[ABSENT]** Booking a whole court, splitting it with named friends, a link or widget for a club's own
  website, and a club's days-ahead or active-bookings-per-player limits.
- **[DOC]** tenis4U lets a club set days ahead, a limit of active bookings per user and a minimum
  length of 30 or 60 minutes ([`integration.md`](integration.md) §5).
- **Assumptions it breaks:** a game is made only by filling; the share is the price divided by the
  seats; a Booking has a pool and sides (P1); the public site holds no session.

**Cost to build** (*reading*)
- Apps: backend, player app, public site, club website.
  - backend 2–3 — one player books the whole court on their card, or splits it with friends who claim
    their share by link; the club's limits; leaving under the cut-off;
  - player app 3 — a club page with free courts by day and length; the booking and payment flow; a
    court booking's row on Home and its details; the split invitation;
  - club website 1 — the limits in its settings;
  - public site 1 — a club's free-hours page with *Open in Rakieta*. Booking there **without the app**
    is 2 more: a customer who is not a User (P3), a payment with no saved card, and an ADR reversing
    *no session* (ADR-0187);
  - root 1.
- **L (≈8–10)**, on P1, P2 and P5. Contract changes on the player, club and public documents.
- Open question: whether a direct booking with named Rakieta players opens a Game, and so feeds results
  and Levels.

**What it changes in the player app**
- New: a club page (Explore is the empty slot for it), *Book a court*, the split invitation, a court
  booking on Home and its details, and its receipt in You › Payments.

### 3. The Games deck inside one calendar

**Exists today**
- **[CODE]** **Sellable court hours** are the Rakieta hours, less exceptions, less what bookings hold,
  less every hour past its book-by, for a live club only, each priced by its band
  (`backend/app/modules/clubs/domain/sellable.py:1-20,87,124`), published through the
  `SellableCourtHours` port (`backend/app/modules/clubs/domain/ports.py:278`).
- **[CODE]** Book-by is the start less the release lead at an Only Rakieta club, or less the minimum
  notice otherwise (`backend/app/modules/clubs/domain/rakieta_terms.py:109-123`); the lead is 1–13 days
  (`:43`).
- **[ISSUE]** [#670](https://github.com/Raketa02/Raketa/issues/670) (open) keeps only the release
  lead, and [#667](https://github.com/Raketa02/Raketa/issues/667) records the consequence: *"No Rakieta
  game can fill later than a day before its start"*.
- **[CODE]** A yes holds no court. The court is the first free one of the sport, picked at the fill
  (`backend/app/modules/bookings/infrastructure/club_courts.py`). Of two cards filling at once, the
  second meets `CourtJustTaken` and the yes is tried once more
  (`backend/app/modules/proposals/application/answers.py:434-441`).
- **[CODE]** When the last court at an hour goes, its cards lose it — *"Its court went to another game
  before it filled again"* (`backend/app/modules/notifications/application/words.py:447`). The proposer
  sweeps every 300 s, and re-deals pools a change made due every 5 s (`backend/app/core/config.py:548-550`).
- **Assumptions it breaks:** Rakieta hours are an **allotment** the club hands over; a book-by at least a
  day ahead; only Rakieta bookings take a court.

**Cost to build** (*reading*)
- Apps: backend, club website; the player app hardly.
  - backend 2 — sellable hours read from the calendar's free time under the club's rules for the deck
    (which courts and hours, and until how long before the start); a book-by from a notice again —
    Instant's minimum notice, now safe because the desk writes into the same calendar; desk bookings
    making pools due; the race between a desk booking and a fill guarded by P2's ledger;
  - club website 1 — the deck's rules in settings;
  - root 1.
- **M (≈4)**, on P1 and P2. The store may need resetting if the release lead's meaning changes.
- Product question: should a card with most seats In hold its court against the desk? Playtomic
  reserves an open match's court in stages, *"4 players: Court always reserved"*
  ([`integration.md`](integration.md) §1).

**What it changes in the player app**
- Cards lose their court more often as the desk sells hours. If the book-by moves close to the start,
  last-minute cards come back, stamped *No free cancellation* (the mechanics §5.4).

### 4. Season and fixed weekly bookings

**Exists today**
- **[ABSENT]** A recurring booking, a series or a fixed weekly slot, in `backend/app/modules/` and
  `frontend_club/src/`. The word *season* appears only in the player record's prose.
- **[ISSUE]** Named out of scope by #667: *"season bookings"*.
- **[DOC]** tenis4U adds fixed slots *"wraz z monitorowaniem godzin wykorzystanych i odrobionych"* —
  with the hours used and made up tracked ([`integration.md`](integration.md) §5).
- **Assumption it breaks:** a Booking is a filled proposal (P1).

**Cost to build** (*reading*)
- Apps: backend, club website.
  - backend 2 — a series (court, weekday, time, length, first and last date, customer, a price per
    occurrence or per season) that lays its occurrences into the calendar, is refused over a clash,
    skips closures, can cancel one occurrence or the rest, and counts made-up hours;
  - club website 1–2;
  - root 1.
- **M–L (≈4–5)**, on P1, P2 and P3; paid at the desk or by invoice (P5, area 11). The deck needs nothing:
  a season hour simply isn't free.

**What it changes in the player app**
- Nothing at first. Later, perhaps, *your fixed slot* for a customer linked to a User.

### 5. Blocks and closures

**Exists today**
- **[DOC] [CODE]** **Exceptions** close a day, a run of days or hours on them, on every court or some,
  with a reason only the club reads (`CONTEXT.md:1331-1335`;
  `backend/app/modules/clubs/domain/hours_exceptions.py`). One over a booking is refused with
  `court_booked_then` (`backend/app/modules/clubs/domain/errors.py:238`); cards on the hour move or
  disappear.
- **[CODE]** A court can be switched off, and is not deleted while a booking is ahead of it
  (`court_has_bookings`, `errors.py:164`). A club can be **Paused** (`CONTEXT.md:1372-1374`).
- **[ISSUE]** A club's cancel moving the game to a free court ([#672](https://github.com/Raketa02/Raketa/issues/672)),
  and Move keeping the court's kind ([#671](https://github.com/Raketa02/Raketa/issues/671)), are open.
- **[ABSENT]** Weekly recurring blocks, blocks to the minute, a block drawn on a calendar, an
  out-of-order-now flag, and courts that share a floor.
- **[DOC]** tenis4U has weekly recurring blocks, *"Blokada wzajemna"*, closed dates and *"Ustawić status
  zalany?"* ([`integration.md`](integration.md) §5).
- **Assumptions it breaks:** whole hours from 07:00 to 23:00; only Rakieta bookings stand in a block's
  way.

**Cost to build** (*reading*)
- Apps: backend 1 — an exception becomes a calendar block with minutes and a weekly repeat, refused over
  any occupant; club website 1 — draw it on the calendar.
- **M (≈2)** once P1 and P2 exist.

**What it changes in the player app**
- Nothing beyond #677's move and cancel notices.

### 6. Prices

**Exists today**
- **[DOC] [CODE]** Per sport: a standard price and optional bands — **weekdays or the weekend**,
  between two whole hours — from 10 to 1 000 zł, refused unless it **splits into whole grosze** among the
  sport's seats (`CONTEXT.md:1336-1340`; `backend/app/modules/clubs/domain/prices.py:44-48,133`). A new
  price reaches new cards only; the share is fixed on the card (`CONTEXT.md:1341-1342`).
- **[ISSUE]** #667's call 2: *"Price is per club per sport today"*.
- **[ABSENT]** Prices per court, per length, per day of the week (a Friday price), member prices, desk
  versus online prices, passes, a prepaid wallet, discounts.
- **Assumptions it breaks:** a price splits by seats; a booking's price is share × seats
  (`club_bookings.py:124-127`); bands know only weekdays and the weekend.

**Cost to build** (*reading*)
- **Per court, per length, per day, desk versus online** — backend 1, club website 1 → **M (≈2–3)**.
- **Member prices** — add 1–2, on P3 and a membership.
- **Passes and a wallet** — money held on the club's account and spent across bookings, refunded, and
  accounted for: backend 2, club website 1, player app 1, and a lawyer → **L (≈5+)**.

**What it changes in the player app**
- The price shown is the one that applies to that player and length. Passes and a balance live in
  You › Payments.

### 7. The club's customers without Rakieta accounts: notes, bans, no-shows

**Exists today**
- **[DOC] [CODE]** Names and held or taken, and nothing else (P3).
- **[DOC]** Whether somebody came is caught at the court and **never shown to the club** (ADR-0195;
  the mechanics §16.7 table, *"Nothing about who came or the score (Q115, Q116)"*).
- **[DOC]** A Block is between two players, never a club's (ADR-0193; `CONTEXT.md` *Blocks*).
- **[ABSENT]** A customer list, notes, bans and desk no-show marks, in the club document and
  `frontend_club/src/features/`.
- **Assumption it breaks:** the club sees only a player's name (§16.14).

**Cost to build** (*reading*)
- Apps: backend, club website; the player app for consent.
- P3, plus backend 1 and club website 1: notes; a ban, which refuses online booking at that club (and
  perhaps its deck — a product question); a no-show mark on a desk booking.
- **M (≈4–5 with P3)**, and an ADR, because it reverses §16.14's privacy rule.

**What it changes in the player app**
- Consent to share contact details with a club. A ban hides that club from the player's booking flow.

### 8. Coaches, lessons and classes

**Exists today**
- **[ABSENT]** Any coach, lesson or class in all four apps. *Coach* appears only in seed copy and test
  fixtures (`backend/app/seeds/cohort.py:885`; *"Coach Andrzej"* in player-app tests).
- **[DOC]** tenis4U: *"Zarządzanie trenerami klubowi i ich zajęciami"* ([`integration.md`](integration.md) §5).
- **Assumption it breaks:** only players and one club login exist (P4).

**Cost to build** (*reading*)
- Apps: all four. Coaches as staff (P4); their availability; lessons (a coach, a court, one or more
  students); classes with places and a waiting list; recurring terms; payment per participant and
  passes; the player app's booking of lessons and classes and their rows on Home.
- **XL (> 10).**

**What it changes in the player app**
- New: lessons and classes to find and book, a coach's page, and lesson rows on Home.

### 9. Leagues and tournaments

**Exists today**
- **[ABSENT]** In every app. *Tournament* is only a closure's reason
  (`backend/app/modules/clubs/domain/hours_exceptions.py:2-11`); *leagues* appear only as a
  questionnaire answer (`backend/app/engines/racketskill/v3/questions.py:215-216`).
- **Assumption it breaks:** a Game is opened only by a booking (`CONTEXT.md` *Proposals*, and ADR-0189's
  2026-10-06 note).

**Cost to build** (*reading*)
- Apps: all four. Competitions, draws or round robins, fixtures laid into the calendar, results feeding
  Levels, standings, entry fees.
- **XL.**

**What it changes in the player app**
- New: competitions, fixtures and standings.

### 10. Benefit cards

**Exists today**
- **[ABSENT]** MultiSport, Medicover or any benefit card in all four apps; a User has no phone number
  (`user.py:46-59`).
- **[DOC]** MultiSport has no booking integration, and the desk counts cards. Medicover Sport runs an API
  keyed on the phone; connecting needs a facility token, a Merchant ID and *"Oficjalna zgoda na
  integrację"*. Kraków clubs take about 15 zł off a card ([`integration.md`](integration.md) §4).
- **Assumption it breaks:** every booking is paid by card, through Stripe.

**Cost to build** (*reading*)
- **Recorded by hand** — the desk records the cards brought and their discount; a player declares
  cards when booking: backend 1, club website 1, player app 1 → **M (≈3)**.
- **Medicover's API** — a port, an adapter, a fake and its demands, a phone number on the player, and
  a contract per club → **L (+2–3)**.

**What it changes in the player app**
- Adding a benefit card under You › Payments, and choosing it when booking.

### 11. Money

**Exists today**
- **[CODE] [DOC]** One payments port with a Stripe adapter and a fake (ADR-0190 §1;
  `backend/app/modules/payments/domain/provider.py`). Direct charges on the club's account: the club is
  the seller (`CONTEXT.md:1612-1613`).
- **[CODE] [DOC]** A share is checked, held, taken at the cut-off, released, refunded by an exact
  amount, or refused, with time to fix the card or time to pay (`CONTEXT.md:1614-1655`).
- **[CODE]** Payouts are released by Rakieta after each club day closes
  (`backend/app/modules/payments/domain/club_payout.py`). The Money page shows a month: collected,
  refunded, card fees, net, totals and payouts, with a link to the club's Stripe dashboard
  (`backend/app/modules/proposals/application/club_money.py`; the screens B7).
- **[CODE] [DOC]** The fake is the default (`backend/app/core/config.py:401`); *"Until then,
  everything runs on the fake payments adapter"* (O7, the mechanics §21); the Stripe test account is
  [#533](https://github.com/Raketa02/Raketa/issues/533), open.
- **[DOC]** BLIK waits (O1); receipts and invoices are the club's, and open (O5).
- **[ABSENT]** Desk sales, payment links, refunds by hand, whole-court charges (P5), invoices and any
  fiscal printer.
- **Assumption it breaks:** money is a seat's share of a Rakieta booking.

**Cost to build** (*reading*)
- P5 (M–L), plus:
  - invoices — backend 1–2 behind a new port to an invoicing service, and club website 1;
  - fiscal receipts for desk and online sales — unknown until a lawyer or accountant answers O5;
    possibly hardware.
- **L.**

**What it changes in the player app**
- Receipts for court bookings, asking for an invoice with company details, and BLIK when O1 is
  answered.

### 12. Unmanned hours: door codes and lights

**Exists today**
- **[ABSENT]** Door codes, lights, relays, locks or any device, in all four apps.
- **[DOC]** tenis4U sells a 2 500 zł controller over a SIM or modem, and its panel drives Shelly relays
  and TTLock locks ([`integration.md`](integration.md) §5).
- **Assumption it breaks:** none in code; it is all new.

**Cost to build** (*reading*)
- Apps: backend, club website, player app, plus hardware.
  - a device port and adapters: lights on for what is booked, a door code per booking; a fake with its
    demands; a console press for the job;
  - the club's setup page;
  - the code on the booked game's details;
  - a field test with real hardware, bought per club (a human step).
- **L (≈5+).**

**What it changes in the player app**
- The door code on the booking's details, and in the booking's notice.

### 13. Staff roles and per-person logins

**Exists today**
- One shared club login; Administrators touch no bookings (P4).
- **Assumption it breaks:** one login per club.

**Cost to build** (*reading*)
- P4: **M (≈4)** — backend and club website. The club website already hosts its own reset page
  (`frontend_club/src/app/(signed-out)/reset/`), so staff invitations need not touch the public site.

**What it changes in the player app**
- Nothing. Whether a coach is a User with a staff role is a later design question.

### 14. Telling players

**Exists today**
- **[DOC] [CODE]** **Notices**: a banner while the app is open, the bell's list of the newest 30, and
  an email *"when it is about money or the club's answer"* (`CONTEXT.md:1830-1839`;
  `backend/app/modules/notifications/`).
- **[CODE]** Email goes through an SMTP port and a purged queue (ADR-0186); locally into Mailpit
  (`docs/environments.md` *Email in `local`*). A production relay — with SPF, DKIM, DMARC and bounces,
  *"none of which exists today"* — is unchosen (`docs/environments.md:456`).
- **[CODE]** Push is built and gated off: `EXPO_PROJECT_ID = null`, `IPHONE_PUSH = false`
  (`frontend_player/src/shared/config/push.ts:23-25`). Its setup is
  [#665](https://github.com/Raketa02/Raketa/issues/665) (a human's) and
  [#666](https://github.com/Raketa02/Raketa/issues/666), both open.
- **[DOC]** The club is emailed a daily summary, the cut-off's call-offs and its payouts (the mechanics
  §16.12; the screens B9), and *"cannot message players"* (§16.14).
- **[ABSENT]** SMS, in all four apps.
- **Assumptions it breaks:** the club never messages players; everybody told has the app.

**Cost to build** (*reading*)
- Apps: backend, club website, player app.
  - an SMS port and adapter — backend 1–2; tenis4U names SMSAPI among its processors
    ([`integration.md`](integration.md) §5);
  - confirmations to customers without the app, by email or SMS — backend 1;
  - a club's message to its players — backend 1, club website 1, and an ADR amending §16.14;
  - push switched on — #665 and #666, already written.
- **M (≈4)**, plus the existing push tickets.

**What it changes in the player app**
- Push on (#666), and new notice kinds for court bookings, door codes and lessons as those land.

### 15. Reports

**Exists today**
- **[DOC]** Overview shows the setup checklist, then what waits for an answer; *"The statistics that will
  live here later are out of scope"* (the mechanics §16.1, line 1100). #674 (open) replaces the waiting
  list with *live* and a link to today's bookings.
- **[CODE]** Money is a month of Rakieta bookings, with totals and payouts
  (`frontend_club/src/features/money/`); Groups shows each official group's Games figure (the screens B8).
- **[ABSENT]** Occupancy, revenue by court or hour, customers, cancellations, and any CSV export, in
  `frontend_club/src/features/` and the club document.
- **[DOC]** tenis4U's panel offers *"Pobierz jako CSV"* ([`integration.md`](integration.md) §5).
- **Assumption it breaks:** statistics are out of scope.

**Cost to build** (*reading*)
- Apps: backend 1–2 (read models over the calendar and the money), club website 1–2 (pages and a CSV
  export).
- **M (≈3).**

**What it changes in the player app**
- Nothing.

### 16. Moving in

**Exists today**
- **[ABSENT]** An import path: none of the club document's 36 paths takes a file or a batch.
- **[DOC]** The seed builds through aggregates and never runs in production (ADR-0029); the games test
  console exists only in `local` (ADR-0194 §1). Both are test tools, not a way in.
- **[DOC]** tenis4U exports CSV. Playmore moves a Reservise club's *"rezerwacje, bazę klientów, cennik
  i całą historię"* ([`integration.md`](integration.md) §4, §5).
- **Assumption it breaks:** every record is born by a use case inside Rakieta.

**Cost to build** (*reading*)
- Apps: backend 1–2 (an import of customers, season series and future bookings, through the real use
  cases, with a dry run that names each clash), club website 1 (the upload and its report), root 1 (the
  file format).
- **M (≈3–4)**, on P1, P3 and area 4. Per-vendor mapping from tenis4U's or Playmore's exports adds a
  ticket each, once someone has seen a real export.

**What it changes in the player app**
- Perhaps a claim flow: an imported customer invited by email or SMS becomes a User linked to that
  customer.

### 17. Trust: environments and deployment

**Exists today**
- **[DOC]** `local` is *"the only one"* that runs; `development` and `staging` are defined, validated and
  not provisioned; `production` does not exist; *"No domain is registered"* (`docs/environments.md:13-22`).
- **[CODE]** The backend's deploy pipeline is `[DORMANT]`, manual-only and gated on an unset
  `AWS_REGION` (`.github/workflows/deploy-ecs.yml:1-27`).
  - **[ABSENT]** A deploy workflow for the club website or the public site — `.github/workflows/` holds
    `ci.yml`, `coverage.yml` and `deploy-ecs.yml`.
- **[DOC]** The deployment guide covers ECS, ECR and CloudWatch logs kept 30 days
  (`backend/docs/deployment/aws-ecs.md`).
  - **[ABSENT]** A backup, restore or alerting plan there.
- **[CODE]** `make taskdef` proves the task definition would start (root `CLAUDE.md`).
- **[DOC]** Missing, and written down: a Stripe test account and push credentials
  ([#533](https://github.com/Raketa02/Raketa/issues/533), open), a mail relay, a map-tile provider, a
  geocoder, store listings (`docs/environments.md` *Turning on a remote environment*). Reactivating
  deployment needs an ADR superseding ADR-0010 (step 1 there).
- **Assumption it breaks:** none in code. *Reading:* today an outage costs a club only its Rakieta
  hours; as its calendar, an outage stops its desk.

**Cost to build** (*reading*)
- **L**, mostly human and infrastructure: the domain, hosting for four apps, backups and restores,
  monitoring and alerting, Stripe in test and then live, a mail relay, push, support and on-call, and a
  data export a club can take away.

**What it changes in the player app**
- Store publication, a production API address, and the Expo project (O6, #665).

### 18. Moving today's Rakieta clubs from Only Rakieta to the full calendar

**Exists today**
- **[DOC]** *"Only `local` has ever run"* (#667, *The store and the migration*; `docs/environments.md:17`),
  so **no real club has data**.
- **[CODE]** Eight seeded clubs, across all three ways of working
  (`backend/app/seeds/club_courts.py:186-310`).
- **[CODE]** What a club holds today:
  - the **Club** (name, district, city, sports, map point) and its **Club account**;
  - **Club courts**: courts (one sport, indoor or outdoor, on or off), Rakieta hours per court,
    exceptions, prices per sport with bands, the way of working ([#670](https://github.com/Raketa02/Raketa/issues/670)
    removes it), the release lead, the cut-off, other clubs' courts, paused, and the payments account
    (`backend/app/modules/clubs/domain/club_courts.py`);
  - **Bookings**, **Seat charges** and **Club payouts**; its **Official groups** and **Administrators**.
- **Conversions:**
  - Rakieta hours become the deck's rule, or opening hours;
  - a per-sport price becomes per court and per length;
  - exceptions become blocks;
  - Rakieta bookings become one kind of occupant (P1).
- **Assumption it breaks:** Rakieta hours are an allotment, stored as the player's `WeeklyHours`.

**Cost to build** (*reading*)
- **S** — a clean cut: reset the local store and re-seed, as #667 does.
- **M** if real clubs exist first: upcasters and expand-and-contract (`docs/environments.md` *Schema
  change: expand and contract*). Building the calendar before the first live club avoids it.

**What it changes in the player app**
- Nothing.

## Summary

| Area | Exists today | Apps | Size | Biggest assumption it breaks |
| --- | --- | --- | --- | --- |
| Root · revenue | Nothing; no fee, by decision | backend, club | M | Rakieta takes no fee (ADR-0189 §4) |
| 1 · Desk calendar | A day list of Rakieta bookings; Move; Cancel | backend, club | L · XL with P1–P5 | A Booking is a filled proposal |
| 2 · Booking directly | Post a game, which books only when every seat says yes | backend, player, public, club | L | A game is made only by filling; the public site has no session |
| 3 · Deck in one calendar | Sellable hours, book-by, a court lost and re-dealt, a race guard | backend, club | M | Rakieta hours are an allotment; book-by ≥ a day |
| 4 · Season bookings | Nothing | backend, club | M–L | A Booking is a filled proposal |
| 5 · Blocks, closures | Exceptions, a court off, Pause; move-by-cancel planned (#672) | backend, club | M | Whole hours, 07:00–23:00 |
| 6 · Prices | A standard price and weekday or weekend bands, per sport | backend, club, player | M · L with passes or a wallet | A price splits into whole grosze by seats, per sport |
| 7 · Customers | A player's name and held or taken | backend, club, player | M | The club sees only a player's name |
| 8 · Coaches, lessons | Nothing | all four | XL | Only players and one club login exist |
| 9 · Leagues, tournaments | Nothing | all four | XL | A Game is opened only by a booking |
| 10 · Benefit cards | Nothing | backend, club, player | M · L with Medicover's API | Every booking is paid by card through Stripe |
| 11 · Money | The port; direct charges; held and taken; refunds; payouts; Money | backend, club, player | L | Money is a seat's share of a Rakieta booking |
| 12 · Unmanned hours | Nothing | backend, club, player, hardware | L | — (all new) |
| 13 · Staff | One shared club login | backend, club | M | One login per club |
| 14 · Telling players | Notices, email; push built and gated off; no SMS | backend, club, player | M | The club never messages players; everybody has the app |
| 15 · Reports | Money's month; payouts; the Groups figure | backend, club | M | Statistics out of scope |
| 16 · Moving in | Nothing (the seed and the console are test tools) | backend, club | M | Every record is born inside Rakieta |
| 17 · Trust | Only `local` runs; deploy dormant | all four, infra | L | — (a human's work, mostly) |
| 18 · Moving today's clubs | Eight seeded clubs, no real ones | backend | S | Rakieta hours are an allotment |
| **P1** Court time not a filled proposal | — | backend, root | M | |
| **P2** Any length, finer grid | Durations in the sport registry, unread | backend, club, root | M · L if games change length | |
| **P3** A customer who is not a User | — | backend, club, root | M | |
| **P4** Staff identities | — | backend, club, root | M | |
| **P5** Money not a seat's share | — | backend, club | M–L | |

## Gaps

- **Stripe, unverified:** whether an application fee can be taken on direct charges to accounts whose
  fees go to Stripe (`fees_collector: stripe`); whether a payment link or a hosted checkout works on a
  connected account for a guest; card terminals at a desk. Not read in Stripe's documents here.
- **Law, unanswered:** fiscal receipts and invoices for desk and online sales (O5); whether passes or a
  prepaid balance held on a club's account raise e-money questions; a club as controller of its
  customers' phone numbers; benefit-card contracts.
- **Sizes are estimates at one grain.** Where a feature splits between apps is the to-tickets step's
  call; the story walk on #530 more than doubled its tickets.
- **The overlap guard is not chosen.** A slot ledger works on SQLite and Postgres alike; whether the
  team would accept a Postgres-only constraint the SQLite suite cannot exercise is unasked.
- **The club website's server-only standard** (every call from its server, no token in the browser) was
  not tested against an interactive calendar's latency.
- **No vendor export was seen** — tenis4U's CSV and Playmore's migration format — so the import's
  per-vendor cost is a guess.
- **Not read in full:** ADR-0190, ADR-0182, ADR-0184, and `docs/research/games-and-fill-in/areas/`
  (CLUBBOOK, COURTS, CLUBMONEY, CLUBSETUP), which may hold more market facts on these areas.
