---
paths:
  - "app/modules/bookings/**"
  - "app/modules/proposals/application/fill.py"
  - "app/modules/proposals/application/home.py"
  - "app/modules/proposals/application/booking_details.py"
  - "app/modules/payments/application/seat_charges.py"
  - "app/modules/payments/application/refunds.py"
  - "app/modules/payments/domain/seat_charge.py"
  - "app/modules/proposals/application/leave_the_game.py"
  - "app/modules/proposals/application/cut_off.py"
  - "app/modules/proposals/application/resume_paused_yeses.py"
  - "app/modules/proposals/application/rescues.py"
  - "app/modules/proposals/domain/rescues.py"
  - "app/modules/proposals/application/club_bookings.py"
  - "app/modules/proposals/domain/club_bookings.py"
  - "app/modules/games/application/no_shows.py"
  - "app/modules/proposals/application/club_money.py"
  - "app/modules/bookings/application/daily_summary.py"
  - "app/modules/proposals/application/time_to_pay.py"
  - "app/modules/proposals/application/holding.py"
  - "app/modules/proposals/application/friends_games.py"
  - "app/modules/bookings/application/friends_games.py"
  - "app/modules/payments/application/covers.py"
---

# Bookings and the fill

Decisions that are load-bearing and not obvious from the code (#541, #544, #545, #547,
#548, #623, #625, #626, #669, #673; ADR-0189 §2–§5, ADR-0196 §1; the mechanics §10.1, §11–§13,
§15, §16.7–§16.12, Q104, Q106, Q108–Q113, Q121).

