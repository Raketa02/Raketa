---
paths:
  - "app/modules/challenges/**"
  - "app/modules/games/**"
  - "app/modules/matchmaking/application/search_workbench.py"
---

# Challenges and games

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **The fill names the challenge it completes, and the gate steps aside for that one court**
  ([ADR-0150](../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)).
  Half the mechanism had been written and unreachable since it was authored: `Challenge.invite`
  had no caller anywhere in `app/`, and ⚡ from a challenge could not have worked if it had —
  `_locked` resolves a hand-seated player *out of this search's own pool or not at all*,
  `gate_of` excludes everybody in `open_challenge_ids`, and ADR-0142 holds that pair for the
  whole of `LINE_UP_INCOMPLETE`, so **everybody who accepted your half-built court was by
  construction absent from the pool of the search meant to finish it.** Four things fix it and
  each is narrow on purpose. `POST /lineups` grows one optional **`completing_challenge_id`**,
  and `sport`, `mode` and `locked_seats` are **refused beside it** rather than made optional —
  all three are facts that challenge holds, and a caller supplying one could lock somebody who
  is not in the challenge or forget somebody who is. `search_workbench.bind` takes that id and
  builds `open_challenge_ids` from every open challenge **except** it, which is why
  `OpenChallenge` and `SharedChallenge` grew a `challenge_id`: the exemption is an **input**,
  the roster still counts ten codes, and a court member excluded for any of the other nine
  still falls out — so `locked_seat_not_available` stops being unreachable on this path and
  starts meaning *somebody has been blocked, held or deactivated since they accepted*.
  `pool_for` takes an `excluding` set so **nobody who has answered that challenge is a
  candidate for its own fill**, which keeps `NobodyIsAskedTwice` a backstop rather than a
  screen a player reaches after choosing somebody. And **`POST /challenges/{id}/seats`** is
  the send's shape minus the mint: it re-verifies the send's five facts with the pair rule
  excepting this one court by id, resolves origins for the **newly seated only**, and calls
  `Challenge.invite`. **Any live member may fill; a court that was never a game is nobody's to
  withdraw once somebody else has joined it** (ADR-0165 §4, below) — the case that decides the fill is the mutual-born doubles
  challenge, `LINE_UP_INCOMPLETE` from birth with an "organiser" who is only whoever's yes
  arrived second. The mode is **inherited, or
  resolved from the filler's declared Play intent** on the deck's own rule, and the **window
  is never re-stamped**, so a mutual-born challenge stays window-less for life. **A mutual's
  own mode is decided at the mint, and it is a friendly or nothing** (ADR-0169 §8): the mint
  reads both declarations for the sport through `FriendlyChoiceQuery` — a port in
  `challenges`' words, adapted over `player_profile`'s declaration repository and never over
  the matcher's `mode_for_intent`, whose *no preference → fun* is about weight vectors and
  not about anybody's evening — and stamps `FOR_FUN` when either chose one; *competitive*,
  *no preference* and *undeclared* all leave it absent and the hand-over reads counted.
  The aggregate refuses `COMPETITIVE` on a mutual, and the event's `mode` is nullable with a
  default rather than a version 2, on `SeatsInvited.invited_by`'s argument: a row without it
  was minted when every mutual was counted, and `None` is what it already meant. The cost is
  recorded rather than softened, on the port and on the two routes that meet it: **a lapsed
  invitee is out of that challenge's own pool for as long as it stands** — `already_asked_at`
  feeding `NobodyIsAskedTwice`, per aggregate, and asking them again is a **new** challenge. It is
  **not** the pair rule and reaches no other search: that rule holds the people still arranging
  a game, and a seat that left is not one of them (#393, which retracted ADR-0150 §4's *every
  sport*). `HalfBuiltCourtQuery` is the **sixth** matcher demand and the only
  one whose posture is `CLOSED` without being a gate: a fill that cannot read the court it
  names would silently become an ordinary ⚡ over a pool that still excludes the very people
  it was meant to seat around.

