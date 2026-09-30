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
  mechanism and its own ADR. Fourteen jobs today — the uncommitted-photo sweep, whose
  **retention window is domain and whose cadence is configuration** (those two must not
  swap places), the candidate index's two loops below, the **exposure roll**, the
  first job here that takes no database session at all, the two **prompt loops**
  (intent drift, availability staleness), which write no value anywhere — each raises a
  question into the prompt ledger and stops, and every threshold behind them is domain
  in `matchmaking/domain/prompts.py` while only the cadences are settings — and the
  **interest expiry loop**, the first of two that delete anything. Turning that one off
  changes no rule a domain test could observe (every ledger read is bounded by `now`,
  so a lapsed yes lifts nobody whether or not it has been swept); what it buys is a
  table the size of what is live, and the one figure a lapsed row could ever be asked
  for — *yeses that expired having never lifted anybody*, `INTEREST_TTL`'s only day-one
  falsifier, which cannot be computed once the rows are gone. The eighth is the
  **scale-pressure probe** — the only job whose work *is* its own scheduling: it measures
  how late the loop woke it, and closes the fifteen-minute window
  [`scale-posture.md`](../../../docs/specs/matchmaking/scale-posture.md) §4 states trigger 1
  over. It reads this process's own counters and writes nothing anywhere, so it needs no
  session and no store, and *N processes, N runs* is what the trigger wants — it is
  stated **per worker**. The ninth is the **photo re-review backfill**
  ([ADR-0132](../../../docs/adr/0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md)),
  the second job that takes no session — its whole input and output are the object store.
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
  The tenth is the **challenge lapse loop** (#252), and it is the only job here that
  **appends a domain event**. A seat past its answer window already reads as lapsed, its
  pair already releases and its challenge already stands as `LAPSED` — a standing is
  folded from the seats and the clock and stored nowhere, so a reader asking *is this
  challenge still open* between a deadline and a sweep gets the same answer either way.
  What the loop buys is the **record**: a `SeatLapsed` in the log, so that *answers
  challenges* has a denominator. What it appends is never a `SeatDeclined` — **a lapse is
  not a decline**, and a Strand that filed silence as judgement would be measuring the
  wrong people. Its read names **candidates rather than conclusions** and that is
  deliberate: a store that could filter on *has this seat lapsed* would be the derived
  standing, stored. `ANSWER_WINDOW` is domain; only the cadence is a setting.
  The eleventh is the **rating catch-up**
  ([ADR-0139](../../../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
  the second that appends a domain event and **the only one on this list that correctness
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
  the second that deletes anything and the only one that deletes an **aggregate** — a room
  and its whole stream, *destroyed, not delisted*. Correctness does not depend on it: a
  room's end is derived on every read — the game's clock off its own stream, or its
  challenge being over, asked of `challenges` — so every route on it answers
  `conversation_not_found` past that instant and every list has already dropped it, whether
  or not anything has swept. What it buys is that the destruction is **real**, which is the
  whole difference between a room that is over and a record with no end. Like the lapse
  loop its read names **candidates rather than conclusions**, and here it could not do
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
