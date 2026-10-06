---
paths:
  - "app/modules/matchmaking/**"
  - "app/engines/matchfit/**"
  - "scripts/judged_pairings/**"
---

# Matchmaking — what the new games kept, and the index until #580

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **The searches, the deck and the radar are gone** (#579, PRD #569). Every route —
  `POST/GET /searches`, `/lineups`, `/forecasts`, `POST/GET /interest`, `/deck`,
  `/deck/reset`, `/passes`, `/prompt-declines`, `/radar` — answers *not found*
  (`tests/api/test_the_old_loop_is_gone.py`). With them went their use cases, the search
  workbench, the shortlist pipeline and its golden walkthroughs, the three Redis ledgers
  (exposure, suppression, prompts) with their fail-soft wrappers, the five durable
  ledgers' tables (`search`, `search_candidate`, `interest`, `player_pass`,
  `prompt_decline`, `deck_reset` — dropped by migration `0047`), the five jobs that served
  them (interest expiry, exposure roll, intent drift, grid staleness, scale pressure) and
  `scripts/ruleset_diff/`. A game is made one way now — a group's Games deck books it.
- **What the new games call is pure and small.** `domain/balance.py` is how even a game
  between two sides is forecast to be (`forecast_the_sides`, over the engine's
  `forecast_and_split`), read once for the Games card (`proposals`'
  `MatcherBalanceForecasts`) and the booked game's screen (`GamesCourtPairing`, #575); it
  holds the group σ (`combine_group_sigma`, also read by the proposer) and the sport's
  `seats_per_side`. `domain/level_window.py` is the level window — `|Δμ| < LEVEL_TOL` at the
  tolerance the curve uses — and the newcomer window that narrows it to the competitive one
  while either side is new (ADR-0113), asked of every pair the proposer, the fill and a
  rescue would seat (`proposals`' `MatcherPlayerFit`). `domain/geography.py` and
  `domain/areas.py` are distances to clubs and the areas a record is drawn with.
- **Three outward demands, contracted in `tests/demands/test_matcher_demands.py`.**
  `AccountHoldQuery` (`NoHoldsExist`) and `AccountStatusQuery` (`UsersAccountStatus`) fail
  **closed** and are the player record's gates (`AccountGates`); `AtStakeQuery`
  (`RatingResultUpdateRule`) fails **soft** and prices a booked game's court side against
  side. `PlayerScoreQuery`, `MatchHistoryQuery`, `HalfBuiltCourtQuery` and
  `SharedCourtQuery` were read by the searches alone and went with them.
- **The candidate index tails the log; the outbox delivers side effects**
  ([ADR-0110](../../../docs/adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md),
  [ADR-0111](../../../docs/adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md),
  [ADR-0112](../../../docs/adr/0112-the-snapshot-is-a-per-partition-container-bound-once.md)).
  **Nothing reads it since the searches went**, and it goes with the ranking (#580); until
  then it still runs, so hold both consumers of a domain event in your head.
  `CandidateIndexTail` reads `event_store` by `sequence_no`, takes the one cursor row
  `FOR UPDATE`, and applies **only the contiguous prefix**, because a position is assigned at
  `INSERT` and not at `COMMIT`. A hole is stepped over only once the snapshot horizon proves
  it permanent — **and never on SQLite**, which has neither a horizon nor a concurrent
  appender, so that path is exercised against Postgres or not at all.
  `DatabaseCandidateSource` holds one immutable container per partition per process,
  refreshes it by copying row references, and calls `gc.freeze()` after every load and after
  every refresh that decoded a row — **not** after one that decoded none, because the freeze
  promotes everything tracked and would otherwise leak whatever was in flight, every two
  seconds, for ever. The refresh recomputes trigger 4 (`domain/scale_triggers.py`) at every
  load. Repair is `make rebuild-candidate-index` and **there is no admin route** — a walk
  over `app/api/` and every `presentation/` fails the build if one appears.
- **The Match Fit ranking is still in the engine and nothing calls it** — scoring, terms,
  modifiers, liveness, the floor, the ruleset's weights and the startup checks in
  `app/bootstrap/matchmaking.py` (its evidence-kind check went with the wire union, #579).
  All of it goes in #580; the balance rules and each mode's level tolerance stay.
