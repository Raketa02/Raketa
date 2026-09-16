# ADR-0173 — A called-off court is cleared from both lists by one act

- **Status:** Accepted — **§2 and §3 narrowed 2026-09-16 by [ADR-0175](0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §5**: the row is cleared
  by everybody the court asked whose seat it closed on, through a door of the challenge's own,
  `POST /challenges/{id}/dismissal`, recording the same event. §1 and §4 stand.
- **Date:** 2026-09-16
- **Narrows, by named sentence:**
  [ADR-0172](0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
  §5's *"The act removes a card, not a fact: the challenge row and the screen behind it keep the
  news for their day"* — the act still removes no fact, and **the row goes with the card**, for
  the reader who cleared it and for nobody else (§1). The screen behind the row is untouched; what
  goes is the row that opened it. ADR-0172 §7's *"The tap opens the challenge screen drawn as an
  ended court … and **no arm**: no fill, no chat door, no leave, no remove"* — the tap and the
  screen still offer nothing; the **row** now reveals one thing on the swipe, and it is not the
  withdraw's remove (§3). ADR-0172 §5's *"nothing else reads [the set]"* — one more read does,
  the inbox's, and it reads one membership of it (§1).
  [`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §1.2's *"Every other challenge
  row reveals nothing and does not move: an invitee's, the organiser's once somebody has joined,
  an ended one on its shelf"* — every ending's row but one: a `CALLED_OFF` row the reader is still
  seated on.
- **Amends** [`the-words.md`](../specs/matchmaking/the-words.md) §22.9 (the card's two buttons,
  and the row's word *Remove this row*); `the-loop-screens.md` §1.1, §1.2 and §4.2; the root
  [`CONTEXT.md`](../../CONTEXT.md)'s **Dismissal** entry; and the challenges read's own note that
  *ended challenges are in the list* — they are, minus the one the reader cleared.
- **Leaves standing** ADR-0172 §5's act and its shape whole — a per-player act on `games`,
  admitted on `CALLED_OFF` only, recorded once per player, derived on every read, no sheet; §5's
  *why a stored fact, and why here*; §7's sentences, tag, face and shelf for every row not cleared,
  and for every reader who has not cleared it; §8's card; §9's sheet.
  [ADR-0165](0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md) §4
  (*Remove the challenge* is admitted while nobody has joined, and refused on every ending — this
  is a different act) and §6 (the gesture, which this row now also wears).
  [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md) whole:
  nothing here is a conclusion, and nothing is recorded on the challenge.
- **Cites** ADR-0172 §4 for `game_id` on the challenge read, which is the join the row clears on;
  [ADR-0168](0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md) §2 for the shape
  of a per-player fact read against the record on every read.
- **Does not decide** a trash on any other ending's row or card; a confirmation on either; whether
  `GET /challenges/{id}` should refuse a court its reader has cleared (it resolves, as a stale
  route does today); a remove on the ended challenge screen's arm; an undo; or any change to the
  24 h shelf for rows not cleared.
- Decided 2026-09-16 with the author in session, from walking the left-behind scenario by hand;
  not grilled. Built in the same session, backend and player app.

## Context

Player A sends a padel four to B, C and D. All three say yes; the line-up completes, the game and
its room open. Then B leaves, C leaves, and D leaves — the third departure calls the game off
(ADR-0165 §3, ADR-0172 §1). The room is destroyed in the act. What A is left with on Chats is one
row: D's face, *tomek.p left*, a red **Called off** tag, and — by ADR-0172 §7 — a day to wait
before the inbox shelves it. On Now, the same court is a **Called off** card with a trash on it,
which A can clear at once (ADR-0172 §5).

The row above it on Chats — a send nobody has answered — **swipes to reveal *Remove the
challenge***. The author's ask was the obvious one: the called-off row should swipe the same way.

**The withdraw cannot be that act.** `Challenge.withdraw` and `Challenge.call_off` share one gate,
and it refuses every ending with `challenge_is_over` — `CALLED_OFF` included, by ADR-0172 §2's
design (*"every seat act meets `challenge_is_over` on it"*). Nor should it be: a withdrawal is a
conclusion recorded on the challenge for everybody on it (ADR-0142), and what A wants is not to
end a court that has ended but to stop looking at it. That is a **dismissal** — the reader's own
act, nobody else's fact — and the record already has one, on the game.

**Every `CALLED_OFF` court has a game.** The standing is reached only two ways, and both are
refused unless the court has become a game: the deserting departure records it under
`game_opened`, and *Call it off* requires `has_become_a_game()`. So for every row that wears the
tag there is a card A can already clear, and the row and the card are one court drawn on two of
A's lists.

**ADR-0172 §5 decided the opposite, in one sentence**, and gave a reason for the sheet rather than
for the row: *"the act removes a card, not a fact: the challenge row and the screen behind it keep
the news for their day"*. The row keeping its day was the shelf rule (§7) applied without
exception, and the exception was not argued because nothing asked for it. Walking the scenario
asks for it: the one person a called-off row is news to has read the news, has a trash for the
same court one tab over, and is offered a swipe on the row above that does nothing on this one.

Three shapes were considered. **A new per-player act on `challenges`** — `ChallengeDismissed`,
`POST /challenges/{id}/dismissal`, its own read subtraction — would be ADR-0172 §5 again, one
context over, with a second event announcing that the same person no longer wants to see the
same court, and two trashes that could disagree: card gone, row still here. **A client-side
hide** — remembering the swipe on the phone — is what §5 refused by name for the card, and the
reason travels whole: the row must be gone on the reader's other phone and after a reinstall.
**Reusing the game's dismissal** — one act, one recorded fact, read on both lists — costs no event,
no endpoint and no wire field, and is what the two surfaces already are: one court.

## Decision

### 1. One act clears one court from the reader's two lists

**`POST /games/{id}/dismissal` is unchanged, and `GET /challenges` now subtracts its reader off
the same set `GET /games` does.** A `CALLED_OFF` row whose game the reader has dismissed is left
off their list — on every read, derived, never stored on the challenge. Nobody else's inbox
moves; a row the reader has not cleared keeps its day like every ending (ADR-0172 §7); every
other standing's row is untouched, because a dismissal is admitted on nothing else.

**Where the read asks, and what crosses.** The challenges read already asks `games` one question
per inbox — *which of these courts became which game* (ADR-0172 §4) — over the been-a-game subset,
through `GameOfCourtQuery`. It now asks a second, **about the reader and not about the game**:
`dismissed_of(challenge_ids, by=reader)` → the subset this player has cleared, asked over the
rows the fold says are `CALLED_OFF` and no others. What crosses the `challenges → games` seam is
one membership — *yes or no, for you* — never the set of who has cleared it, and still not the
game's standing, court or ending, which the challenge's own fold answers (ADR-0172 §1). The
subtraction is in the read model, after the fold, and nowhere else: the four acts' replies never
meet a dismissed court, because every act on an ended challenge is refused before it could.

**Why the read model and not the fold.** A challenge event for this would announce on the
challenge's stream what the game's stream already says, about a person rather than the court —
the second-copy shape ADR-0172 §4 refused for `game_id`, with the same fix: read, not recorded.

### 2. Who may — the game's own rule, and the row never offers what the server refuses

`Game.dismiss` is unchanged: admitted for a player on the court, on a game that is `CALLED_OFF`,
refused as a stranger for anybody else — the leaver whose departure called it off included, whose
seat was vacated. The row reads the same rule off the row it already holds, `mayDismiss`: the
standing is `CALLED_OFF`, there is a game behind it, and **the reader holds an accepted seat**.
A leaver's seat reads `LEFT`, and their own row left the inbox at once (ADR-0165 §6, ADR-0172
§7), so the row that would be refused is a row nobody sees. The presser's own row is theirs to
clear — they are still seated — as is every other seated player's; the one left behind by three
departures is the case that asked for this, and is the same rule.

### 3. The row swipes, reveals *Remove this row*, and the act is the press

**The `Called off` row the reader is still on wears §6's gesture** — the same `SwipeRow` the
organiser's unanswered send and every conversation row wear — and reveals one control, spoken
**`Remove this row`**. **No sheet**, on ADR-0172 §5's reason, which widening the act does not
touch: it removes the court from the reader's own two lists and nothing from the record, nobody
else's row or rail moves, and a confirmation would put the withdraw's ceremony on the least
consequential act in the app. So the door's *open* is the act; a second press while the first is
in flight sends nothing. The row's accessibility action offers the same door under the same word,
as the removal's does.

**Success is the reply, and both lists move on it.** The dismissal's cache effect is declared
once, in `games`, and it now touches two lists: the card is dropped from the games list, and the
row is dropped from the challenges list **through the one write that list lets another feature
make** — `dropCourtOfGame(client, gameId)`, keyed by the game because that is the one id the act
has and the one the row carries for this join (ADR-0172 §4) — and both lists are re-read. So the
row is gone before any re-read, as the leaver's is, and **the Now card is gone with it whichever
list the act was met from**: the trash on the card clears the row, and the swipe on the row clears
the card. **A refusal is the re-read and no words**, the trash's own posture (ADR-0172 §5): the row
under the finger is not the row the server holds, and the fold the re-read lands on is the answer.

### 4. Two words for one act, each exact where it is read

The card's control is still spoken **`Remove this card`** and the row's is **`Remove this row`**
— *this row* and not *the challenge*, because *Remove the challenge* is the withdraw's word and
ends a court for the people asked, and this ends nothing. One act, named on each surface by what
the reader sees go from it; the copy deck says so (`the-words.md` §22.9).

### 5. The record's own words move with it

`GET /challenges`' contract description now says *ended challenges are here too — except the one
you cleared yourself*; the emitted document and the generated client types are regenerated with
it, and the drift and freshness gates stand. The `challenges → games` adapter's note that it
*translates a game into its id and nothing else* now says *and into one reader's yes-or-no*.

## Consequences

- **The one left behind clears the row when they say so**, on every device, and the card with it.
  No new event, endpoint, wire field or client type; the contract document changes in one
  description.
- **The row and the card are now coupled by the act.** A player cannot keep the card and lose the
  row, or the reverse. Accepted, because they are one court and the news on each is the same
  sentence; the day that reads wrong is the day this is reopened.
- **The inbox read walks `games` twice for the `CALLED_OFF` subset** — once for the id, once for
  the membership — on a subset that is empty for most readers and rarely more than one. ADR-0172's
  consequences already name this read as the one to make a single call the day a measurement
  shows it; that day, both questions become one read.
- **The first reader-keyed question across the `challenges → games` seam.** Every earlier read on
  that arrow asked about a court; this asks about a person. It is stated on the port and the
  adapter so the next one is argued rather than inherited, and it crosses as a membership, not the
  set.
- **A dismissed court's challenge screen still resolves.** `GET /challenges/{id}` is not asked
  about the dismissal (not decided above), so a stale route or a back-stack entry lands on an
  ended court with no arm — the screen ADR-0172 §7 already draws. The row that opened it is gone.
- **The client's feature barrels gain a `games → challenges` edge** (the list key and the one
  write), beside the `challenges → games` edge that already carried `gameKeys`. Cycles of this
  shape already exist (`games ↔ conversations`) and resolve at call time; ADR-0149 §1's one-way
  edge, `games ↛ plans`, is untouched and still lint-enforced.
- **ADR-0172 §5's sentence about the row is now wrong as written**, and its status line says so.
  The reason it looked right — the shelf rule applied without exception — is kept there, because
  it is what the exception was argued against.