**No club confirms a game** (#669; ADR-0196 §1): On request — the request, the club's
yes, no and silence, the payment its yes waited on — is removed, its seven events
unregistered and the local store reset, so the last yes books the game at every club.

- **The last yes books the game, in that yes's own transaction** (`proposals/application/fill.py`).
  `SayYes` loads the proposal **locked** (`load_for_update`, `FOR UPDATE` on its row — SQLite
  renders none, Postgres holds it) so two last yeses fill it once, and the yes that leaves
  `open_seats` at nought hands the proposal to `Fill`, naming the player whose own act it
  was (`Fill.run(by=…)`: the yes, a join, a confirmed payment; `None` for a paused yes coming
  back) — `ProposalFilled.filled_by`, so Notifications never tells them
  back what they just did (#621, `notifications.md`). **First the people**: the game fills only
  with people who all fit each other (§7), and a pair already In can stop fitting after both
  said yes — the later of their yeses is taken out (`SeatReopened`, `NO_LONGER_FITS`) and
  nothing is asked of anybody. Then **the club**: a club no longer selling, or with no court
  of the sport left at the hour, records `CourtHourLost` and the yes answers
  `proposal_is_over` (`COURT_HOUR_LOST`); then the money, then the booking. **Two cards at one hour can read
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
  **verdict** on each **Seat charge**: every hold `SeatChargeKept` with the booking — **held
  until the club's cut-off** (`HELD`, `held_until`), which takes it (#637, below) — or, for a
  game booked after its cut-off, `SeatChargeTaken` at once; or the refused seats
  `SeatChargeFailed` and every other hold `SeatChargeReleased`. The capture or the
  cancellation is `SettleSeatCharges`' — an outbox subscriber added per delivery run over its
  session and provider (`subscribe_the_seat_charge_settler`) — which records the provider's answer
  (`Captured`, `Cancelled`). So a crash between the verdict and the money leaves a decision a
  subscriber retries, never money moved with nothing written. **A hold key is the game, the
  player, the attempt and the hour** — the attempt is the proposal's stream version, so a retried
  request is answered the same holds and the next try after a refusal asks afresh; a hold orphaned
  by a transaction that never committed is answered again within the hour or lapses at the
  provider untaken. A player whose card has a new brand (`terms_needed`), or no method at all, is
  refused **without asking the provider** (`TERMS_NEEDED`, `NO_METHOD`). **A hold that would not
  last until the cut-off is a Card check** (#639): booked before its cut-off, a seat whose hold's
  last moment is less than six hours past it — a Visa held over 4½ days ahead — is let go at
  once (`SeatChargeChecked`) and held again at its Holding time, four days before the cut-off,
  by the `holding` job (below); one whose Holding time has come already is kept and taken by its
  last safe moment (the fallback, `payments.md`). The booking email says so: *Your card was
  checked. 40 zł will be held from Sat 19:00 and taken on Wed 19:00, the club's cut-off.*
- **A refused share at the fill gets time to pay** (#625, #626; Q109–Q112;
  `proposals/application/fill.py`, `time_to_pay.py`, `Proposal.paying`). *The reopening
  waits*: the refused player **stays In**, the seat theirs alone until `TIME_TO_PAY` (thirty
  minutes, `domain/limits.py`) from the refusal, **never past the book-by**
  (`Proposal.time_to_pay_ends`; a payer refused again keeps the time they had). Every
  refusal gets it — the bank's check, a decline, terms to accept again, no method; a seat
  reopened because two no longer fit gets none. **Every other hold is kept**:
  `GameToCharge.pay_by` makes `ChargeTheSeats` record the new holds held and release
  nothing, and the confirm email names the time (*Confirm your payment by 14:40 to keep your
  seat*). The game is **full, so nobody else is dealt the seat or may take it** — every
  `open_seats` read stays nought (`waiting_for_a_payment`; the book-by reads). **Paid in
  time** — `ConfirmPayment` with the refused payment, or a plain yes once the terms or a
  method are fixed (`SayYes._paying_again`) — the fill books at once on the kept holds and
  nobody's bank is asked again (`ProposalFilled` marks `booked_on_a_payment`, so the booking
  is told *booked · you paid*, never a second *It's a game!*); with a seat open meanwhile it
  is `TimeToPayMet`, the payer In with their payment held. **Out of time** the `time-to-pay`
  job (`RunOutTheTimeToPay`, see `jobs.md`) records `TimeToPayRanOut`: the seat **reopens**
  exactly as a refused share's used to — offered to others, theirs to take back while free —
  and **a payer's own act past the time runs it out first** (`run_out_if_due`), so a late
  confirmation is a yes on a reopened seat. **What was kept is let go**
  (`let_go_of_what_was_kept`): a leaver of a game waiting for a payment takes their hold
  with them, and once no payment is awaited and the game did not book, every hold is
  released but the payers' own (a confirmed one waiting for the fill, a refused one for its
  player). **A seat opening while it waits** — a leave, a paused week, a block — falls the
  game back (`FellBackToFilling`, named only for a player's own act: another booking taking
  the hour is `own=False`) and the payer's time runs on. **Full again while a payment is
  still awaited** it simply waits for that payment: `Fill.run` fills only on the payer's own
  act, so no card is asked — hers least of all, *nothing retries a card by itself*; her
  payment then holds the newcomer's share and books it. Each share refused gets its own
  thirty minutes; one refused again keeps what it had. **There is no booking and no court
  held**: a card that books the court hour meanwhile ends it (`CourtHourLost` by the
  proposer, or the fill's own court check when the payment comes), its people dealt a new
  card first; Home and the details read the game off its proposal (`domain/home.py`'s
  `without_a_booking`, found by `ProposalDirectory.payment_awaited_of` over
  `proposals.payment_awaited_at`), *Waiting for one payment*, then *Seat open*, or *called
  off* — `PAYMENT_NOT_IN_TIME` when the time ran out on the book-by. **The book-by sweep
  leaves a game with a payment awaited** (`proposals.paying_until`, migration 0053): the job
  ends it first. **Before the club's cut-off it is time to fix the card** (#638; Q113): one
  machinery, two names. The fill decides off the cut-off it already holds — the court's —
  with `TimeTo.at(now, cut_off=…)`, records it on `TimeToPayGiven.time_to`
  (`Paying.time_to`, `Proposal.time_to`; older rows read `PAY`), and `time_to_pay_ends(now,
  cut_off=…)` never runs a time to fix past the cut-off. A time to fix ends by the cut-off
  and a payment is refused after it only on its payer's own act, which runs out first, so
  everybody's at once is the same. Everything else is time to pay's: the kept holds, the
  job, confirming the same payment, running out
  (`TimeToPayRanOut.fixing` names whose was to fix). Every read beside a payment-due moment says which (`time_to`, `FIX_THE_CARD`
  or `PAY`): Home's card and `GET /bookings/{id}` (one for `payment_due_by` and
  `your_payment_due_by`), the proposal details and `your_payment`, the To confirm
  rows.
  **At the Holding time, on a booked game** (#639; `application/holding.py`, `TheHolding`,
  the `holding` job): every checked share due is held again — one transaction per game,
  locked first, only while its cut-off is ahead — and **a refused holding gives its player
  time to fix the card on the booked game**: `Booking.card_to_fix` (`CardToFix`, the payment
  and why, until thirty minutes on and never past the cut-off; `booking_seats.
  card_to_fix_until`, migration 0056). **The game stays booked**; only the payer reads it —
  `your_payment_due_by` with `time_to` `FIX_THE_CARD` (`BookedGame.cards_to_fix`, folded into
  `paying`), and a *To confirm* row while the time runs (`owed_by`, over
  `BookedGameChanges.cards_to_fix_of`) — nobody else is told or asked anything. **Fixed in
  time** — `POST /seat-charges/{id}/confirmation` on that payment (`ConfirmPayment.
  _card_fixed`) — the share is kept until the cut-off (`CardsToFix.keep_fixed`) and
  `CardFixed` recorded; a refusal for terms or a method is held again by the job once they
  are fixed. **Run out** — the `time-to-pay` job (`run_out_the_cards_to_fix`, over
  `cards_to_fix_past`), the holding itself, or the payer's own late confirmation, which runs
  it out first and is then a leaver's (`rescue_not_offered`) — their seat opens as a
  leaver's (`SeatLeft` with `card_not_fixed`, the Game's seat vacated), offered on Fill in,
  the others told *Ivan left your game*, their refused holding let go, nothing owed; **on the
  record it is a leave before the cut-off** — on it only if the game is then called off (a
  call made without a ruling, #634).
- **A refused payment reopens the seat, and confirming it is the yes again.** Once its time
  to pay ran out — or where no time was given: the book-by had come — the refused
  player's **seat reopens** (`SeatReopened` or `TimeToPayRanOut`, with the
  reason and the charge — not *Lapse*, which
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
  theirs. **The Stripe risk owed to #533**: confirming re-uses the payment that failed, on the
  club's clone of the card, as before; Stripe's docs do not say whether a clone a failed
  attempt used can be confirmed again — check it in test mode once keys exist.
- **The provider's notices fold onto a charge, only forward.** The Connected accounts endpoint's
  `payment_intent.*` kinds are `SeatPaymentChanged`; `ReceivePaymentNotice` reads the payment as
  it stands and `SeatCharge.heard` records only a move the charge has not made yet — a hold heard
  after its capture is the past arriving late, and a hold the provider let go on its own is
  cancelled so no fill takes it. It never says the yes: the route does. **What it cannot yet
  settle** is a taken hold whose capture the provider refuses (a hold that lapsed through a
  days-long outage): `SettleSeatCharges` retries it, and the charge stays `TAKING` — a booked
  seat nobody paid for is an operator's question, not answered here.
- **A Booking is born booked, under the proposal's own id** (`bookings/domain/booking.py`)
  — one id from the first card to the court, and a second booking of one proposal an
  append conflict.
  It holds what the fill decided: the court, its name and **its kind**, indoor or outdoor
  (**the first free court** of the sport, in the club's order, read off what it sells
  **before any deadline**, as a card's held hour is; `BookedCourt.indoor`, on
  `bookings.confirmed` at **version 2** since #671 — a row of version 1, which named no
  kind, is a decoding error, the local store reset with the change),
  the sides (**the engine's own forecast** over every arrangement, the deck's `evenest`), the
  cut-off as the club's setting stood at the fill, and the Game it opened. Its projections —
  `bookings` (its `state`, and one court hour per booking held by a **partial** unique index:
  a called-off booking holds nothing, migration 0041) and `booking_seats` — answer the Club
  context's `CourtBookings` (what a club can no longer sell: booked, or booked with a seat
  open) and the proposals' `BookedGames` (*games per week*, *one game per hour*:
  **booked only**, whole or with a seat open, and never a seat the player left) and
  `PaymentCommitments.upcoming_games`; the club's *Games* figure counts booked ones only.
