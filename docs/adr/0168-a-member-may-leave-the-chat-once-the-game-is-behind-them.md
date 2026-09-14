# ADR-0168 — A member may leave the chat once the game is behind them, and the exit holds for as long as it is

- **Status:** Accepted
- **Date:** 2026-09-14
- **Narrows, by named sentence:**
  [ADR-0165](0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)'s
  *"Nobody is in the chat separately from being on the court … So **leave the chat** can only mean
  **leave the game**"* — true exactly while a seat on the court can still be left or taken, and not
  after; once the game's agreed moment has passed, or the game has been played, a member may leave
  the room and keep the seat they played in (§1).
  [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §7's *"Membership is
  derived … Never stored"* — the roster is still derived from the court; the room now stores **one
  subtraction from it**, its members' own exits, admissible only once the roster can no longer
  move, and whose *effect* is derived on every read (§2).
- **Amends** [`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §1.1's shelf life for
  a completed court's row (§5), §1.3 and §2.5's *Leave the game* row — the swipe's one button
  follows the game (§5) — and §3's list of what ends a room, which gains a sentence saying what
  does **not** (§4).
- **Leaves standing** [ADR-0153](0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
  §2 and §4 — the room's clock, `entry_closes_at` or 48 h after *we played*, is untouched, and a
  member's exit is not on the list of things that end a room;
  [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)'s
  *destroyed, not delisted* — a room is still never delisted for **everybody**, and what one
  member's list loses is that member's own membership; [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)
  §4's moment guard, which this record reads rather than duplicates; ADR-0165 §1–§6 in every
  other sentence, its author's rule 1 included — *everybody in a chat can leave it, from the list,
  by the same gesture; the others keep the chat*.
- **Cites** [ADR-0151](0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md)
  for the 48 h grace this record does not move, and ADR-0165 §6 for the gesture.
- Settles the grilling of 2026-09-14; built by the backend and player tickets it is filed with.

## Context

**Sunday noon, and a chat that will not go.** Kuba challenged Ania on Thursday evening; she said
yes, which opened their room and made the game. They agreed Saturday 18:00 and played. Sunday
09:00 Kuba tapped *We played* and put in 6‑4 6‑3. At noon Ania opens Chats: the room is still in
her list, and will be until **Tuesday 09:00** — `GamePlayed` plus `CONVERSATION_GRACE` (ADR-0153
§4). She swipes it left. The one button reads **Leave the game**; the sheet says *Your seat opens
for someone else and you'll leave the chat*; she confirms, and the sheet answers **"This game has
already happened, or never will."** The row stays.

**The refusal is right about the game and wrong about Ania.** `POST /challenges/{id}/departure`
is an act on the **seats**: the seat reopens and somebody may be seated in it. Once a game has
been played the line-up is the record of an evening and nothing on it moves — `game_is_history`,
ADR-0162 §4 — so there is nothing to leave. Ania never wanted her seat back. She wanted the room
off her list, and the app has no act that does that.

**Two rooms linger, and only two.** A game called off takes its room in the same act (ADR-0163).
A game nobody marked as played loses its room the instant *we played* stops being sayable. What
lingers is the room of a game that **has happened** — 48 h after *we played* — and the room of a
game whose **agreed moment has passed and whose entry is still open**: Saturday 21:00, they have
played, nobody has said so yet, and the room lives until `entry_closes_at`, up to eight days after
Thursday's yes. There the swipe is refused with the other sentence, *The time you agreed has
passed, so there's nothing to leave now* (`game_moment_has_passed`). Neither sentence is wrong;
both answer a question Ania did not ask.

**ADR-0165 argued that *leave the chat* can only mean *leave the game*, and the argument has a
boundary it did not draw.** Membership is derived from the court, so *"there is no fact to remove
somebody from a room without removing them from the court, and inventing one would leave a player
counted 3 of 4 in on a plan they no longer read."* That is exactly right **while the plan is
ahead**: a member who stopped reading the room would be planned around. It says nothing about a
plan that is spent. Once the agreed moment has passed — or the game has been played — nobody is
planning around anybody; the seat change is refused for that very reason (ADR-0162 §4); and the
one thing the room is still for is the conversation after the game, which the 48 h grace exists to
hold (ADR-0153 §4). A member who does not want that conversation is asking for nothing the court
needs to know.

**The author's own rule points the same way.** ADR-0165's rule 1 — *everybody in a chat can leave
it, from the list, by the same gesture* — was stated without a date on it. What the exits built
honours it while the game is ahead and refuses it afterwards, which is the one time a WhatsApp
group's *exit* is what the person means.

## Decision

### 1. *Leave the chat* is a member's own exit from the room, admitted exactly where the seat change is refused

**A new act on `conversations`**, a member's, on the room it names. It is admitted when, and only
when, a seat on this court may no longer be left or taken — the game's agreed moment has passed, or
the game has happened or never will — and it is refused everywhere else:

| The court | The seat change (ADR-0162 §4) | Leave the chat |
| --- | --- | --- |
| no game yet, or a game awaiting its entry with its moment ahead or unagreed | admitted | **refused** — *the game is still ahead; leave the game instead* |
| a game awaiting its entry whose agreed moment has passed | `MOMENT_PASSED` | **admitted** |
| a game that has happened, or never will | `GAME_IS_HISTORY` | **admitted** |
| a room that has ended | — | `conversation_not_found`, as for every read of one |

**One question, two acts, complementary.** `games` already answers *may a seat on this court still
be left or taken* for `challenges`' three seat acts (`SeatableCourt.line_up_change_on`). This
record asks the **same question through a demand of this context's own** — `conversations` may
read `games` (ADR-0148 §8, the direction `.importlinter` holds open) — and admits the exit where
the answer refuses the seat. The two acts can therefore never both be admitted and never both be
refused on one court at one instant, which is what lets the client draw **one** button (§5). A room
without a game asks nothing and refuses: before a court is whole the exit is *Leave the game*, as
ADR-0165 §1 built it.

**A hold refuses it**, on the departure's own sentence: the exit writes a line into a room other
people read, which is reach (`account_held`). The row then waits for the clock like anybody's
who forgot.

**It is the room's own act, not a telling.** Like *Say something*, it is written by the member
through the room's own route, under the room's lock, with a sequence number of its own — one new
event on the conversation's stream, which is at once the membership fact (§2) and the entry the
others read (§3). Nothing is published outward; a conversation still tells nothing.

### 2. The exit is recorded once, and its effect is read against the game on every read

**Membership stays *the people who have agreed to be on this court right now* — minus the members
who have left the room, for as long as the game is behind them.** The roster is still derived from
the court (ADR-0146 §7 as ADR-0162 amended it); the exit is the one fact the room stores about its
own membership, and it is a **subtraction only** — a room can never hold somebody the court does
not.

**Its effect is conditional, and the condition is the game's.** The exit removes its member from
the room while, and only while, the seat change on the court is refused. A plan is editable by any
member at any time (ADR-0144, ADR-0164 §1), and a plan whose moment has passed may be moved to a
future one — a rained-off Saturday becomes Wednesday. When it is, the seat change is admitted
again, the game is *ahead* again on every phone, and the member who left is **back in the room**,
because a game that is ahead is a game they are in — the very fact ADR-0165's argument protects.
After *we played* the game can never be ahead again, so in the ordinary case the exit is simply
final.

**Never undone by a message.** A message from the others brings nobody back; a rematch is a new
challenge, which is how the app already thinks about asking again. The one thing that restores a
member is the court's own moment moving ahead of them, and that is the court's act, not the
room's. No *{name} is back* line is written: nothing happened in the room, and the plan's own
*{name} set the day* line is what happened next.

**Derived rather than stored, deliberately.** A stored *left* flag that a plan move had to clear
would be ADR-0146 §7's second copy in the column that decides who may read the messages, and the
plan cannot clear it — `plans` does not know the room exists. Reading the exit's effect off the
game on every read costs one more question to `games` per room **that has a leaver**, on a list
read that already asks `games` about every room with a game; a room nobody has left costs nothing
new.

### 3. What the others read: a line, and the faces they played with

**A new system line code, with the leaver as its value** — rendered *{name} left the chat*. **Not
`SEAT_LEFT`**: that code says a seat is open again, and no seat moved. The room orders on it as on
any entry; a member leaving is news to the people still there, as *{name} left — that seat is open
again* already is.

**The header keeps every face and every stem.** The room is about the game these people played,
and the line-up is the record of that evening (ADR-0162 §4); the line is what tells Kuba that Ania
has gone. In singles the alternative is a header with nobody in it.

**Nothing else moves for them.** Their room lives to its clock, their challenge row keeps its own
life (§5 names the one exception), the score argument on `games` is untouched, and the pair rule
neither releases nor binds — the seat never moved.

### 4. The room's clock is untouched, and an exit is not an end

**A member's exit is not on the list of what ends a room** (ADR-0153 §2, `the-loop-screens.md`
§3), and this record adds nothing to that list. The leaver's row goes **by membership**, as a
departed seat's does today; the room is destroyed by its clock, for everybody, as before. A room
every member has left is a room nobody can read, and the clock takes it; no new destruction path
is written for a case nothing observes.

**The 48 h grace stands** (ADR-0153 §4, ADR-0151). It is for the member who forgot; this record is
for the member who did not. Its falsifier gains a second reading: *exits within hours of
`GamePlayed`, against the share of rooms in which anything is said on the second day* — a grace
most people leave before it starts is a grace measuring the wrong thing.

### 5. The client: one button that follows the game, a sheet, and two rows that go at once

**The swipe on a chat row reveals one button, and its word follows the game's card** — the same
card name the room's header already folds for its state word (ADR-0157): **Leave the game** while
the game is ahead — *planning*, *game on*, *needs a player* — and **Leave the chat** once it is
behind — *needs result*, *confirm*, *counted*, *uncounted*. A room without a game reads *Leave the
game*. The two refusal sentences of `the-words.md` §22.10 stay for the stale case and stop being
the ordinary one.

**The sheet is §22.10's shape with its own words**, and it says the three things the leaver may
not expect — it is for good, the others are told, and the score is untouched:

| | |
| --- | --- |
| Title | `Before you leave` |
| Body | `This chat and its challenge leave your list for good, and the others are told. The game and its result stay as they are.` |
| Act | `Leave the chat` |
| In flight | `Leaving…` |
| Dismissal | `Stay in` |

**Refusals are said on the sheet, in words**, as §22.10 already has it: the server finding the
game still ahead — *This game is still ahead. Leave the game instead.* — leaves the sheet up, and
the lists re-read on *Stay in* so the button redraws; a hold says the hold's own sentence; a room
already gone closes the sheet and takes the row with nothing said, on `challenge_not_found`'s
*leave* arm — what was asked for has happened.

**Both rows go the moment the reply lands.** The chat row by membership, as today. **The challenge
row by a rule this record adds to §1.1's shelf life: a completed court's row — *You're in —
everybody's in* — is drawn only while the reader still has the room for it.** The row is kept a day
because a court filling is news; once the chat for that court is over — by the clock, or by the
reader leaving it — it is not news to anyone. The consequence for the **other** members is named
and accepted: their row for a game whose room ended on the clock goes with the room rather than at
the end of its own day, which only happens when the room ends first — a game arranged and played
the same evening. The exact alternative, the wire carrying *left the chat* on the seat, would have
`challenges` reading `conversations`, the one direction ADR-0146 shut, to buy a row a day.

**The game screen's door into the chat follows membership**, as it already does for a room that
has ended: no room of yours, no door. A second device holding the room when its owner leaves it
elsewhere keeps the stream and the header and says §22.5's *This chat has ended.* in the
composer's place — the sentence already drawn when a room stops existing under somebody, and the
leaver is the one person who does not need telling why.

**The act lives on the row's swipe and the row's accessibility action, and nowhere else.** Not on
the game screen, which is the record; the room's *Details* is that screen, so not there either.

### 6. What this record does not touch

Now, the game card and its shelf; the score, the result argument and the rating; `GET
/challenges`, which still holds the seat; the pair rule; the room's clock; every refusal on the
seat acts; ADR-0165's exits before the court is whole. Nothing notifies anybody — there is no
channel — so the line is read on the next open, as every line is.

### 7. Records and copies

ADR-0165's and ADR-0146's status lines name what narrowed. `the-loop-screens.md` §1.1, §1.3, §2.5
and §3 carry the amendments in §5 and §4. The root `CONTEXT.md`'s **Member** and **Lifetime**
entries say so, and the Conversation section gains **Leaving the chat**. `the-words.md`'s new
sentences — the button, the sheet, the line, the refusal — are the player ticket's, as ADR-0165 §7
had it. `backend/CLAUDE.md` and `frontend_player/docs/features/conversations.md` document what is
built and move with the code.

## Consequences

- **Ania's Sunday ends with one swipe.** The two refusal sentences leave the ordinary path; the
  row and the challenge row go together; Kuba keeps his room and is told.
- **The first membership fact a room stores.** ADR-0146 §7's *never* becomes *never anything the
  court does not already say, and one subtraction the court cannot*. It is bounded on both sides
  — admissible only once the roster is frozen, effective only while it stays so — and the bound is
  read from `games`, not kept here. Whoever next proposes storing a roster will cite this record;
  the answer is that this is not one.
- **A second question to `games` on the list read**, for rooms with a leaver. The list already
  asks `games` about every room with a game (`entry_closes_at`, membership); this adds the
  seat-change question for a subset. If it shows up in a measurement, the fix is asking both
  questions in one call, not storing the answer.
- **A rescheduled game brings a leaver back without a line saying so.** Ania leaves Saturday
  night; Kuba moves it to Wednesday; her chat is back and Kuba's backlog still reads *Ania left
  the chat* above *Kuba set the day*. Accepted: the second line is what happened next, and a
  *back* line would announce a derived fact (ADR-0146 §6). Falsifier: leavers of rescheduled games
  leaving again, which would say the return surprised them.
- **The other members' *everybody's in* row can go a day early**, when a room ends before the
  row's shelf does. Named in §5; it happens on same-evening games and nowhere else.
- **A held account cannot leave a chat**, and waits for the clock — under 48 h, on the same rule
  that stops it leaving a game.
- **The phone's ladder and the server's clock can disagree at the boundary.** A button reading
  *Leave the chat* at 17:59 by one clock and refused at 18:00 by the other is the case §5's refusal
  sentence exists for, on the shape every refusal on this sheet already has.
- **Tests that pinned the old rule move**, named rather than discovered: the departure's
  `game_is_history` and `game_moment_has_passed` as the *only* answers to a swipe on those rooms;
  membership as a pure fold over the court; `belongsOnTheInbox`'s `ON` row against a Conversations
  cache it did not read; the conversation row revealing *Leave the game* unconditionally.
- **No new dependency**, no new gesture, no change to the wire's existing routes: one route
  added, one system line code, one refusal code.
