# ADR-0172 — The court ends with the game, the ending says who, and a called-off card can be cleared

- **Status:** Accepted — **§5's *"the challenge row and the screen behind it keep the news for
  their day"* narrowed 2026-09-16 by
  [ADR-0173](0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md)**: the act still
  removes no fact, and the challenge row goes with the card for the reader who cleared it —
  `GET /challenges` subtracts its reader off the same set `GET /games` does, and a `CALLED_OFF`
  row the reader is still seated on swipes to reveal *Remove this row*, which posts this same
  dismissal. §5's *"nothing else reads [the set]"* gains that one reader; §7's *no arm* on the
  tap stands, as does everything else here — **and four sentences superseded 2026-09-16 by
  [ADR-0175](0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)**: §1's second act is the hour and not a press, §3's *every ending names whose act* has
  one exception that names nobody, §7's presser row and its two sentences are retired, and §8's
  heading is the shortage's alone. §5's admission is widened from the row to everybody the court
  asked. The two-streams shape, the seventh standing, the tag, the face and the shelf stand.
- **Date:** 2026-09-15
- **Narrows, by named sentence:**
  [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) §2's title — *"a court
  that has been a game does not end by its seats"*, kept standing by
  [ADR-0165](0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md) §3
  — to **by its seats alone**: such a court ends **with its game**, by either of the two acts
  that call the game off, and the ending is recorded on the challenge in the transaction that
  tells the game (§1). The fold still reaches no ending for it from the seats, which is the half
  of the sentence that was load-bearing.
  ADR-0165 §3's *"on a game the departure use case … hands `call_off` to `games` … and `called_by`
  is the player whose departure emptied the court"* — it still does, and it now records the
  court's own ending beside it; and its Consequence *"the sentence the others read must say
  **left** and not **called it off**, and that sentence is #428's"* — the sentence is here (§7),
  and it is keyed by what the wire now says rather than guessed from a game card.