- **A booked game is an ordinary Game, opened as a completed line-up opens one** — through
  `OpenPlannedGame`, the booking's id in the arrangement's slot (`challenge_id`), **with its hour**
  (`GamePlanned.starts_at`, nullable and defaulted). The hour is what moves: its entry window runs
  from the hour's end (`windows.entry_closes_at(…, starts_at=…)`), not a week from the booking,
  which would end a game booked a fortnight ahead before its hour — and its room's end with it. **Its chat is
  opened by `GamePlanned`** (the room teller's `_open`) — and since #575 by nothing else: a
  booking's yeses are silent and open nothing, so the game is the opening, the room filed under
  the booking (`booking_id`), born about the game and its members the game's line-up. **The
  details reach it as a join** (ADR-0149 §3): `GET /conversations` finds rooms through the
  reader's games (#542), and the room's `game_id` is the booked game's — no booking read
  carries a conversation id, and `proposals` is on the fence that keeps every context from
  knowing a conversation exists.
- **What the fill does to everybody's other yeses**: each player's other live yes at the booked
  hour is **withdrawn** (`YesWithdrawn`, as their own tap writes), and a player whose booked games
  this week reach their *games per week* has every other yes that week **paused** (`YesPaused`,
  projected `PAUSED`) — counted nowhere, and **back** when one of those games stops being
  theirs (#544, below). The proposer is told everywhere (`ProposalFilled` is a club change: a
  court hour left).
- **Emails are the money's** (`payments/application/seat_charge_emails.py`): *It's a game! · 30 zł
  held* to every player when the game books before its cut-off — *30 zł is held on your card and
  taken on Fri 17:00, the club's cut-off. Leave before then and nothing is taken.* (#637) — or
  *It's a game! · you paid 30 zł* when it books after it, the club named as the seller; and
  *Confirm your payment to keep your seat* to each refused player, worded by reason.
- **Seeded by `app/seeds/bookings.py`**: two of the protagonist's games — the first hour
  still to come today at Bonarka Arena (else inside the cut-off) and the first Kazimierz
  Padel sells next week (#669; it worked On request, and books at once now) — each made by
  `MakeProposal` and filled by four `SayYes`, hers last, through the run's fake. **No game
  fills later than its release time** (#670), so today's is read off what Bonarka sold
  before any deadline and filled **as if earlier**, an hour before its release time, and the
  cut-off job is run at its cut-off (`the_cut_off_if_it_passed`), which takes it — and the
  seed's outbox captures it (the fake **adopts a hold another
  process made**, as it answers a card it never saved); next week's **held** until its cut-off
  (#637) — or, run early in the week, only **checked**, its hold not lasting until the cut-off
  (#639) — so her receipts list one. **And one game of the crowd's filled far ahead** (#639):
  four crowd members with no game that week fill Bonarka's first padel hour whose cut-off is
  more than five days off (`FAR_AHEAD`), every seat checked and held at its Holding time —
  the console's *hold the shares* — the run failing by name if none was checked; later layers
  keep out of its hour (`SeededBookings.starts`). The played history (`booked_history.py`) runs the cut-off
  job at each past game's cut-off, so every past game is taken and settled.
  `FakePayments.phone_confirms_payment` is a phone confirming a payment.
- **Home and the details read the bookings; Proposals assembles them** (#542; the mechanics
  §14). `GET /home`, `GET /bookings/{id}` and `GET /proposals/{id}` are Proposals' reads
  (`application/home.py`, `booking_details.py`, `proposal_details.py`), over `PlayerBookings` —
  signed in `proposals/infrastructure/bookings.py`, folding each booking's stream — beside the
  deck's people and forecasts. **Home's read is bounded** (#613): the bookings are read only
  from `on_home_since` — the earliest hour a game can still ask anything of its players, off
  the games' own clocks (`windows.A_BOOKED_GAME_NEEDS_ITS_PLAYERS_FOR`: the hour, the entry's
  day, then a day for a score's answer; a late *I was there* closes inside it, #657) — and of
  those a card is sent only while it is live, ended less than a day after its hour's end (the
  phone's own shelf), or `needs_you` (`domain/home.py`'s `on_home`), so the badge counts what
  it always did. **A score
  put on the table again reaches further back**: a correction re-dates its side's score and
  may be made again while the other side has not answered, so an older game is still read
  when a score may still wait on it (`GameResults.waiting_among`, over `games`' `ScoredGames`:
  a score put on its table inside the last day) among the reader's older games
  (`PlayerBookings.games_before`, ids only). Seeds read every
  booking (`of_player(…, since=None)`). **A status is folded on every read** (`proposals/domain/home.py`):
  *booked* until the hour, then the Game's result states (`GameResults`, over `games`' own
  `standing_at`); *called off* with its `called_off_reason` is the booking's own. **A full
  game waiting for one payment has no booking** (#625): Home and the details read it off its
  proposal (`domain/home.py`'s `without_a_booking`) — *waiting for a payment*, then, its time
  run out or another seat opened, a full game gone back to filling (`FILLING_AGAIN`, Q106):
  *seat open* with `filling_again`, nobody paid, `needs_you` false (the badge never counts
  it), no Leave, no court, the people In now standing in the order they said yes. *Called
  off* · `BOOK_BY_PASSED` once its book-by passes first, · `PAYMENT_NOT_IN_TIME` when the
  time to pay ran out on it, and · `COURT_HOUR_LOST` once its court goes. A departure on it
  withdraws the yes. **The club never sees it**: it has no booking, so it is on no page of
  the club's, whose document keeps its own two-value `CalledOffReason`. On a booked game,
  *seat open*, *called off · short at the cut-off* and *uncounted · a seat was empty* are
  #544's (below); the club's cancel is #547's. **The
  forecast is the Game's pairing** (`GET /games/{id}/pairing`) — the details only say
  whether it is drawn. **No code to show at a desk**: desk check-in is removed (#651, below).
- **Held until the cut-off, taken at it; leaving before it takes nothing; a game plays full or
  not at all** (#544, #637; `proposals/application/leave_the_game.py`, `cut_off.py`,
  `bookings/application/leaving.py`; the mechanics §12.2, §12.3, §13, §14.1, §15.4, Q113).
  `POST /bookings/{id}/departure` locks the game's proposal row first, as every act on a game
  does. **Before the cut-off** the leaver's seat opens (`SeatLeft` — the booking `SEAT_OPEN`,
  their `booking_seats` row kept with `left_at`, the Game's seat vacated through games' own
  `VacateSeat`, so they drop out of the room, whose members are the line-up) and their **hold
  is let go** (`SeatRefunds.refund` → payments' `GiveTheSharesBack`: a `HELD` charge is
  `let_go`, `SeatChargeReleased` with the reason, cancelled from the outbox — no refund, no
  fee, emailed *You left the game · nothing was taken*); **after it** the seat opens and stays
  paid — refunded, less the fee, when a rescue takes it (below); a share only **checked**
  (#639) has nothing held, and leaving closes it — nothing let go, never a receipt; **while a
  payment is awaited** it is `WithdrawYes`' act (#625); **after the start** `game_has_started`. **The money line is
  folded off the clock** (`domain/home.py`'s `money_of`): `share_state` `HELD` with
  `free_to_leave_until` and `taken_at` the cut-off until it comes — `CHECKED` with `held_from`,
  its Holding time, while **the reader's own** share is only checked and that time is ahead
  (#639; `HoldingTimes`, over the `seat_charges` projection's `hold_at`) — then `TAKEN` and
  `paid` —
  `paid` means taken, never only held — and for a game booked after its cut-off `TAKEN` from
  its `booked_at`; `refunded_grosze` is the share only on a game its club cancelled after the
  cut-off (`BookedGame.cancelled_at`). What leaving would cost is on the details before the
  player leaves (`leaving`): **no quote before the cut-off** (`refund_grosze` and
  `card_fee_grosze` `null` — nothing is taken), and after it the share less **exactly the
  fee kept on the reader's own payment** (#641, `LateRefunds`, asked only after the cut-off)
  — *38,24 zł* of 40 zł on a business card — and `null` again while that fee is not yet known
  (a club on its own pricing, or a take not yet captured): never an estimate. A leave after
  the cut-off emails that figure, or none (`SeatRefunds.left_after_the_cut_off`). **The
  cut-off job** (`cut-off`, see
  `jobs.md`; `TheCutOff`) does two things, the call-offs first: it calls off every game with a
  seat open since **before** its cut-off (`CalledOffAtCutOff`, naming everybody still in) —
  every hold let go, nobody pays anything, a share taken already (#639's fallback) refunded in
  full — the court is free (the partial index), the Game is called off by nobody
  (`CallOffGame`, which steps over a game that already started short) and its room with it,
  the desk is emailed *A game was called off at the cut-off*, each player *Game called off ·
  nothing was taken*; and it **takes every share held for a full game** whose cut-off has
  come (`HeldShares.due`/`take`, over the `seat_charges` projection's `status`/`held_until`,
  migration 0054), captured from the outbox with the real fee — each share at its own
  `held_until`, so a holding's fallback is taken by its last safe moment, before the cut-off
  (#639).
  **Short at the cut-off is read off the clock** (`Booking.short_from`,
  `BookedGame.called_off_reason`), so Home reads *called off · `SHORT_AT_THE_CUT_OFF`* from
  the cut-off on, before the job runs. A seat left **after** the
  cut-off lets the game go ahead short: at its hour the Game's standing is **`STARTED_SHORT`**
  — derived from `starts_at` and the line-up, refusing a result (`the_game_started_short`),
  in no tally — and Home reads *uncounted · `SEAT_EMPTY`*. **A seat a rescue took is not
  open**: `open_since`, `open_before_the_cut_off`, `short_from` and `keeping_of` read the
  departures still open (#545, below).
- **Refunds are decided in the act and made from the outbox** (`payments/application/refunds.py`,
  `SeatCharge.refund`): `SeatChargeRefundDecided` (withhold the fee, or not) in the leaving's
  or the call-off's transaction; `SettleSeatCharges` captures first if the capture's own
  delivery has not run yet, then refunds **exactly** the share or the share less the fee kept
  on that payment (#636) under `raketa-refund-<charge>` and records `SeatChargeRefunded` with
  the amount and what was kept — a fee not yet known makes the refund wait. A receipt's refund row
  is dated from the decision (`refund_decided_at`), not the provider's answer. **The fake's
  payment ids carry their amount** (`pi_fake_3000g_…`) so a fake in another process — a seed
  run, a laptop after a reload — adopts a taken payment for a refund at what it was for.
- **The record: a booked game is a plan with a moment** (`bookings/domain/keeping.py`,
  `BookingHistoryQuery`). *Keeps plans* (since #544) is read by the Player Score: **kept** is
  a game whose hour came with every seat held, for everybody in it — whoever Didn't come
  included (#659); **broken** is leaving before the cut-off — or a card not fixed in time —
  when the game is then called off (`Broken.CALLED_OFF_BY_LEAVING`), or after it when
  nobody takes the seat by the start (`Broken.LEFT_AFTER_THE_CUT_OFF`) — two ways Player
  reliability prices apart, its prices `player_score`'s. `keeping_for` answers every settled `Keeping`, oldest
  first; the six months are `player_score`'s. Leaving free
  when the game still plays, a game never booked, and staying in a game that went ahead short
  or was called off because of somebody else's seat (§14.1) are nothing.
  A leaver is found through their kept `booking_seats` row (`ever_seated`).
- **A paused week comes back** (`proposals/application/resume_paused_yeses.py`): an outbox
  subscriber to `SeatLeft` (the leaver) and `CalledOffAtCutOff` (everybody still in), added
  per delivery run over its session and provider, resumes each paused yes their week now has
  room for (`YesResumed`, projected `YES`) — and a yes that comes back as a game's last seat
  **fills it** through the fill. One that cannot come back (filled without them, an hour now
  booked, a full week, no longer In) stays paused, silent.
- **A seat a leaver opened is a rescue, and the first join wins** (#545;
  `proposals/application/rescues.py`, rules in `proposals/domain/rescues.py`,
  `bookings/application/rescues.py`; the mechanics §8.1, §10.1, §12.3, §19). **Offered**
  while the booking is `SEAT_OPEN` and not short at its cut-off — **until the cut-off whatever
  the number of open seats, then until the start** (`Booking.rescuable_at`) — to every member
  of the pool who **fits** everybody on it (`PlayerFit`, the kind's window), wants its kind
  (their Play intent; none declared is nothing), is **free for the hour** in their week, has no
  game then, and is within their Games & money; never to somebody on it or who left it
  (`domain/rescues.py`'s `offered_to`). **The board** is `GET /pools/{id}/fill-in?sport`
  (Seats to fill and its badge; *You're In* is still `GET /players/me/live-yeses`); **the
  deck** deals a `SEAT_OPEN` card (`CourtState.BOOKED`, `court_name`, tiles `paid`) only to the
  **best fits** — the offered members whose game with them in the seat is forecast most even,
  three per open seat, the pool's order breaking a tie; on a For-fun game the best company for
  the players still on it, by the vibe first (#831, `proposals.md`) — and never again to somebody who said
  no (`POST /bookings/{id}/no`, `NoSaidToTheSeat`; the board keeps the row). Derived at every
  read: the reader's own offer is asked first, and the whole pool is read only when a seat is
  offered to them. An outsider offered the seat reads `GET /bookings/{id}` from outside — in
  the seat, unpaid, with `rescue` (deadline, *fills by the cut-off*), no leaving.
  **Joining** (`POST /bookings/{id}/seats`, `JoinARescue` over `Rescuer`) locks the proposal
  row first, so two joiners for the last seat are one after the other and **the second reads
  it gone** (`seat_just_taken`) **before its bank is asked**. Then the money is the fill's own
  all-or-nothing for one seat (`SeatCharges.charge` with `rescue=True`: its holds keyed
  `raketa-rescue-…`, the attempt the booking's version) — **held until the cut-off like every
  seat it joins, or taken in the act after it** (#637) — **or, far ahead of the cut-off,
  checked and held at its Holding time**, by the reach rule the fill's seats follow (#639,
  #640) — so a crash leaves a hold that lapses rather than money taken for no seat; the
  joiner is emailed *It's a game! · 30 zł held* (*Your card was checked …* far ahead), or
  *you paid* after the cut-off, and the join answers the joiner's money line as Home reads it
  (`money`: `HELD`, `CHECKED` or `TAKEN`; `money_of` over `HoldingTimes`, on a second tap
  too). The rescuer is free to leave until the cut-off like everybody else. A leaver before
  the cut-off whose seat a rescue takes had nothing taken, and is refunded nothing.
  **The seat that opened first is taken, on its side** (`SeatRescued`, naming the leaver it
  replaces; the joiner's `booking_seats` row), on the Game too through games' own
  `TakeASeat` — a `LineUpReseated` with one more seat filled, so the room, whose members are
  the line-up, takes them in — and **the leaver who left at or after the cut-off is refunded,
  less exactly the fee kept on their payment, decided in the same transaction**
  (`RefundReason.SEAT_TAKEN`; #641) and **told when the refund is made** — the email and the
  notice *You've been refunded 38,24 zł · your seat was taken* / *40 zł less the 1,76 zł kept
  on your payment*; a fee not yet known makes the refund, and the telling, wait; one who left
  before it had nothing taken. The
  joiner's other yeses at the hour are withdrawn and a full week pauses the rest
  (`Fill.other_yeses`). **A refused share keeps a seat for its rescuer** (#640; Q113, a call
  made without a ruling): `SeatKept` on the booking — until `TIME_TO_PAY` on, to fix the
  card before the cut-off (never past it) or to pay after it (never past the start;
  `kept_until`), with the payment and why — and **offered to nobody else meanwhile**: every
  offer read is keeper-aware (`rescuable(…, by=)`, `Booking.rescuable_at(…, by=)`,
  `seats_kept`) and **off the clock**, so a keep whose time is up keeps nothing whether or
  not its running out is recorded. A keep holds **a seat, not a particular one**: the seats
  are still taken in the order they opened. The answer's `your_payment` carries
  `confirm_by` and `time_to` (`YesAnswer.kept_until`; no `payment_awaited_until`: no game
  waits on it), a second tap is `payment_to_confirm`, and `POST /seat-charges/{id}/
  confirmation` on a booked game is **the join again** (`ConfirmPayment` hands a `FILLED`
  proposal's payment to the `Rescuer`), the confirmed hold taken rather than asked for again
  — or, refused for terms or a method, the join itself once fixed. Refused again within it,
  the rescuer keeps the time they had (`SeatKept` again). The keeper reads it on their *To
  confirm* rows (`kept_for`, over the `booking_keeps` projection, migration 0057) and on
  `GET /bookings/{id}` from outside (`your_payment_due_by`, `time_to`), and is emailed and
  told *Fix your card by 14:40 to take the seat* / *Confirm your payment by 14:40 to take
  the seat*. **Run out** — the `time-to-pay` job (`run_out_the_keeps`, over `keeps_past`), or
  the rescuer's own late act, which runs it out first and is then a join like anybody's —
  `KeptSeatRanOut`: the seat is offered again, still theirs to take while it is free (their
  refused payment stays to confirm — on their *To confirm* rows without a time, while the
  seat is free and the payment waits on their bank, as a reopened seat's does; the
  projection's row stays, marked `ran_out`), but **never kept for them again on that game**
  (`keeps_ran_out`; `domain/rescues.py`'s `kept_until`), so a refusal for terms pressed
  again and again cannot hold a seat. A game called off or cancelled keeps no seat. The
  last seat taken releases every rescue payment still pending on the game; so does the
  cut-off's call-off. **The record**: a leaver whose seat was taken broke nothing,
  whatever becomes of the game; the joiner keeps the game when its hour comes whole.
  **Seeded by `app/seeds/rescues.py`**: two of the crowd's games she is not on, each left by
  one of its four — one **past the cut-off by a day** (*fills by the cut-off*, on every run)
  and one **inside it** (*offered until the start*), filled as if earlier, as her game today
  is (#670), which needs an hour of her week that Bonarka sells inside its 24-hour cut-off —
  none from Saturday afternoon to Monday evening, nor late on a weekday evening — and is
  otherwise skipped by name; `assert_the_fill_in` fails a run whose board lacks what was
  seeded.
- **The club runs its bookings** (#547; `proposals/application/club_bookings.py`, rules in
  `proposals/domain/club_bookings.py`, acts in `bookings/application/at_the_club.py`; the
  mechanics §16.7, §16.9, §16.14; the screens B4, B6). **The club surface is
  proposals'** — a cancel refunds and owes a new card, and every act locks the game's
  proposal row first: `GET /api/v1/club/bookings?date&filter` (one club calendar day,
  07:00–23:00, every state; `ALL`, `SEAT_OPEN`, `CALLED_OFF`, with the whole day's
  `counts`), `GET …/{id}/free-courts`, `POST …/{id}/move` (`{court_id}`),
  `GET …/{id}/cancellation/preview?reason` and `POST …/{id}/cancellation`
  (`{reason, anyway}`, answering `MOVED` with the court or `CALLED_OFF`, #672). **The
  club's status is folded on every read**:
  *called off* — short at the cut-off, or cancelled — *played* once the hour is over
  (never recorded: a `BookingPlayed` event was in the screens' C1 and is not built; a game
  that went ahead short, or one somebody Didn't come to, is *played* — the club is paid and
  sees no attendance, #657),
  else *seat open* or *booked*. **What the club sees of a player is the `nickname` (#725), `paid` (a
  charge `TAKING`/`CAPTURED`, `BookingTakings` over each booking's Seat charges — one
  `of_game` read per booking listed) and `held` (a charge `HELD` until the cut-off,
  #637)**; the money is the court's price (share × seats), what was collected —
  **taken shares only** — and what was refunded (given, or decided and not yet given: the
  share, less the fee kept where withheld); the group comes from `groups`
  (`PoolOrigins`). **Move and Cancel are the club's while the game is booked or seat open, not
  short at its cut-off, and not started** (`booking_is_called_off`,
  `game_has_started`). **Move** (`CourtMoved`, at **version 2** since it carries the new
  court's kind, #671) is onto a court of `ClubCourtsAtTheHour.free_courts`
  — every court of the sport the club still sells at the hour, read before any deadline, each
  with its kind, the game's own excluded since its booking holds it — **that keeps the
  game's kind** (`MoveTheBooking.free_courts` over `BookedCourt.may_move_to`; the mechanics §16.4, Q122):
  the same kind, or an indoor court for an outdoor game, never outdoors from indoors, which
  would be a different game to the players; anything else is `court_not_free`, and a
  race on the court hour's index is `court_just_taken` — so **a club that is not live (its
  payments account needs attention) has no court to move to**, and cancels instead. **A
  booked game always names its court's kind** — Home's rows, the details, Fill in's rows,
  the deck's `SEAT_OPEN` card and the club's row carry `indoor`, folded off the booking,
  so the kind follows a move — and **a move wakes the proposer** (`CourtMoved` in
  `MarkDueForProposing`'s `CLUB_EVENTS`), since the court the club's own Move left is free
  at the hour again;
  every player on the booking is told *Game moved* (`notifications.md`). **Cancel tries a
  move first — a move by cancel** (#672; the mechanics §16.9, Q122; ADR-0196 §2):
  `Booking.absorbing_court` over `ClubCourtsAtTheHour.free_courts`, which carries each
  court's share at the hour (`FreeCourt`), picks a court other than the game's own **sold at
  the booking's share, of its kind or indoor for an outdoor game (`may_move_to`), and
  indoor only for `WEATHER`** — an outdoor court at the same hour is rained on too — the
  same kind first, then indoor, each in the club's order (a stable sort). The same club,
  sport, day and hour are the read's. The share stands for the price (`share_of` splits a
  price exactly), compared against what the club sells the court at **now**, so a club
  that has raised its price since the fill has no court to absorb the cancel. If one
  absorbs it, `CancelTheBooking` **moves** the booking there (`CourtMoved` with the cancel's
  `reason` and the court it left, `moved_from` — both defaulted, version 2 unchanged, so a
  move recorded before reads as the club's own), and **nothing else happens**:
  `CancelTheGame` refunds nobody, lets no hold go, releases no rescue's payment and records
  no `ClubCancelled` — nobody is owed a card — so every hold or taken share stays as it
  was, before or after the cut-off; the proposer is marked due by `CourtMoved` as for a
  Move. **The cancel decides afresh** at every press, whatever the preview
  (`PreviewTheCancel`, the same `absorbing_court` read) said: a court booked in between
  leaves the next one, or none; a race on the court hour's index is `court_just_taken`,
  and pressing again decides afresh. **`anyway`** — *Cancel the game anyway*, for a club
  closing the whole hour — skips the move. **Otherwise the game is called off**
  (`CancelledByClub`, reason `WEATHER`/`REPAIR`/`DOUBLE_BOOKING`/`OTHER`), which frees the court
  (partial index), calls the Game off by nobody **whole or with a seat open** (`Game.call_off_whole`,
  through `GameChanges.call_off_whole`), **before the cut-off lets every hold go** — nothing
  taken, nobody refunded, no fee for anybody, emailed *Game cancelled by <club> · nothing was
  taken* (#637) — and **after it** refunds **in full** — `RefundReason.CANCELLED_BY_THE_CLUB`,
  emailed *Game cancelled by <club> · you're refunded*, with the reason — everybody still in
  **and a leaver whose seat was still open and paid** (left after the cut-off; one refunded
  already is refunded nothing twice), under a reason of their own
  (`CANCELLED_AFTER_YOU_LEFT`, #623): told and emailed in a leaver's words, *The game you left
  was cancelled · you're refunded*, and promised no new game — releases undecided rescue
  payments, and records
  **`ClubCancelled` on the proposal** with the people still in: `Proposal.owes_a_new_card`
  and `owed_to` (the leaver is not owed), the projection's `proposals.club_cancelled`
  (migration 0043), read by `owed_a_new_card_in`, so the proposer deals them **the owed
  card** first, closest to the cancelled game (#673; ADR-0196 §3; `proposals.md`) — the
  *never at that club and hour* rule is gone.
  **A club's cancel closes the court the game was on for its hour** (#673; a ruling made
  while building it, beyond ADR-0196's text): moved by the cancel or called off — `anyway`
  too — `CancelTheBooking` closes it once the booking's save has freed it, through
  **`CourtClosures`**, a demand of the Club context in Bookings' words, signed by
  `ClosedByTheCancel` (`infrastructure/club_courts.py`) over clubs' own
  `CloseACourtForAnHour` (`clubs/application/hours_exceptions.py`, no commit — the
  cancel's transaction): an ordinary **hours exception** on the Club courts stream, the one
  court for the one hour, worded by the cancel's reason — *Game cancelled · weather*,
  *· repair*, *· booked twice*, or *Game cancelled* — on the desk's list, which the desk
  removes to sell the court again. The court can't be played then, so neither the four's
  owed card nor anybody else is sold it, and a second cancel cannot move a game back onto
  it. A court the club no longer has is nothing to close. The club's own **Move** closes
  nothing: the desk chose to leave the court.
  `CancelledByClub` resumes paused weeks and marks the proposer due everywhere. **Home and
  the details** read `called_off_reason: CANCELLED_BY_THE_CLUB`, `club_cancel_reason`, and
  `money.refunded_grosze`; **nothing goes on anybody's record** (`keeping_of` answers `None`
  for every called-off reason but short at the cut-off). **Desk check-in is removed** (#651;
  ADR-0195 §4, §9): no per-seat code or QR payload, no keyed derivation, no club route, no
  *We check players in*, and nothing reads who the desk saw. Check-ins lived only in event
  streams, so nothing was migrated: a stored `bookings.player_checked_in` stays registered
  and **folds to nothing** but the stream's version, and a stored
  `clubs.rakieta_settings_changed` keeps decoding its `check_in`, which nothing reads (a row
  saved since carries `null`) — `tests/unit/test_retired_check_in_rows_still_fold.py`.
- **Somebody Didn't come: caught at the court, and the Game's** (#657, replacing #547's
  report; ADR-0195 §3; written up in `games.md`). A player at the club taps *isn't here yet*
  in the first 30 minutes; no arrival by then is **Didn't come**, and a confirmed *I was
  there* within a day makes it Came late. **Nothing at a club's desk is asked** (#651): a
  check-in stored before the removal stops no tap, and the club sees no attendance. The
  Game's club is the booking's: **`GameClubs`** (`infrastructure/game_clubs.py`,
  `BookedGameClubs`) answers where it is, and how far a position is from it, for an attendance
  tap. **A *Didn't come* is priced once** (#659; ADR-0195 §1): −25 on *shows up*, read off
  the Game (`Game.turnout_of`, the late claim's day over), and the booking they held is
  **kept** on *keeps plans* — `keeping_of` lost `no_shows` and `GameNoShows` went; Came late
  is also the Game's to say. Home reads *uncounted · `DIDNT_COME`* from the tap window's end, and
  *needs result* while somebody is not here yet (`NOT_HERE_YET`, the game still being
  played) — `needs_you` then only for the player awaited, whose *I'm here* it is; and
  `needs_you` while a late claim waits on the reader — their own *I was there*, or somebody
  else's to confirm (`Game.attendance_waits_on`). Who tapped is not on the wire.
- **A friends game is the Booking's second birth, booked the moment it is sent** (#751;
  ADR-0202 §5–§6; the friends mechanics §8–§10.3, §11.2;
  `proposals/application/friends_games.py` orchestrates, `bookings/application/friends_games.py`
  acts, `payments/application/covers.py` holds). `bookings.booked_by_a_friend` (v1) carries
  the card's sides with the sender on one, the pay mode (`SPLIT_THE_COST` / `WHOLE_COURT`),
  `invited_until` (24 h from the send, **never past the cut-off — or, sent after it, the
  start**: `invited_until`, `TIME_TO_ANSWER`) and the club's cut-off; it folds with **only the
  sender In** and every other player an `InvitedSeat`, answered by
  `bookings.invited_seat_accepted` (seated on their side, `last_seat` when it made the game
  whole), `…invited_seat_declined` and `…invited_seat_ran_out`, and ended by
  `bookings.called_off_by_the_sender` (`CalledOff.BY_THE_SENDER`, everybody In and every
  invitee still waiting named). **An invited seat is neither held nor open**: the booking is
  `BOOKED` with fewer players than seats, so no read sees a rescue (`open_seats` nought, no
  departure) and the cut-off never calls it off for one. The Game opens with the invited
  seats open (`GameOpening.open` takes `None` on a side) and `TakeASeat` seats each accept,
  so the room — the line-up — has the sender from the send and each friend from their
  accept. Projections: `bookings.sender_id` and `booking_invitations` (migration 0066), read
  by Home's *FRIENDS GAME* row (`invitations_of`), the invitations job (`invitations_past`)
  and the send's **at most 2 waiting** (`friends_games_waiting_of`, `FRIENDS_GAMES_WAITING`).
  **No proposal stands for it, so every friends act locks the booking's own row**
  (`BookingRepository.load_for_update`, through `FriendsGameBookings.locked`); the cut-off's
  take locks it when no proposal row is found. **The send** reads the line-up through the
  card's own `ReadFriendsLineUp`, then asks, in the sheet's order: a method, the waiting cap,
  the sender's hour and week (`you_play_then`, `games_per_week_booked`), and the court still
  in the card's list — a court gone is `court_just_taken`. **The court is claimed first**,
  so a race on the court hour's index is `court_just_taken` before any bank is asked;
  **then the money**; a refused card rolls the claim back and records the same answers
  — the same keys, so the provider answers the same — as nothing booked
  (`SendersCourts.refused`); then the sender's other yeses (`Fill.other_yeses`). **Accepting** is refused for a game at the hour or a full week, holds the
  friend's own share with *Split* (`GameToCharge.accepting`: keyed `raketa-accept-…`, the
  refusal *to take the seat* by their invitation's end — the seat stays theirs to retry,
  nothing recorded on the booking), holds nothing with *Whole court*, and withdraws their
  other yeses at the hour. A refused share confirmed in the app is the accept again
  (`ConfirmPayment` → `FriendsGameConfirmation`, when no proposal stands for the game;
  the accept itself is `Accepting`, shared by `AcceptAFriendsGame`).
  **The cut-off** settles covers before the take (`CoversAtTheCutOff`, only once the cut-off
  has come and no invitation waits). **Call it off** is the sender's before the cut-off
  (`cut_off_has_passed` after): every hold and cover let go (`RefundReason.
  CALLED_OFF_BY_THE_SENDER`), the Game called off whole, the court free (the partial index);
  the club reads it `BY_THE_SENDER`. **Calls made without a
  ruling**: a send made after the cut-off takes the sender's
  share at once and holds the covers until the invitations end, when they are decided;
  `payments-to-confirm` lists no friends game's payment (no proposal to name); a sender's
  holding refused far ahead is one card to fix for all his charges (`cards_to_fix` is one
  per player), so confirming it fixes one and the cut-off takes only the covers held — and
  not fixed in time, his seat opens as a leaver's and the game turns ordinary — owed to a
  later ticket. **Seeded by
  `app/seeds/friends_games.py`** (`seeds.md`).
- **A friends game's empty seats, its cover warning and its leaving** (#752; the friends
  mechanics §10–§11; `Booking.empty`, `vacancies`, `covering`, `ordinary`;
  `proposals/application/friends_games.py`, `leave_the_game.py`, `cut_off.py`,
  `rescues.py`). **A seat nobody holds is either empty or open.** *Empty*
  (`EmptySeat`, named by whose it was — the friend who declined, didn't answer or left) is
  the sender's to fill before the cut-off and **no rescue**: the booking stays `BOOKED`,
  `open_seats` nought. *Open* is a `Departure` like a leaver's — the rescue machinery's one
  input — and on a friends game it may be **covered** (`Departure.covered`): paid by the
  sender's card, so a taker after the cut-off refunds **him**, never the friend it is named
  after, and it never calls the game off. **The fold decides** (`_emptied`,
  `_the_sender_left`): on a game the sender **covers** (*Split* with him not left before the
  cut-off, or *Whole court* whatever he did), a card invitation declined or run out — a
  run-out dated by its `until` — or an accepted friend's leave **before** the cut-off is
  empty; **at or after** it a rescue at once, covered unless the leaver paid it themselves
  (`_paid_their_own`: anybody on *Split*; on *Whole court* the sender and a rescuer, never
  a friend who accepted free). **The sender's own leave**: *Split* before the cut-off
  turns the game **ordinary** (`sender_left_at`) — every open seat uncovered, and his seat,
  every empty seat **and every card seat still waiting** open at once (§11.2, *any seat no
  friend has taken*): its friend may still accept it, first come — their accept takes their
  own open seat, a rescue ending their invitation `TAKEN` — and the game is short at the
  cut-off like any game; *Whole court* before it his seat opens **covered** by his own
  share; after the cut-off his leave is a late leave. `state` is
  `_restate`'s: `SEAT_OPEN` exactly while a departure is open. **An invitation into a seat**
  (`bookings.seat_invited`, `InvitedSeat.seat_of`/`invited_by`, a `booking_invitations` row
  like the card's): by anybody In, of an empty or open seat, the invitee never on the game
  before, `invited_until`'s clock; **the first accept or the first rescue takes the seat**
  and every other invitation into it ends `bookings.invited_seat_taken` (`Answer.TAKEN`),
  recorded by the same act. A seat invitation declined or run out leaves the seat as it was.
  **Open to the group** (`bookings.seat_opened`) is the sender's, In, before the cut-off;
  **the cut-off opens every seat still empty** on a covered game (`open_at_the_cut_off`,
  `at_the_cut_off`), in `TheCutOff._take` after the covers are settled and the shares
  taken — an invitation whose time is up run out first. The read of a rescue is unchanged:
  `rescues_in` (`state = SEAT_OPEN`), the board, the deck's `SEAT_OPEN` card, the alerts.
  **No proposal stands for it**, so `JoinARescue`, `SayNoToARescue`, `LeaveTheGame` and the
  cut-off's call-off lock its booking row (`rescues.py`'s `lock_the_game`), and the
  `Rescuer` reads its pool off the booking (`Pool(id=pool_id, GROUP)`) — a guest, in no
  such group, is never offered it. **Who a taken seat pays back** is
  `the_seat_paid_back`: covered → one of the sender's covers (`SeatRefunds.seat_taken(…,
  cover=True)`, nothing while a cover is still held — the cut-off's `SettleTheCovers` lets one
  go for the taker's own share); a leaver's after the cut-off → their own share; a *Whole
  court* invitee taking a seat pays nothing and refunds nobody. **The cover warning**
  (`bookings.cover_warned`, once) reads `Booking.cover_line` — inside
  `COVER_WARNING_BEFORE` (24 h) before the cut-off of a *Split* game the sender covers from
  inside it, `unpaid_seats`: every seat but his without its own player's payment, a waiting
  invitation included, each named by its last invitee — the one read the job, the warning
  and every notice's cover line share; it is the `cover-warning` job's (`jobs.md`). **A club's cancel** moves a friends game as any booked
  game's (a move by cancel changes nothing else: every hold, cover and invitation stays) and
  calls it off with the same refunds — the sender's whole court in full after the cut-off.
  **Calls made without a ruling**: re-inviting anybody ever on the game — a friend who
  declined or left included — is `already_on_the_game` (one `booking_invitations` row a
  player); the warning is the first run inside the window, so a seat emptying in that first
  tick may be told twice; a seat taken by a *Whole court* invitee leaves the cover paid; a
  *Whole court* sender who left can no longer open an empty seat — it waits for the
  cut-off; **the cancel that calls a friends game off still owes nobody a card** — no
  proposal records `ClubCancelled`, and the proposer's owed card is built on one (a gap
  for a later ticket). **#751's local friends games fold anew**: a decline at or after the
  cut-off is now an open seat while its projected row still reads `BOOKED` — reseed the
  local store (`make seed`) rather than trust one sent before this.
- **The club's money, and its day of new bookings** (#548; the mechanics §16.11, §16.12;
  the screens B7, B9). **The Money page** is Proposals', beside the Bookings page
  (`application/club_money.py`): `GET /api/v1/club/money?month=YYYY-MM` reads every booking
  whose game starts in the club's month (`ClubBookings.on_day` over the month's hours) and
  lists those that took money, soonest first — the court, the status, and from
  `BookingTakings` what was collected, refunded, the **card fees** and the **net** (what the
  club keeps, below nought on a game given back whole) — **each the real figure or `null`,
  *not yet known*** (#641; `known_sum`: a total is `null` if any part is), never an estimate:
  a club on its own negotiated pricing is told its fees after the take — with the month's
  totals, and
  `paid_out` once a payout carried it (the payouts themselves are `payments.md`'s). **The
  daily summary** is Bookings' (`application/daily_summary.py`, the `new-bookings-summary`
  job): at the close of each club day the desk is emailed *New bookings today* — every
  booking **booked** (`bookings.booked_at`, the fill) since the close before,
  soonest game first, a called-off one marked so — and nothing on a day nothing was booked.
  Sent once: the summary is a stream of its own per club per day
  (`NewBookingsSummarised`, `domain/summary.py`), born in the transaction that queues the
  email, so a second process collides on it.
- **What a booking puts in *Needs your answer* carries its arrival** (#815; `proposals.md`):
  `InvitedSeat.invited_at` (the send for the card's own seats, `bookings.seat_invited` for a
  seat invited into later), `RefusedHolding.refused_at` and `KeptSeat.refused_at`. Each is
  folded off the event that first recorded it, and **kept** when it is recorded again (a holding
  refused again while its card is still to fix, a rescuer refused again within their time) or
  runs out. No answer or change of state moves it. Each is an event's `occurred_at`, so no
  stored row changed.
