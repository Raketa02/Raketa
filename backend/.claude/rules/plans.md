---
paths:
  - "app/modules/plans/**"
---

# Plans

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A plan is the challenge's, and it is born by being used**
  ([ADR-0144](../../../docs/adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
  [ADR-0145](../../../docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md),
  [ADR-0148](../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md),
  [ADR-0164](../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)).
  `app/modules/plans/` is the ninth context and the third event-sourced racket-sport one; it
  adds **no table and no migration**, because the streams live in `event_store` beside
  everybody else's. Eight things about it are load-bearing.
  **Its aggregate id is the challenge's**, so *one plan per challenge for ever* is a fact
  about the store rather than a rule a caller keeps — and it is the one context here whose
  reads need no payload match: *this court's plan* is a stream read and *these courts'
  plans* is an `IN`. One challenge has at most one room and at most one game and both carry
  `challenge_id`, so the room draws the plan by its own id **from its opening** and the game
  the challenge becomes inherits it; the four plan events carry `challenge_id` and are
  registered at **version 2**, with version 1 — `game_id` — deliberately unreadable, because
  no environment but `local` has ever run and its database is disposable.
  **Nothing is written at birth**: there is no opening event, no subscriber to `SeatAccepted`
  or `GamePlanned` and no outbox hop, so the first slot write is the birth — and `GET /plans`
  still answers **one row for every court the reader holds an accepted seat on, written or
  not**, three empty slots and the anchor for a court nobody has written on, because the row
  is what carries the anchor and says there is a plan to draw. An invitee still deciding and
  somebody who left get no row, and are refused as a stranger is: `plan_not_found`, **one
  code for three cases** — and so is the organiser **before the first yes**: their seat is
  accepted from birth and makes no court on its own, because the room the plan is drawn in
  opens on that yes and a slot written earlier would be a line with no room to land in. The
  fold asks for the room's precondition — somebody else's accepted seat, or a game — rather
  than for the room. **Three slot events and no fourth slot** — a place, a day and an
  hour recorded — because *setting a slot and moving one are the same event told with two
  sentences*; there is no completion event (the third recording **is** the completion), no
  clearing event and no cancel. **Beside them is a fourth event that is an act rather than a
  slot** — `PlanLocked`, from
  [ADR-0155](../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
  which supersedes ADR-0144's *there is no lock* and nothing else in it. **The count and the
  lock are two facts**: a complete plan is one everybody *could* agree, and `is_locked` is
  `locked_at is not None` and deliberately not `slot_count == SLOTS`. It announces itself where
  a completed plan may not — no arrangement of the three slots reaches *these people have
  agreed*, which is ADR-0142 §3's test and the one `GamePlanned` fails — and its whole
  destination is a **system line in the room**. It **freezes nothing** (a slot moved afterwards
  keeps the lock and writes its own line) and there is **no unlock**, for the same reason there
  is no clearing event. **And the lock waits for the court** (ADR-0164 §5): where, day and
  hour are proposals anybody on the court may make and move, whole or not, and *we are
  agreed* is refused with a code of its own — `the_court_is_not_whole`, beside
  `the_plan_is_not_complete` and asked before it — until every seat is accepted; a lock
  already taken survives a later departure. Whether the court is whole is a fact the
  aggregate borrows, exactly as `record_day` borrows the anchor. **Nothing derived is
  stored**: not the slot count, not the agreed point, and neither the anchor nor
  `planned_at` is ever written — `planned_at` keeps meaning *when it became a game*, and the
  plan writes to `games` at no point at all. **The horizon runs from an anchor that only
  moves later** (ADR-0164 §4): the challenge's send until the game exists, then the game's
  `planned_at`, so a day set by two of four stays valid when the court fills and the chips
  widen rather than shrink; it rides on the plan row as `anchor`. **The court being over is
  the only thing that freezes the slots** — the game leaving `AWAITING_ENTRY` once there is
  one, the challenge ending before there is — read through *one port asking one question*,
  `PlannableCourts`, which the Plan declares in its own words and contracts on
  `plan_demands.py`: *which courts is this player arranging, and which are history*, every
  challenge on which the reader holds an accepted, live seat, with the two refusals a write
  can produce, the anchor, and whether the court is whole. It is answered by
  `plans/infrastructure/plannable_courts.py`, which folds the challenge and, for a court that
  has become a game, the game, through the two providers' own ports — `conversation_demands`'
  *one rule read against two records* one context over — and its five answers (arranging,
  on and awaiting entry, history, not on it, left it) are each pinned in
  `tests/unit/test_plannable_courts_fold.py`. `games` no longer publishes `PlanningCourt`; the
  one thing it still asks of the Plan, `AgreedMoment`, is keyed by the challenge the game was
  opened from. And
  **one platform zone**, `Europe/Warsaw`, recorded as a locale assumption in the shape
  `weekly_hours.py`'s `_WEEKEND` already uses, with its falsifier named: the first shard
  whose players are somewhere else. The conversion goes through the kernel's `slot_start`
  and nowhere else — **a dead function comes alive**, since it was written for the booking
  grid the 2026-08-25 reset deleted and had no caller in `app/` until now.
  Three cross-module facts are deliberate and all run one way. `PLAN_HORIZON` **stays in
  `games/domain/windows.py` and `plans` imports it**, because its interlock with
  `ENTRY_GRACE` is the argument and two numbers whose relationship is the argument must not
  be separated; **`plans` reads `challenges` as it reads `games`**, through their ports and
  only in `infrastructure/` (ADR-0164 §3); and **`games` may not import the Plan**, which is
  ADR-0145 §4's *"beside that context without being let into it"* made checkable —
  `.importlinter` holds it, and `challenges` and `games` import neither the Plan nor each
  other's aggregates.