- **Supersedes, by named sentence:**
  [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md) §4's *"**No `called_off_by`.** …
  that is a later field rather than a field nothing draws"* — this is the day a design wants the
  name (§4). ADR-0163's *"the act is the withdraw, grown to the court it was refused on"* and
  §7's *"the challenge is `WITHDRAWN`"* — *Call it off* records an ending of its own,
  `CALLED_OFF`, and `WITHDRAWN` is *Remove the challenge*'s alone (§1). ADR-0163 §5's
  *"`GameCalledOff` reaches the room **not at all**"* — it has reached it since the departure's
  call-off arrived without a withdrawal beside it ([#424](https://github.com/Raketa02/Raketa/issues/424),
  `tell_the_room.py`'s `_called_off`), and §6 says which arm destroys the room on each path.
  ADR-0163's Consequence *"who withdrew a court whose game had already ended is not recorded"* —
  it is now (§4).
  [`the-words.md`](../specs/matchmaking/the-words.md) §22.7's and §22.9's *"nobody is named"*
  and [`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §4.3's *"Nobody is named:
  the room went with the act"* — the card names nobody and the screen behind it names the person
  (§8). The loop-screens' §5.2 *"an ending's card offers nothing and opens nothing"* — one ending's
  card offers two things (§8).
  The client's rule that dropped the row of a court ended by somebody else's departure
  (`endedOnADepartureLeavingTheReader`, added 2026-09-14 from
  [#429](https://github.com/Raketa02/Raketa/issues/429) because the only sentence available would
  have read *? said no*) — retired, because the sentence exists (§7).
  **Narrows** [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)'s
  title and §3's *"the rule's **one** exemption … Nothing else in this context qualifies today"* —
  there are two, and the second passed §3's own test in writing (§1); §3's test itself, §1's pair
  rule and §5 stand whole, and §4's `ENDED` is four.
  [ADR-0153](0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §2's
  fourth arm gains a second event that destroys the room in the act (§6); its clocks do not move.
- **Amends** `the-words.md` §13 (a seventh row and the ended-row sentences keyed by `ended_by`),
  §22.7, §22.8, §22.9 and §22.10 (the ending block, the sheet's two ending lines) and §23.1 (the
  events that publish nothing); `the-loop-screens.md` §0.1, §1.1, §1.2, §2.1, §2.5, §2.6, §4.2,
  §4.3, §5.1 and §5.2; and the root [`CONTEXT.md`](../../CONTEXT.md)'s **Standing**,
  **Departure**, **Withdraw**, **Call off**, **Game** and **Lifetime** entries and the Challenges
  invariant on announced conclusions, which gain **Dismissal**.
- **Leaves standing** ADR-0165 §1 (a yes can be taken back), §2 (`game_opened` off completion),
  §3's rule itself (*at most one player on it and no seat awaiting*), §4 (*Remove the challenge*,
  and the risk it accepted), §5 (*Call it off* is any player's — the permission is untouched, the
  record it writes is not) and §6 (the gesture); ADR-0163 §2 (the hand-over port), §3 (the fourth
  end is settled and in neither tally) and §6's stepping over a ghost; ADR-0162 §3–§8;
  ADR-0142 §1 (the pair rule, which `CALLED_OFF` releases as every ending does) and §3's **test**
  (passed a second time in §1 — what narrows is the count, not the rule);
  [ADR-0168](0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md) whole; and
  ADR-0153's clocks — the room is destroyed on a call-off exactly as today.
- **Cites** ADR-0142 §3 for the test the second recorded conclusion passes (§1); ADR-0168 §2 for
  the shape of a per-player fact stored once and read against the record on every read (§5);
  [ADR-0171](0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md) for the
  name every sentence here is written with.
- **Does not decide** keeping the room readable after a call-off, a trash on *Never played*,
  *Counted* or *Uncounted*, a confirmation on the trash, a *Find another game* door on the ended
  row, a room line naming the presser, or any change to live filling rows, the badge, the sort or
  the 24 h shelf.
- Settles [#448](https://github.com/Raketa02/Raketa/issues/448); written by
  [#452](https://github.com/Raketa02/Raketa/issues/452), built by
  [#453](https://github.com/Raketa02/Raketa/issues/453) (backend) and
  [#454](https://github.com/Raketa02/Raketa/issues/454) (player app). Grilled 2026-09-15,
  session *left-alone*, from QA plan #429's D1 finding and its screenshot, on the names
  vocabulary of ADR-0171. The mock every screen was decided on:
  [Diego Left](https://claude.ai/artifact/N7wHrEwhWmFvuJE8B4kRYn) — row look *A · Tag, red*,
  faces *only who the sentence names*; the other switches were the alternatives and stay for
  comparison.

## Context

**Paula sent Diego a tennis challenge; he said yes; a chat opened; Now shows the game as
*Planning*. Diego swipes the chat row → *Leave the game* → confirm.** What Paula sees the next
second, walked on 2026-09-15 as #429's D1:

- **Chats → CHALLENGES:** a row with no face and no name, reading *Tennis · 1 in, 1 seat open —
  the chat is already open*. Every clause is false. The *1 in* is herself; no seat is open for
  anybody, because nobody can be seated into a called-off game; the chat is gone. Rafa's row after
  the third of his doubles leaves has the same shape: blank, *1 in, 3 seats open*.
- **Chats → CONVERSATIONS:** the room was destroyed in the same instant. The *Diego left* line was
  written into it first, and nobody can ever read it.
- **Now:** the card reads *Called off*; the screen behind it says *It was called off — Nobody is
  marked for that.* Diego's name is nowhere, by design — ADR-0163 §4 put no name on the wire and
  said the day a design wanted one would be a later field.
- **Tapping the blank row** opens the challenge screen's filling arm — ⚡ Fill the seats · Open the
  chat · Leave the game — a fill she cannot do, a chat that is gone, a leave of a game already off.
- **When Oscar presses *Call it off*** on a doubles with a seat open, Rafa's row reads *You
  withdrew this* for a day and Arnau's *Rafa withdrew this — that court is closed*. Both false:
  Oscar pressed it, and the sentence is keyed on `WITHDRAWN` and the organiser's seat.
- **One step earlier**, when Oscar joins Rafa's four, the other two say no and Oscar leaves, Rafa's
  row **vanishes** with no sentence. That was a fix taken on 2026-09-14, from the same QA plan,
  because the only sentence §13 could offer was *{name} said no* naming the first decline in court
  order — and on a court somebody had joined and walked out of, that name was nobody's.
- **Diego's sheet**, a moment before he left, read *Your seat opens for someone else and you'll
  leave the chat.* In singles his seat opens for nobody; it ends Paula's game.

### The server told two stories in one act

ADR-0162 §2 kept the fold from ending a court that has been a game, for a reason that was right:
ending the challenge by its seats would have ended it *without the game being told* — the room
destroyed, the game standing `AWAITING_ENTRY` with an open seat and nobody informed. ADR-0163
gave the reopened court an exit that told the game, and it reached for the event already there:
the withdraw. ADR-0165 §3 then let the departure that leaves one player on a game call the game
off, in the departure's own transaction — and left the challenge's standing exactly as it found
it, `LINE_UP_INCOMPLETE` with one seat `LEFT`, because the record that could say *this court is
over* had been told not to say it by its seats and had no other way to say it.

So after Diego leaves, **the game is called off and the challenge is still being filled.** Every
reader downstream is right about its own record and wrong about the court: the inbox draws a
filling court, and a filling court's row hides the people who left — `othersOn`'s rule, correct
for a four that is a two, which on a singles court leaves nobody to draw. The tap opens the filling
arm because the standing is the filling standing. The sheet says the seat opens for somebody
because on a `LINE_UP_INCOMPLETE` court it would. Nothing here is a bug in a screen. **It is one
fact — this court ended when its game was called off — that the challenge's record was not
allowed to hold.**

### And the ending never said who

Every ending sentence the row can say is keyed on the standing and, for the two folded endings,
on a name the client picks by walking the seats — *the first decline in court order*, which is
wrong the moment a departure ended it, and undefined when nobody declined. `ChallengeWithdrawn`
carries no player (ADR-0163 §1, on ADR-0142 §3's argument that the organiser's seat is on the
stream), which was true of *Remove the challenge* and false of *Call it off* the day ADR-0165 §5
made the button any player's. And `GameCalledOff.called_by` — the one field that always knew —
was kept off the wire on purpose. The row, the card and the screen each had a standing and none
had a person, so the honest sentences were unwritable: *Diego Fabregat left*; *Oscar Bertran
called the game off*; *Leaving now calls the game off — for Paula Gallego too.*

### What the author decided

**One ending, told once, and it says who.** When Diego leaves, Paula's court is over — not
*still filling* — and the app knows whose act ended it. The row keeps his face and name and says
what he did; the card offers *What happened?* and a way to clear it; the screen behind each says
it in a sentence; the leaver is told what their leaving does to the person they leave. One word
for the ending everywhere: **called off**. And the room is destroyed as today — the chat was the
plan, the plan is dead, and who and why live on the row and the card.

## Decision

### 1. A court that has been a game ends when its game is called off, whichever way — and the ending is recorded

**The challenge gains one event, `ChallengeCalledOff(challenge_id, called_by, occurred_at)`,
written by the two acts that call a game off and by nothing else**, in the same transaction as
the hand-over to `games`:

- **the departure that deserts a game** — `LeaveGame`, when `is_deserted_at` fires after the
  `SeatLeft` on a court that has been a game — records it with `called_by` the leaver, then hands
  `call_off` over as ADR-0165 §3 has it; the seat, the court's ending and the game's end commit
  together or none of them does;
- ***Call it off*** on a reopened court — any player's on it, ADR-0165 §5 — records it with
  `called_by` the presser **instead of `ChallengeWithdrawn`**, then hands `call_off` over as
  ADR-0163 §2 has it. **`WITHDRAWN` is *Remove the challenge*'s alone**: a court nobody besides
  the organiser had joined, ADR-0165 §4 exactly as written.

**The aggregate gains the act by name.** `Challenge.withdraw` has done both jobs behind one method
and one route since ADR-0163; it now does one — *Remove the challenge*, with
`SomebodyHasJoinedTheCourt` as its refusal — and **`Challenge.call_off(player_id, occurred_at)`**
does the other, keeping `OnlyAHalfBuiltLineUpIsWithdrawn` and *the caller is on the court* exactly
as ADR-0165 §5 left them. The route is the withdrawal's, as today: which act a court gets is the
fold's to say (`has_become_a_game`), never the client's, and the client keeps one button per
screen.

**The fold reads it first, beside `withdrawn`.** `standing_of`'s first rung becomes *was a
conclusion recorded* — `WITHDRAWN` or `CALLED_OFF` — for the reason ADR-0142 §3 gave for the
withdraw: every other answer is still *yes*, and a fold that read the seats first would answer
with the standing somebody has just ended. The rung that skips the endings on `game_opened`
stands untouched underneath it: **a court that has been a game still reaches no ending from its
seats.** What falls is the other half of ADR-0162 §2's sentence — that such a court has no ending
of its own until it is re-seated. It has one, it is the game's, and it is written where the game
is told.

**It passes ADR-0142 §3's test, and the test is worth restating for the second event it
admits.** *An event may announce a conclusion only when no arrangement of the seats could reach
it.* The seats can reach **deserted** on a court that has been a game — `deserted` is a fold, and
ADR-0165 §3 reads it. They cannot reach **called off**. A court deserted by a fill's newcomer
saying *Not this time* — #429's D4, a documented shape — is a game with one player on it and a
seat to fill, and it is not called off; a court whose last other player *left* is. Which of the
two a deserted court is, the seats cannot say, because the game's end is an act (ADR-0163 §2)
and only the act that took it knows. The conclusion this event announces is *the game this court
became is called off* — the fourth end, seen from the court — and there is no first place for it
in the seats. Both of `tests/unit/test_challenge_aggregate.py`'s guards grow to two named values
and no more: the standings no arrangement reaches are `{WITHDRAWN, CALLED_OFF}`, and the events
not about a seat are `{ChallengeWithdrawn, ChallengeCalledOff}`. The actor's field is
**`called_by`**, as on `GameCalledOff`, and not `player_id`: this is a whole-court conclusion
with an actor, not a seat's answer, and the proxy test reads the field names.

**Two shapes were refused, and each is the failure ADR-0162 §2 was written to prevent.**

- **Folding `CALLED_OFF` off `game_opened and deserted`** would end the challenge on every path
  that deserts it — the newcomer's *no* and the newcomer's lapse included — and on those paths the
  game is told nothing, the room lives, and the row would say *called off* over a game whose card
  says *Needs a player*. It also cannot reach the button at all: two people still on the court
  are not a deserted court, so the presser's ending would need an event anyway, and there would be
  two ways to reach one standing.
- **Asking `games` at the read** — *is this court's game called off* through the seam that already
  answers *may its seats still change* — would make a challenge's standing depend on another
  context's answer on every list read, and would borrow `ended_at` and `ended_by` from a record
  that is not the row's. The withdraw already showed the honest shape: two streams, each holding
  its own end, committed in one transaction (ADR-0163 §2). This record takes it for the second
  ending and refuses to make the challenge's copy a read of the game's.

### 2. `CALLED_OFF`, the seventh standing, is an ending like the other three

`Standing` gains `CALLED_OFF`. It joins **`ENDED`** (four) and is outside **`ARRANGING`**, so
the pair releases the instant it is recorded, as for every ending (ADR-0142 §1); the card block
draws nothing on it, on ADR-0143 §8's rule that a card stops when the deciding does; every seat
act meets `challenge_is_over` on it, as on the other three, and `refuse_a_court_closed_to_seating`
returns before reading the game. **`ended_at` is exact** — the event's own instant, as the
withdrawal's is — and the inbox's day-long shelf is measured from it. **Never re-entered**: there
is no fill, no acceptance, no re-seat from it, and re-asking the same people is a new challenge.
The mutual mint's idempotence already reads `SETTLED` on the game and `ARRANGING` on the
challenge; both answer *mint again*.

**Nothing changes for the leaver on the wire.** Their game leaves their rail by membership as
today (`GameDirectory.playing` walks the current line-up); their rows go on the reply as today
(ADR-0165 §6). The presser is still on the court, so their game stays on their rail as a
*Called off* card and their row stays its day — *You called the game off* is their own act, and
§7 says why it is not dropped as an own *no* is.

### 3. `ended_by` — every ending names whose act ended it

**A new field on the challenge read, on every standing in `ENDED` and `null` elsewhere: the
player whose act ended the court.**

| Standing | `ended_by` | Where it comes from |
| --- | --- | --- |
| `CALLED_OFF` | the last leaver, or the presser | `ChallengeCalledOff.called_by` |
| `WITHDRAWN` | the organiser | the organiser's seat — the stream already holds it, and `ChallengeWithdrawn` gains no field |
| `DECLINED` | the seat whose *no* or departure completed the desertion | the fold |
| `LAPSED` | the seat whose window was the last to run out | the fold |

**The folded two are read by the fold that already dates the ending.** `ended_at_of` answers
*when* as the latest instant at which one of the people asked left — a lapse exact, a departure
exact off `departed_at`, a decline bounded late by the stream's last write — and `ended_by` is
**the occupant of the seat that instant was read from**, so the row's name and the row's date
agree by construction and cannot be read against two clocks. Where two seats share the bound —
two nos, dated alike — court order breaks the tie, which is the rule the client had; what the
field fixes is that the choice is made once, on the server, from the same facts the date is made
from. **The sentence is always true of the person named**, whichever the bound picks: it is keyed
by `ended_by`'s own seat (§7), so a seat that `LEFT` reads *left* and a seat that `DECLINED` reads
*said no*, and a lapsed seat is never named on a `DECLINED` court because a no outranks silence in
the fold that picks the name.

**On the wire it is a player id, and always the occupant of one of the court's seats** — never a
second copy of the name. The face and the name the row draws are that seat's, which is what lets
§7's rule be one lookup: *the face is who the sentence names*.

### 4. `game_id` on the challenge read, and `called_off_by` on the game read

**`game_id: UUID | null` on `ChallengeSchema`, `null` until the line-up first completed and the
same id ever after** — through a re-seat, through the ending. It is the one fact the challenge
read lacked (#428 named the gap, and §2.5 of the loop-screens spec built around it), and it is
what lets the Chats list and the leaver's sheet tell a court that has been a game from one that
has not without a join on the client (ADR-0009). **Read, not recorded.** The hand-over already
learns the id back and discards it; recording it would put a challenge event on the stream
announcing what the completing acceptance already says, with a foreign id on it — two places for
*has this court been a game*, one of them the fold's `game_opened`. Instead the list read asks
`games` once, for the whole list, on the arrow `challenges → games` that already carries three
reads: *which of these courts have a game, and which game*, asked only about the courts the fold
says have been a game, so a list with none costs nothing and `null` is the fold's answer rather
than the other context's. An id rather than a boolean, because the game screen is keyed on it and
a later door from the ended court to the game — which this record does not build — would cost
nothing on the wire.

**`called_off_by` on `GameSchema`: the player and their name, `null` on every standing but
`CALLED_OFF`** — from `GameCalledOff.called_by`, the field ADR-0163 §4 kept for this day, and
`PlayerNames.names_of` over one more id in the union the read already asks about. The name is
carried because the leaver's seat is **vacated** on the game (`player_id: null`, ADR-0162 §3),
so the court cannot supply it; its `name` is nullable exactly as a seat's is, for an account
`users` no longer answers for. **A departure is told from a press by whether `called_off_by` still holds
a seat on the game**: the presser does, the leaver's seat is open. No second field says which;
the record already does.

**ADR-0163 §6 stands, and its costed gap closes.** *Call it off* on a court whose game already
ended by its clock still steps over the ghost: the game stays `NEVER_PLAYED` and charged, the pair
releases, the room is destroyed if the sweep has not reached it. The challenge is now `CALLED_OFF`
with `ended_by` the presser — **the actor is on the record**, which ADR-0163's Consequences named
as lost. The two readings that court produces — a row reading *{name} called the game off* over a
card reading *Never played* — are each true of their own record and named in the Consequences.

### 5. The card's dismissal — a per-player act on `games`, derived on every read

**A new act on `games`, the reader's own: *dismiss*.** `POST /api/v1/games/{id}/dismissal`,
admitted on a game that is `CALLED_OFF` and refused on every other standing with its own code,
`game_is_not_called_off`; admitted for a player the rail would show the card to — on the court —
and answered as a stranger is answered for anybody else, on the one rule every act here shares.
**Recorded once per player on the game's stream**, `GameDismissed(game_id, dismissed_by,
occurred_at)`, `games.dismissed` at version 1; a second dismissal by the same player writes nothing and answers
as done, on *writes nothing twice*. **Its effect is derived on every read: `GET /games` omits a
game its reader has dismissed.** The aggregate folds the set of players who have; the rail's read
subtracts the reader; nothing else reads it — not the tallies, not the settled query, not the
mutual mint, not the room, which is gone before the card can be dismissed.

**Why a stored fact, and why here.** The card must be gone on the reader's other phone and after
a reinstall (#448, story 10), so it is not the client's. It is a fact about **this game's card
for this reader**, so it belongs on the game and is read where the rail is folded — ADR-0168 §2's
shape for the room's one membership fact: stored once, subtraction only, effect derived against
the record on every read. A per-user *hidden games* table would be a projection with no fold
behind it, and the first list `games` kept that its aggregates did not.

**Why no sheet on the client.** The act removes a card, not a fact: the challenge row and the
screen behind it keep the news for their day, the record is untouched, and nobody else's rail
moves. A confirmation would put the withdraw's ceremony on the least consequential act in the
app. It is instant, and the card leaves the rail on the reply.

**Why `CALLED_OFF` only.** The other endings' cards — *Never played*, *Counted*, *Uncounted* —
carry a score or a strand's verdict and are the record for the day they stay (§5.2 of the
loop-screens spec); this one carries nothing the row does not, and it is the one a player wants
gone. Widening the trash is a design of its own and is out of scope by name.

### 6. The room is destroyed, as today, and the *left* line is still written first

**Nothing new is decided about the room, and one sentence is corrected.** The room's teller
destroys the room on `games.called_off` — `tell_the_room.py`'s `_called_off`, which has been so
since the departure's call-off arrived with no withdrawal beside it (#424) and which ADR-0163 §5's
*not at all* predates — and on **the withdrawal's arm, now subscribed to `challenges.called_off`
beside `challenges.withdrawn`**: the same arm, no line, no nudge. On both paths both events are
written in one transaction, so both are delivered; **whichever arrives first finds the room and
the other finds nothing**, exactly as `challenges.withdrawn` and `games.called_off` already
behave beside each other. On ADR-0163 §6's ghost path the game is not told, and the challenge's
own event is what destroys a room the sweep has not reached — the job `challenges.withdrawn` did
there before. **`games.dismissed` reaches the room not at all**: there is no room by then.

**The *{name} left — that seat is open again* line is still written first**, off
`challenges.seat_left`, into a room the next delivery destroys. It is the record's, even if nobody
reads it, and the alternative — a departure that writes no line when it is the last — would make
the room's teller re-derive the challenge's fold to decide whether to speak. What the people left
behind read instead is the row and the card.

### 7. The Chats list — the row says who, the tag says what, the face is who the sentence names

**The ended-row sentences, keyed by the standing and by `ended_by`'s own seat:**

| Standing · `ended_by`'s seat | The row |
| --- | --- |
| `CALLED_OFF` · `LEFT` | `{name} left` |
| `CALLED_OFF` · still seated, another player | `{name} called the game off` |
| `CALLED_OFF` · still seated, the reader | `You called the game off` |
| `DECLINED` · `LEFT` | `{name} left — nobody else is coming` |
| `DECLINED` · `DECLINED` | `{name} said no — that seat is open again` — as today, now naming `ended_by` |
| `LAPSED` | `{name}'s day ran out — that seat is open again` — as today, now naming `ended_by` |

**The departure-drop rule is retired.** `endedOnADepartureLeavingTheReader` dropped the row of a
`DECLINED` court the reader was left alone on after somebody walked out; it existed because the
only sentence was *? said no*, and the fourth row above is that sentence. Such a row now keeps its
day like every ending. **What still leaves at once is the reader's own act** — their own *no*,
their own *left*, their own removal — as ADR-0165 §6 and #388 have it. **The presser's own row
is not one of those and stays its day**: *You called the game off* is the reader's own act, but
the row is the one place the others' court is still shown to them with every seat's word behind
it, and a person who ended a game for three others is owed the same day's record the others get.
The one court both readings fit — a game whose others all left, called off by the last departure —
reads *{name} left* to the reader alone on it, and the leaver's own row is gone.

**The tag.** A **`Called off`** tag in the kit's *bad* variant — red on red-soft — at the row's
trailing edge, on `CALLED_OFF` rows only, and on no other ending. It carries the state word the
Now card carries, in the colour meaning picks. **The clock stripe's rule is untouched**: a row
whose line is a duration has its amber stripe, and nothing else does; the tag and the stripe never
share a row, because a `CALLED_OFF` row has no clock of anybody's. Look *A* on the mock; *B*
(quiet tag), *C* (recessed ground) and *D* (red sentence) were the alternatives.

**The face is who the sentence names — one rule for the whole shelf.** An ended row draws
`ended_by`'s face and name, and no other. A filling court still names the people still on it
(`othersOn`'s rule for `ARRANGING`, from #429). Today's doubles *said no* rows go from three faces
to one, and the tap answers *which court*; the faces that left one by one never come back on the
row that ends it, and an ended row is never blank — the two failures the other two switches on
the mock kept one of each. The rule replaces `othersOn`'s *an ended court names everybody it
asked*, which was written so a singles *said no* row would not name nobody; naming the one person
the sentence is about does that better.

**The tap opens the challenge screen drawn as an ended court**: the sentence above, the court with
every seat and what each person did — *You · in*, *Javier Fabregat · left*, *Arnau Gallego · said
no*, *Oscar Bertran · called it off* — and **no arm**: no fill, no chat door, no leave, no remove.
Nothing on it is an act the server would refuse. The `CALLED_OFF` arm and the departure-ended
`DECLINED` arm are the same drawing; the sentence is the row's.

### 8. The Now card and the game screen

**The `Called off` card names nobody under its slots, and offers two things** in the action row
where a live card has its wide door: **`What happened?`** — the on-dark fill, the tag's own quiet
colour — opening the game screen; and beside it a square button with the Feather trash glyph,
spoken **`Remove this card`**, that dismisses the card at once (§5). The card keeps its slots and
its court, as every ending's does; the shelf — a day from `called_off_at` — is unchanged for a
card nobody clears.

**The game screen's ending block, keyed by how it ended** — a departure told from a press by
whether `called_off_by` still holds a seat:

| | Heading | Body |
| --- | --- | --- |
| a departure, singles | `The game was called off for lack of players` | `{name} left, so the singles game is called off. Nobody is marked for it — not you, not them.` |
| a departure, doubles | `The game was called off for lack of players` | `{name} was the last to leave, so the doubles game is called off. Nobody is marked for it — not you, not any of them.` |
| the button | `{name} called the game off` — the reader's own: `You called the game off` | `Nobody is marked for it — not you, not any of the others.` |

The body still says what the ghost's body says about the strands, because it is the same fact
about the same people (ADR-0163 §3); what changes is that the heading is a sentence and the body
names the person. No plan editing, no doors, no act on the court — as *Never played*.

**One word: called off.** The tag, the *Call it off* button and its sheet, the ending's headings
and every sentence in this record use it. ***Cancel* appears nowhere** — not on a control, not in a
sentence, not in a code — and the loop-screens' *Cancelled* stays on the list of the seven states
the app does not name.

### 9. The leaver's sheet says what the leaving does

**The sheet's one line changes when the leaving would end the court** — reached from the Chats
list's swipe and from the challenge screen alike, and read off the row the list already holds: the
reader is the only other accepted seat, and no seat is awaiting an answer. Which sentence it is,
`game_id` decides:

| The court | The line |
| --- | --- |
| a game (`game_id` set) | `Leaving now calls the game off — for {name} too. Your chat goes with it.` |
| never a game | `Leaving now closes this court for {name}. Your chat goes with it.` |
| otherwise | `Your seat opens for someone else and you'll leave the chat.` — today's line, unchanged |

`{name}` is the one person left, the whole name (ADR-0171). **The game screen's own *Leave this
game* sheet — three lines — gains the same first line in the same case**, above its own; there
the court is the game's line-up, and the case is the same one — besides the reader's own seat,
exactly one is still occupied and none is awaiting. The rule is read off a list that may be a
beat stale; the server's answer is what happens, and a refusal is said on the sheet as today
(`the-words.md` §22.10).

### 10. Records and copies

ADR-0142's, ADR-0162's, ADR-0163's and ADR-0165's status lines name what moved, and ADR-0153
§2's callout gains a sentence. `the-words.md` §13's table
gains the seventh row and the six ended-row sentences; §22.7 and §22.9 drop *nobody is named*, and
§22.9 gains the two headings and the three bodies; §22.8 and §22.10 gain the sheet's two ending
lines; §23.1 gains `challenges.called_off` and `games.dismissed`. `the-loop-screens.md` §0.1 gains the routes and fields;
§1.1 retires the departure-drop rule and states the face rule; §1.2 gains the tag and the ended
court's tap; §2.1 gains the ended arm, §2.5 and §2.6 the word *Call it off* now records; §4.2
gains *What happened?* and the trash, §4.3 its correction; §5.1 and §5.2 the ending block and the
two doors. The root `CONTEXT.md`'s **Standing** (Challenges) gains `CALLED_OFF`;
**Departure**, **Withdraw** and **Call off** say which act records which ending; **Game**'s
fourth end says who; **Dismissal** is defined under Games. QA plan #429 is corrected by comment:
D1 step 2, B2 and C5, F1, and the singles sheet line in C2. `backend/CLAUDE.md`, the feature
records under `frontend_player/docs/features/` and every docstring quoted above document what is
built and move with the code in #453 and #454.

## Consequences

- **Paula's row says *Diego Fabregat left* under a red *Called off* tag, and every clause is
  true.** The court ends once, the challenge and the game agree about it, and each screen reads
  its own record.
- **The challenge stream has a second announced conclusion.** ADR-0142 §3's exemption was *first
  and only* for one record; it is now two, each argued in writing, and both guards in
  `test_challenge_aggregate.py` name the pair rather than counting to one. The next candidate
  passes the same test the same way or not at all — and the shape of *deserted but not called off*
  (D4) is what to check it against.
- **Two records each hold the court's end, committed together — and only a split transaction
  could make them disagree.** The same shape ADR-0163 §2 took for the withdraw, taken again. If it
  ever happened, the challenge's copy is the one the row reads and the game's is the one the card
  reads, and the mismatch would be visible on one screen rather than silent.
- **`ENDED` grew, and every reader was re-read**: the pair rule, the card block, the standing gate,
  the mutual mint, the inbox's `STILL_BEING_ARRANGED` record and the client's standing vocabulary
  assertion, which fails `pnpm typecheck` on the seventh value until it is taught the word —
  which is the drift check being red between #453 and #454 by design.
- **`ended_by` on a `DECLINED` court is read off a bound**, as `ended_at` is, so between two people
  who both said no it names one by court order. The person named always did what the sentence
  says; which of two is named is the same tie-break the client already made, moved to where the
  date is made.
- **A `LINE_UP_INCOMPLETE` court whose newcomer says no is still not over** (D4). The seats
  desert it and the game is not called off; the row reads a filling court, honestly. Ending it
  would take an act that tells the game, and none was asked for here.
- **The ghost path reads two true things that jar**: *{name} called the game off* on the row,
  *Never played* on the card, when the button was pressed after the entry window closed on the
  open seat. ADR-0163 §6 chose the ghost over un-charging a strand and this record keeps it; the
  actor is now recorded, which is more than that path had.
- **A dismissed card is gone for good, and there is no undo.** A mis-tap on the trash loses the
  card and nothing else — the row and the screen behind it keep the day — which is why the trash
  has no sheet. Falsifier: dismissals within seconds of the card first being drawn, which would say
  the button is where a thumb lands.
- **A game with four dismissals has four events on its stream and one more set on the
  aggregate.** Nothing else folds them; a later reader adding a fifth ending's trash meets the same
  standing gate and the same *once per player* rule.
- **Two reads grow by one question each**: the challenge list asks `games` which of its
  been-a-game courts stand for which game, and the game read asks `users` about one more id. Both
  are set reads on lists already reading those contexts; if either shows up in a measurement the
  fix is one call rather than a stored copy.
- **The presser's row stays a day and reads their own act back to them.** Chosen over dropping it
  as an own *no* is dropped, because the court behind it — every seat and what each did — is theirs
  to read too; if it reads as nagging, the alternative is one rule wider in `OWN_ACT_LEAVES_AT_ONCE`.
- **Doubles *said no* rows lose two faces.** The row names the one person the sentence names; the
  court is one tap behind it. Chosen on the mock over both alternatives, each of which kept a
  failure this record was opened to remove.
- **The leaver's sheet reads its rule off the client's list**, which can be a beat behind the
  server: a second departure landing while the sheet is up could make *closes this court for
  {name}* true of a court that has already ended. The server's answer is what happens, said on the
  sheet as every refusal there is.
- **Tests that pinned the old rules move**, named rather than discovered: the fold's *a court that
  has been a game reaches neither ending by its seats* (stands, and gains *— and reaches
  `CALLED_OFF` by the event*); the exemption's two guards; the withdraw's `WITHDRAWN` on a reopened
  court; `OnlyAHalfBuiltLineUpIsWithdrawn`'s count of standings; the inbox filter's
  departure-drop row and `othersOn`'s *everybody it asked*; the *Called off* card's *no door*; the
  game screen's *It was called off*; and the room's teller, which gains an arm and a test that the
  button's ending destroys a room whose game is a ghost.
