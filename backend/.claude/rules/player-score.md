---
paths:
  - "app/modules/player_score/**"
  - "app/modules/bookings/domain/keeping.py"
  - "app/modules/games/domain/answering.py"
---

# The Player Score

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A Player Score is what the platform watched, and two strands is what it can see**
  ([ADR-0140](../../../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
  `app/modules/player_score/` is the seventh context and the first that **keeps no record at
  all** — no aggregate, no repository, no table, no migration. It folds `games`' and
  `bookings`' published ports (`challenges`' until #578) and does arithmetic over them, because a stored score would be a
  second place for *did that game happen* to be true and the copy is what gets believed. Four
  things about it are load-bearing. **Its port is `PublishedScoreQuery` and not
  `PlayerScoreQuery`** — the matcher's port of that name is the *demand* and this is the
  *publication*, and ADR-0137's rule applies: the cost of a shared word is paid by whoever
  arrives second. **Three of six strands are live and three are absent, never nought** —
  since #544 the live three are *shows up*, *answers about results* and **keeps plans**, folded
  off `bookings`' `BookingHistoryQuery` (a booked game is a plan with a moment: kept when its
  hour comes with every seat held, broken by leaving so that it is called off at the cut-off,
  or after the cut-off with nobody taking the seat — `bookings/domain/keeping.py`), and *answers challenges* **stood down**
  (challenges no longer wait for answers, the mechanics §15.4; challenges' `answering_for`
  went with it). *Settles up* has no provider, *sportsmanship* is published in its own right
  and the matcher may not read it, and a player with no record at all is absent from the
  answer, which is the one rule the demand suite is written around. **No weight moved**: each
  name keeps its published share, and the matcher's rulesets already weighed *keeps plans* —
  so no ruleset release, no gate moved (no corpus has a Player Score), and no wire enum
  changed; the client's label for `KEEPS_PLANS` is its own to rename.
  **The published weights live in the context and never in a ruleset**, because a weight release
  must not change what somebody's own profile says about them; they sum to a hundred by
  arithmetic and not by rule — 85 for as long as a name was missing — since the blend
  renormalises over the strands present. And **reliability stopped being absent
  platform-wide**: `NoPlayerScoresExist` retired, `build_absent_terms` answers empty and lost its
  argument, a stood-down reliability is now `NOTHING_FROM_THEM`, and the evidence gate counts
  eight live terms rather than seven — excluding nobody, at a margin of zero rather than one.
- **A results strand counts answers, and never agreements**
  ([ADR-0160](../../../docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md)).
  `ReliabilityStrand.ANSWERS_RESULTS` is the third live strand, and the thing to hold in your
  head is that **it is not the strand ADR-0137 struck**. *Confirms results* counted agreements,
  and because silence already confirms a lone score it could only ever have counted
  disagreements — every denominator tried on it docked somebody ADR-0049 protects. This one
  counts **answers**: a counter scores exactly as an acceptance does, so disagreeing costs
  nothing and only silence is priced. Four things are load-bearing. **There is at most one
  opportunity per game and the opener has none** (`games/domain/answering.py`): the entry that
  says *we played* carries a score, so one side asks and the other answers, and once both sides
  have put a score up the argument is capped — filing the opener's silence would price
  **surrender**, which is docking somebody for disagreeing by a later route. **It is the only
  strand that forgets** — twelve months, a named exception to ADR-0140 §4, because turning up is
  a commitment somebody made and answering a score is a habit of opening an app; the window is
  `player_score`'s (`ANSWERED_RESULTS_WINDOW`) and crosses to `games` as an instant, it equals
  the matcher's `horizon_days` by choice, and since a provider may not read the consumer's
  ruleset the two spellings are held together by a **test** rather than by construction.
  **`min_observations` is a bar per strand** — five here, three everywhere else, exhaustive and
  refused if a key is missing — because raising the single number instead would take a newcomer
  with three games and three turn-ups from a full score to no score at all; the bar is the
  *matcher's* and the published figure still has none, which is deliberate: on the sheet the
  honesty mechanism is printing the fraction, and inside a ranking nobody can see it. And it is
  a **ruleset release**, `2026.09.08-a`, with the six-name vectors **restored rather than
  retuned** — ADR-0140 §7's rescaling of five survivors is undone exactly, the two offline gates
  move nothing but a version stamp because no corpus has a Player Score, and the whole claim is
  the one the report cannot print: every player with a record is re-mixed on deploy.
  `2026.08.26-a` is edited once more to say **nought** about a word it never knew.
- **A confirmed no-show is the strongest mark because it is two** (#547; the mechanics §15.4):
  a miss on *shows up* (`attendance_for` reads a `NO_SHOW` game per player) and a broken booked
  game on *keeps plans* (`keeping_of(…, no_shows=)` over `bookings`' `GameNoShows`), where an
  ordinary mark is *keeps plans* alone. No weight moved and no ruleset release. A game the
  club cancelled is on nobody's record. See `bookings.md`.
