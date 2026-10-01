---
paths:
  - "app/modules/bookings/**"
  - "app/modules/proposals/application/fill.py"
  - "app/modules/payments/application/seat_charges.py"
  - "app/modules/payments/domain/seat_charge.py"
---

# Bookings and the fill

Decisions that are load-bearing and not obvious from the code (#541; ADR-0189 §2, §4–§5; the
mechanics §11–§12.2).

- **The last yes books the game, in that yes's own transaction** (`proposals/application/fill.py`).
  `SayYes` loads the proposal **locked** (`load_for_update`, `FOR UPDATE` on its row — SQLite
  renders none, Postgres holds it) so two last yeses fill it once, and the yes that leaves
  `open_seats` at nought hands the proposal to `Fill`. **First the people**: the game fills only
  with people who all fit each other (§7), and a pair already In can stop fitting after both
  said yes — the later of their yeses is taken out (`SeatReopened`, `NO_LONGER_FITS`) and
  nothing is asked of anybody. Then **the club**: an **On request** club's full game waits
  untouched (#543 builds the request); a club no longer selling, or with no court of the sport
  left at the hour, records `CourtHourLost` and the yes answers `proposal_is_over`
  (`COURT_HOUR_LOST`); otherwise the money, then the booking. **Two cards at one hour can read
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
- **A Booking is born booked, under the proposal's own id** (`bookings/domain/booking.py`) — one
  id from the first card to the court, and a second booking of one proposal an append conflict.
  It holds what the fill decided: the court and its name (**the first free court** of the sport,
  in the club's order, read off what it sells **before any deadline**, as a card's held hour is),
  the sides (**the engine's own forecast** over every arrangement, the deck's `evenest`), the
  cut-off as the club's setting stood at the fill, and the Game it opened. Its projections —
  `bookings` (one court hour per booking, a unique index) and `booking_seats` — answer the Club
  context's `CourtBookings` (what a club can no longer sell) and the proposals' `BookedGames`
  (*games per week*, *one game per hour*) and `PaymentCommitments.upcoming_games`.
- **A booked game is an ordinary Game, opened as a completed line-up opens one** — through
  `OpenPlannedGame`, the booking's id in the arrangement's slot (`challenge_id`), **with its hour**
  (`GamePlanned.starts_at`, nullable and defaulted). The hour is what moves: its entry window runs
  from the hour's end (`windows.entry_closes_at(…, starts_at=…)`), not a week from the booking,
  which would ghost a game booked a fortnight ahead — and its room's end with it. **Its chat is
  opened by `GamePlanned`** (the room teller's `_note_game`): a booking's yeses are silent and open
  nothing, so the game is the opening, the room born about it and its members the game's line-up.
  The Chats tab finds rooms through challenges, so a booked game's room is reached from its game.
- **What the fill does to everybody's other yeses**: each player's other live yes at the booked
  hour is **withdrawn** (`YesWithdrawn`, as their own tap writes), and a player whose booked games
  this week reach their *games per week* has every other yes that week **paused** (`YesPaused`,
  projected `PAUSED`) — counted nowhere, and back when one of those games is called off (#544).
  The proposer is told everywhere (`ProposalFilled` is a club change: a court hour left).
- **Emails are the money's** (`payments/application/seat_charge_emails.py`): *It's a game! · you
  paid* to every player when the seats are taken, the club named as the seller and the cut-off
  line, and *Confirm your payment to keep your seat* to each refused player, worded by reason.
- **Seeded by `app/seeds/bookings.py`**: two of the protagonist's games at Bonarka Arena — the
  first hour on sale today (else inside the cut-off) and the first next week — each made by
  `MakeProposal` and filled by four `SayYes`, hers last, through the run's fake; the seed's outbox
  then captures them (the fake **adopts a hold another process made**, as it answers a card it
  never saved). `FakePayments.phone_confirms_payment` is a phone confirming a payment.
