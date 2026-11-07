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
#625, #626, #663, #673; ADR-0189 §5 and its 2026-10-09 amendment; ADR-0195 §3, §5; the
mechanics §13, §17.2, Q101–Q105, Q107–Q110; the screens A7.2, A9).

- **A player is told, and nothing asks** (`.importlinter`'s *No context knows
  Notifications exists*). `notifications/application/telling.py` subscribes to
  `proposals`', `bookings`', `payments`' and — since #663 — `games`' events, as a room
  is told (ADR-0146 §5) — **its `TOLD_ABOUT` table is the only list of what an event
  tells a player**, and `application/asking.py`'s `AskHowDidItGo` and
  `application/get_your_level.py`'s `TellGetYourLevel` the two notices a clock tells — and
  reads what a notice says through ports of its own (`GameBriefs`, `GameCourts`,
  `EndedHours`, `Decks`, `PaidShares`, `SeatOffers`, `Names`, and for *Get your level*
  `GroupJoiners` and `RatedAccounts`), signed in
  `infrastructure/told_by.py` over Proposals' own deck (`ReadGroupDeck.shows`) and
  `RescueOffers`, the Booking, the Game and the Seat charge. The teller and the pusher write, so both are added **per
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
  join or confirmed payment that left no seat open (`Fill.run(by=…)`), `None` for a paused
  yes coming back, and read as `GameBrief.filled_by` — and **a rescuer** (`seats_taken`),
  whose join showed them *It's a game!* too.
