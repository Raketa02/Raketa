---
paths:
  - "app/modules/notifications/**"
  - "app/bootstrap/push_demands.py"
  - "app/bootstrap/notification_demands.py"
  - "app/modules/payments/domain/seat_charge.py"
  - "app/modules/payments/application/refunds.py"
---

# Notifications

Decisions that are load-bearing and not obvious from the code (#549, #621, #622, #623,
#625, #626; ADR-0189 §5 and its 2026-10-09 amendment; the mechanics §13, §17.2,
Q101–Q105, Q107–Q110; the screens A7.2, A9).

- **A player is told, and nothing asks** (`.importlinter`'s *No context knows
  Notifications exists*). `notifications/application/telling.py` subscribes to
  `proposals`', `bookings`' and `payments`' events, as a room is told
  (ADR-0146 §5) — **its `TOLD_ABOUT` table is the only list of what tells a player
  anything** — and reads what a notice says through four ports of its own
  (`GameBriefs`, `Decks`, `PaidShares`, `SeatOffers`, `Names`), signed in
  `infrastructure/told_by.py` over Proposals' own deck (`ReadGroupDeck.shows`) and
  `RescueOffers`, the Booking and the Seat charge. The teller and the pusher write, so both are added **per
  delivery run** over its session (`app/bootstrap/events.py`), and the push service is a
  **per-run seam** beside the payment provider: `create_event_batch_for(..., push=)` is
  required — the API's is Expo (`PUSH_PROVIDER`, refused as `recording` deployed), a seed
  run's records and pushes nothing, a test's is the `pushes` fixture.
