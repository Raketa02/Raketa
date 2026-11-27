---
paths:
  - "app/bootstrap/jobs.py"
  - "app/infrastructure/jobs/**"
---

# Background jobs

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **Background work is an `asyncio` loop in the API process, and a job must be safe to
  run beside itself** ([ADR-0092](../../../docs/adr/0092-periodic-jobs-as-embedded-loops.md)).
  `PeriodicJob` (`app/infrastructure/jobs/`) is the whole mechanism — the outbox worker
  is written on it too — and **`app/bootstrap/jobs.py` is where the next job goes**,
  built from the composition root so it reaches the same bucket and event store a
  request does. There is no cron, no beat process and no lock: with N API processes a
  job runs N times per interval, so a job that cannot tolerate that needs a different
  mechanism and its own ADR. **A new job is decided about in the dev console too**: it gets a
  *Run it now* in `app/api/dev/jobs.py`'s `RUN_IT_NOW`, run over the request's session and
  clock through the same builder the job calls, or a line in `NOT_RUN_HERE` saying why not —
  `tests/api/test_games_test_console_time.py` fails a registered job that is neither
  (#592). Fifteen jobs today — two went with the challenges (#578), five
  with the searches (#579): the **exposure roll**, the two **prompt loops** (intent drift,
  availability staleness), the **interest expiry loop** and the **scale-pressure probe** —
  and two with the ranking (#580): the **candidate index's tail and refresh**, with trigger 4
  that the refresh recomputed; all with their settings. The ordinals below are the
  register's, so the gaps are those. The first is the uncommitted-photo sweep, whose
  **retention window is domain and whose cadence is configuration** (those two must not
  swap places). The ninth is the **photo re-review backfill**
  ([ADR-0132](../../../docs/adr/0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md)),
  the job that takes no session — its whole input and output are the object store.
  Every photo uploaded before ADR-0129's checker landed carries `review: allowed` written
  by a pass-through that looked at nothing, and **the note is what tells the three
  populations apart**: no `review-note` key is the pass-through era, `unavailable=…` is a
  photo that arrived while the sidecar was down and that population keeps growing, and a
  full `clip;m=…;p=…;c=…;s=…` was really scored. The job fixes the first two and
  **counts the third without touching it** — reviewed against captions that have since
  moved is a judgement nobody has made, and `PROMPT_SET_FINGERPRINT` is what makes it
  answerable. Four rules, each a way it could go wrong invisibly: it re-reviews
  **through the `PhotoReview` port**, so there is one copy of `verdict_from_similarities`
  and a batch cannot disagree with the upload path about one image; it **never rewrites a
  note that is already right**, because an S3 metadata update is a copy of the object onto
  itself; a run against a sidecar it cannot **reach** stops rather than stamping a fresh
  `unavailable` over an old one, while a refusal about one image is counted and stepped
  over — ending the run on one would stall the job at that photo for ever
  (`PhotoReviewUnavailability.is_about_the_reviewer` is the split); and a note it cannot
  parse reads as *nobody looked* — the deliberate inverse of the sweep, whose action is a delete. The budget, the
  pause and the cadence are settings and none of them selects which photos are chosen.
  The tenth was the **challenge lapse loop** (#252) and, after it, the **hour loop**
  (`unfilled-court`, ADR-0175 §3); both went with the challenges (#578), and their settings
  with them.
  The eleventh is the **rating catch-up**
  ([ADR-0139](../../../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
  the first that appends a domain event and **the only one on this list that correctness
  depends on**. Every other job buys a record or a table's size; this is the only path a
  result settled by a window closing has to a Level, because ADR-0137 refused a
  `ResultConfirmed` event — silence settling a score is a clock passing and announces
  nothing — and recorded that cost by name. **It runs every minute** (#654,
  [ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §5: Levels move within a minute of a result settling; the hourly cadence is retired), and
  *That's right*, which settles at once, moves its game's Levels from the outbox
  (`subscribe_the_rating_settler`, the use case's `settle(game_id, at=…)`, folded at the
  tap) — so the walk usually steps over an agreed game, and an agreement may be applied up
  to a minute before a silence-settled result that became final just before it. It **holds no
  cursor**: every move records the game that caused it, so *have I applied this* is answered
  by replaying the aggregate that would change, and a half-finished run is re-derived in full
  by the next tick rather than being a lost result. Its walk is over every game the platform
  has recorded — the same cost profile as every other read in `games`. The **rule** it applies
  is `engines/racketskill/results.py` and is emphatically not configuration: an environment
  that could pick a K-factor is an environment that decides how a marketplace rates people.
  The twelfth is the **conversation sweep**
  ([ADR-0153](../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)),
  the one that deletes an **aggregate** — a room
  and its whole stream, *destroyed, not delisted*. Correctness does not depend on it: a
  room's end is derived on every read — the game's clock off its own stream (#575) — so
  every route on it answers
  `conversation_not_found` past that instant and every list has already dropped it, whether
  or not anything has swept. What it buys is that the destruction is **real**, which is the
  whole difference between a room that is over and a record with no end. Its read names
  **candidates rather than conclusions**, and here it could not do
  otherwise: a store that could answer *which rooms have ended* would be the stored
  `ends_at` ADR-0153 §5 refuses. It leaves a hole in `event_store.sequence_no`; nothing
  tails the log by position since the candidate index went (#580). `CONVERSATION_GRACE` is
  domain; only the cadence is a setting.
  The thirteenth is the **mail worker** (`mail-delivery`,
  [ADR-0186](../../../docs/adr/0186-email-goes-through-a-port-and-a-purged-queue.md) §2), a queue
  drain written as a job the way the outbox's is, and one **correctness depends on**: nobody
  receives a reset until it runs, and the purge that clears a link and a code off the mail
  queue is its to do. It claims one message per transaction `FOR UPDATE SKIP LOCKED`, so it is
  safe beside itself; a process dying between a send and its commit sends that message again.
  The fourteenth is the **book-by sweep** (`proposal-expiry`, #538), and like the lapse loop
  it **buys the record, not correctness**: a proposal past its book-by is over at every read,
  because every read compares the book-by with its clock, so what it appends —
  `ProposalExpired`, silently — is what a poster will be told from. The book-by is the club's
  (`clubs/domain/rakieta_terms.py`); only the cadence is a setting.
  The fifteenth and sixteenth are **the proposer** (`proposer`, #540) and **its short tick**
  (`proposer-on-changes`), and **correctness depends on them**: nothing else deals a pick,
  hands a seat a no left to the next best fits or widens a pick at half In — but
  `POST /pools/{id}/deal` (#739), which runs the same batch for one pool when a member asks,
  and is never relied on: the phone falls back to the deck as it stands. The sweep walks
  every pool; the tick walks the pools a change this process delivered made due, and is
  registered only where an outbox drain runs beside it (the lifespan builds one
  `DueForProposing` per process for both). Safe beside itself with no lock: it writes
  through the dealer's own acts, one transaction each, a pick's id is its game so a second
  process collides on the stream, and whatever the world moved past is refused and counted.
  One pool failing is logged and passed over. What is dealt is domain
  (`proposals/domain/proposer.py`); only the two cadences are settings.
  The seventeenth was the **On request timeout** (`request-timeout`, #543), which called off
  a request its club did not answer in time; it went with On request (#669; ADR-0196 §1),
  with its switch and its interval, since no club confirms a game.
  The eighteenth is the **cut-off** (`cut-off`, #544, #637; `TheCutOff`), and **correctness
  depends on it**, twice over. A booked game with a seat open since before
  its cut-off reads *called off · short at the cut-off* at every read from the cut-off on
  (`BookedGame.called_off_reason`, `keeping_of`), but only this lets everybody's hold go,
  frees the court and emails the club; and **a full game's shares read *paid* from the
  cut-off on** (`money_of`), but only this takes them — until it runs the club has collected
  nothing and the payout waits. Its reads name **candidates** — the call-offs first
  (`short_at_the_cut_off`: `SEAT_OPEN`, `open_since < cut_off`, `cut_off <= now`), then the
  games with a share still held whose cut-off has come (`HeldShares.due`: the `seat_charges`
  projection, `status = 'HELD'` and `held_until <= now`) — **no upper bound on the hour**, so
  a run late past a game's start still does both; each one transaction that locks the game's
  proposal row first, a conflict counted and stepped over, and a game short at its cut-off is
  never taken (the take re-reads it). The cut-off is the
  club's free-cancellation setting, kept on each booking as it stood at the fill; only the
  cadence (thirty seconds) is a setting here.
  The nineteenth is **club payouts** (`club-payouts`, #548), and **correctness depends on
  it**: nothing else pays a club. At the close of each club day it decides, per club, one
  payout of what the closed days' games over and settled left it — one a day at most — and
  the outbox makes it at the provider and tells the desk (see `payments.md`); the job never
  asks the provider. Its read names **candidates** (`ClubPayoutRepository.owed`: games of
  closed days, a share taken, carried by no payout); whether a game is over is asked of
  `GamesOver` and whether its money is settled of its Seat charges. Safe beside itself: a
  club day's payout is one stream and a game is carried once. When a club is paid is domain;
  only the cadence (five minutes) is a setting. The twentieth is the **new bookings summary**
  (`new-bookings-summary`, #548), which buys the record, not the fact — the Bookings page
  shows a booking the moment it is made: once a club day closes, its desk is emailed the
  day's new bookings, once (a stream per club per day, born with the email).
  The twenty-first is **time to pay** (`time-to-pay`, #625, #626), and **correctness
  depends on it**: a payer's own act past their time already runs it out first, but only
  this reopens the seat for everybody else and lets the holds the others kept go; and the
  book-by sweep leaves a game with a payment awaited for it. Its read names
  **candidates** (`ProposalDirectory.paying_past`, over `proposals.paying_until`), each one
  transaction that locks its game first, a conflict counted and stepped over. The thirty
  minutes are domain (`TIME_TO_PAY`); only the cadence (thirty seconds) is a setting. It
  has a *Run it now*, and a game's pane on the console carries its `PAYMENT_DUE` moment.
  **It runs out a booked game's time to fix the card too** (#639): a holding refused at its
  Holding time, its candidates `BookedGameChanges.cards_to_fix_past` (over
  `booking_seats.card_to_fix_until`), each game one transaction locked first — the player's
  seat opens to Fill in as a leaver's before the cut-off, and their refused holding is let go.
  **And a seat kept for a refused rescuer** (#640): its candidates
  `BookedGameChanges.keeps_past` (over `booking_keeps.until`), each game one transaction
  locked first — `KeptSeatRanOut`, and the rescuer told their time ran out. Correctness
  does not depend on this pass: every read of the keep is off the clock, so the seat is
  offered to everybody the moment it is up; the job records it, clears the projection's row
  and tells the rescuer.
  The twenty-second is **the holding** (`holding`, #639; `TheHolding`), and **correctness
  depends on it**: a share the fill only **checked** — its card's hold would not have lasted
  until the cut-off — is held nowhere until this holds it again at its **Holding time**, four
  days before the cut-off, and until then the cut-off has nothing of that player's to take.
  It is **the one job that asks the provider inline** (over the process's own provider,
  `build_payment_provider`), as the fill does, because whether the hold is made decides what
  the booked game asks of its player: a refused one gives them time to fix the card. Its
  read names **candidates** (`CheckedShares.due`: the `seat_charges` projection, `CHECKED`
  and `hold_at <= now`, and a holding refused for terms or a method, asked again once they
  are fixed), each one transaction that locks the game's proposal row first — a time to fix
  already up run out first — a conflict counted and stepped over; a key per charge, attempt
  and hour, so two processes are answered one hold. **Only while the cut-off is ahead**: a
  game the job reaches only after its cut-off — days of outage — is an operator's question.
  The four days and the six hours a hold must outlast the cut-off by are domain
  (`payments/domain/seat_charge.py`); only the cadence (thirty seconds) is a setting. It has
  a *Run it now* (*hold the shares*), and a game's pane carries its `HOLDING` moment.
  The twenty-third is **How did it go?** (`how-did-it-go`, #663; `AskHowDidItGo` in
  `notifications/application/asking.py`), and it **buys the asking, not correctness**: a
  game waits for its score whether or not it runs. When a Competitive booked game's hour
  ends, all four are asked for the score — a clock passing announces nothing, so no event
  could tell it (`notifications.md`). Its read names **candidates** (`EndedHours.ended`,
  over `BookingDirectory.booked_starting`: `state = 'BOOKED'` and the hour started an hour
  before the window — **no index of its own**, a call: `bookings` has none on `(state,
  start)`, and an index is a migration), the games whose hour ended within `ASKED_WITHIN`
  (30 min, domain: `notifications/domain/notices.py`), each read off its court and asked only while it awaits its score; each
  one transaction. **Safe beside itself with no lock**: the notice is given at the hour's
  end under a key of the game's, so every process tells it on one day's stream — a second
  run tells nothing, and two at once collide on a player's day and the second is counted
  and stepped over. Every game in the window is read on every tick, 60 times over its half
  hour — the price of holding no cursor. Only the cadence (thirty seconds, like the other
  seat jobs) is a setting. It has a *Run it now* (*the hour ends · How did it go?*), and a
  counted game's pane carries its `HOUR_ENDS` moment while nobody has put a score up.
  The twenty-fifth — out of order, beside the seat jobs — is **a friends game's
  invitations** (`invitations`, #751; `RunOutTheInvitations` in
  `proposals/application/friends_games.py`), and it **buys the telling, not correctness**:
  every read says *didn't answer* off the clock (`InvitedSeat.waiting_at`), the accept is
  refused past it, and the cut-off decides the covers whether or not it ran. Each invitation
  whose 24 hours ended is run out (`bookings.invited_seat_ran_out`) and the sender told *Ania
  didn't answer*; a payment the friend was refused for the seat is let go. Its read names
  **candidates** (`FriendsGameBookings.invitations_past`, over `booking_invitations`,
  `answer = 'WAITING'` and `until <= now`, indexed), each game one transaction that locks its
  booking row first, a conflict counted and stepped over. The 24 hours are domain
  (`TIME_TO_ANSWER`); only the cadence (thirty seconds) is a setting. It has a *Run it now*
  (*a friend's 24 hours run out*).
  The twenty-sixth — beside it — is **a friends game's cover warning** (`cover-warning`,
  #752; `WarnTheCovers` in `proposals/application/friends_games.py`), and it **buys the
  telling, not correctness**: the cut-off takes the covers whether or not it ran. A *Split*
  game its sender covers from inside it, inside the day before its cut-off
  (`COVER_WARNING_BEFORE`, domain), with a seat lacking its own payment, is warned once
  (`bookings.cover_warned`, the booking's own *once*). Its read names **candidates**
  (`FriendsGameBookings.cover_warnings_due`, over `bookings`: a sender, not called off, the
  cut-off within the next day), each one transaction that locks its booking row first, a
  conflict counted and stepped over; a candidate warned already, or with nothing unpaid, is
  rolled back. Only the cadence (thirty seconds) is a setting. It has a *Run it now* (*a day
  before the cut-off · the cover warning*). **The cut-off's own step for a friends game**
  is no job of its own: `TheCutOff._take` opens every seat still empty on a covered game
  after settling its covers (`bookings.md`), and a friends game turned ordinary is called
  off short as any game, its booking row locked when no proposal is found.
  The twenty-fourth is **Get your level** (`get-your-level`, #727; `TellGetYourLevel` in
  `notifications/application/get_your_level.py`), and it **buys the nudge, not
  correctness**: nothing waits on it. A day after an account's first group join, while it
  holds no Skill rating, it is told *Get your level so your groups can deal you games.* —
  once per account, ever (`notifications.md`). Its read names **candidates**
  (`GroupJoiners.first_joined`, over `GroupDirectory.first_joined`: `MIN(joined_at)` of
  `group_members` per account, so **the earliest join among the groups it is in now** — an
  account that left every group is none), those whose first join fell
  `GET_YOUR_LEVEL_AFTER` (24 h) ago, within `GET_YOUR_LEVEL_WITHIN` (a week) of it — a
  run that reaches an account later tells nothing, and Home's card still asks — **less
  every account ever told it on any day** (`NoticeDirectory.told`, over `notices`) and every
  account rated in any sport (`RatedAccounts`); each one transaction. **Safe beside itself
  with no lock**: the notice is given a day after the join under a key of the account's, so
  every process tells it on one day's stream and two at once collide there, the second
  counted and stepped over; the never-told filter is what holds *once* across days when a
  leave makes a later join the earliest. A week of joiners is read on every tick. Only the
  cadence (five minutes) is a setting. It has **no *Run it now***: it is an account's, not a
  game's (`NOT_RUN_HERE`).
