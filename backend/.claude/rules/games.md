---
paths:
  - "app/modules/games/**"
  - "app/modules/matchmaking/infrastructure/games_court_pairing.py"
---

# Games

Moved verbatim from `backend/CLAUDE.md` (2026-09-30), and cut to the booked game when
`challenges` and `plans` were removed (#578); decisions that are load-bearing and not obvious
from the code.

- **A game is opened by a booking, and a result is the record that it happened**
  ([ADR-0137](../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md), #541).
  `app/modules/games/` is event-sourced and adds **no table**: its streams live in
  `event_store` beside everybody else's. **Nothing creates a game over HTTP, nothing moves a
  seat on one over HTTP, and nothing ends one over HTTP.** `bookings` opens the game through
  `OpenPlannedGame` **inline, in the transaction of the fill that booked the court**, and
  vacates a seat (`VacateSeat`, #544), seats a rescue (`TakeASeat`, #545), calls a game off
  at its cut-off (`CallOffGame`, #544) and calls it off whole for its club
  (`CallOffTheWholeGame`, #547) the same way — all through
  `bookings/infrastructure/games_opening.py`. **The booking's id sits in `challenge_id`**, on
  the event, the aggregate, the commands and `GameRepository.for_challenge`: the field keeps
  the name it was born with when a challenge's completed line-up opened games, because
  renaming a stored field is a version 2. **On the wire it is `booking_id`** (`GET /games`,
  #578), the same key a game's chat is filed under, so no field calls a booking a challenge.
  **One booking is one game**: `OpenPlannedGame` answers `None` for a booking that already
  has one, and `bookings` treats that as a bug upstream rather than a retry.
- **The line-up is frozen until somebody leaves it**
  ([ADR-0162](../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
  `SeatVacated` opens the seat on the game — drawn `player_id: null`, never dropped — and a
  rescue's `LineUpReseated` fills one open seat at a time (`LineUp.seated`, the first open one
  on the leaver's side), so the stream reads find the newcomer and the room's members (the
  line-up) take them in. The court may still be short after a rescue; `departed` is emptied
  only once it is whole. A result is refused while a seat is open
  (`the_court_has_an_open_seat`), every fold reads the current court, and the pairing read
  omits the forecast, the split and the stakes until it is whole. A seat no longer moves once
  the game is not awaiting its entry (`the_line_up_is_settled`).
- **Four ends are folded from the record and the clock, and the fifth is announced; none is
  stored.** There is no `ResultConfirmed`, no sweep and no job, because a derived standing has
  exactly one place to be true; *silence confirms* is a clock passing, so the test for it
  advances a clock and there is deliberately no method called `confirm`. `GameCalledOff` may
  announce its end only because no arrangement of the record could reach it (ADR-0142 §3's
  exemption): it is read first by `standing_of`, in `SETTLED`, out of `PLAYED`, and **in no
  tally**, and it says who (`called_off_by`, ADR-0172 §4) — nobody, for a booking's cut-off
  and its club's cancel. **`CallOffGame` steps over a game that *started short*** and over
  nothing else: a booking's cut-off call-off can arrive after its hour, and the game keeps the
  end it already reached. The step-over a reopened challenge court needed over a ghost went
  with the challenges, as did the old card's dismissal (`POST /games/{id}/dismissal`) —
  `games.dismissed` is retired: nothing writes it, and it stays registered so a stored row
  still decodes and folds to nothing (stored events outlive the code that wrote them).
- **One route resolves three acts** — `POST /games/{id}/result` is a proposal, a correction or
  a counter depending on what already stands, so a client cannot mislabel one, and there is no
  rejection endpoint because *a counter must carry a score*. And **a bad score is a refusal,
  never an `invariant`**: a score arrives from a person typing it, so a level set answers with
  `a_score_must_name_a_winner` rather than a 500 — the split `CONTEXT.md`'s *Invariant vs
  Unavailability* names, applied at the one value object in this repository a player composes
  by hand. Its clocks are in `games/domain/windows.py` and **none of them is configuration**.
  Its fourth published read is `ConfirmedResultLedger`, which exists **because nothing
  announces a confirmation**: the rating context walks confirmed counted results forward,
  oldest first, ordered on the derived moment each became final
  ([ADR-0139](../../../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)).
- **It has two inward ports, and the first is a single field wide**: `PlayerNames` puts a
  **name** on a seat and nothing else about the person in it
  ([ADR-0141](../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md); the
  name and never the nickname since
  [ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
  A Level, an area or a run of form on a record of an evening would be an as-of-now fact
  stapled to the past; the name is what four people already knew about each other by the time
  they were on a court together. **The court is the whole of the permission and nothing is
  re-gated against the reader**: a block does not reach into a game already agreed. It is
  **one set read per response** over the union of every court in the answer, and a name
  `users` cannot answer for is `null` with the seat kept. A null there never means *unnamed*:
  the naming is onboarding's first step, so the entry gate holds an unnamed account there and
  `GET /users/me` is the one read where `name` and `nickname` may be null.
- **The second inward port is `CourtPairing`, and it is read *beside* the game and never on
  it** ([ADR-0161](../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
  `GET /games/{game_id}/pairing` answers the forecast, the split, what is at stake and each
  seat's Level — **for the reader**, only for somebody on the court (`404 game_not_found`, one
  code for two cases) and only while the game is `AWAITING_ENTRY` (`409 pairing_is_history`).
  The port is declared in `games`' own types and signed by
  `matchmaking/infrastructure/games_court_pairing.py` on the matcher's side of the arrow, so
  `games` still does not import the matcher. **It answers from the balance forecast
  directly** (#575): the court is read side against side from `rating`'s estimates through the
  engine's `forecast_and_split` under the live ruleset — the reading a Games card makes of the
  same people (`proposals`' `MatcherBalanceForecasts`), so **the card and the game come to one
  number for one court**, and a test says so. Three things are decided in the adapter and each
  is an absence rather than a number: a seat with no rating in the sport leaves the forecast
  **omitted, never provisional**; `at_stake` is omitted on a friendly and on a game is priced
  **side against side** through `AtStakeQuery`'s court-shaped read; and the seats' Levels come
  from `rating`'s **published** read (`RatedPlayerQuery.published_for`). `GET /games` is
  untouched: a seat there still carries a name and nothing else.
- **A booked game is a game with an hour** (#541, `bookings.md`). `GamePlanned.starts_at`
  carries the booked hour (nullable, defaulted: a row written before bookings is a game with no
  hour, and only such a row still measures its entry window from `PLAN_HORIZON`).
  `Game.entry_closes_at` runs from that hour's end plus `ENTRY_GRACE`. *We played* is not yet
  refused before the hour (#544, #547).
- **A booked game whose hour comes with a seat open has *started short*** (#544; the
  mechanics §14.1, §19). `GameStanding.STARTED_SHORT` is folded from `starts_at` and a line-up
  with a seat open at `now >= starts_at`, asked right after a call-off and before the entry
  window. It is in `SETTLED` and **in no tally** (not `PLAYED`, never a ghost): the history walk
  answers `None` for it, so *shows up*, the pairwise read and variety leave it out and nothing
  goes on the record of the players who stayed. A result is refused `the_game_started_short`
  and a seat can no longer move.
- **A booked game takes a report of somebody not coming, and its club's cancel** (#547): two
  standings (`NO_SHOW_REPORTED`, `NO_SHOW`), a 24-hour dispute that falls to `UNSCORED`, the
  desk's check-in asked through `ClubCheckIns`, and `Game.call_off_whole` — a booked game called
  off by nobody whole or with a seat open. Written up in `bookings.md`'s last bullet.