- **A game is read as it stands, at the event's own instant** (`GameBriefs.about(...,
  at=event.occurred_at)`), never at the delivery's clock — a test's events carry its
  `MovableClock` and the drain runs on the wall clock. A game that moved on before the
  delivery is told as it is: a card that filled meanwhile needs nobody, and whoever took a
  leaver's seat before the `SeatLeft` was delivered is not told the seat was left.
- **Three streams.** *Notification preferences*, one per player under the player's own id,
  born by being used — three choices (*You complete it* and *Challenges for you* on,
  *Fill in alerts* off) and at most ten phones, the oldest let go — projected into
  `notification_preferences` (who wants a choice among a pool, one read) and
  `push_devices` (**a phone is one player's at a time**: registering it as somebody else
  removes it from the last one, in the same transaction). **A push token never enters
  the event store or the outbox** (ADR-0184 §4 — whoever holds it may push to the
  phone): the stream names a phone by the token's SHA-256 (`device_of`), the act hands
  the token to the repository, and `push_devices` is its only home — so a removed phone's
  token is gone, and the table cannot be rebuilt from the stream. A phone signs out with
  `POST /players/me/devices/removal` and the token in the body, never in a path. *A player's notices of one day*,
  one stream per player per **day in Kraków** (`day_id_for`, `uuid5`), so two processes
  telling one player one day collide instead of passing a cap — projected into `notices`,
  the list behind the bell, ordered by the trigger's instant and then the store's
  `sequence_no` (the outbox delivers the rows of one transaction in any order) — a
  notice a later one was bundled into takes that one's instant and moves up. *The bell*,
  one per player under the player's own id (`notice_bell`), below.
- **Seen is one moment per player, never a flag per notice** (#621, Q101 — answering
  #549's handover call 11, *no seen or unread marker*; old notices are still never
  pruned). `POST /players/me/notices/visit` (`application/opening.py`) records
  `RecentNoticesOpened` on the player's **Bell** — only when later than the last by the
  clock, so it is idempotent and never moves back; two phones colliding on the stream
  keep the other's visit — projected into `notices_opened`: when, and **`seen_through`,
  the newest `sequence_no` among the player's notices at the visit**. **The bell's
  number** is `GET /players/me/notices`' `new_count`: the rows past `seen_through`, none
  `own`, counted whole past the rows sent (`ix_notices_player_id_sequence_no`), and each
  row's `new` — one SQL rule (`_is_new`) in one statement, so the two are one reading;
  `last_opened_at` is the moment. **New is read in the store's order, never off the
  clock**: a row's `given_at` is the trigger's instant, and the outbox delivers after the
  act — late by a whole backlog when a delivery is failing — so a notice that reached the
  list after the visit is new whatever it tells happened before it; a bundle rewrites the
  row's `sequence_no`, so a notice that moved up is new again. **The watermark is the
  newest notice listed, never the visit's own place**: a store place is taken at insert,
  not commit, and a delivery can hold one for seconds (a capture in the same delivery)
  — still in flight it is not read, and a later notice of the same day's stream can only
  commit after it, above it. Two windows stay open: a notice of *another* day's stream
  committing between two of the same player's, and one listed between the phone's read
  and its visit, which the route asks the phone to keep short. The count travels on the
  notices' own read and never on Home's: nobody knows Notifications exists.
- **A notice of the player's own act is born seen** (Q102): `Notice.own` →
  `NoticeGiven.own` (defaulted `False` for older rows) → `notices.own` → `your_own` on the
  wire. Listed, never counted, and **pushed to nobody** — `NoticePushes` answers `None`
  for it, so the pusher skips it and the dev console's *Sent* pane says so. Today it is
  `SeatChargeTaken`'s *It's a game! · you paid* to the payer whose own act booked the
  seat: **the filler** — `ProposalFilled.filled_by`, recorded by the fill from the yes,
  join or confirmed payment that left no seat open (`Fill.run(by=…)`), `None` for the
  club's yes and a paused yes coming back, and read as `GameBrief.filled_by` — and **a
  rescuer** (`seats_taken`), whose join showed them *It's a game!* too. And it is the
  copy of *It's a game! · … answers by* (below) to **the player whose act put the game
  to its club** — the same `by`, recorded on the request as `BookingRequested.filled_by`
  (#622). The club's yes (*… confirmed your game*) is the club's act and counted for all
  four.
- **Two notices mark the four matched, and the card a club's answer promised** (#622; the
  mechanics Q103, Q107). Both always on, never capped, never emailed:
  - **`WAITING_FOR_THE_CLUB`** — *It's a game! · Kazimierz Padel answers by 21:15* / *Padel ·
    Fri 19:00. Nobody pays until it confirms.* — on `BookingRequested`, to **everybody on
    the request** (its two sides), opening the game still filling (`PROPOSAL`). Each time
    the game goes to the club: full again after a seat opened, it is a new request with a
    new deadline and all four are told again. **Only while the game still waits on that
    very request** (`GameBrief.answer_by` equal to the event's): a request taken back, or
    answered, before its delivery is told by what came of it — *filling again*, or the
    club's answer — never with a deadline the club no longer has. **The deadline is kept
    on the notice** (`Notice.until` → `NoticeGiven.until` → `notices.until`, migration
    0051) and said against **the moment it was given** (`Said.given_at`): the hour alone
    that day, the weekday and the hour on another — Home's *answers by*, frozen, so the row
    reads the same later in the list.
  - **`NEW_GAME`** — *Your new game · Fri 19:00 at Bonarka Arena* / *The same players ·
    40 zł a share — say yes to book it.* — on `proposals.redealt`, which names the card
    (`card_id`) and **those the owed game promised it to who are on it** (`player_ids`:
    `owed_to` ∩ the card's names — a best fit completing the card was promised nothing,
    and is dealt it like any card), told to those of them whose deck shows the card now
    (`Decks`), opening the group's deck with it on top (`DECK`, the card's own game, pool,
    sport and kind). Once per card: `Redealt` is recorded once per owed game. **A card the
    proposer deals for any other reason tells nobody** — a lost court hour's new card first
    included, which no notice promised; older `Redealt` rows name no card and tell nobody.
- **A time to pay names its time and never its payer** (#625, #626; Q109, Q110). Always
  on, never capped, and emailed only where money is — the payer's confirm email:
  - **`CONFIRM_PAYMENT`** with `until` — *Confirm your payment by 14:40 to keep your seat* /
    *Padel · Tue 19:00 at Bonarka Arena — the others are waiting.* — while the payer's time
    runs at the delivery (`GameBrief.paying`); a refused share on a game already over (the
    club's yes past the book-by) tells nothing.
  - **`WAITING_FOR_A_PAYMENT`** on `TimeToPayGiven` — *It's a game! · waiting for one payment
    until 14:40* / *Padel · Tue 19:00 at Bonarka Arena. Nobody pays until it's in.*; at the
    club's yes (`AT_THE_CLUBS_YES`) *Your Fri 19:00 is waiting for one payment, until 21:20*
    / *Padel at Kazimierz Padel. Nobody pays until it's in.* — to everybody In but the
    payers, the filler's copy their own; keyed by the game and the deadline, so two refused
    at one fill, or a payer refused again, tell it once; only while the game still waits.
  - **`GAME_BOOKED` · `PAYMENT_CAME_IN`** — *Your Tue 19:00 is booked · you paid 40 zł* /
    *Padel at Bonarka Arena.* on a game that booked on the payment it waited for
    (`GameBrief.booked_on_a_payment`); at the club's yes it stays *… confirmed your game*.
  - **`TIME_TO_PAY_RAN_OUT`** on `TimeToPayRanOut` to the payers — *Your time to pay ran out
    · Tue 19:00* / *Your seat is open to others now — confirm your payment to take it back
    while it's free.* — and *filling again* (`FELL_BACK`) to everybody else still In; past
    the book-by, `GAME_CALLED_OFF` · `PAYMENT_NOT_IN_TIME` to them all (*A payment didn't go
    through in time*), as `PaymentNotInTime.at_once` tells the club's yes with no time left.
  - **`FellBackToFilling`** — a leave or a paused week while it waited, at a club that books
    at once — is told as `RequestWithdrawn` is; a court lost while it waited is *called off ·
    nobody paid* with `COURT_LOST_WAITING_FOR_A_PAYMENT`.
- **Caps and bundling are decided as each trigger is delivered** (`NoticesOfADay.give`);
  the screens' C3 *Notifications job* is not built. *You complete it* once a day,
  *Challenges for you* three times — past the cap each **joins the day's last notice of
  its kind** (`NoticeBundled`: the row's `gathered` grows, its words count them, no phone
  is pushed) — and *Fill in alerts* three times, a fourth **not given at all**. A notice's
  `key` is what makes it told once: the delivered event's id for one always on, the kind
  and the game for a chosen one (a card that needs only you after a yes, a withdrawal and
  a yes again is told once a day).
- **No notice is ever sent for a single swipe.** A yes tells nobody that it was said; only
  a yes (or a resumed yes) that leaves **one** seat tells the people **named** on the card
  who have not answered — *the named player keeps two advantages … the You complete it
  alert* (the mechanics §6.3), so a next best fit dealt the seat a no left is dealt a
  card and told nothing. **A post's own yes is its birth**, told as the challenge its
  `VersionDealt` is. **An alert never points at a card the reader cannot find**: *You
  complete it*, a challenge and *Your new game* go only to a reader whose deck shows the
  card now (`Decks` → `ReadGroupDeck.shows`: intent, Games & money, a week or an hour already
  booked, the club, pool membership, the pair rule, *Mixed pairs*).
- **The money notices hang off the money's events.** `SeatChargeTaken` is *It's a game! ·
  you paid* — or, on a booking that waited for its club and to anybody but a rescuer, *the
  club confirmed*: one notice for the club's yes, never two. `SeatChargeFailed` is
  *Confirm your payment* (to take the seat, on a booked game). **A refund now says why**:
  `SeatChargeRefundDecided.reason` — the `RefundReason`, now in the payments domain —
  defaulted `None` for older rows: called off at the
  cut-off or by the club is *Game called off · with the refund*, a seat taken is *You've
  been refunded*, and **a leaver's own refund is told nobody** (their act, and emailed).
  The emails stay where they were, queued by the acts in `payments`.
- **Somebody leaving**: `SeatLeft` tells everybody seated. *Fill in
  alerts* go out on `SeatLeft`: who in the pool switched them on is read first (one query),
  and only they are put to `RescueOffers` — a pool nobody asked to be alerted in is never
  read whole.
- **Every ending and fall-back of a full game is told to everybody still in it, in its own
  words** (#623; Q104, Q105, Q108) — always on, never capped, and **never saying whose card
  failed, whose week filled or who no longer fits**:
  - **`RequestWithdrawn`** — a full game falling back while its club decided, to everybody
    still In (`_fell_back`). The request now says **who took their own yes back**
    (`RequestWithdrawn.left`, written by `withdraw_a_yes` — *Leave*, *Withdraw*, leaving the
    group, a block — and empty from the fill's *one game per hour* and *games per week*, a
    pair that stopped fitting and a share refused at the club's yes). A leaver still out is
    named — *Oscar Bertran left your game — it's filling again* (`SOMEONE_LEFT`,
    `FILLING_AGAIN`); anything else is *Your Fri 19:00 at Kazimierz Padel is filling again* /
    *A seat opened — nobody paid.* (`SOMEONE_LEFT`, `FELL_BACK`). **Past the book-by** the
    game can no longer fill: *Your Fri 19:00 is called off · nobody paid* / *Oscar Bertran
    left after its last moment to book — Padel at Kazimierz Padel.* (`GAME_CALLED_OFF`,
    `LEFT_AFTER_THE_BOOK_BY`; *A seat opened after …* with nobody named). A request whose
    game was full again before the delivery — asked again, or booked — is told by that.
  - **A full game gone back to filling that ends first** (`GameBrief.fell_back_at`, the
    booking's `taken_back_at`): `ProposalExpired` — *… is called off · nobody paid* / *It
    didn't fill again before its last moment to book …* (`BOOK_BY_PASSED`; told already, and
    not again, when it fell back at or after its book-by; a post's poster is told this and
    never *your post didn't fill*) — and `CourtHourLost` — *Its court went to another game
    before it filled again …* (`COURT_HOUR_LOST`). A card that never filled is still told
    nothing.
  - **The club's no and its silence read apart** (`CLUB_COULD_NOT_TAKE_IT`'s reason):
    *Kazimierz Padel said no* and *Kazimierz Padel didn't answer in time*, each with *Padel ·
    Fri 19:00. Nobody paid — you'll get a new card first.* **Both are emailed** — the one
    always-on notice emailed with no money moving — and the email is queued by the act, as
    every email is: Bookings' `CallOffTheRequest`, to each player on the request, over its
    own `PlayerAddresses` (users; `booking_demands.py`).
  - **A leaver is told only when it touches them** (Q108), in a leaver's words and never
    promised a new game: **`Notice.you_left`** → `NoticeGiven.you_left` (defaulted `False`) →
    `notices.you_left` (migration 0052), opening the game they left (`PROPOSAL` — they have
    no seat on the booking). `CalledOffAtCutOff` tells **each leaver whose empty seat called
    it off** (`GameBrief.left_it_short`: an open departure from before the cut-off) *Tuesday's
    19:00 at Bonarka Arena, which you left, was called off* / *Your seat stayed empty, so it
    counts on your record. Your 38,40 zł refund stands.* — the refund read through
    `PaidShares.of_player`, and never emailed: no money moves. A leaver whose seat was taken,
    or whose game still plays, hears nothing. **The club's cancel refunds a paid leaver under
    a reason of their own** (`RefundReason.CANCELLED_AFTER_YOU_LEFT`, split off by
    `CancelTheGame`): *Tuesday's 19:00 at Bonarka Arena, which you left, was cancelled* /
    *Bonarka Arena cancelled it because of the weather — you're refunded 40 zł.*, and the
    email *The game you left was cancelled · you're refunded 40 zł*, with no *we'll look for
    another game*. A leaver refunded already is refunded nothing twice, and told nothing.
- **A push fails soft, and that is deliberate.** The outbox retries a raised delivery at
  the head of every batch with no backoff and rolls back everything delivered beside it,
  so a push service down for an hour, raising, would hold the queue for that hour.
  `PushTheNotice` logs `PushUnavailable` and gives the push up — the notice is listed
  whatever happens, and money is emailed. A phone Expo answers `DeviceNotRegistered` for is
  removed in the delivery's own transaction. Expo's *receipts* (the second read) are not
  asked. **A push is at least once**, like every delivery: a commit that fails after the
  push delivers the notice again, and the phone shows it twice. **What a notice is pushed
  as is decided once** (`NoticePushes`: its words as given, before anything was gathered
  into it, and the data a tap opens): the pusher sends it, and the dev console's *Sent*
  pane shows it for a player with no phone (#594).
- **A notice records facts, never words** (`NoticeGiven`: the game, pool, club, hour,
  amount, the people it names by id, a reason code, a deadline (`until`), whether its reader
  had left the game (`you_left`), and where a tap
  opens it — `BOOKING`, `PROPOSAL` or `DECK`). The words are `application/words.py`'s, drawn at push
  time and again at every read, as an email's copy lives in the backend: a push is shown by
  the phone's system before the app runs. Deployed, an `EXPO_ACCESS_TOKEN` with Expo's
  enhanced push security makes a leaked phone token useless to anybody else.
- **Two registers**: `push_demands.py` (the two adapters of the push port — the recording
  service and Expo, asked over a loopback server speaking Expo's documented API, never
  Expo) and `notification_demands.py` (what Notifications reads of others). Seeded by
  nothing of its own: the seed's drain gives every seeded player their notices, listed,
  and pushes nothing.
