# ADR-0175 — Nobody calls a game off: the court ends by its seats or by its hour

- **Status:** Accepted
- **Date:** 2026-09-16
- **§4 narrowed 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md) to the Classic play loop**: a game made in a group is left from its game details, with *Leave the game*.
- **Supersedes, by named sentence:**
  ADR-0165
  §5 whole — *"Call it off is any player's"* — the press exists for nobody (§1); and §3's
  *"at most one player on it and no seat awaiting an answer"* is narrowed to **nobody on it,
  whoever is still deciding; or one player on it and no seat awaiting** (§2).
  [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md) §1's *whose act* whole (already
  narrowed by 0165 §5, now empty), its *"the act is the withdraw, grown to the court it was
  refused on"* (already superseded by 0172 §1, now with no act behind it), and §6's *"a court
  whose window has already closed is withdrawn without the game being told … who withdrew it is
  not recorded"* — the hour calls such a court off with nobody on its record (§3).
  [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
  §1's *"by either of the two acts that call the game off"* — the second act is the hour, not a
  press (§3); §3's *"`ended_by` — every ending names whose act ended it"* — every ending but the
  hour's, which is nobody's and says so (§3); §7's *"the presser's own row … stays its day"* and
  the two presser sentences, *{name} called the game off* and *You called the game off* —
  retired (§3, §6); §8's *"the game screen's heading … names the presser"* — one heading, the
  shortage's (§6); §5's *"admitted for a player the rail would show the card to — on the court"*
  is widened, from the row, to everybody the court asked (§5).
  [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) §4's *"the moment
  guard"* gains a moment for a court with no day agreed: the end of its horizon (§3).
  `the-loop-screens.md` §2.5's and §2.6's *Leave the
  game* on the challenge screen's arms, §4.2's *Open the chat* door on the game screen and its
  *courtActs* — *Leave this game* and *Call it off* — under *We played*: the screen draws one act,
  *Fill the seat*, directly under the card (§4).
- **Narrows** ADR-0173 §2's
  *"the reader holds an accepted seat"* to **everybody the court asked whose seat it closed on**
  — an accepted seat, a seat still deciding, a seat whose day ran out (§5) — and its §3's *"posts
  the existing game dismissal"* to a door of the challenge's own that records the same event.
- **Amends** [`the-words.md`](../specs/matchmaking/the-words.md) §13 (the `CALLED_OFF` rows: the
  presser's two sentences go, *Nobody filled the seat* arrives), §22.3 (the withdraw's refusal
  table: `court_has_been_a_game`), §22.8 (*Leave this game* on the game screen, retired), §22.9
  (*Call it off*, its sheet and its refusals, retired; the hour's heading and body; the ended
  court's *was still deciding*), §22.10 (*Remove this row* for everybody the court asked); the
  root [`CONTEXT.md`](../../CONTEXT.md)'s **Standing**, **Withdraw**, **Call off**, **Departure**
  and **Dismissal** entries; and `backend/CLAUDE.md`'s challenges paragraph.
- **Leaves standing** ADR-0165 §1 (a yes can be taken back), §2, §4 (*Remove the challenge*,
  now refused on a court that has been a game with its own code) and §6 (the gesture);
  ADR-0172 §1's two-streams shape, §2 (`CALLED_OFF` is an ending like the other three), §4
  (`game_id`, `called_off_by`), §5's act, §6, §7's tag, face and shelf, §9; ADR-0173 §1 (one
  set, both lists) and §4 (two words for one act); ADR-0163 §2 (the hand-over port) and §3 (in
  neither tally); [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §3's test, passed a third time (§3); [ADR-0092](0092-periodic-jobs-as-embedded-loops.md)
  for the loop's shape.
- **Cites** ADR-0172 §1 for why the challenge's standing is never a read of the game's, which
  is what makes the hour a sweep and not a fold (§3); the lapse loop
  (`lapse_expired_seats.py`) for one transaction per court with conflicts stepped over.
- **Does not decide** a sentence on the game screen saying where a seat is left from; a note on
  the row between the hour and the sweep's tick; a remove on the ended challenge screen's arm; an
  undo on the dismissal; or whether the hour should warn anybody ahead of itself.
- Decided 2026-09-16 with the author in session, grilled over three rounds; built in the same
  session, backend and player app.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** Challenges, the Chats row, the dismissal and the hourly job that called off a court still short of a player are gone, so §1's `court_has_been_a_game`, §2's fold, §3's job, §4's *Fill the seat* and Chats swipe, §5 and §6's words describe nothing that runs. The record's rule outlived its loop: **no player can call a game off**. A booked game ends short only by its club's cut-off — a seat that opened before it and is still open at it calls the game off, with nobody named (`called_off_by` is `null`) — or by the club taking the court back, and the game screen's ending says the shortage and names nobody, as §1 and §3 decided.

## Context

**The author walked the game screen and found four buttons under a *needs a player* card**, and
one of them was wrong as a product. *Call it off* — ADR-0163's exit for a reopened court, made
any player's by ADR-0165 §5 — let one of three remaining doubles players end the game for the
other two with a press. *"None of the players should depend on someone else's single decision."*
The other three were clutter: *Leave this game* and *Open the chat* have homes elsewhere (the
Chats row's swipe; the Now card's bubble and the Chats tab), and *Fill the seat* — the one act
that belongs to the state the card names — sat at the bottom of the scroll.

**Removing the press alone would have been worse than keeping it.** Three facts found while
sizing the removal:

1. A game court with a seat open that nobody fills and nobody leaves has, without the press,
   exactly one end: the entry window closing eight days after the arrangement. The game becomes
   *Never played* — a **ghost charged to the players who stayed**, on their *shows up* record —
   the court stays `LINE_UP_INCOMPLETE` for ever, which **holds every pair on it for ever**
   (`players_in_it_at` reads a reopened court as still being arranged), and its *needs a player*
   row never leaves Chats. ADR-0163 §6 named this gap and made the press its remedy; the press was
   the only thing standing between those players and that outcome.
2. The last seated player's departure did **not** call the game off while a fill invitation was
   pending: `deserted` required *no seat awaiting*, so a court could stand with nobody on it,
   waiting for an invitee to join nobody.
3. A court with no day agreed had **no moment**: the guard admitted a fill and a departure right
   up to the window closing on the ghost.

**The author's rule, once the three were on the table:** a game is called off by its seats — the
departure that leaves at most one player on it — and, where the seats do not settle it, by the
platform at the agreed hour. Never by a press. And whoever a called-off court was news to may
clear it, the invitee still deciding included.

## Decision

### 1. The press goes, for everybody, and the server refuses it

**There is no *Call it off*.** Not on the game screen, not on the challenge screen, not for the
organiser, not for anybody. `Challenge.call_off` is deleted; the withdrawal route on a court that
has been a game is refused with its own code, **`court_has_been_a_game`** (409), asked after
*whose act* and *has it ended* and before *has somebody joined* — so an organiser alone again on
a reopened court with a fill still deciding is not told nobody joined a court that has been
played for. `not_a_half_built_line_up` goes with the act. The client's `mayRemove` reads
`game_id` and never offers the removal on such a court; the refusal has a sentence for the stale
row that reaches it anyway.

**Why the server and not only the button.** A rule that lives in a button is a rule until the
next build; the author's reason — nobody depends on one person's decision — is a rule about the
record.

### 2. The seats end it: the last departure, whoever is still deciding

**`deserted` is narrowed.** A court is over by its seats when **nobody is on it**, whatever seats
are still deciding; or when **one player is on it and no seat is awaiting an answer**. The first
clause is new: the last seated player leaving ends the court on the spot — before a game, as
`DECLINED`; on a game, as `CALLED_OFF` with the leaver named — and the pending invitation is
over with it: the invitee's *yes* meets `challenge_is_over`, and their row reads *Called off* for
its day. The second clause is ADR-0165 §3 as written, kept for the reason the author gave: one
player alone with somebody still deciding is a court that may yet be a game, and a newcomer's
*no* that leaves them alone is that newcomer's decision and ends nobody's game — the one left may
fill again or leave, and the hour ends it if they do neither.

**A departure still calls a game off only when it deserts the court.** In doubles, three left of
four is *needs a player*; two left is *needs a player*; one left is called off. That is
ADR-0165 §3's rule and the author's, unchanged where it was already right.

### 3. The hour ends it: the platform calls off a court still short of a player

**A game court still `LINE_UP_INCOMPLETE` when its moment passes is called off by the
platform.** The moment is the plan's agreed point — and, for a court with no day agreed, **the
end of its horizon**, `planned_at + PLAN_HORIZON`, the last instant it could have been played;
the moment guard reads the same instant, so nobody may be seated into, or leave, a game whose
week is over. The ending is recorded on the challenge as `ChallengeCalledOff(called_by=None)`
and the game is told in the same transaction, `GameCalledOff(called_by=None)`, on ADR-0172 §1's
two-streams shape; both fields are widened to nullable at version 1, and every reader of them
answers *nobody* for the hour. Nobody is charged — `CALLED_OFF` is in neither tally, as ADR-0163
§3 has it — the pair releases, the room is destroyed as on any ending, and the row keeps its day
under the tag reading **Nobody filled the seat**. The game screen's heading is the shortage's,
*The game was called off for lack of players*, over a body that says nobody filled the seat in
time.

**It is a sweep, and correctness depends on it.** The challenge's fold cannot read a plan, and
ADR-0172 §1 refused to make the challenge's standing a read of the game's; so the ending is
written by a job — `CallOffUnfilledCourts`, on the lapse loop's shape: candidates are every court
somebody ever left (`LeftCourtQuery`, one event type on the log), the fold says which are games
still short of a player, the moment guard (`SeatableGameQuery`, the same port the fill and the
departure read) says which are past their hour or already history, and each is called off in
its own transaction with a version conflict counted and stepped over. **Every minute**
(`UNFILLED_COURT_INTERVAL_SECONDS`), because the interval is how long a court past its hour
reads *needs a player* with nothing to press. A court whose window already closed — while the
loop was down, or before it existed — is called off all the same, so its pair releases and its
row gets its day; the game keeps the ghost it reached, on ADR-0163 §6's *never un-ghosted*.

**Why the hour and not the window.** The window closes eight days after the arrangement; the
hour is when the game would have been played. After the hour nothing can happen to the court —
no fill, no departure, no result — so there is nothing left to wait for, and a *needs a player*
card sitting for a week over a game that is not going to happen is the dead control #324 refuses.

**Why the platform and not one player.** The author's rule. A ghost charged to people who had
no way to play, and a pair held for ever, are the platform's failures to fix, and fixing them
with a button hands one player the others' game.

### 4. The game screen draws one act, under the card; leaving is one gesture in one place

**On the plan lead the game screen draws the card, *Fill the seat* directly under it, the
court's pairing, the plan, and *We played*.** The fill is offered while a seat is open and the
moment is ahead, and past the moment nothing is drawn for the court — the hour is on its way.
*Leave this game* and *Open the chat* are gone from the screen; the `courtActs` slot became
`fill`. *Open the chat* went because the Now card's bubble and the Chats tab both reach the room,
and the screen no longer reaches `features/conversations` for the word, the route or the join —
ADR-0149 §3's widened seam closes back to its one importer.

**Leaving is the conversation row's swipe, only.** *Leave the game* comes off the challenge
screen's two live arms too: every court a player has said yes to has a conversation row on
Chats, so nothing becomes unreachable, and one way to leave is one thing to explain. The
`DepartureDoor` stays what it was; its other two surfaces go, and the arms' `mayLeave` with
them.

### 5. Everybody the court asked may clear its row, through a door of the challenge's own

**`POST /challenges/{id}/dismissal`** — *Remove this row*, the reader's own act, admitted for
anybody holding a seat on the court and refused with `court_is_not_called_off` on any standing
but `CALLED_OFF`. It hands the act to `games` on the hand-over and records the same
`GameDismissed` the Now card's trash records — on the court's word that the reader was asked, so
`Game.dismiss_for_the_court` asks only that the game agrees it is called off. One set, read by
both lists (ADR-0173 §1); one act, two doors.

**Why a second door.** The invitee still deciding when the last departure called the court off
(§2) has a row and never had a card: the game never held a seat for them, and its own door
answers them as a stranger — rightly, so a game id is not confirmed to people it was never for.
The row is drawn for everybody the court asked; the row's door admits everybody the court asked.
On the client `mayDismiss` is *`CALLED_OFF`, and the reader holds a seat the court closed on* — an
accepted seat, one still deciding, one whose day ran out; never one they gave up themselves,
whose row left with the act. The ended court's screen reads such a seat as *was still deciding*.

### 6. The words that go, and the one that arrives

*{name} called the game off*, *You called the game off* and the ended court's *called it off*
are retired from the copy deck with the press; *Call it off*, its sheet and its three refusals
with them; *Leave this game* with the control. **Nobody filled the seat** is the hour's row;
*was still deciding* is the invitee's seat on an ended court; *This one became a game, so it's
not yours to remove any more* is the withdraw's new refusal. A record naming somebody still
seated as `called_off_by` — written while somebody could press — folds as a departure by the
person it names, which is the nearest true sentence and the only one left.

## Consequences

- **No player can end a game for the others with a press**, and no court can be left in the
  state the press was the only exit from: a ghost charged to players who could not play, a pair
  held for ever, a row that never leaves.
- **A new job, and the first one a challenge's standing depends on.** Every earlier loop bought
  a record; this one buys correctness. If it is off or down, a court past its hour reads *needs
  a player* until it runs — bounded above by the interval while it runs, unbounded while it does
  not. Named in `config.py` beside the flag.
- **A dead minute.** Between the hour and the next tick the row and the card say *needs a
  player* with nothing to press. One interval, by construction; a sentence for that minute is
  not decided.
- **The candidate read walks every court somebody ever left, every minute**, over an unindexed
  column — the lapse loop's cost with a shorter interval. The index belongs with the first query
  that measures it, as the lapse read says of its own.
- **Three events widened to nullable at version 1** (`ChallengeCalledOff.called_by`,
  `GameCalledOff.called_by` — and `Conclusion.by`, which is not an event): a payload written
  before this decodes unchanged, and no reader outside this process ever read them.
- **Old records with a presser on them read as departures.** A local store seeded before this
  change can hold `CALLED_OFF` courts whose `ended_by` still holds a seat; every screen now reads
  such a person as having left. Only `local` runs, and the store is reset on a re-key.
- **The invitee's removal is a second endpoint for one act.** Chosen over widening the game's
  own door, which would have confirmed a game id to people it was never for. The client's row
  door posts the challenge route for everybody; the card's trash still posts the game's.
- **The moment guard changes for courts with no day agreed**: a fill and a departure are refused
  after the horizon's end, a day earlier than before. Nobody could have played that game either
  way.
- **ADR-0163 §1, ADR-0165 §5 and three sentences of ADR-0172 are now wrong as written**, and
  their status lines say so. The reason the press looked right — a reopened court needed an
  exit, and a button was the cheapest one — is kept there, because it is what the hour was built
  against.
