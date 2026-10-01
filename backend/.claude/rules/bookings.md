---
paths:
  - "app/modules/bookings/**"
  - "app/modules/proposals/application/fill.py"
  - "app/modules/proposals/application/club_requests.py"
  - "app/modules/proposals/application/home.py"
  - "app/modules/proposals/application/booking_details.py"
  - "app/modules/payments/application/seat_charges.py"
  - "app/modules/payments/application/refunds.py"
  - "app/modules/payments/domain/seat_charge.py"
  - "app/modules/proposals/application/leave_the_game.py"
  - "app/modules/proposals/application/cut_off.py"
  - "app/modules/proposals/application/resume_paused_yeses.py"
---

# Bookings and the fill

Decisions that are load-bearing and not obvious from the code (#541, #543, #544; ADR-0189
§2–§5; the mechanics §11–§13, §15.4, §16.8, §16.12).

- **The last yes books the game, in that yes's own transaction** (`proposals/application/fill.py`).
  `SayYes` loads the proposal **locked** (`load_for_update`, `FOR UPDATE` on its row — SQLite
  renders none, Postgres holds it) so two last yeses fill it once, and the yes that leaves
  `open_seats` at nought hands the proposal to `Fill`. **First the people**: the game fills only
  with people who all fit each other (§7), and a pair already In can stop fitting after both
  said yes — the later of their yeses is taken out (`SeatReopened`, `NO_LONGER_FITS`) and
  nothing is asked of anybody. Then **the club**: a club no longer selling, or with no court
  of the sport left at the hour, records `CourtHourLost` and the yes answers
  `proposal_is_over` (`COURT_HOUR_LOST`); an **On request** club is **asked** (below); otherwise
  the money, then the booking. **Two cards at one hour can read
  one court free at once**: the second claim meets `bookings`' unique court-hour index
  (`CourtTaken` → proposals' `CourtJustTaken`), the transaction is rolled back, and the yes is
  tried **once more** from the start — the courts left, and the same holds answered again
  under the same keys; a second race in a row reaches the client as `409 court_just_taken`.
  **`proposals` orchestrates, and the arrows are `proposals → bookings` and `proposals →
  payments`** — both demanded through ports in
  `proposals/domain/ports.py` (`GameBookings`, `SeatCharges`, `UndecidedCharges`) and signed in
  `proposals/infrastructure/{bookings,payments}.py`; `bookings` imports neither, and
  `.importlinter` holds both arrows.
- **All or nothing: hold inline, decide in the transaction, move the money after the commit**
  (`payments/application/seat_charges.py`, ADR-0190 §4). `ChargeTheSeats` clones each player's
  card onto the club's account and **authorises** it with manual capture — inline, because the
  answer *is* the response (*It's a game!* or *your payment didn't go through*) — then records the
  **verdict** on each **Seat charge**: every hold `SeatChargeTaken` with the booking, or the
  refused seats `SeatChargeFailed` and every other hold `SeatChargeReleased`. The capture or the
  cancellation is `SettleSeatCharges`' — an outbox subscriber added per delivery run over its
  session and provider (`subscribe_the_seat_charge_settler`) — which records the provider's answer
  (`Captured`, `Cancelled`). So a crash between the verdict and the money leaves a decision a
  subscriber retries, never money moved with nothing written. **A hold key is the game, the
  player, the attempt and the hour** — the attempt is the proposal's stream version, so a retried
  request is answered the same holds and the next try after a refusal asks afresh; a hold orphaned
  by a transaction that never committed is answered again within the hour or lapses at the
  provider untaken. A player whose card has a new brand (`terms_needed`), or no method at all, is
  refused **without asking the provider** (`TERMS_NEEDED`, `NO_METHOD`).
- **A refused payment reopens the seat, and confirming it is the yes again.** The refused
  player's **seat reopens** (`SeatReopened`, with the reason and the charge — not *Lapse*, which
  is a seat's answer window; not a withdrawal, and no verdict on the card). They find the payment
  in `GET /players/me/payments-to-confirm` (proposals': games still filling whose seat reopened
  on a payment to confirm, so it never lists a game that moved on), and a plain swipe yes is
  refused `409 payment_to_confirm` naming it — the bank would be asked the same question.
  `GET /seat-charges/{id}` hands the phone the payment's secret and the club's account **asked
  of the provider now and never recorded** (`AWAITING_THE_PLAYER`);
  `POST /seat-charges/{id}/confirmation` (`ConfirmPayment`, proposals') asks the provider whether
  it holds the payment now (`read_payment`), records it `SeatChargeConfirmed`, and says the yes —
  and the fill **takes that hold rather than asking again**, since a bank that checks every time
  gives only the one the player confirmed. When another seat is refused instead, it is let go
  with every other hold: *if any fails, the others are cancelled*. A seat somebody else took
  first — or a game that filled or ended — lets it go too (`proposal_is_full` /
  `proposal_is_over`). A fill releases every charge on its game it was not paid with, and a
  lost court hour (the fill's or the proposer's) and the book-by sweep release every charge on
  theirs.
- **The provider's notices fold onto a charge, only forward.** The Connected accounts endpoint's
  `payment_intent.*` kinds are `SeatPaymentChanged`; `ReceivePaymentNotice` reads the payment as
  it stands and `SeatCharge.heard` records only a move the charge has not made yet — a hold heard
  after its capture is the past arriving late, and a hold the provider let go on its own is
  cancelled so no fill takes it. It never says the yes: the route does. **What it cannot yet
  settle** is a taken hold whose capture the provider refuses (a hold that lapsed through a
  days-long outage): `SettleSeatCharges` retries it, and the charge stays `TAKING` — a booked
  seat nobody paid for is an operator's question, not answered here.
- **On request: the club confirms, and nobody pays until it does** (#543;
  `proposals/application/club_requests.py`, `bookings/application/requests.py`). The last yes at
  an On request club **asks the club**: the first free court is **reserved** (`BookingRequested` —
  the booking born *waiting for the club*, its row holding the court hour as a booked one does),
  the sides are drawn, the answer is due at the yes plus the club's **time to confirm**, and the
  desk is emailed *A booking is waiting for your answer* in the same transaction. The yes answers
  `waiting_for_the_club`. **The proposal stays filling, full** — `Proposal.waiting_for_the_club`
  — and **its book-by no longer ends it**: the game filled in time, and the answer may be due
  past the book-by (never past the start — the longest time to confirm is the shortest notice),
  so `standing_at` keeps it `FILLING`, the sweep leaves it, and the projection's
  `waiting_for_the_club` keeps it on the live reads. The club surface is
  `GET /api/v1/club/bookings/waiting` (the one due first, first; players by **Name** only; a
  request past its deadline not listed), `POST …/{id}/acceptance` and `POST …/{id}/refusal`
  (an optional note, kept for the club and **never shown to a player**). **Accept** runs the
  fill's own all-or-nothing charge on the **reserved** court with the sides the players were reading
  (`Fill.accept`), then `BookingAccepted` opens the Game — and the chat — exactly as a booked
  game's; a share refused, or a pair In that stopped fitting while it waited, instead opens a
  seat — nobody pays, the request is withdrawn, the game fills again, and the club answer is
  `SEAT_OPENED`. **Refuse**, and **no answer** (the `request-timeout` job, `request_timed_out`
  at every answer past the deadline whether recorded or not), call it off with nobody paid
  (`BookingRefused`/`BookingTimedOut`), end the proposal `TURNED_DOWN`, free the court, and
  owe the players a new card first — the proposer deals it by the first run that finds them an
  hour (`Redealt` once it has), never at the club and hour that turned them down. **A seat
  opening while it waits withdraws the request, in the same transaction** (`RequestWithdrawn`,
  naming every seat that opened): **nobody keeps a seat on it**, so it leaves everybody's Home
  — the people still In find the game filling again in You're In, and a `CALLED_OFF` card
  beside a game still filling would say two things about one game. Whoever takes the yes away
  calls `ClubRequests.withdraw` — `WithdrawYes` (*Leave the game*), a group leaver's
  withdrawals, and the fill's *one game per hour* and *games per week* on another booking —
  because the reserved court must be free the moment the seat is, or the proposer would read
  the card's own court as gone. **Full again, the same game is asked again on the same
  stream** (`BookingRequested` once more, the court and the people as they are now). The
  club's answers, a player's *Leave* and the timeout **lock the proposal row first**, so they
  are one after another; a group leaver's withdrawals and the fill's on other games rely on
  the stream version, as every act on a proposal does.
- **A Booking is born booked, or born waiting for the club, under the proposal's own id**
  (`bookings/domain/booking.py`) — one id from the first card to the court, and a second
  booking of one proposal an append conflict (a request asked again is the same stream).
  It holds what the fill decided: the court and its name (**the first free court** of the sport,
  in the club's order, read off what it sells **before any deadline**, as a card's held hour is),
  the sides (**the engine's own forecast** over every arrangement, the deck's `evenest`), the
  cut-off as the club's setting stood at the fill, and the Game it opened. Its projections —
  `bookings` (its `state`, and one court hour per booking held by a **partial** unique index:
  a called-off booking holds nothing, migration 0040) and `booking_seats` — answer the Club
  context's `CourtBookings` (what a club can no longer sell: waiting, booked, or booked with
  a seat open) and the proposals' `BookedGames` (*games per week*, *one game per hour*:
  **booked only**, whole or with a seat open, and never a seat the player left) and
  `PaymentCommitments.upcoming_games`; the club's *Games* figure counts booked ones only.
