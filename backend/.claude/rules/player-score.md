---
paths:
  - "app/modules/player_score/**"
  - "app/modules/bookings/domain/keeping.py"
  - "app/modules/games/domain/attendance.py"
---

# The Player Score

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A Player Score is what the platform watched, and it keeps no record of its own**
  ([ADR-0140](../../../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)
  §1, which [ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §1 keeps). `app/modules/player_score/` is the seventh context and the first that **keeps no
  record at all** — no aggregate, no repository, no table, no migration. It folds `games`' and
  `bookings`' published ports and does arithmetic over them, because a stored score would be a
  second place for *did that game happen* to be true and the copy is what gets believed. **Its
  port is `PublishedScoreQuery` and not `PlayerScoreQuery`** — the matcher's port of that name
  was the *demand* and this is the *publication*, and ADR-0137's rule applies: the cost of a
  shared word is paid by whoever arrives second.
- **Player reliability is points** (#659; ADR-0195 §1; `domain/points.py`). **Everyone starts
  at 100**; each line on the record has a price — *Didn't come* −25, *Came late* −10, leaving
  after the cut-off with the seat left empty −15, leaving before it (or a card not fixed in
  time) when the empty seat calls the game off −10, a game **played through** +5 — clamped to
  0–100 at each step, taken **in time order** over the last **six calendar months**
  (`remembered_after`: a line counts while younger; on 31 August the window opens on 28
  February). Two lines at one moment take the larger cost first (a call: the booked hour is
  both a game's turnout and its booking's keeping). **Each line is dated when it happened** —
  a game by its booked hour, a keeping by the hour or the cut-off that settled it — so *missed
  on 13 October* drops out on 13 April. The **band** is the engine's (`ReliabilityBand`,
  `RELIABILITY_BAND_FLOORS` in `app/engines/matchfit/core.py`: 90 / 75 / 50, one home for the
  record, Members and #661's filter); **New** is fewer than 3 games played through **ever**,
  so every line is read for it and only the six months for the rest. **The counts** — *turned
  up* of *turned up of*, *late*, *kept* of *kept of*, *left in dispute* — are over the same
  six months; noughts are measured now, not invented. **Everybody asked is answered**: a
  player with nothing reads *100 · New*, so the absence rule this context was written around
  is retired and the record's reliability zone is never omitted. One figure across sports.
- **What each line is is the provider's, and the price is this context's.** `games`'
  `games_on_the_record_for` gives a `GameOnTheRecord` per player per game once
  `Game.turnout_of` is final — `PLAYED_THROUGH` (a played standing, on time: scored, disputed
  or *Played · no score*), `CAME_LATE` (from the arrival or the confirmed claim: final then,
  so priced then, while the game carries on), `DIDNT_COME` (once the late claim's day is
  over), `TURNED_UP_UNCOUNTED` — and `left_in_dispute` (`Game.left_in_dispute_by`).
  `bookings`' `keeping_for` gives every settled `Keeping` with how it was `Broken`
  (`LEFT_AFTER_THE_CUT_OFF`, `CALLED_OFF_BY_LEAVING`) or kept. `PointsFromTheRecord` maps both
  onto `Happened` and calls `score_of`. Both reads are **unbounded**: the window is this
  context's to apply. **Calls made without a ruling** (#659): **the players who came on time
  to a game somebody Didn't come to earn nothing** — `TURNED_UP_UNCOUNTED`, on *Shows up*'s
  count and priced 0, since the game took no score (the ticket's *scored or Played · no
  score*), as one that started short earns those who stayed nothing; ADR-0195 §1's *reached
  its hour full* could be read the other way. Came late is priced at the arrival; the ties
  rule; calendar months.
- **A *Didn't come* is priced once** (ADR-0195 §1): `keeping_of` no longer takes `no_shows`,
  the booking a player Didn't come to reads **kept**, and `bookings`' `GameNoShows` demand,
  its adapter and its register row are gone. **Silence on a score costs nothing**: *answers
  about results* (ADR-0160), `ResultAnswering`, `games/domain/answering.py` and
  `Game.score_put_to_a_side_at` are gone, and so are the strands, `StrandRatio`, the published
  weights and `ReliabilityStrand` — off the wire too. A game the club cancelled is on nobody's
  record. See `bookings.md`.
