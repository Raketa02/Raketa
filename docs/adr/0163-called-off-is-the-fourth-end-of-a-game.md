# ADR-0163 — *Called off* is the fourth end of a game

- **Status:** Accepted — **§1's *whose act* superseded 2026-09-13 by ADR-0165 §5**: any player on
  the court, with no organiser-first clause and no fallback; and a game is also called off
  **by the departure** that leaves one player on it (ADR-0165 §3). §2–§7 stand — **and three
  sentences superseded 2026-09-15 by
  [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)**:
  §4's *no `called_off_by`* (the game read carries the player and their name, §4 there); §5's
  *`GameCalledOff` reaches the room not at all* (the departure's call-off destroys the room
  through the game, and has since #424 — §6 there); and the record's *the act is the withdraw* /
  §7's *the challenge is `WITHDRAWN`* (*Call it off* records `CALLED_OFF`, the challenge's
  seventh standing, and `WITHDRAWN` is *Remove the challenge*'s alone — §1 there). The
  Consequences' *who withdrew a court whose game had already ended is not recorded* is recorded
  now. §2, §3 and §6 stand whole — **and §1 is empty and §6's remedy retired 2026-09-16 by
  [ADR-0175](0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)**: nobody presses *Call it off* any more; a court still short of a player when its
  hour passes is called off by the platform, with nobody on its record, and a ghosted court
  the same way. §2 and §3 stand.
- **Date:** 2026-09-12
- **Supersedes, by named sentence:**
  [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)'s *"a game reaches exactly
  three ends"* — there are four, and the fourth is the one an act reaches.
  ADR-0144 §*There is no completion
  event and no cancellation*'s *"Calling the game off is out of scope"* — it is in scope, and it
  did not need the state ADR-0137 refused, because the standing is still folded.
  [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md) §2's
  **withdraw half** — *"`ON` has become a game, and ending the challenge would not touch it"*: a
  withdraw on a court that has been a game **does** touch it, in the transaction; and §2's
  *organiser only* gains its fallback — once the organiser's own seat is open, any player still
  on the court holds the exit.
  [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) §2's *"a court that
  has been a game is the one `LINE_UP_INCOMPLETE` that does not [get the act] — until the act
  that touches the game exists"*: this is that act.
- **Amends** ADR-0152 §4: a
  called-off game is **settled** and releases the pair as a ghost does, and the challenge is
  `WITHDRAWN`, which already released it. **Amends**
  [ADR-0153](0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §2's
  fourth arm: the withdrawal that destroys the room in the act now includes one on a court that
  has been a game, and the room's `game_id` is no evidence against it.
- **Cites** ADR-0142 §3 for the exemption `GameCalledOff` passes, and ADR-0162 §9 for the
  fold that let the last person leave *because* this record would give the court an exit.
- Settles [#417](https://github.com/Raketa02/Raketa/issues/417), the second child of
  [#411](https://github.com/Raketa02/Raketa/issues/411); the author's rule 4, grilled 2026-09-11.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** `challenges` is gone, so the withdraw that called a game off and its hand-over through `PlannedGameHandover` (§2's first half), the `SeatableCourt`, plan and mutual bullets in §3, the room destroyed by `challenges.withdrawn` (§5's body) and §6 describe nothing. `CALLED_OFF` stands as the fourth end: settled, in neither tally, refused by `the_game_was_called_off` and `pairing_is_history`, with `called_off_at` on the wire. `Game.call_off` is now told by `bookings`, with nobody on the record, when the cut-off finds a seat still open, and `call_off_whole` sits beside it for when the club takes the court back. `GameCalledOff` destroys the room in the act and writes no line.

## Context

**A reopened court has no exit, and ADR-0162 said so in three places.** Its §2 refused the
withdraw on a court that has been a game *with the code it already has* and named this ticket as
the reason; its §9 let the last person leave rather than refusing it, *"because the alternative is
a rule about a count that #417 replaces with an act"*; and its Consequences named the two costs of
waiting — **a ghost is charged to the people who stayed**, and **a reopened court holds its pair
until it is re-seated or called off**. The second is the failure ADR-0142 §1 and ADR-0143 §8 were
written to remove: two people on a court nobody fills are gone from each other's decks in every
sport for as long as it stands, and a `LINE_UP_INCOMPLETE` court that has been a game never ends
by its seats. The first is the one that makes waiting dishonest rather than merely inconvenient —
`attendance_for` files a court left open until its window closes against the three who did not
leave, exactly as it files any ghost, and *leaving costs nothing* (#411 rule 7) was being paid by
the wrong people.

### What already exists, and why the act is the withdraw

Everything the exit needs but the game's end is already the withdraw's. `Challenge.withdraw`
records `ChallengeWithdrawn`, the one conclusion no arrangement of the seats could reach
(ADR-0142 §3); `WITHDRAWN` is in `ENDED` and out of `ARRANGING`, so the pair releases on the
instant; the room's teller destroys the conversation on `challenges.withdrawn` and writes no line
(ADR-0153 §2); the client already has the sheet, the sentence and the `WITHDRAWN` arm. And the
standing gate already admits the court: a reopened court re-derives `LINE_UP_INCOMPLETE` after
`ON`, which is the one standing the withdraw is for. What ADR-0162 §2 added was a *second*
refusal on `game_opened`, stated as interim, because ending the challenge while the game stood
`AWAITING_ENTRY` with a seat open would have been an ending nobody on the court was told about.

So the act is the withdraw, grown to the court it was refused on, and what is new is the
**hand-over**: the game is told, in the transaction, on the port ADR-0162 already grew for the
departure. A second route — `POST /games/{id}/cancellation`, say — would put the same act on two
records with two permissions and two sheets, and the room's destruction would have to be taught a
second trigger.

### The three things the obvious shape gets wrong

**Organiser-only has no reason left on a reopened court.** ADR-0142 §2 made the withdraw the
organiser's for Phase 1's sake — withdraw-and-resend as a pestering vector, which `NobodyIsAskedTwice`
cannot see across two aggregates. On a court that has been a game the people who agreed did
nothing wrong, the organiser may have been the one who left (#411 rule 1, *the organiser
included*), and a court whose organiser is gone would then have an exit nobody holds — the
precise shape ADR-0142's own Context called a failure. Somebody still on the court has to be
able to end it.

**A game is not called off by its window closing, and a court whose window has closed still
needs the exit.** ADR-0162 §4's moment guard reads the game's standing *and* the plan's moment;
the departure, the fill and the acceptance all meet it. If the withdraw met it too, a reopened
court whose entry window closed on the open seat — a ghost, charged already — would be refused
`game_is_history` and would hold its pair for the life of the database, with a *Call it off*
button on both members' screens that always fails. And a call-off that reached a ghost would
un-ghost it: `called_off_at` read first would flip `NEVER_PLAYED` to `CALLED_OFF`, uncharging a
strand after the fact and contradicting a card the platform already drew, which is
`TheEntryWindowHasClosed`'s argument exactly.

**A called-off game is neither an evening nor a ghost.** `Attendance.ghosts` is *plans whose
entry window closed with nobody ever saying so* — silence, the thing every strand here prices. A
call-off is an act: somebody said *we are not playing this*, before the window closed, with the
seat still open. Filing that as a ghost would charge the people who stayed for somebody else's
departure, which rule 7 refuses; filing it as played would count an evening nobody had. It goes
in neither tally, the way a game still inside its window goes in neither.

## Decision

### 1. Whose act — the organiser, or once the organiser has left, anybody still on the court

> **Superseded 2026-09-13 by ADR-0165 §5.** *The caller is still live on the court, and is the
> organiser or the organiser is not* loses its second clause: **the caller is on the court.** The
> organiser holds no power over a court somebody else has joined, on the author's rule that
> nobody does. One code, the same sentence, its second clause gone. The interim on
> `game_opened` and `ChallengeWithdrawn` carrying no player are as below.

`Challenge.withdraw` admits the organiser, as today, **or any live member once the organiser's
own seat is no longer live** — `LEFT`, or given away to a newcomer after a departure, which
`organiser_seat_required` already answers `None` for. Stated as one rule: *the caller is still
live on the court, and is the organiser or the organiser is not.* **Asked first, and it reads no
standing**: a non-organiser on a court whose organiser is still in is told
`withdraw_is_the_organisers` before the fold is consulted, exactly as before; so is somebody
whose own seat is declined, lapsed or left, because *remaining* means live — **the organiser
who has left included**: the exit fell back to the people still on the court, and a stranger to
them now does not end their game. One code, because it is one sentence — *the act is not
yours* — and the sentence the client prints gains its second clause. On a court that was never
a game the organiser is live from birth and nobody can leave, so the rule collapses to ADR-0142
§2's *the organiser and nobody else*.

The interim refusal on `game_opened` goes, and with it ADR-0162's stated debt.
`OnlyAHalfBuiltLineUpIsWithdrawn` is back to being one code for exactly five standings.

**`ChallengeWithdrawn` still carries no player.** ADR-0142 §3's argument — *only the organiser
may withdraw, and the organiser's seat is on the stream* — is narrowed rather than broken: on a
court that was never a game only the organiser can withdraw, and on one that has been a game the
act reaches the game's record, which names who (§2). The one case that falls between is named in
§6 and costed in the Consequences. A player on the event would also make it *about a seat* to
`test_the_one_event_that_is_not_about_a_seat_is_the_withdrawal`, whose whole job is to keep the
exemption's shape countable.

### 2. The hand-over — `PlannedGameHandover.call_off`, and `Game.call_off`

`withdraw_challenge` gains the one port it refused to have. After the aggregate has recorded the
withdrawal and before the commit, **when the court has been a game** (`has_become_a_game_at`),
it hands `call_off(challenge_id, by, occurred_at)` to `games` on the same port the departure
uses, in the same transaction: the `WITHDRAWN` on the challenge and the end on the game commit
together or neither does. A court that never was a game costs no read and hands over nothing —
the regression the existing withdraw tests hold.

`games` grows `CallOffGame` beside `VacateSeat`, and `Game.call_off(by, occurred_at)` writes
**`GameCalledOff(game_id, called_by, occurred_at)`**. The aggregate keeps its own invariant —
*the button is UX, the server is the correctness mechanism* — and refuses with one code,
`not_a_game_to_call_off`, unless the game is `AWAITING_ENTRY` **with a seat open**; `called_by`
must be on the court, on the one rule every act here shares. The challenge guarantees the open
seat by construction (a withdraw is admitted in `LINE_UP_INCOMPLETE` and nowhere else, and a
game with a whole court is a challenge that is `ON`), so that half is a backstop; the standing
half is not, and §6 says what the use case does with it.

**`GameCalledOff` passes ADR-0142 §3's test the way `ChallengeWithdrawn` does.** The three ends
ADR-0137 folded are readings of the record and the clock; this one is a decision a person took,
and there is nothing on the record to fold it out of. The event is not a second place for the
standing to be true — it is the only one, and `standing_of` reads it as `Challenge.standing_of`
reads `withdrawn_at`: **first**. `games.called_off` joins the durable name list at version 1, the
ninth, and the second on that list that is a conclusion rather than a seat or a score.

### 3. The fourth end — `GameStanding.CALLED_OFF`, settled, and neither played nor a ghost

`GameStanding` gains `CALLED_OFF`, an **end**: `SETTLED` grows to four, and `PLAYED` does not
move. Everything that reads a standing gets the right answer without a branch, and each is
asserted rather than inherited:

- `PlanningCourt.plannable_for` answers `open_to_planning: False`, so a slot write is
  `409 plan_is_history` — nothing new on that route;
- the pairing read (ADR-0161) answers `409 pairing_is_history`, because a pairing is a claim
  about a game that has not happened and this one never will;
- `SeatableCourt` answers `GAME_IS_HISTORY`, though nothing reaches it: the challenge is
  `WITHDRAWN`, and `refuse_a_court_closed_to_seating` now returns before the read on a court
  that has ended, so the departure, the fill and the acceptance all meet the challenge's own
  `challenge_is_over` — the *standing, then moment* order ADR-0162 §1 stated, kept on the one
  path where an ended court that has been a game now exists;
- `state_result` refuses with its own code, `the_game_was_called_off`, asked before the entry
  window exactly as the ghost's `the_entry_window_has_closed` is its own — an entry is the one
  act a player composes, and it is told which end it met; `accept_result` refuses through
  `SETTLED` with `the_result_is_settled`, as it does a ghost;
- `SettledGameQuery` reads `SETTLED`, so a mutual whose game was called off may mint again
  (ADR-0152 §4, amended below); the sportsmanship court reads `SETTLED & PLAYED` and offers no
  card, because there was no evening;
- `ConfirmedResultLedger` never sees it, because it walks `CONFIRMED`.

**In neither tally.** `_pairwise_outcome` answers `None` for a called-off game, so
`played_counterparts`, `attendance_for`, `counted_games_for` and `variety_of` all leave it out —
not `PLAYED`, not `PLANNED_NEVER_PLAYED`, not a ghost. Familiarity is untouched (it reads
`PLAYED` only), *shows up* moves for nobody, and #411 rule 7 holds on the stayers as well as on
the leaver. **This is what ADR-0162 meant by *the honest way out***: a court the stayers cannot
fill is charged to them only if they let the window close on it, and this record gives them the
act that avoids that.

**The pair.** The challenge is `WITHDRAWN`, which released it the moment the withdrawal was
recorded (ADR-0142 §1); the game is `SETTLED`, which releases a mutual's idempotence hold
(ADR-0152 §4). Both are asserted through the routes: the two may challenge each other again
afterwards, in either direction.

### 4. The wire — `called_off_at` beside `played_at`, and no name

> **The name is on the wire since 2026-09-15:
> [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §4.**
> `GameSchema` carries `called_off_by` — the player and their name, from the `called_by` this
> section kept on the record for exactly this day — and the game screen names them. Everything
> else here stands: `called_off_at`, `entry_closes_at` going `null`, the refusal codes.

`GameSchema` gains `called_off_at: datetime | null`, in `played_at`'s shape: `null` until the
act, the act's own instant after it. It is what the client shelves the ending card by — a day
from the end, as `belongsOnTheRail` already reads `entryClosesAt ?? playedAt` — because
`entry_closes_at` would keep a called-off card on the rail for eight days. So `entry_closes_at`
is `null` on a called-off game, as it is once somebody has said they played: the window no
longer matters. **No `called_off_by`.** The room is destroyed and the card says *Called off*;
`GameCalledOff.called_by` is on the record for the day a design wants the name, and that is a
later field rather than a field nothing draws. `GameStanding` gains a value a client switch has
to learn to fall through, and one refusal code reaches the contract — `the_game_was_called_off`
on the entry; `not_a_game_to_call_off` is the aggregate's backstop and no route surfaces it.
Everything is additive.

### 5. The room — destroyed in the act, told nothing new

> **`GameCalledOff` does reach the room** — since the departure's call-off
> (ADR-0165 §3,
> built by #424) arrived with no withdrawal beside it, the room's teller destroys the room on
> `games.called_off` too, and finds nothing where the challenge's own ending got there first.
> [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §6
> says which arm destroys the room on each path; *destroyed in the act, no line, no nudge* stands.

`challenges.withdrawn` already destroys the room, and the arm does not read `game_id`:
`_withdrawn` looks the room up by challenge and destroys whatever it finds, and `lifetime`'s
unanchored conclusion — the only place `game_id is None` is a condition — is consulted on a read
and never on a withdrawal. Both were verified rather than assumed, and the first is now held by a
test that withdraws a court whose room already has its game. `GameCalledOff` reaches the room
**not at all**, and the telling table says why: the challenge's own withdrawal destroys it in the
same transaction, so there is nobody left to read a line and no room to be a length. No line, no
nudge — the news is on the challenge screen and the card.

### 6. A court whose game has already ended by its clock — the withdraw ends the challenge alone

A reopened court can outlive its game's entry window: nobody filled the seat, the window closed,
the game is `NEVER_PLAYED` and charged, and the challenge — which cannot read the game — is
still `LINE_UP_INCOMPLETE`, still holding its pair, still drawing *Fill the seat* and *Call it
off* on two people's screens. The fill is already refused there (`game_is_history`). **The
withdraw is admitted**, and `CallOffGame` **steps over a ghost** rather than raising: the ghost
stands as the end it already is, the challenge is `WITHDRAWN`, the pair releases, and the room —
already past its end on `planned_at`'s anchor — is destroyed if the sweep has not reached it.
`Game.call_off` still refuses; the leniency is the use case's and it is **one standing wide**,
`NEVER_PLAYED` and nothing else: *a game that has already ended by its clock has nothing to call
off, and the withdraw was never about it.* Every other end is unreachable from a challenge the
withdraw admits — a played game has a whole court, and a whole court is a challenge that is
`ON` — so on any of them the aggregate's refusal fires and rolls the withdrawal back, which is
what a broken precondition should do.

**The withdraw does not read the moment guard**, and that is deliberate rather than an
omission. ADR-0162 §4's guard exists so a no-show cannot vacate a seat to block a result and a
newcomer cannot accept into *Sunday* on Monday. On a court with a seat open there is no result
to block — `the_court_has_an_open_seat` already refuses it — and nothing is being seated. A
court past its agreed moment with a seat still open will become a ghost for the people on it,
and calling it off is the honest thing they can do with it.

### 7. Records and copies

`CONTEXT.md`: **Standing** (Games) gains `CALLED_OFF`; **Game** gains the fourth end; a new
term, **Call off**, beside **Withdraw**, whose *organiser* and *not call off* sentences move;
**Lifetime** (Conversation) notes the court that has been a game. `the-loop-screens.md` §5.1
gains the *Called off* arm — an ending, no door — and §5.2 its row; `the-words.md` §22.3 gains
the sheet reworded for a reopened court, §22.7 the *Called off* word, and §23.1 the ninth event
that publishes nothing. The superseded sentences carry blockquotes; the index carries this line.
`withdraw_challenge.py`'s *no port here* and `OnlyAHalfBuiltLineUpIsWithdrawn`'s *and for one
more, until #417* are rewritten, and `standing.py`'s *five values, three ends* becomes six and
four.

## Consequences

- **A game has an end an act reaches, and the standing is still folded.** ADR-0137's *never
  stored and never announced* survives as *never stored*: `GameCalledOff` is announced, on
  ADR-0142 §3's exemption, because no arrangement of the record could reach it. A reader who
  took *nothing announces a conclusion* as absolute now has one exception per event-sourced
  racket-sport context, each argued in writing, and the test that counts `challenges`' has no
  twin here — `games`' events are all about a seat, a score or a moment, and this one is the
  first that is about the game as a whole. The next one has to pass the same test in writing.
- **The organiser is no longer the only holder of the exit, and the fallback is a fact about
  liveness, not a role.** *Any remaining player* is derived from the seats on every read, so the
  permission moves the instant the organiser leaves and moves back for nobody. The Phase 1
  pestering argument stands where it applies — a court that was never a game is still the
  organiser's alone to withdraw.
- **A call-off costs nobody anything, which means a court can be called off to dodge a ghost.**
  Three people who know they will not turn up may call the game off rather than let the window
  close, and *shows up* will not see it. That is rule 7 applied honestly: a departure is
  unpriced, and pricing the call-off that follows one would price the departure through the
  people who stayed. The record — `SeatLeft`, `GameCalledOff` with its instant and its actor —
  is what lets a later ADR weigh it without rewriting history, which is ADR-0162 §8's argument
  extended by one event.
- **Who withdrew a court whose game had already ended is not recorded.** `ChallengeWithdrawn`
  carries no player and `GameCalledOff` is not written when the game is stepped over (§6), so on
  that one path — a non-organiser ending a court whose window has closed — the actor is in
  nobody's stream. The ghost is already charged and the room already past its end, so what is
  lost is a support answer rather than a fact a strand reads. Recording it would mean a second
  version of `ChallengeWithdrawn`, which is the right fix the day the question is asked.
- **`SETTLED` grew, and every consumer of it was re-read.** The mutual mint, the sportsmanship
  court and the settled-game query each got the answer this record wanted without a branch;
  the sportsmanship sweep's *every standing has a builder* went red on the new value, which is
  what it is for. A future reader adding a fifth end meets the same test.
- **The contract grows and every piece is additive**: one enum value, one nullable field, one
  refusal code, three route descriptions. A client build that switches on `GameStanding` without
  a default meets `CALLED_OFF` the first time somebody calls a game off it is looking at, which
  is the same cost ADR-0162 named for `SeatAnswer.LEFT`; #419 is where the client learns the
  word.
- **Two refusals on `POST /games/{id}/result` now name an end each, and `accept_result` names
  neither.** That asymmetry is inherited rather than introduced — a ghost already got its own
  code on the entry and the umbrella on the acceptance — and it is kept because the entry is the
  one act a player composes by hand, and the acceptance is a tap on a score that is already on
  the table.