- **A booked game is an ordinary Game, opened as a completed line-up opens one** — through
  `OpenPlannedGame`, the booking's id in the arrangement's slot (`challenge_id`), **with its hour**
  (`GamePlanned.starts_at`, nullable and defaulted). The hour is what moves: its entry window runs
  from the hour's end (`windows.entry_closes_at(…, starts_at=…)`), not a week from the booking,
  which would ghost a game booked a fortnight ahead — and its room's end with it. **Its chat is
  opened by `GamePlanned`** (the room teller's `_note_game`): a booking's yeses are silent and open
  nothing, so the game is the opening, the room born about it and its members the game's line-up.
  **The details reach it as a join** (ADR-0149 §3): `GET /conversations` finds rooms through the
  reader's games as well as their accepted challenges (#542), and the room's `game_id` is the
  booked game's — no booking read carries a conversation id, and `proposals` is on the fence
  that keeps every context from knowing a conversation exists.
- **What the fill does to everybody's other yeses**: each player's other live yes at the booked
  hour is **withdrawn** (`YesWithdrawn`, as their own tap writes), and a player whose booked games
  this week reach their *games per week* has every other yes that week **paused** (`YesPaused`,
  projected `PAUSED`) — counted nowhere, and **back** when one of those games stops being
  theirs (#544, below). The proposer is told everywhere (`ProposalFilled` is a club change: a
  court hour left).
- **Emails are the money's** (`payments/application/seat_charge_emails.py`): *It's a game! · you
  paid* to every player when the seats are taken, the club named as the seller and the cut-off
  line, and *Confirm your payment to keep your seat* to each refused player, worded by reason.
- **Seeded by `app/seeds/bookings.py`**: two of the protagonist's games at Bonarka Arena — the
  first hour on sale today (else inside the cut-off) and the first next week — each made by
  `MakeProposal` and filled by four `SayYes`, hers last, through the run's fake; the seed's outbox
  then captures them (the fake **adopts a hold another process made**, as it answers a card it
  never saved). **And one game waiting for Kazimierz Padel** (On request, a kilometre away, an
  hour to confirm): the same four yeses at its first padel hour clear of her games, the last
  answered *waiting for the club* — it waits an hour from the run's now, then the timeout calls
  it off; a re-run puts a fresh one. `FakePayments.phone_confirms_payment` is a phone confirming a payment.
- **Home and the details read the bookings; Proposals assembles them** (#542; the mechanics
  §14, §15.1). `GET /home`, `GET /bookings/{id}` and `GET /proposals/{id}` are Proposals' reads
  (`application/home.py`, `booking_details.py`, `proposal_details.py`), over `PlayerBookings` —
  signed in `proposals/infrastructure/bookings.py`, folding each booking's stream — beside the
  deck's people and forecasts. **A status is folded on every read** (`proposals/domain/home.py`):
  *booked* until the hour, then the Game's result states (`GameResults`, over `games`' own
  `standing_at`); *waiting for the club* and *called off* with its `called_off_reason`
  (`REFUSED`, `NO_ANSWER`) are the booking's own (#543) — with `game_id` and `court_name`
  `null` until the club gives them, and nobody `paid`; a request taken back because a seat
  opened is on nobody's Home; *seat open*, *called off · short at the cut-off* and
  *uncounted · a seat was empty* are #544's (below); the club's cancel is #547's. **The
  forecast is the Game's pairing** (`GET /games/{id}/pairing`) — the details only say
  whether it is drawn. **A check-in code is derived,
  never stored** (`bookings/domain/check_in.py`): an HMAC of the booking and the player under a
  key drawn from `JWT_SECRET_KEY` with its own prefix (`KeyedCheckInCodes`), six characters in
  the typed-code alphabet plus a `RAKETA-CHECK-IN:1:<booking>:<player>:<code>` QR payload, shown
  on the club's calendar day of the game while it stands — #547's desk recomputes it.
