---
paths:
  - "app/modules/notifications/**"
  - "app/bootstrap/push_demands.py"
  - "app/bootstrap/notification_demands.py"
  - "app/modules/payments/domain/seat_charge.py"
  - "app/modules/payments/application/refunds.py"
---

# Notifications

Decisions that are load-bearing and not obvious from the code (#549, #621; ADR-0189 §5 and
its 2026-10-09 amendment; the mechanics §17.2, Q101, Q102; the screens A7.2, A9).

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
  rescuer** (`seats_taken`), whose join showed them *It's a game!* too. The club's yes
  (*… confirmed your game*) is the club's act and counted for all four.
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
  complete it* and a challenge go only to a reader whose deck shows the card now
  (`Decks` → `ReadGroupDeck.shows`: intent, Games & money, a week or an hour already
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
- **Somebody leaving**: `SeatLeft` tells everybody seated; `RequestWithdrawn` tells the
  people still In **only for a yes taken back** (`GameBrief.withdrawn`) — a share refused
  at the club's yes is the refused player's to be told, and nobody's departure. *Fill in
  alerts* go out on `SeatLeft`: who in the pool switched them on is read first (one query),
  and only they are put to `RescueOffers` — a pool nobody asked to be alerted in is never
  read whole.
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
  amount, the people it names by id, a reason code, and where a tap opens it —
  `BOOKING`, `PROPOSAL` or `DECK`). The words are `application/words.py`'s, drawn at push
  time and again at every read, as an email's copy lives in the backend: a push is shown by
  the phone's system before the app runs. Deployed, an `EXPO_ACCESS_TOKEN` with Expo's
  enhanced push security makes a leaked phone token useless to anybody else.
- **Two registers**: `push_demands.py` (the two adapters of the push port — the recording
  service and Expo, asked over a loopback server speaking Expo's documented API, never
  Expo) and `notification_demands.py` (what Notifications reads of others). Seeded by
  nothing of its own: the seed's drain gives every seeded player their notices, listed,
  and pushes nothing.
