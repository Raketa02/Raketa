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
  - "app/modules/proposals/application/rescues.py"
  - "app/modules/proposals/domain/rescues.py"
  - "app/modules/proposals/application/club_bookings.py"
  - "app/modules/proposals/domain/club_bookings.py"
  - "app/modules/games/application/no_shows.py"
  - "app/modules/proposals/application/club_money.py"
  - "app/modules/bookings/application/daily_summary.py"
---

# Bookings and the fill

Decisions that are load-bearing and not obvious from the code (#541, #543, #544, #545,
#547, #548; ADR-0189 §2–§5; the mechanics §10.1, §11–§13, §15, §16.7–§16.12).

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
  a called-off booking holds nothing, migration 0041) and `booking_seats` — answer the Club
  context's `CourtBookings` (what a club can no longer sell: waiting, booked, or booked with
  a seat open) and the proposals' `BookedGames` (*games per week*, *one game per hour*:
  **booked only**, whole or with a seat open, and never a seat the player left) and
  `PaymentCommitments.upcoming_games`; the club's *Games* figure counts booked ones only.
- **A booked game is an ordinary Game, opened as a completed line-up opens one** — through
  `OpenPlannedGame`, the booking's id in the arrangement's slot (`challenge_id`), **with its hour**
  (`GamePlanned.starts_at`, nullable and defaulted). The hour is what moves: its entry window runs
  from the hour's end (`windows.entry_closes_at(…, starts_at=…)`), not a week from the booking,
  which would ghost a game booked a fortnight ahead — and its room's end with it. **Its chat is
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
  deck's people and forecasts. **Home's read is bounded** (#613): the bookings are read only
  from `on_home_since` — the earliest hour a game can still ask anything of its players, off
  the games' own clocks (`windows.A_BOOKED_GAME_NEEDS_ITS_PLAYERS_FOR`: the hour, the entry's
  day, then a day for a score's answer or a report's dispute) — and of those a card is sent
  only while it is live, ended less than a day after its hour's end (the phone's own shelf),
  or `needs_you` (`domain/home.py`'s `on_home`), so the badge counts what it always did and an
  *uncounted* card whose report the reader may still dispute outlives the shelf. **A score
  put on the table again reaches further back**: a correction re-dates its side's score and
  may be made again while the other side has not answered, so an older game is still read
  when a score may still wait on it (`GameResults.waiting_among`, over `games`' `ScoredGames`:
  a score put on its table inside the last day) among the reader's older games
  (`PlayerBookings.games_before`, ids only). Seeds read every
  booking (`of_player(…, since=None)`). **A status is folded on every read** (`proposals/domain/home.py`):
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
  the seat opens and stays paid — refunded, less the fee, when a rescue takes it (below);
  **while the club decides** it is `WithdrawYes`' act (#543); **after the start**
  `game_has_started`. What
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
  in no tally — and Home reads *uncounted · `SEAT_EMPTY`*. **A seat a rescue took is not
  open**: `open_since`, `open_before_the_cut_off`, `short_from` and `keeping_of` read the
  departures still open (#545, below).
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
  three per open seat, the pool's order breaking a tie — and never again to somebody who said
  no (`POST /bookings/{id}/no`, `NoSaidToTheSeat`; the board keeps the row). Derived at every
  read: the reader's own offer is asked first, and the whole pool is read only when a seat is
  offered to them. An outsider offered the seat reads `GET /bookings/{id}` from outside — in
  the seat, unpaid, with `rescue` (deadline, *fills by the cut-off*), no check-in, no leaving.
  **Joining** (`POST /bookings/{id}/seats`, `JoinARescue` over `Rescuer`) locks the proposal
  row first, so two joiners for the last seat are one after the other and **the second reads
  it gone** (`seat_just_taken`) **before its bank is asked**. Then the money is the fill's own
  all-or-nothing for one seat — **held and taken in the act, captured from the outbox**
  (`SeatCharges.charge` with `rescue=True`: its holds keyed `raketa-rescue-…`, the attempt the
  booking's version), never the provider's `charge_now`, so a crash leaves a hold that lapses
  rather than money taken for no seat; the joiner is emailed *It's a game! · you paid*.
  **The seat that opened first is taken, on its side** (`SeatRescued`, naming the leaver it
  replaces; the joiner's `booking_seats` row), on the Game too through games' own
  `TakeASeat` — a `LineUpReseated` with one more seat filled, so the room, whose members are
  the line-up, takes them in — and **the leaver who left at or after the cut-off is refunded,
  less the card fee, in the same transaction** (`RefundReason.SEAT_TAKEN`, emailed *You've been
  refunded · your seat was taken*); one who left before it was refunded when they left. The
  joiner's other yeses at the hour are withdrawn and a full week pauses the rest
  (`Fill.other_yeses`). **A refused share takes no seat**: `your_payment` names it, a second
  tap is `payment_to_confirm`, and `POST /seat-charges/{id}/confirmation` on a booked game is
  **the join again** (`ConfirmPayment` hands a `FILLED` proposal's payment to the `Rescuer`),
  the confirmed hold taken rather than asked for again — and let go if somebody took the seat
  first. The last seat taken releases every rescue payment still pending on the game; so
  does the cut-off's call-off. **The record**: a leaver whose seat was taken broke nothing,
  whatever becomes of the game; the joiner keeps the game when its hour comes whole.
  **Seeded by `app/seeds/rescues.py`**: two of the crowd's games she is not on, each left by
  one of its four — one **past the cut-off by a day** (*fills by the cut-off*, on every run)
  and one **inside it** (*offered until the start*), which needs an hour of her week that
  Bonarka still sells inside its 24-hour cut-off — none from Saturday noon to Monday evening,
  nor late on a weekday afternoon — and is otherwise skipped by name; `assert_the_fill_in`
  fails a run whose board lacks what was seeded.
- **The club runs its bookings** (#547; `proposals/application/club_bookings.py`, rules in
  `proposals/domain/club_bookings.py`, acts in `bookings/application/at_the_club.py`; the
  mechanics §15.1, §16.7–§16.10, §16.14; the screens B4, B6). **The club surface is
  proposals'**, as On request's is — a cancel refunds and owes a new card, and every act
  locks the game's proposal row first: `GET /api/v1/club/bookings?date&filter` (one club
  calendar day, 07:00–23:00, every state but a request taken back; `ALL`, `WAITING_FOR_YOU`,
  `SEAT_OPEN`, `CALLED_OFF`, with the whole day's `counts`), `GET …/{id}/free-courts`,
  `POST …/{id}/move` (`{court_id}`), `POST …/{id}/cancellation` (`{reason}`) and
  `POST /api/v1/club/check-ins` (`{code}`). **The club's status is folded on every read**:
  *waiting for you* until the answer is due, *called off* — refused, no answer (read off the
  clock from `answer_by`), short at the cut-off, or cancelled — *played* once the hour is over
  (never recorded: a `BookingPlayed` event was in the screens' C1 and is not built; a game
  that went ahead short, or one somebody did not come to, is *played* — the club is paid),
  else *seat open* or *booked*. **What the club sees of a player is the name, `paid` (a
  charge `TAKING`/`CAPTURED`, `BookingTakings` over each booking's Seat charges — one
  `of_game` read per booking listed) and `checked_in_at`**; the money is the court's price
  (share × seats), what was collected, and what was refunded (given, or decided and not yet
  given: the share, less the fee estimate where withheld); the group comes from `groups`
  (`PoolOrigins`). **Move and Cancel are the club's while the game is booked or seat open, not
  short at its cut-off, and not started** (`booking_not_booked`, `booking_is_called_off`,
  `game_has_started`). **Move** (`CourtMoved`) is onto a court of `ClubCourtsAtTheHour.free_courts`
  — every court of the sport the club still sells at the hour, read before any deadline, the
  game's own excluded since its booking holds it; anything else is `court_not_free`, and a
  race on the court hour's index is `court_just_taken` — so **a club that is not live (its
  payments account needs attention) has no court to move to**, and cancels instead. **Cancel**
  (`CancelledByClub`, reason `WEATHER`/`REPAIR`/`DOUBLE_BOOKING`/`OTHER`) frees the court
  (partial index), calls the Game off by nobody **whole or with a seat open** (`Game.call_off_whole`,
  through `GameChanges.call_off_whole`), refunds **in full** — `RefundReason.CANCELLED_BY_THE_CLUB`,
  emailed *Game cancelled by <club> · you're refunded*, with the reason — everybody still in
  **and a leaver whose seat was still open and paid** (left after the cut-off; one refunded
  already is refunded nothing twice), releases undecided rescue payments, and records
  **`ClubCancelled` on the proposal** with the people still in: `Proposal.owes_a_new_card`
  and `owed_to` (the leaver is not owed), the projection's `proposals.club_cancelled`
  (migration 0043) beside `ended = 'TURNED_DOWN'` in `owed_a_new_card_in`, so the proposer
  deals them a new card first, **never at that club and hour** — the turned-down rule.
  `CancelledByClub` resumes paused weeks and marks the proposer due everywhere. **Home and
  the details** read `called_off_reason: CANCELLED_BY_THE_CLUB`, `club_cancel_reason`, and
  `money.refunded_grosze`; **nothing goes on anybody's record** (`keeping_of` answers `None`
  for every called-off reason but short at the cut-off). **Check in** is the desk's when the
  club's *We check players in* is on (`check_in_is_off`, `DeskCheckIns` over the club's own
  stream — read whether or not it sells). `FindTheSeat` reads the code (`check_in.read_code`:
  a QR payload names its seat and is checked against the digest; six typed characters,
  spaces, dashes and case ignored, name nothing) and places it: **typed codes are looked for
  among this club's seats today, then this club's ±14 days, then every club's today** —
  each tier one read of the held seats (`BookingDirectory.seats_at`) and a digest a seat, a
  stream read only for the seat the code is — so a
  code for another day (`check_in_code_for_another_day`, `details.starts_at`) or club
  (`check_in_code_for_another_club`, nothing about it said) is told apart from nobody's
  (`404 check_in_code_unknown`, which a leaver's seat and a request's are too); another
  club's code on another day is unknown. `PlayerCheckedIn` is the booking's, once
  (`already_checked_in`, `details.checked_in_at`); tiles carry `checked_in`.
- **Somebody did not come: the report is the Game's** (#547; `games/domain/game.py`,
  `standing.py`, `games/application/no_shows.py`; the mechanics §15.3–§15.4). On a **booked**
  game (`starts_at`) whose hour has come, inside its entry window, with nothing entered, a
  player on the court reports another (`POST /games/{id}/no-shows`, `NoShowReported`); a
  reported player disputes inside **24 hours** (`POST /games/{id}/no-shows/dispute`,
  `NoShowDisputed`, `NO_SHOW_DISPUTE_WINDOW`). **A player the club checked in cannot be
  reported** — `ClubCheckIns`, games' demand, signed in `bookings/infrastructure/games_records.py`
  over the booking's stream, never a copy on the game. A report **is the game's entry**: a
  score is refused beside one (`a_result_is_entered`, `a_no_show_is_reported`), and **the
  game does not count whatever it comes to**. Standings: `NO_SHOW_REPORTED` while any
  undisputed report's day runs (not settled — a later report or a dispute may still come),
  then `NO_SHOW` (settled, in no tally, not rateable) once one undisputed report stood its day;
  **every report disputed is `UNSCORED`** — nobody arbitrates, as with two scores — an
  evening on nobody's record. History is dated from the first report. **The strongest mark is
  two strands**: a stood report is a miss on *shows up* (`attendance_for` reads `NO_SHOW` per
  player: the absent a ghost, everybody else played) **and** a broken booked game on *keeps
  plans* (`keeping_of(…, no_shows=)`, fed by `GameNoShows` once the hour has come); an
  ordinary mark is *keeps plans* alone. Home reads *uncounted · `NO_SHOW`* from the report on
  (`needs_you` for the reported player while they may dispute — `Game.may_dispute`, their
  own report's day); a disputed one is plain
  *uncounted*. The reporter is not on the wire.
- **The club's money, and its day of new bookings** (#548; the mechanics §16.11, §16.12;
  the screens B7, B9). **The Money page** is Proposals', beside the Bookings page
  (`application/club_money.py`): `GET /api/v1/club/money?month=YYYY-MM` reads every booking
  whose game starts in the club's month (`ClubBookings.on_day` over the month's hours) and
  lists those that took money, soonest first — the court, the status, and from
  `BookingTakings` what was collected, refunded, the **card fees** and the **net** (what the
  club keeps, below nought on a game given back whole) — with the month's totals, and
  `paid_out` once a payout carried it (the payouts themselves are `payments.md`'s). **The
  daily summary** is Bookings' (`application/daily_summary.py`, the `new-bookings-summary`
  job): at the close of each club day the desk is emailed *New bookings today* — every
  booking **booked** (`bookings.booked_at`, filled or accepted) since the close before,
  soonest game first, a called-off one marked so — and nothing on a day nothing was booked.
  Sent once: the summary is a stream of its own per club per day
  (`NewBookingsSummarised`, `domain/summary.py`), born in the transaction that queues the
  email, so a second process collides on it.