- **Leaving is free until the club's cut-off, and a game plays full or not at all** (#544;
  `proposals/application/leave_the_game.py`, `cut_off.py`, `bookings/application/leaving.py`;
  the mechanics §12.3, §13, §14.1, §15.4). `POST /bookings/{id}/departure` locks the game's
  proposal row first, as every act on a game does. **Before the cut-off** the leaver's seat
  opens (`SeatLeft` — the booking `SEAT_OPEN`, their `booking_seats` row kept with `left_at`,
  the Game's seat vacated through games' own `VacateSeat`, so they drop out of the room, whose
  members are the line-up) and their charge is refunded **less the card fee**; **after it**
  the seat opens and stays paid — the refund on replacement is #545's; **while the club
  decides** it is `WithdrawYes`' act (#543); **after the start** `game_has_started`. What
  leaving would cost is on the details before the player leaves (`leaving`: the share less
  `card_fee_on`, the payments' **estimate** — Stripe's EEA price, 1.5 % + 1 zł, which the
  fake withholds exactly). **The cut-off job** (`cut-off`, see `jobs.md`) calls off every
  game with a seat open since **before** its cut-off (`CalledOffAtCutOff`, naming everybody
  still in): everybody still in is refunded **in full** (the club bears those fees), the
  court is free (the partial index), the Game is called off by nobody (`CallOffGame`, which
  steps over a game that already started short) and its room with it, the desk is emailed
  *A game was called off at the cut-off*, each player *Game called off · with the refund*.
  **Short at the cut-off is read off the clock** (`Booking.short_from`,
  `BookedGame.called_off_reason`), so Home reads *called off · `SHORT_AT_THE_CUT_OFF`* with
  `refunded_grosze` from the cut-off on, before the job runs. A seat left **after** the
  cut-off lets the game go ahead short: at its hour the Game's standing is **`STARTED_SHORT`**
  — derived from `starts_at` and the line-up, refusing a result (`the_game_started_short`),
  in no tally — and Home reads *uncounted · `SEAT_EMPTY`*. **Until rescues (#545) every seat
  that opened stays open**: `open_since`, `left_before_the_cut_off` and `keeping_of` all say
  so in a comment, and are where #545's `SeatRescued` must reach.
- **Refunds are decided in the act and made from the outbox** (`payments/application/refunds.py`,
  `SeatCharge.refund`): `SeatChargeRefundDecided` (withhold the fee, or not) in the leaving's
  or the call-off's transaction; `SettleSeatCharges` captures first if the capture's own
  delivery has not run yet, then refunds under `raketa-refund-<charge>` and records
  `SeatChargeRefunded` with the amount and **the fee the provider kept**. A receipt's refund row
  is dated from the decision (`refund_decided_at`), not the provider's answer. **The fake's
  payment ids carry their amount** (`pi_fake_3000g_…`) so a fake in another process — a seed
  run, a laptop after a reload — adopts a taken payment for a refund at what it was for.
- **The record: a booked game is a plan with a moment** (`bookings/domain/keeping.py`,
  `BookingHistoryQuery`). *Keeps plans* (`ReliabilityStrand.KEEPS_PLANS`, live since #544)
  replaces *answers challenges* in the Player Score: **kept** is a game whose hour came with
  every seat held, for everybody in it; **broken** is leaving before the cut-off when the
  game is then called off, or after it when nobody takes the seat by the start; leaving free
  when the game still plays, a game never booked, and staying in a game that went ahead short
  or was called off because of somebody else's seat (§14.1) are nothing.
  A leaver is found through their kept `booking_seats` row (`ever_seated`).
- **A paused week comes back** (`proposals/application/resume_paused_yeses.py`): an outbox
  subscriber to `SeatLeft` (the leaver) and `CalledOffAtCutOff` (everybody still in), added
  per delivery run over its session and provider, resumes each paused yes their week now has
  room for (`YesResumed`, projected `YES`) — and a yes that comes back as a game's last seat
  **fills it** through the fill. One that cannot come back (filled without them, an hour now
  booked, a full week, no longer In) stays paused, silent.
