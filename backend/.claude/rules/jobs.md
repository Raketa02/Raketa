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
  mechanism and its own ADR. Fourteen jobs today — two went with the challenges (#578), and five with the
  searches (#579): the **exposure roll**, the two **prompt loops** (intent drift,
  availability staleness), the **interest expiry loop** and the **scale-pressure probe**,
  with their settings. The ordinals below are the register's, so the gaps are those. The
  first is the uncommitted-photo sweep, whose
  **retention window is domain and whose cadence is configuration** (those two must not
  swap places), then the candidate index's two loops below — which nothing reads since the
  searches went, and which go with the ranking (#580); the refresh still recomputes
  trigger 4 at every load. The ninth is the **photo re-review backfill**
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
  confirmed result has to a Level, because ADR-0137 refused a `ResultConfirmed` event — a
  confirmation is a clock passing and announces nothing — and recorded that cost by name. A
  player whose game confirmed on Tuesday keeps Monday's Level until it runs. It **holds no
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
  `ends_at` ADR-0153 §5 refuses. It leaves a hole in `event_store.sequence_no`, which the
  candidate index's tail is built for — a gap is stepped over once the snapshot horizon
  proves it permanent, so a destruction costs that projection a tick of lag and never an
  event. `CONVERSATION_GRACE` is domain; only the cadence is a setting.
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
  (`clubs/domain/raketa_terms.py`); only the cadence is a setting.
  The fifteenth and sixteenth are **the proposer** (`proposer`, #540) and **its short tick**
  (`proposer-on-changes`), and **correctness depends on them**: nothing else deals a pick,
  hands a seat a no left to the next best fits or widens a pick at half In. The sweep walks
  every pool; the tick walks the pools a change this process delivered made due, and is
  registered only where an outbox drain runs beside it (the lifespan builds one
  `DueForProposing` per process for both). Safe beside itself with no lock: it writes
  through the dealer's own acts, one transaction each, a pick's id is its game so a second
  process collides on the stream, and whatever the world moved past is refused and counted.
  One pool failing is logged and passed over. What is dealt is domain
  (`proposals/domain/proposer.py`); only the two cadences are settings.
  The seventeenth is the **On request timeout** (`request-timeout`, #543), and **correctness
  depends on it**: every read already refuses a club's answer past its deadline
  (`request_timed_out`) and drops the request from the club's list, but only this calls the
  game off — *Called off · no answer* — frees the court the request held and makes its
  players owed a new card first. Its read names **candidates** (`unanswered`, by state and
  `answer_by`), each one transaction that locks its game first, a conflict counted and
  stepped over. The deadline is the club's time to confirm, a Raketa setting; only the
  cadence (thirty seconds — the window is minutes long) is a setting here.
  The eighteenth is the **cut-off** (`cut-off`, #544), and **correctness depends on it** as
  on the timeout: a booked game with a seat open since before its cut-off reads *called off ·
  short at the cut-off* at every read from the cut-off on (`BookedGame.called_off_reason`,
  `keeping_of`), but only this gives everybody still in their money back, frees the court
  and emails the club. Its read names **candidates** (`short_at_the_cut_off`: `SEAT_OPEN`,
  `open_since < cut_off`, `cut_off <= now` — **no upper bound on the hour**, so a run late
  past a game's start still owes the money back), each one transaction that locks the
  game's proposal row first, a conflict counted and stepped over. The cut-off is the
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