- **No notice waits on a club** (#669; ADR-0196 §1): no club confirms a game, so
  *It's a game! · … answers by*, *… confirmed your game* and *… said no* / *… didn't answer
  in time* (`WAITING_FOR_THE_CLUB`, `CLUB_CONFIRMED`, `CLUB_COULD_NOT_TAKE_IT`) went with On
  request, with their words and their reasons. **A deadline on a notice is kept on it**
  (`Notice.until` → `NoticeGiven.until` → `notices.until`, migration 0051) and said against
  **the moment it was given** (`Said.given_at`): the hour alone that day, the weekday and the
  hour on another, so the row reads the same later in the list.
- **The card a club's cancel promised is told** (#622; the mechanics Q107) — always on,
  never capped, never emailed:
  - **`NEW_GAME`** — *Your new game · Fri 19:00 at Bonarka Arena* / *The same players ·
    40 zł a share — say yes to book it.* — on `proposals.redealt`, which names the card
    (`card_id`) and **those the owed game promised it to who are on it** (`player_ids`:
    `owed_to` ∩ the card's names — a best fit completing the card was promised nothing,
    and is dealt it like any card), told to those of them whose deck shows the card now
    (`Decks`), opening the group's deck with it on top (`DECK`, the card's own game, pool,
    sport and kind). Once per card: `Redealt` is recorded once per owed game. **A card the
    proposer deals for any other reason tells nobody** — a lost court hour's new card first
    included, which no notice promised; older `Redealt` rows name no card and tell nobody.
    **At the club and hour the cancel took it names the kind of court** (#673; Q123) — *The
    same players · outdoor · 40 zł a share — say yes to book it.* — since the kind (or the
    price) is then what changed: the teller compares the card's club and hour with the
    cancelled game's (`GameBriefs.about` of each) and asks the deck for the kind the card
    promises (`Decks.kind_of_court`, over `ReadGroupDeck.kind_of_court` — the deck's own
    `CourtKinds` read), kept on the row as `notices.indoor` (migration 0059's column, so the
    row reads the same later); `None` there when its free courts are mixed, and never asked
    at another club or hour, which names no kind.
  - **The cancel notice promises it** (#673; Q123): the players still in read *Bonarka Arena
    cancelled padel · Thu 15 Oct, 19:00 because a court needs repair. We'll look for another
    game for you first.* — the email's own line (`words.py`'s `_called_off`, the club's
    cancel only). A leaver's cancel notice and a game short at its cut-off promise nothing.
- **The club's own Move is told** (#671; the mechanics §16.4, §17.2, Q122) — always on,
  never capped, never emailed, since no money moves:
  - **`GAME_MOVED`** on `bookings.court_moved` — *Bonarka Arena moved your game to Court 3 ·
    Thu 19:00* / *Padel · indoor · nothing else changes* — to everybody with a seat on the
    booking (`GameBrief.seated`), opening the booked game (`BOOKING`). **The court and its
    kind are the event's, and kept on the notice** (`Notice.court_name`, `indoor` →
    `NoticeGiven` → `notices`, migration 0059, defaulted `None` for every other kind and
    every row before), so the row reads *Court 3 · indoor* after a second move too; a
    notice told without them says *another court*.
  - **A move by cancel says why** (#672; the mechanics §16.9, Q122): the same `GAME_MOVED`,
    told off the same `bookings.court_moved`, which then carries the cancel's `reason` and
    the court it left (`moved_from`) — *Bonarka Arena moved your game to Court 3 · Thu
    19:00* / *Court 2 can't be played · Padel · indoor · nothing else changes*, the court
    left worded per reason (`words.py`'s `_CANNOT_BE_PLAYED`): *can't be played in this
    weather*, *can't be played* (repair), *was booked twice*, *isn't available* (other) —
    a call, since the mechanics give *can't be played* alone. The reason rides on
    `notices.reason`; the court left is kept on the row (`Notice.moved_from` →
    `NoticeGiven` → `notices.moved_from`, migration 0060, `None` on every other kind and
    every row before), so it too reads the same after a second move. Nothing about the
    money is told: nothing moved.
- **A time to pay names its time and never its payer** (#625, #626; Q109, Q110). Always
  on, never capped, and emailed only where money is — the payer's confirm email:
  - **`CONFIRM_PAYMENT`** with `until` — *Confirm your payment by 14:40 to keep your seat* /
    *Padel · Tue 19:00 at Bonarka Arena — the others are waiting.* — while the payer's time
    runs at the delivery (`GameBrief.paying`); a refused share on a game already over tells
    nothing.
  - **`WAITING_FOR_A_PAYMENT`** on `TimeToPayGiven` — *It's a game! · waiting for one
    payment until 14:40* / *Padel · Tue 19:00 at Bonarka Arena. Nobody pays until it's in.*
    — to everybody In but the payers, the filler's copy their own; keyed by the game and the
    deadline, so two refused at one fill, or a payer refused again, tell it once; only while
    the game still waits.
  - **`GAME_BOOKED` · `PAYMENT_CAME_IN`** — *Your Tue 19:00 is booked · you paid 40 zł* /
    *Padel at Bonarka Arena.* on a game that booked on the payment it waited for
    (`GameBrief.booked_on_a_payment`).
  - **`TIME_TO_PAY_RAN_OUT`** on `TimeToPayRanOut` to the payers — *Your time to pay ran out
    · Tue 19:00* / *Your seat is open to others now — confirm your payment to take it back
    while it's free.* — and *filling again* (`FELL_BACK`) to everybody else still In; past
    the book-by, `GAME_CALLED_OFF` · `PAYMENT_NOT_IN_TIME` to them all (*A payment didn't go
    through in time*).
  - **Before the cut-off it is the payer's time to fix the card** (#638; Q113), and only the
    payer's words change: **`FIX_YOUR_CARD`** in place of `CONFIRM_PAYMENT` — *Fix your card
    by 14:40 to keep your seat* / *Nothing is paid now. Padel · Tue 19:00 at Bonarka Arena —
    the others are waiting.* — chosen while the time runs and the payer is in
    `GameBrief.fixing`; and **`TIME_TO_FIX_RAN_OUT`** for those `TimeToPayRanOut.fixing`
    names — *Your time to fix your card ran out · Tue 19:00* / *Your seat is open to others
    now, and you owe nothing — you can still take it back while it's free.* Both always
    on; the others keep *Waiting for one payment* either way.
  - **At the Holding time, on a booked game** (#639): `SeatChargeHoldingRefused` is told as
    `SeatChargeFailed` is — *Fix your card by 19:30 to keep your seat* while the time runs,
    `GameBrief.paying`/`fixing` folding in the booking's cards to fix — and a time run out
    (`SeatLeft.card_not_fixed`) tells the payer `TIME_TO_FIX_RAN_OUT` with reason `SEAT_OPEN`,
    *Your seat is open to others now, and you owe nothing.* (never *take it back*: a leaver is
    never offered their seat), opening the game they left (`you_left`); everybody else is told
    as for any leave.
  - **A rescuer whose share was refused has a seat kept** (#640): `SeatChargeFailed` on a
    booked game the payer holds no seat on is a rescue's (`GameBrief.seated`), told with a
    fact of its own, **`Notice.rescue`** → `NoticeGiven.rescue` (defaulted `False`) →
    `notices.rescue` (migration 0057), so the words say *to take the seat*, never *to keep
    your seat*: `FIX_YOUR_CARD` — *Fix your card by 14:40 to take the seat* / *Your bank
    declined the 27 zł hold — fix it with another card. Nothing is paid now. Padel · Sat 17:00
    at Bonarka Arena — the seat is kept for you until then.* — before the cut-off, and
    `CONFIRM_PAYMENT` by its time after it, `GameBrief.paying`/`fixing` folding in the
    booking's kept seats. `KeptSeatRanOut` tells the rescuer `TIME_TO_FIX_RAN_OUT` (or
    `TIME_TO_PAY_RAN_OUT`, its `to_fix_the_card` saying which) with `rescue` — *The seat is
    offered to others again, and you owe nothing — you can still take it while it's free.* —
    opening the booking; never one who took the seat in the same act (their late
    confirmation ran it out first). Both always on; nobody else is told.
  - **`FellBackToFilling`** — a leave, a paused week, a block or a pair that stopped
    fitting while it waited — is told to everybody still In, as below; a court lost while
    it waited is *called off · nobody paid* with `COURT_LOST_WAITING_FOR_A_PAYMENT`.
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
- **The money notices hang off the money's events.** `SeatChargeKept` is *It's a game! · 30
  zł held* — the cut-off kept on the notice as `until`, when the share is taken (#637), and
  `SeatChargeChecked` the same for a seat only checked far ahead (#639): free to leave until
  the cut-off all the same; a share kept because its card was fixed at its holding
  (`SeatChargeKept.fixed`) and one held again there (`SeatChargeHeldAgain`) tell nothing —
  and `SeatChargeTaken` at once after the cut-off is *It's a game! · you paid*. **The take
  at the cut-off tells nothing** (`SeatChargeTaken.kept`) — the quiet row and receipt of
  Q113 are not built yet. **A hold let go says why** (`SeatChargeReleased.reason`): at the
  cut-off or the club's cancel before it, *Game called off · nothing was taken*
  (`amount_grosze` `null`); a leaver's own let-go is told nobody, and a leaver whose empty
  seat called the game off reads *Nothing was taken from you*. `SeatChargeFailed` is
  *Confirm your payment* (to take the seat, on a booked game). **A refund now says why**:
  `SeatChargeRefundDecided.reason` — the `RefundReason`, now in the payments domain —
  defaulted `None` for older rows: called off at the cut-off or by the club is *Game called
  off · with the refund*, and **a leaver's own refund is told nobody** (their act, and
  emailed). **A seat taken is told when the refund is made** (#641; `SeatChargeRefunded`,
  `_seat_taken_refunded`): *You've been refunded 38,24 zł · your seat was taken* / *40 zł
  less the 1,76 zł kept on your payment — Padel at …* — the refund and what was kept, the
  provider's own figures (`PaidShare.refunded_grosze`, `kept_grosze`, `seat_taken`), the fee
  kept recorded on the notice (`Notice.kept_grosze` → `NoticeGiven.kept_grosze` →
  `notices.kept_grosze`, migration 0055) so it reads the same later; a notice given before
  it says *Somebody took your seat*. **No figure a notice says is an estimate**: a refund
  whose fee is not yet known waits, and so does its telling. The emails stay where they
  were, queued by the acts in `payments` — but the seat-taken refund's, queued when it is
  made (`EmailTheSeatTakenRefund`).
- **Somebody leaving**: `SeatLeft` tells everybody seated. *Fill in
  alerts* go out on `SeatLeft`: who in the pool switched them on is read first (one query),
  and only they are put to `RescueOffers` — a pool nobody asked to be alerted in is never
  read whole.
- **Every ending and fall-back of a full game is told to everybody still in it, in its own
  words** (#623; Q104, Q108) — always on, never capped, and **never saying whose card
  failed, whose week filled or who no longer fits**:
  - **`FellBackToFilling`** — a full game waiting for one payment falling back, to
    everybody still In (`_fell_back`). It says **who took their own yes back**
    (`FellBackToFilling.left`, written by `withdraw_a_yes` — *Leave*, *Withdraw*, leaving
    the group, a block — and empty from the fill's *one game per hour* and *games per
    week* and a pair that stopped fitting). A leaver still out is named — *Oscar Bertran
    left your game — it's filling again* (`SOMEONE_LEFT`, `FILLING_AGAIN`); anything else
    is *Your Fri 19:00 at Bonarka Arena is filling again* / *A seat opened — nobody paid.*
    (`SOMEONE_LEFT`, `FELL_BACK`). A game full again before the delivery — booked, or
    waiting for a payment once more — is told by that.
  - **A full game gone back to filling that ends first** (`GameBrief.fell_back_at`):
    `ProposalExpired` — *… is called off · nobody paid* / *It
    didn't fill again before its last moment to book …* (`BOOK_BY_PASSED`; told already, and
    not again, when it fell back at or after its book-by; a post's poster is told this and
    never *your post didn't fill*) — and `CourtHourLost` — *Its court went to another game
    before it filled again …* (`COURT_HOUR_LOST`). A card that never filled is still told
    nothing.
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
- **Each new step at the court reaches the person it waits on** (#663; ADR-0195 §3,
  §5) — five kinds, **always on**, never capped, never emailed, **each opening the
  game's result screen** (`Opens.RESULT`, the phone's `booking/{game_id}/result`), and
  **told only of a Competitive game: For fun is told none of them**. Each is read off
  the game's court (`GameCourts` → `GameStreamCourts`: the Game's own stream, by its id or its
  booking's) at the event's own instant, so what was answered before the delivery is
  told by nothing:
  - **`NOT_HERE_YET`** on `AbsenceNoted` — *Ivan is at Ogrody 33 and you're not there
    yet* / *Tap I'm here when you arrive — Padel · Wed 17:00.* — to the player tapped,
    **while still awaited**; one who arrived first is told nothing.
  - **`AT_THE_CLUB`** on `ArrivalNoted` — *Oscar is at Ogrody 33* / *Padel · Wed 17:00
    — arrived at 17:22.* — to **whoever first tapped *isn't here yet*** (the absence's
    `noted_by`), on time or late alike; **their own** when they tapped *they're here*
    themselves (the arrival's `noted_by`, Q102).
  - **`HOW_DID_IT_GO`** — *How did it go?* / *Padel at Bonarka Arena · Sat 10 Oct, 17:00
    — put the score up.* — to all four, **at the hour's end**. A clock passing
    announces nothing, so no event tells it: **`AskHowDidItGo`, the `how-did-it-go`
    job** (`jobs.md`), every thirty seconds over the booked games whose hour ended
    within **`ASKED_WITHIN`** (30 min, `domain/notices.py`: *while they are still at
    the club* — a
    run that reaches it later asks nothing; the result screen and Home still ask) —
    candidates off the `bookings` projection (`EndedHours` → `BookedHours`:
    `state = 'BOOKED'`, so a game short or called off is none), each asked only while
    it **awaits its score** (`AWAITING_ENTRY`: no score up, nobody awaited or Didn't
    come). **Given at the hour's end** whenever the run comes to it, keyed by the game,
    so every process tells it on one day's stream and once; each game one transaction,
    a collision counted and stepped over.
  - **`IS_THAT_RIGHT`** on `ResultProposed`, `ResultCorrected` (`CORRECTED`) and
    `ResultCountered` (`COUNTERED`) — *Is that right? · marta put a score up* / *Padel ·
    Wed 17:00 at Ogrody 33. If nobody answers by Thu 18:05, it becomes the result —
    saying nothing costs nothing.*; *… changed the score*; *… put a different score up*
    / *The two scores don't match — unless one side agrees with the other's by Thu
    18:20, it settles then. Saying nothing costs nothing.* — to **those across the net from the poster whose
    agreement it waits on** (`Game.awaits_agreement_from`), naming the person who put
    it up, `until` the moment silence settles it (games' own `settlement_of`: the
    later score's day when two stand). A score agreed with before the delivery asks nobody; a correction asks
    again.
  - **`WERE_THEY_THERE`** on `PresenceClaimed` — *Was oscar at Ogrody 33?* / *oscar
    tapped I was there for Padel · Wed 17:00 — confirm it by 17:30 if so.* — to
    **everybody else on the court who may confirm it** (not absent themselves), `until`
    the late claim's day ends; a claim confirmed first asks nobody.
- **The first notice about no game: *Get your level*** (#727; ADR-0200 §7; the mechanics
  §17.2, Q126) — **`GET_YOUR_LEVEL`**, *Get your level so your groups can deal you games.* /
  *Pick the sports you play — a few questions each.* (the group door's own words), **once per
  account, ever**, to an account in at least one group whose first group join was a day ago
  and which holds no Skill rating. **Always on**, never capped, never emailed, opening
  **`Opens.HOME`**. It carries **none of a game's six facts**: `Notice`, `NoticeGiven`,
  `RecordedNotice` and the `notices` row hold `game_id`, `pool_id`, `sport`, `game_kind`,
  `club_id` and `starts_at` as `None` for it (migration 0062 made the columns nullable; every
  other kind writes all six, and `NoticeGiven` kept its version since no older row reads
  differently), the wire's `game_id`, `pool_id`, `sport` and `game_kind` are `null`, its push
  data is `notice_id`, `kind` and `opens` alone, and its words come from its kind alone
  (`words.py`'s `words_about_no_game`; the list's `_drawn` branches on `game_id`). Told by
  the `get-your-level` job (`jobs.md`): given **a day after the join** under the key
  `GET_YOUR_LEVEL:{player}`, and never to an account ever told it on any day
  (`NoticeDirectory.told`), so a leave that makes a later join the earliest asks nothing
  twice. Candidates are when each account first joined a group it is in now
  (`GroupJoiners` → `DirectoryGroupJoiners`, over the groups' own
  `GroupDirectory.first_joined`) and who holds a rating (`RatedAccounts` →
  `RatingsRatedAccounts`, over rating's published `estimates_for`, one batch per sport).
- **Two notices are about a friendship** (#745; ADR-0202 §1; `friends.md`) — **`FRIEND_REQUEST`**
  and **`FRIENDS_MADE`**, always on, never capped, never emailed, told off `friends.friend_requested`
  and `friends.friends_made` by the teller over a port of Notifications' own, `Friendships`
  (`FriendsOfTheReader` in `told_by.py`, over Friends' `ReadRequestsWaiting` and `ReadRelations`;
  `notification_demands.py`'s tenth row). About no game: `game_id`, `game_kind`, `club_id` and
  `starts_at` are `None`, **the group a request was asked from rides as `pool_id`** and its sport
  as `sport` (both `None` for a link's, whose `reason` is `BY_LINK`), and the person is `people[0]`
  — `player_id` on the wire (`NoticeSchema.player_id`) and in the push data. Words from
  `words.py`'s `words_about_no_game(SaidOfNoGame)`, the group's name read through
  `Names.of_groups`. `FRIEND_REQUEST` is told **once per request, only while its card is on the
  reader's Home at delivery** (`Friendships.waiting_on`), opening `HOME`; **its row leaves the
  list and the bell's number once the card leaves Home** — answered, set aside, cancelled, ended
  or hidden by a block — `ReadRecentNotices` leaving out (`NoticeDirectory.recent(…,
  leaving_out=)`, in the one reading) every `FRIEND_REQUEST` row whose `(people[0], given_at)` is
  not a waiting `(requester, asked_at)` (`NoticeDirectory.of_kind`) — so a request set aside and
  **brought back by opening its requester's link** (#748, `friends.friend_request_brought_back`,
  told nobody) has its row back with its card. `FRIENDS_MADE` goes to whoever
  asked (*… said yes — you're friends*), and to both, `reason` `CROSSED`, when the requests
  crossed (*You and … are friends now*), while they still are, opening **`Opens.RECORD`**, the
  friend's record. No migration: every column was there.
- **Two notices are about an ask for a level** (#749; ADR-0202 §4; the words §29.5; `friends.md`)
  — **`LEVEL_ASKED`** on `friends.level_asked`, to the friend asked: *tomek wants to play padel
  with you.* / *Get your padel level so tomek can add you.* (§29.5's one sentence, split at its
  full stop), `sport` set, `pool_id` `None` (the friend may be in none of the asker's groups),
  opening **`Opens.QUESTIONNAIRE`** — that sport's questionnaire, through the level pass; and
  **`LEVEL_GOT`** on `friends.level_got`, to the friend who asked: *zofia has a padel level —
  you can seat zofia now.* / *In Ogrody open play, on the Friends tab.* (the body a call: §29.5
  gives the title alone; *On your group's Friends tab.* once the group cannot be named), the
  ask's group as `pool_id`, opening **`Opens.PICKER`** — that group's Friends tab picker in
  `sport`. Both **always on**, never capped, never emailed, about no game, the person as
  `people[0]`, and **told only while the two are still friends** (`Friendships.are_friends`) —
  a removal or a block before the delivery tells nobody. Two friends who asked one player are
  each told off their own pair's `level_got`. **A notice about no game hands its push the
  group and the sport it names** (`pool_id`, `sport`, beside `player_id`), so a tap can open
  the questionnaire or the picker — a friend request's push carries them too, unused. No
  migration: `kind` and `opens` are strings wide enough.
- **Five notices are a friends game's** (#751; the words §29.8–§29.10) — always on, never
  capped, never emailed, each off a Booking event, the game briefed off its booking when no
  proposal stands for it (`told_by.py`'s `_a_friends_game`, `GameBrief.sender`, `invited`,
  `whole`):
  **`FRIENDS_GAME_INVITATION`** on `bookings.booked_by_a_friend` — *Tomek invited you to a
  game* / *Saturday 10:00 · Ogrody 33 · Padel · Competitive* — to each friend still invited
  at the delivery, `until` their 24 hours' end, opening `HOME`; **`CANT_MAKE_IT`** and
  **`DIDNT_ANSWER`** on `…invited_seat_declined` / `…invited_seat_ran_out` — *Ania can't make
  it* / *Saturday 10:00 · Invite a friend, or open the seat to Ogrody open play.* — to the
  sender, the group read for them (`reading.py`'s `_NAMING_THE_GROUP`); **`GAME_BOOKED` ·
  `LAST_SEAT_TAKEN`** — *It's a game!* / *… — every seat is taken.* — on the accept that took
  the last seat (`InvitedSeatAccepted.last_seat`), to everybody seated, the accepter's their
  own; and **`GAME_CALLED_OFF` · `BY_THE_SENDER`** — *Tomek called off Saturday 10:00* /
  *Nobody paid.* — to everybody In and every friend still invited, the sender's own copy
  born seen.
  **A friends game's money tells nothing on its own**: `_seats_booked` steps over it, so the
  sender's four holds at send and a friend's at their accept are no *It's a game!*. Not
  built: answering an invitation on Home does not take its row off the bell.
  **Its empty seats add four** (#752; the words §29.8–§29.10): `bookings.seat_invited` is a
  `FRIENDS_GAME_INVITATION` to the friend invited into a seat, the inviter named (and the
  birth's own now goes only to the card's friends); **`INVITED_SEAT_TAKEN`** — *Someone took
  that seat first.* / *{when} · {club}* — to a friend whose invitation somebody else's accept
  or rescue ended, opening `BOOKING`; `bookings.seat_opened` alerts the pool as a leaver's
  seat does (*Fill in alerts*); and **`COVER_WARNING`** on `bookings.cover_warned` — *Saturday
  10:00 · 1 seat still empty* / *At Fri 10:00 you pay 50 zł: your 25 zł and ania's seat.*
  (*… 2 seats still empty* / *… and 2 empty seats.*) — to the sender, opening `BOOKING`,
  `amount_grosze` what the cut-off takes, `until` the cut-off, `people` every seat unpaid.
  *Can't make it* / *didn't answer* go to **the sender**, whoever made the invitation (the
  mechanics §12), and a card seat its answer opened — after the cut-off, or the one the
  cut-off opens as its invitation ends there — **alerts the pool** as any rescue does
  (`_alert_the_pool` reaches only a seat somebody is offered).
  *Someone left your game* on a seat left **empty** reads `reason` **`SEAT_EMPTY`** — *… —
  the seat is empty.* — and no alert is given, since nobody is offered it. **The cover
  line**: inside the day before the cut-off of a *Split* game its sender covers from inside
  it, his copy of *can't make it*, *didn't answer* and *left your game* ends *At Fri 10:00 you
  pay 50 zł: your 25 zł and ewa's seat.* — `GameBrief.unpaid` (`Booking.cover_line`),
  carried as `amount_grosze`, `until` and `people` after the one it is about
  (`Notice.people`'s order, read **by position** through `Said.named`, `None` for one no
  longer named, so nobody is ever named in another's place): **no new notice field and no
  migration**.
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
  opens it — `BOOKING`, `PROPOSAL`, `DECK`, `RESULT` or `HOME`). The words are `application/words.py`'s, drawn at push
  time and again at every read, as an email's copy lives in the backend: a push is shown by
  the phone's system before the app runs. Deployed, an `EXPO_ACCESS_TOKEN` with Expo's
  enhanced push security makes a leaked phone token useless to anybody else.
- **Two registers**: `push_demands.py` (the two adapters of the push port — the recording
  service and Expo, asked over a loopback server speaking Expo's documented API, never
  Expo) and `notification_demands.py` (what Notifications reads of others — since
  #663 the court, `GameCourts`, and the hours just ended, `EndedHours`; since #727 the
  first group joins, `GroupJoiners`, and who is rated, `RatedAccounts`). Seeded by
  nothing of its own: the seed's drain gives every seeded player their notices, listed,
  and pushes nothing.
