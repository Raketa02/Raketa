---
paths:
  - "app/modules/matchmaking/**"
  - "app/engines/matchfit/**"
---

# Matchmaking — what the new games kept

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **The searches, the deck, the radar, the ranking and the candidate index are gone**
  (#579, #580, PRD #569). Every old route — `POST/GET /searches`, `/lineups`,
  `/forecasts`, `POST/GET /interest`, `/deck`, `/deck/reset`, `/passes`,
  `/prompt-declines`, `/radar` — answers *not found* (`tests/api/test_the_old_loop_is_gone.py`).
  With them went the search workbench, the shortlist pipeline, the ledgers and their
  tables (migration `0047`), the "who fits whom" ranking (scoring, its eight terms and
  evidence, the modifiers, Liveness, the quality floor, the line-up enumeration and the
  group objective `G`), the candidate index with its projection, cursor, tail and refresh
  jobs, `make rebuild-candidate-index` and trigger 4 (its three tables dropped by migration
  `0048`), the judged-pairings and ruleset-diff scripts, and the golden walkthroughs. A
  game is made one way now — a group's Games deck books it — and **nothing scores one
  player against another**.
- **What the new games call is pure and small.** `domain/balance.py` is how even a game
  between two sides is forecast to be (`forecast_the_sides`, over the engine's
  `forecast_and_split`), read once for the Games card (`proposals`'
  `MatcherBalanceForecasts`) and the booked game's screen (`GamesCourtPairing`, #575); it
  holds the group σ (`combine_group_sigma`, also read by the proposer, which ranks a
  court's possible sides by the engine's `forecast`) and the sport's `seats_per_side`.
  `domain/level_window.py` is the level window — `|Δμ| < LEVEL_TOL` at each kind of
  game's tolerance — and the newcomer window that narrows it to the competitive one while
  either side is new (ADR-0113), asked of every pair the proposer, the fill and a rescue
  would seat (`proposals`' `MatcherPlayerFit`). The engine's `group_availability` is a
  Games card's overlap grade (`proposals/domain/overlap.py`). `domain/geography.py` and
  `domain/areas.py` are distances to clubs and the areas a record is drawn with.
- **The engine is what those call and nothing else.** `app/engines/matchfit/` holds
  `SearchMode` (the kind of game), `ReliabilityBand` and its floors (Player reliability's
  four bands, read by the record, Members and #661's filter — the six strands left, #659),
  the forecast's shapes (`Forecast`, `Split`, `SigmaCombiner`), `LevelReading`,
  `GridCell`, and `v1/group.py`'s `forecast`, `forecast_and_split`, `forecast_pct` and
  `group_availability` — and since #830 `v1/vibe.py`'s **Social vibe** of a For-fun table
  (ADR-0207 §2, §11): `social_vibe_share`, exact (a `Fraction`, for the proposer's unrounded
  comparison, #831), and `social_vibe`, its whole percent rounded half up
  (`floor(100·x + ½)`); each `None` under two people or with nobody carrying a tag. It is handed
  sets of the tags that count — compared for equality and nothing else, so no tag weighs more
  and related tags earn nothing — and holds no vocabulary: the Player profile's `counted` drops
  💘 before it is asked. No constant and no ruleset section: the bands are the app's. **The ruleset is two sections**: the balance rules and each kind
  of game's level tolerance, in one released dataset
  (`infrastructure/rulesets/r2026_09_15_a.py`), validated at import and never selected by
  the environment. A new number is a new dataset with a new name, never an edit.
- **Three outward demands, contracted in `tests/demands/test_matcher_demands.py`.**
  `AccountHoldQuery` (`NoHoldsExist`) and `AccountStatusQuery` (`UsersAccountStatus`) fail
  **closed** and are the player record's gates (`AccountGates`); `AtStakeQuery`
  (`RatingResultUpdateRule`) fails **soft** and prices a booked game's court side against
  side. `PlayerScoreQuery`, `MatchHistoryQuery`, `HalfBuiltCourtQuery` and
  `SharedCourtQuery` were read by the searches alone and went with them.