- **A game is opened by a completed line-up, and a result is the record that it
  happened** ([ADR-0137](../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
  `app/modules/games/` is the sixth context and the second event-sourced racket-sport one;
  it adds **no table and no migration**, because the streams live in `event_store` beside
  everybody else's. Four things about it are load-bearing and none of them is obvious from
  the code alone. **Nothing creates a game over HTTP, and nothing moves a seat on one over
  HTTP either** — `challenges` calls `PlannedGameHandover` **inline, in the transaction of
  the acceptance that filled the last seat**, on `MutualChallengeMinting`'s argument: a
  subscriber would have to re-derive *did this accept complete the line-up* by reading
  somebody else's aggregate, and the player who taps the last accept would be told the game
  is on by a screen that cannot yet show it. **A yes can be taken back, and a court is over
  when one is left**
  ([ADR-0162](../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md),
  [ADR-0165](../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)):
  `POST /challenges/{id}/departure` writes `LEFT` over an accepted seat on any court that
  still stands — half built, awaiting, or a game; there is no `not_a_game_yet` — and, where
  the court has become a game, hands `vacate_seat` over on the same port in the same
  transaction, so `SeatVacated` opens the seat on the game — drawn `player_id: null`, never
  dropped — and the next completed line-up hands over a **re-seat** of the same game
  (`LineUpReseated`, same id, same `planned_at`) rather than the opening of another. A result
  is refused while a seat is open (`the_court_has_an_open_seat`), every fold reads the
  current court, and the pairing read omits the forecast, the split and the stakes until it
  is whole. The **moment guard** is three ports and no arrow moves: `games` demands
  `AgreedMoment` of the Plan in its own words (signed in `plans/infrastructure/`, contracted
  on `game_demands.py`), publishes `SeatableCourt` (`games_demands.py`), and `challenges`
  reads it through its own `SeatableGameQuery` — on the departure, the fill and the
  acceptance, and only on a court that has been a game; a half-built court has no moment
  to guard. The challenge folds one fact beside its seats for this, `game_opened`, **off
  the acceptance that completed the line-up** (and the mint of a mutual-born singles) —
  never off `SeatLeft`, which can now be written on a court that was never a game. **The
  ending rule is organiser-blind**: `standing.py`'s `deserted` — *at most one player on it
  and no seat awaiting an answer* — replaces the *no live seat besides the organiser's*
  clause, and **a departure is a no**, so before a game the fold reaches `DECLINED` and the
  room ends with its challenge, and the ending is dated by the departure's own instant
  (`departed_at`, folded off `SeatLeft` for #388's reason). **On a game the fold reaches no
  ending by the seats alone, and the court ends with its game**
  ([ADR-0172](../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md),
  #453): `Challenge.leave` asks the same rule as it records the departure and, when it
  fires on a court that has been a game, writes `ChallengeCalledOff(called_by=the leaver)`
  right after the `SeatLeft` — the seventh standing, `CALLED_OFF`, the second conclusion an
  event may announce, passed on ADR-0142 §3's test because the seats can reach *deserted*
  and cannot say whether that game is called off (a fill's newcomer's *no* deserts a game
  too, and ends nothing). The use case then hands `call_off` over on the same port right
  after the seat, so the seat, the court's ending and the game's end commit together or
  none does: the game is `CALLED_OFF` **naming the leaver** (`called_off_by`, off
  `GameCalledOff.called_by`, the field ADR-0163 §4 kept for this day — their seat is
  vacated, so the court cannot supply the name), singles included, and the room is
  destroyed by whichever of `challenges.called_off` and `games.called_off` is delivered
  first, the other finding nothing (`telling.py` names both). The game admits that caller
  because it folds `departed` off `SeatVacated` — *the people who may act are the people who
  were on the court*. **Every ending names whose act it was** — `ended_by` on the challenge
  read, read by the same fold that dates it (`ending_of`): the leaver or the presser off
  `Conclusion`, the organiser off the stream for a withdrawal, and for the two folded
  endings the occupant of the seat whose leaving is read — a no or a departure on
  `DECLINED`, never a lapse, an exact instant outranking a bound and court order breaking
  what is left. **And `game_id` is on the challenge read, read from `games` and never
  recorded**: `GameOfCourtQuery` is the fourth port on the arrow `challenges → games`, asked
  once per list about the courts the fold says have been a game, and once per act for the
  redraw — before the commit, because it is the store the act just wrote to. **The withdrawal
  route is two acts, told apart by whether the court has been a game** (ADR-0165 §4–§5,
  #426), and since ADR-0172 §1 two events. On a court that was never a game it is ***Remove
  the challenge***: the organiser's,
  admitted **exactly while nobody besides the organiser holds an accepted seat** — before
  anybody has answered, and again once everybody who joined has left, whatever seats are
  still deciding — and refused with `somebody_has_joined` the moment one person is in, since
  a court somebody has joined is nobody's to end for the others; from there the organiser
  leaves like anybody else. ADR-0142 §2's pre-answer refusal is reversed, and the
  withdraw-and-resend it guarded against is an accepted risk with its falsifier named. Two
  things follow from a removed challenge holding seats whose day is still running, and both
  are asserted: an answer on one meets `challenge_is_over` (the seat's own refusals first,
  then the challenge's), and neither `seats_awaiting_answers` nor the lapse loop counts
  it — the read asks the fold, and `Challenge.lapse` records no day the removal cut short,
  which is ADR-0142 §5 on the write side; `WITHDRAWN` is this act's alone. **A court that
  has been a game is nobody's to end, and the route refuses it with `court_has_been_a_game`**
  ([ADR-0175](../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
  §1; *Call it off* lived here under ADR-0163 and ADR-0172 §1 and is gone). Such a court is
  called off two ways and no third, each recording `ChallengeCalledOff` — never a withdrawal
  — and handing `call_off` over on the same port in the same transaction, so `GameCalledOff`
  is the fourth end — read first by `standing_of`, in `SETTLED`, out of `PLAYED`, and **in
  no tally**: **the departure that deserts it** (`deserted`: nobody on it, whoever is still
  deciding; or one player and no seat awaiting — ADR-0175 §2), `called_by` the leaver; and
  **the hour** (ADR-0175 §3), `called_by=None` on both events, written by the
  `unfilled-court` loop every minute over every court somebody ever left (`LeftCourtQuery`),
  for those the fold says are `LINE_UP_INCOMPLETE` and the moment guard says are past their
  hour — the plan's agreed point, or the horizon's end where no day was agreed — or already
  history. **Correctness depends on that loop**: the challenge's fold cannot read a plan, so
  a court past its hour reads *needs a player* until it runs. A ghosted court is called off
  the same way and `CallOffGame` steps over that end — and, since #544, a booked game's
  *started short* — and no other. **The card's
  dismissal is the reader's own act on `games`** (ADR-0172 §5): `POST /games/{id}/dismissal`
  answers `204`, admitted on a `CALLED_OFF` game for somebody on its court and refused with
  `game_is_not_called_off` on every other standing; `GameDismissed` is recorded once per
  player (`games.dismissed`, a second press writes nothing), the aggregate folds the set,
  and `ReadGames` subtracts its reader — as does `ReadChallenges`, through `GameOfCourtQuery`'s
  `dismissed_of`, so the challenge row goes with the card (ADR-0173); and the row has a door of
  its own, `POST /challenges/{id}/dismissal`, for everybody the court asked — the invitee still
  deciding when it was called off has a row and never had a card — which hands the act to
  `Game.dismiss_for_the_court` on the court's word (ADR-0175 §5). Nothing else reads the set,
  and the room it might have reached is gone before a card can be dismissed. **Three ends
  are folded from the record and the clock and the fourth is announced, and all four are
  never stored** — there is no `ResultConfirmed`, no sweep and no job, because a derived
  standing has exactly one place to be true, and `GameCalledOff` may announce its end
  only because no arrangement of the record could reach it (ADR-0142 §3's exemption,
  argued again for `games`); *silence confirms* is a clock passing, so the test for it
  advances a clock and there is deliberately no method called `confirm`. **One route
  resolves three acts** — `POST /games/{id}/result` is a proposal, a correction or a
  counter depending on what already stands, so a client cannot mislabel one, and there is
  no rejection endpoint because *a counter must carry a score*. And **a bad score is a
  refusal, never an `invariant`**: a score arrives from a person typing it, so a level set
  answers with `a_score_must_name_a_winner` rather than a 500 — the split
  `CONTEXT.md`'s *Invariant vs Unavailability* names, applied at the one value object in
  this repository a player composes by hand. Its three clocks are in
  `games/domain/windows.py` and **none of them is configuration**. Its fourth published read
  is `ConfirmedResultLedger`, which exists **because nothing announces a confirmation**: the
  rating context walks confirmed counted results forward, oldest first, ordered on the derived
  moment each became final
  ([ADR-0139](../../../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)).
  It has **two inward ports**, and the first is a single field wide:
  `PlayerNames` puts a **name** on a seat and nothing else about the person in it
  ([ADR-0141](../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md); the name and
  never the nickname since
  [ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md),
  which is also why the port stopped being called `PlayerHandles` — a **handle** is now the
  nickname's word, drawn as `@…` on a record and the You tab and said nowhere). A card is
  what a *searcher* reads to decide about a game that might happen, so a Level, an area or a run
  of form on a record of an evening would be an as-of-now fact stapled to the past; the name is
  what four people already knew about each other by the time they were on a court together, and
  without it the screens named **sides** — a result agreed with nobody, and three padel games in
  a week told apart by nothing but how long ago they were arranged. **The court is the whole of
  the permission and nothing is re-gated against the reader**: the four fail-closed gates decide
  who may be *introduced*, ADR-0095 §7 already settled that a block does not reach into a game
  already agreed, and a name that vanished from a row would be §8's trace. It is **one set read
  per response** over the union of every court in the answer, and a name `users` cannot answer
  for is `null` with the seat kept — the opposite of the shortlist, which drops a row it cannot
  name. A null there never means *unnamed*: sign-up creates an account with credentials only
  and **the naming** (`PUT /api/v1/users/me/name`, one event carrying name and nickname,
  repeatable) is onboarding's first step, so the entry gate holds an unnamed account there and
  `GET /users/me` is the one read where `name` and `nickname` may be null.
  **The second inward port is `CourtPairing`, and it is read *beside* the game and never on it**
  ([ADR-0161](../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)).
  `GET /games/{game_id}/pairing` answers the forecast, the split, what is at stake and each
  seat's Level — **for the reader**, only for somebody on the court (`404 game_not_found`, one
  code for two cases) and only while the game is `AWAITING_ENTRY` (`409 pairing_is_history`),
  because a pairing means what a card means *because this game has not happened*. The port is
  declared in `games`' own types and signed by `matchmaking/infrastructure/games_court_pairing.py`
  on the matcher's side of the arrow, so `games` still does not import the matcher; the adapter
  reads `PairWithACourt` — the challenge card's own use case — so **the card and the game come to
  one number for one court**, and a test says so. Three things are decided in the adapter and
  each is an absence rather than a number: a seat the index cannot describe leaves the forecast
  **omitted, never provisional**, with **no reason beside the absence**; `at_stake` is omitted on
  a friendly and on a game is priced **side against side** through `AtStakeQuery`'s court-shaped
  read, because every seat is known and that is the pair `settle_results` will deliver — which
  is why a four's figure here is not the card's head-to-head one, and why a side with one
  unrated seat is priced over its rated members rather than omitted; and the seats' Levels come
  from `rating`'s **published** read (`RatedPlayerQuery.published_for`), never from the index.
  **Two providers stand behind the one port and fail on their own**: a process with no index
  draws no forecast and still names every Level and prices the court. `GET /games` is
  untouched: a seat there still carries a name and nothing else.

- **A booked game is a game with an hour** (#541, `bookings.md`). A Booking opens it through
  `OpenPlannedGame` exactly as a completed line-up does — the booking's id in `challenge_id`,
  the arrangement it came from — and `GamePlanned.starts_at` carries the booked hour
  (nullable, defaulted: every older row is a game with no hour). `Game.entry_closes_at` runs
  from that hour's end plus `ENTRY_GRACE` rather than `planned_at + PLAN_HORIZON`, because a
  booking a fortnight ahead would otherwise ghost before it was played; every other rule here
  is unchanged. *We played* is not yet refused before the hour (#544, #547).
- **A booked game whose hour comes with a seat open has *started short*** (#544; the
  mechanics §14.1, §19). `GameStanding.STARTED_SHORT` — the seventh standing, and the fourth
  end the record and the clock reach — is folded from `starts_at` (only a booked game has
  one) and a line-up with a seat open at `now >= starts_at`, asked right after a call-off and
  before the entry window. It is in `SETTLED` and **in no tally** (not `PLAYED`, never a
  ghost): the history walk answers `None` for it, so *shows up*, the pairwise read and
  variety leave it out and nothing goes on the record of the players who stayed. A result is
  refused `the_game_started_short`; a seat can no longer move; and `CallOffGame` **steps over
  it** as it steps over a ghost, since a booking's cut-off call-off can arrive after the hour.
  Bookings vacate and call off a booked game through games' own `VacateSeat` and
  `CallOffGame` (`bookings/infrastructure/games_opening.py`), the booking's id where a
  challenge's is.
- **A booking's rescue takes one open seat at a time** (#545): `Game.take_seat` records a
  `LineUpReseated` whose court has one more seat filled — the first open one on the leaver's
  side (`LineUp.seated`) — through games' own `TakeASeat`, so the stream reads find the newcomer
  and the room's members (the line-up) take them in. Unlike a challenge's re-seat the court may
  still be short after it; `departed` is emptied only once it is whole. Refused once the game
  is no longer awaiting its entry (its hour has come).
- **A booked game takes a report of somebody not coming, and its club's cancel** (#547): two
  standings (`NO_SHOW_REPORTED`, `NO_SHOW`), a 24-hour dispute that falls to `UNSCORED`, the
  desk's check-in asked through `ClubCheckIns`, and `Game.call_off_whole` — a booked game called off
  by nobody whole or with a seat open. Written up in `bookings.md`'s last bullet.
