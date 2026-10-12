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
- **Its ends are folded from the record and the clock, and one is announced; none is
  stored.** There is no `ResultConfirmed`, no sweep and no job, because a derived standing has
  exactly one place to be true; *silence confirms* is a clock passing, so the test for it
  advances a clock and there is deliberately no method called `confirm`. `GameCalledOff` may
  announce its end only because no arrangement of the record could reach it (ADR-0142 §3's
  exemption): it is read first by `standing_of`, in `SETTLED`, out of `PLAYED`, and **in no
  tally**, and it says who (`called_off_by`, ADR-0172 §4) — nobody, for a booking's cut-off
  and its club's cancel. **`CallOffGame` steps over a game that *started short*** and over
  nothing else: a booking's cut-off call-off can arrive after its hour, and the game keeps the
  end it already reached. The step-over a reopened challenge court needed over a closed window went
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
  Its fifth published read is `ScoredGames` (#613): which of some games, by id, had a score
  proposed, corrected or countered at or after an instant — ids over the stream index, nothing
  folded — **because a correction re-dates its side's score** and may be made again while the
  other side has not answered, so a game long past its hour can still wait on somebody; Home
  asks it about the games older than the hour it reads from.
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
  `Game.entry_closes_at` runs from that hour's end plus `ENTRY_GRACE`. *We played* is refused
  before the hour (`the_game_has_not_started`, #654).
- **A score is asked once, and settled by one tap or by silence** (#654;
  [ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §5). The rules are **one fold**, `standing.settlement_of` — which score settles and when —
  and the standing, `agreed_score` and `settled_at` all read it, so they cannot disagree.
  *That's right* (`accept_result`) **settles at once and closes the game**: the result is
  final at the tap, no counter is taken after it (so in doubles the first agreement from the
  other side wins), and the six-hour `ACCEPTANCE_GRACE` is retired. A lone score settles by
  silence a day after it went up. **Two scores** settle when the later one's day is up: naming
  the same winner, `CONFIRMED` with the **closer** (`Score.margin`, games won across every set;
  a tie goes to the first put up); naming different winners, **`DISPUTED`** — in `SETTLED` and
  in `PLAYED`, no Level moves, and `Game.left_in_dispute_by` names the two who put the scores
  up (the record's *Results left in dispute*, read by #659). `UNSCORED` went with the no-show
  report, its last case (#657). **A
  correction is refused once the entry window has closed** (`corrections_have_closed`); a
  counter is not a correction and stays open while the score it answers waits. **For fun asks
  nothing**: its first score is the result at once, nobody is asked
  (`score_put_to_a_side_at` is `None`), and no Level moves. The wire carries no agreement —
  it is never pending — so `acceptance` and a proposal's `settles_at` are gone. **Levels move
  within a minute**: `games.result_accepted` is delivered to rating's
  `SettleRatingsOnAnAgreement`, which settles that one game as it stood at the tap
  (`ConfirmedResultLedger.confirmed_counted_result`), and the catch-up runs every minute for
  everything a window closing settled (`jobs.md`).
- **A booked game whose hour comes with a seat open has *started short*** (#544; the
  mechanics §14.1, §19). `GameStanding.STARTED_SHORT` is folded from `starts_at` and a line-up
  with a seat open at `now >= starts_at`, asked right after a call-off and before the entry
  window. It is in `SETTLED` and **in no tally** (not `PLAYED`): the history walk answers
  `None` for it, so *shows up*, the pairwise read and variety leave it out and nothing goes on
  the record of the players who stayed. A result is refused `the_game_started_short` and a
  seat can no longer move. A stream with **no hour** reaches it when its entry window closes
  on a seat still open (#655) — *played* is a full court's word.
- **A full booked game nobody recorded was played: `PLAYED_NO_SCORE`** (#655;
  [ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §2). It replaced `NEVER_PLAYED` — the ghost charged to the whole court — on the wire too
  (`GameStanding`, and Home's `HomeStatus`/`ResultStage`). `standing_of` reaches it when the
  entry window closes with nobody having said *we played*, nobody **Didn't come**, and the
  court **full**. It is in `SETTLED` **and in `PLAYED`**, so everything that reads *played*
  reads it with no branch of its own: *shows up* credits everybody on the court (a final
  *Didn't come* is the only miss left — `Attendance.missed`, which was `ghosts`, and
  `PlayedOutcome` is gone), it is a **counted game** for who they have played with
  (`_counted_and_played`, variety), and sportsmanship draws a card for it. It has **no
  score, no outcome and no Level** — nothing in `ConfirmedResultLedger`. Its moment
  (`became_history_at`) is the entry window closing; its card's (`GamesSettledCourts`) is the
  **booked hour**, since nobody said when. A score after it still meets
  `the_entry_window_has_closed`.
- **Turning up is caught at the court** (#657;
  [ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §3; `domain/attendance.py`, `application/attendance.py`). **Only a real absence starts
  anything**: nothing is recorded about a player nobody tapped. Four acts on the Game, four
  events, four routes under `POST /games/{id}/attendance/…`: **`not-here-yet`**
  (`note_absent`, `AbsenceNoted`) by a player on the court about another, partner included,
  never yourself, never while yourself awaited or Didn't come; **`arrival`** (`note_arrival`,
  `ArrivalNoted`) — *I'm here* naming yourself, *they're here* a courtmate — about somebody
  tapped, the first one counting; both only in the **tap window** (`TAP_WINDOW`, the start to
  30 min after it, `the_tap_window_has_closed` from 17:30) and only **at the club**;
  **`claim`** (`claim_presence`, `PresenceClaimed`) — *I was there* — by the player who Didn't
  come, from the window's end for **`LATE_CLAIM_WINDOW`** (a day); and **`confirmation`**
  (`confirm_presence`, `PresenceConfirmed`) by anybody else on the court inside the same day
  (a call: refused from a player who Didn't come themselves — two absentees cannot vouch for
  each other). **The outcome is folded per player** (`attendance.state_of`, against the
  server's clock): the arrival within `ON_TIME_GRACE` (10 min) is **on time** — nothing
  recorded, the row reads `ON_TIME`; after it **Came late**; no arrival by the window's end
  **Didn't come**, provisional until the late claim's day ends (`CLAIMED` while a claim waits),
  and a confirmed claim is `CONFIRMED`, Came late. **Two standings come of it**, read right
  after `STARTED_SHORT`: `NOT_HERE_YET` while anybody is awaited, and **`DIDNT_COME`** once
  anybody Didn't come — no score and no agreement is taken beside either
  (`somebody_is_not_here_yet`, `somebody_did_not_come`), in no tally, and **not in
  `SETTLED`**, because a confirmation brings the ordinary game back, score and Level
  included. A Came late game carries on as usual. **A score still waiting for its answer
  stops no tap** (a call): the entry window opens at the hour and a score carries no
  location, so an absent player's side could otherwise post one from home at 17:00 and never
  be caught — it waits with the game and counts for nothing if they never come; only a
  **settled** result refuses a tap (`the_result_is_settled` — a For fun score settles at
  once, the one way left round it). **The windows are half-open**: an arrival at exactly
  17:10 is Came late, and a tap at exactly 17:30 is refused. `Game.didnt_come_at` is the final set — the record's (`attendance_for` per player,
  `bookings`' `GameNoShows` on *keeps plans*: the old strongest mark until #659), and
  `Game.attendance_waits_on` is Home's `needs_you` — the awaited player's *I'm here*, the
  absent player's *I was there*, a courtmate's confirmation; while somebody is not here yet
  Home reads *needs result* and needs nobody else. **At the club** is
  decided in the application layer: the tap's one-shot fix (`LocationFix`, whose repr
  withholds it) goes to the inward demand **`GameClubs`** — the booking's club and its map
  point, measured with the platform's great-circle `distance_km`, signed by `bookings`
  (`bookings/infrastructure/game_clubs.py`), since `games` imports neither `bookings` nor the
  matcher — and the Game is handed only a `ClubVerdict`: within `AT_THE_CLUB_WITHIN_M` (300 m),
  allowing the fix's own accuracy up to `ACCURACY_ALLOWED_UP_TO_M` (200 m). **The
  coordinates are never stored** — no event field, no log, no table; an event a tap writes is
  itself the record of *at the club, at that time*, since one from anywhere else is refused
  (`not_at_the_club`, *You can say so only from Ogrody 33.*). **The late claim and its
  confirmation carry no fix** (a call: they are made a day later, from wherever, and what
  proves them is the courtmate). **Every refusal is a plain sentence** on `message`.
  **The no-show report is retired** (ADR-0195 §9): `games.no_show_reported` and
  `games.no_show_disputed` stay registered, decode and fold to nothing, so a game that held a
  report reads `PLAYED_NO_SCORE`; the routes, `NO_SHOW_REPORTED`, `NO_SHOW` and `UNSCORED` are
  gone. Tested in `tests/unit/test_attendance_at_the_court.py` and
  `tests/api/test_attendance_at_the_court.py`.
- **A booked game is called off whole by its club** (#547): `Game.call_off_whole` — called
  off by nobody, whole or with a seat open. Written up in `bookings.md`.
