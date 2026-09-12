# The loop screens

**What each surface draws, what each control does, and which screen behaviours are decisions
rather than interface choices.**

Produced by [Write the screen specs](https://github.com/Raketa02/Raketa/issues/339) on the map
[Closing the loop — a challenge answered, a game talked about, a result that moves a level](https://github.com/Raketa02/Raketa/issues/321).

**The decisions live in ADRs; this file is the shape to check work against.** The withdraw is
[ADR-0142](../../adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md),
the challenge card is
[ADR-0143](../../adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md),
the Plan is [ADR-0144](../../adr/0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md) and
[ADR-0145](../../adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md), the two
contexts are
[ADR-0146](../../adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md), the live
channel is
[ADR-0147](../../adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
the wire is
[ADR-0148](../../adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md), the
composition and the chat door are
[ADR-0149](../../adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md), the
line-up re-entry is
[ADR-0150](../../adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md),
and the answer window is
[ADR-0151](../../adr/0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md).
**The conversation's lifetime was ADR-0142's and is now
[ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)**,
which was filed outside the map and governs §3 anyway.

> **This is the shape, not the visual design.** What each surface *says* is
> [`the-words.md`](../matchmaking/the-words.md); where one component stops and the next begins is
> [`the-loop-components.md`](the-loop-components.md); what it *looks like* is
> [`design-system.md`](../../../frontend_player/docs/design-system.md), which is locked and which
> this map amends through [Part 16](../../../frontend_player/docs/design-system.md#part-16--amendments-after-locking)
> rows scheduled by [#338](https://github.com/Raketa02/Raketa/issues/338).

> **Every state on every screen here is reachable by `make seed`.** The map's standing constraint,
> and it is already this repo's law
> ([ADR-0029](../../adr/0029-seed-data-through-aggregates-never-in-production.md)): a plan at
> nought, one, two and three slots is four seeded plans and never four fixtures, and there is no
> `__DEV__` data path, no mock module and no fixture imported by a screen. A client with one stops
> exercising the endpoints it exists to prove.

---

## 0. The routes, after this work

### 0.1 The wire

[`the-two-contracts.md`](../matchmaking/the-two-contracts.md) §1 and
[`the-play-screens.md`](../matchmaking/the-play-screens.md) §0 fix what the matcher serves. This
map adds nine routes and two fields, across four contexts.

| Route | Answers | Decided by |
| --- | --- | --- |
| `GET /api/v1/challenges` | unchanged shape, **plus `read_at` at the envelope and `nickname` on `SeatSchema`** | [ADR-0143](../../adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md) §9 |
| **`GET /api/v1/challenges/{challenge_id}`** | one challenge richly — the arrangement, the person and the pairing, recomputed for the reader | ADR-0143 |
| **`POST /api/v1/challenges/{challenge_id}/seats`** | the send's shape minus the mint, `{search_id, court}` | [ADR-0150](../../adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md) §6 |
| **`POST /api/v1/challenges/{challenge_id}/withdrawal`** | the challenge as it now stands, `WITHDRAWN` | [ADR-0142](../../adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md) |
| **`POST /api/v1/challenges/{challenge_id}/departure`** | the challenge as it now stands, `LINE_UP_INCOMPLETE` with the caller's seat `LEFT`; the game keeps its id with that seat `player_id: null` | [ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) |
| `POST /api/v1/lineups` | grows one optional **`completing_challenge_id`**; `sport`, `mode` and `locked_seats` are **refused** beside it | ADR-0150 §2 |
| **`GET /api/v1/conversations`** | `read_at` + rows: members with handles and photos, sport, `last_entry`, `conversation_id`, `challenge_id`, nullable `game_id` | [ADR-0148](../../adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md) |
| **`GET /api/v1/conversations/{id}`** | its own `read_at`, the header **and** the newest page — one fold | ADR-0148 |
| **`GET /api/v1/conversations/{id}/entries?before_seq=&limit=`** | a page backward, no header. `limit` 50 default, `le=100` | ADR-0148 |
| **`POST /api/v1/conversations/{id}/messages`** | the created message. `client_message_id` in the **body** | ADR-0148 |
| **`GET /api/v1/conversations/{id}/stream`** | `text/event-stream`; the frame is `{v, conversation_id, last_seq}` and nothing else | [ADR-0147](../../adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md) |
| **`GET /api/v1/plans`** | every plan for games you are on the court of. **No `read_at`** | ADR-0148 |
| **`PUT /api/v1/plans/{game_id}/place` · `/day` · `/hour`** | one route per slot, because ADR-0144 has three events | ADR-0148 |

**Two reads for the Chats tab, never one**, and **two reads plus a client-side join for Now** —
ADR-0148's own costs, restated here because a build session reading only this file would otherwise
reach for the cheaper shape.

### 0.2 The screens, and which tab column stays lit

`tabForPathname` is **pure on the first path segment**, and `INSIDE_A_TAB` exists only because
Now's root is `/` and has no segment of its own
([ADR-0149](../../adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §9).
Everything this map adds under `/chats/…` lights the Chats column **for free**, so
`INSIDE_A_TAB` is untouched and keeps its single entry.

| Route | Screen | Column | New |
| --- | --- | --- | --- |
| `/chats` | The Chats tab — two sections | Chats | grown from a placeholder |
| `/chats/challenge/[challengeId]` | The challenge screen | Chats | ✅ |
| `/chats/challenge/[challengeId]/fill` | The builder, re-entered — **`features/play`'s screen at a second route** | Chats | ✅ |
| `/chats/conversation/[conversationId]` | The conversation — **the column is lit and the bar is not drawn** (§3) | Chats | ✅ |
| `/chats/conversation/[conversationId]/details` | The game screen — **the same component `/games/[gameId]` renders** | Chats | ✅ |
| `/` | Now — the rail | Now | grown from a placeholder |
| `/games/[gameId]` | The game screen | Now, via `INSIDE_A_TAB` | renamed |

**One row lights a column on a bar that is not there.** The conversation stands the tab bar down
(§3, [#400](https://github.com/Raketa02/Raketa/issues/400)), and `tabForPathname` still answers
*Chats* for it: which column a route is inside and whether the bar is drawn are two questions, read
by two callers, and the second is `barStandsDown` beside the first in `shellTabs.ts` — pure on the
whole path rather than on the first segment, because the inbox, the challenge screen and the game
screen behind the room's *Details* door all keep their bar. The column staying lit is what makes
*back* land on a lit *Chats* rather than on a bar that has to work out where it is.

**Both dynamic segments under `/chats` carry a static kind above them, and that is a decision
rather than a style.** A challenge id and a conversation id are different ids of different things,
and `/chats/[id]` for both would be one segment a router cannot resolve and a reader cannot read.
The cost is one segment; what it buys is that no conversation id may ever collide with the word
`challenge`, and that a path states what it is looking at.

> **This is a correction to a spelling rather than to a decision.** #336 §9 wrote the details route
> as `/chats/[conversationId]/details` and ADR-0150 §7 put the fill *"under `/chats/…`"*; neither
> was choosing between one id kind and two, because neither had both screens in front of it. The
> **reason** each gave — a path under a tab root lights that tab's column for free, so
> `INSIDE_A_TAB` never grows — is untouched and is why both still sit here.

**Two routes over one screen component, twice**, and it is the same argument both times
(ADR-0149 §9): each route lights its own column, *back* is correct in both directions **by
construction**, and neither `tabForPathname` nor `INSIDE_A_TAB` grows a `from` parameter that
would make a pure function impure. The game screen is the case that record decided; the builder is
its second instance, and it costs nothing new because `/chats/challenge/[challengeId]` has to
exist anyway.

**Nothing in the Chats flows calls `resetShellStack`** (ADR-0150 §7). That reset dismisses the
stack and ends the Play session, and `landOnNow`'s argument — *"there is nothing left to be behind:
the court is gone"* — is false here, where the thing behind is the challenge you were completing.
The builder is a plain push and **the send pops back to the challenge screen**, which is the
surface that draws the result: the new seats, their fresh deadlines, and a standing that may now be
`AWAITING_ANSWERS` again.

---

## 1. The Chats tab

**Two sections, one obligation and three rooms.** Decided on the prototype `prototype/chats-tab`
by [#335](https://github.com/Raketa02/Raketa/issues/335), which is that decision's primary source.

### 1.1 The two sections

| | Heading | Holds |
| --- | --- | --- |
| first | `CHALLENGES` | every challenge you hold a seat in that is still being arranged, and every one that ended in the last 24 h |
| second | `CONVERSATIONS` | every conversation you are a member of |

Headings are `eyebrow` / `muted` / uppercase — [#338](https://github.com/Raketa02/Raketa/issues/338)
§8 struck *and section* from `h2`'s purpose and gave the role to `eyebrow`, which already labels
*"a region you are reading."*

**`CHALLENGES`, and no count at all.** *Challenges for you* had to widen, because a challenge you
**sent** belongs in this list and is drawn nowhere in the app today. Widening breaks the number:
`CHALLENGES FOR YOU · 1` agrees exactly with the tab badge, which
[#326](https://github.com/Raketa02/Raketa/issues/326) §3 says counts **only** what is addressed to
you and unanswered — and two numbers meaning different things on one screen is that record's own
named failure. **The badge is the only number on this screen.**

**The challenge section is ordered by whose turn it is, then by the clock**: rows you can clear
first, in order of least time remaining; then everything else, newest first. That is the badge's
predicate reused as a sort, so the thing the badge is counting is the thing at the top of the
list.

**An ended challenge keeps its row, in place, and it leaves 24 h after the challenge ended.** The
wire keeps ended challenges for ever and says so, but a screen that draws all of them turns an
inbox into an archive. What the row carries is **actionable news** — *{name} said no — that seat is
open again* says the pair rule has released and you may send again, which
[ADR-0142](../../adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
made possible for the first time. News has a shelf life; nothing is lost and nothing lies, because
the list still holds them. **A no of the reader's own is not news to them, and its row leaves with
the tap** rather than after a day — §2.5 has the argument, and it is this paragraph's read from the
other side.

**The instant it is subtracted from is on the wire, and one standing here is not on the list**
([#388](https://github.com/Raketa02/Raketa/issues/388), [#395](https://github.com/Raketa02/Raketa/issues/395)).
`ChallengeSchema.ended_at` dates the three standings the contract calls endings — exactly for a
lapse and a withdrawal, and as an **upper bound** for a decline, since nothing records the instant
somebody said no. This paragraph's rule was written before that field existed and the client had
been approximating it off the latest `answer_by` on the court, which dated a withdrawal not at all
and so kept that row for ever. **`ON` is the standing that is news to this screen and not an
ending** — a completed line-up is exactly when two people have a game, which is the opposite of
nothing being left, so the contract serves it no instant — and it is dated here off the court's own
deadlines, which for a court where everybody accepted inside their day bounds the last acceptance.

**This 24 h is not the conversation's, and it did not travel with it.** A row here and §4.1's
ended card are **shelf lives on an inbox**, where the record survives and only the row departs,
while a conversation's end **destroys an aggregate** — so moving that lifetime left both of these
exactly where they are, and what agreement is left between the numbers is a coincidence rather
than a rule ([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §7).

### 1.2 The challenge row

**Face or faces · the whole handle or handles · the sport · one line · the stripe.** Fully
clickable, 44pt minimum, opening `/chats/challenge/[challengeId]`.

**The face is a photograph or a generated poster, and there is no monogram.** #338 §5 refused the
avatar outright: `CandidatePhoto` already is the photograph-or-poster switch, a poster is **a fact
about an id** ([ADR-0134](../../adr/0134-the-poster-draws-a-player-and-no-value-is-invented.md)),
and initials are a derived familiar form
[ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md) refuses. The cost is
stated there: the rows lose the six coloured initial tiles `chat_tab.png` draws.

**The handle list truncates by dropping whole names, never by shortening one.** §15 is categorical
— *"a nickname is not shortenable"* — so the ellipsis falls at a separator and never inside a
handle. Whoever is dropped is whole on the screen behind the row.

> **The one line is §13's standing sentence — except on a challenge that is yours to answer and
> unanswered, where it is the time you have left.**

Two sources for one slot, chosen by **is this mine to clear**: `organiser_id != me`, your own seat
`answer == null`, standing `AWAITING_ANSWERS` or `LINE_UP_INCOMPLETE`. That is the badge's own
predicate (#326 §3), so **the badge, the sort and the line agree by construction** rather than by
three implementations remembering the same rule.

- **Yours to answer** → §14's new fourth sentence, `{duration} left to answer`, folded from your
  seat's `answer_by` against the response's `read_at` and **never against this phone's clock**
  (`durations.ts`'s untouched discipline). §14's `{name} · {duration} left` names somebody else and
  is the **organiser's** screen's sentence; naming yourself on your own row would be the app
  telling you who you are.
- **Everything else** → §13, one line, tail-truncated.

**The urgency stripe is drawn on exactly the rows whose line is a duration.** Full height always,
**`amber`**, absent when there is no clock of yours, and **hidden from the accessibility tree**
because the sentence carries the fact.

- **Presence, never magnitude.** §20.8 already ruled a meter decoration in this app, and a bar
  encoding the remaining fraction would be a second spelling of the duration — the exact failure
  the design commits with *"lapses Tomorrow · 17:00 17:00"*.
- **`amber` and not coral**, decided by #338 §6: §1.2 lists five coral uses and says *Nothing
  else*, #326 has already claimed the sixth, and a coral stripe on every row with a live clock is
  coral on most of a section at once. 1.3 reads amber as *watch this — reversible, not yet
  wrong*, which is exactly what a live answer window is.
- **No stripe on the organiser's row.** The clock is live but it is not yours to clear, and the
  stripe marks what the badge counts.

### 1.3 The conversation row

**Faces · the whole handles · the sport · the last entry, one line, tail-truncated.** Fully
clickable, opening `/chats/conversation/[conversationId]`.

**No pill.** ADR-0148 §6's *the last line is what a pill would have said* is a product argument and
not only a wire one, and the design's pill could now only be derived client-side off the games
cache — a join feature-first Clean Architecture otherwise refuses
([ADR-0009](../../adr/0009-feature-first-clean-architecture-frontends.md)). The three pills go, and
*Settle up* was already gone with ownership.

**The last entry is rendered by the same two components the stream uses** — a message renders as
its text, a system line renders from its code and values (ADR-0146 §4), filling `{name}` from the
members the row already holds and never from `values`.

**When a system line does not fit, the fix is a shorter value rather than a second line.**
`Zofia P. set the place · Zabłocie Sport, court 3` is long because the *value* is long; a place
line rendering the place without the court is a copy decision this build makes, and it keeps one
rule for both row kinds instead of two.

**A padel four whose membership is still growing draws the members it has.** Membership is derived
from the accepted seats and grows one acceptance at a time (ADR-0146 §7); a row that drew four
faces for a two-member room would be drawing the court rather than the room.

### 1.4 The row that is in both sections at once

**A `LINE_UP_INCOMPLETE` challenge you accepted draws a row in both sections, with two different
jobs.** §13's own sentence asserts both facts in one breath — *"You're in. {m} seats open, and the
chat is already open"* — so a screen asserting both in two places is the copy's shape rather than a
duplicate. The challenge row is the **obligation** (somebody still owes an answer, and you can see
who); the conversation row is the **room**. Drawing it only under `CHALLENGES` would make it the
waiting room [#221](https://github.com/Raketa02/Raketa/issues/221) says it is not.

**Stated rather than glossed: this is the answer most worth a device**, and it was taken on the
argument. *Argued as one thing* and *reads as a duplicate* are entirely compatible, and
`prototype/chats-tab`'s `bothSides` dataset is one tap away.

### 1.5 The panel, and the two empty states

**The panel states the limit that makes this a sports app**, and both of the design's promises are
dropped: *"when you count yourself into something tonight"* is Around, which this build does not
have, and *"inside a game or a plan"* is wrong in the other direction, because a conversation opens
on the **first acceptance**, before there is a game at all. The sentence that does the work is
kept — [`the-words.md`](../matchmaking/the-words.md) §22.1.

**Neither section may assert that nothing is happening.** Now's standing refusal, inherited for the
same reason: a send lands here now. Both empty states are **one line of `tiny` in `muted`,
present-tense, naming the act** — the shape #338 §9 promoted out of `PlaceholderScreen`'s docstring
into 10.1 — and `shellCopy.test.ts`'s *never says nothing is happening* **moves with the copy
rather than being deleted**.

**`PLACEHOLDER_COPY.chats` dies with them**, and `PlaceholderScreen` survives unchanged for Around
and You.

### 1.6 The tab badge

Decided whole by [#326](https://github.com/Raketa02/Raketa/issues/326) and not reopened. What this
file owes it is the placement: **the badge is the bar's, the section header carries no count, and
the row's stripe answers *which* rather than *how many*.** One number, drawn once, spoken once — on
the column's own `accessibilityLabel`, because `Column` is `accessible` and a `<Text>` dropped
inside it would be swallowed.

---

## 2. The challenge screen

`/chats/challenge/[challengeId]`. **A state-keyed surface over the five challenge standings and the
sixth ADR-0142 added — never a `GameStanding`.** A challenge with no acceptance has no `game_id` to
key a screen on, which is why there are two state-keyed surfaces and not one
([#324](https://github.com/Raketa02/Raketa/issues/324) §2). Decision 7 is untouched: both of *its*
doors are game doors.

### 2.1 The arms

**Side is derived from whether the reader holds the organiser seat** — one list, one code, and
nothing on the wire carries a side.

| Standing · reader | The sentence | Card block | Controls, in order |
| --- | --- | --- | --- |
| `AWAITING_ANSWERS` · invitee, unanswered | §13 *They're waiting on you* | **yes** | **`I'm in`** · **`Not this time`** |
| `AWAITING_ANSWERS` · invitee, accepted | §13.2 *You're in. Waiting on {n} answers…* | **yes** | **Open the chat** *(the door, below)* |
| `AWAITING_ANSWERS` · invitee, declined / lapsed | §13.2's **two sentences** — *You said no…* / *Your day ran out…* | no | none |
| `AWAITING_ANSWERS` · organiser | §13 *Waiting on {n} answers* | **yes** | **Open the chat** *(the door, below)* |
| `LINE_UP_INCOMPLETE` · member | §13 *{n} in, {m} seats open…* / *You're in. {m} seats open…* | **yes** | **⚡ Fill the seats** · **Open the chat** · **Withdraw** *(organiser only)* |
| `LINE_UP_INCOMPLETE` · reader who left | §13's **two new sentences** — §2.5 | no | none |
| `DECLINED` · both | §13 *{name} said no…* / *You said no* | no | none |
| `LAPSED` · both | §13 *{name}'s day ran out…* / *Your day ran out* | no | none |
| `WITHDRAWN` · both | §13 *You withdrew this* / *{name} withdrew this — that court is closed* | no | none |
| `ON` · both | §13 *Everybody's in* / *You're in — everybody's in* | no | **Open the chat** *(the door, below)* |
| `LINE_UP_INCOMPLETE` · member, **a court somebody left** | §13 *{n} in, {m} seats open…* — the same sentence, on a court that has been a game | **yes** | **⚡ Fill the seats** · **Open the chat** · **Call it off** *(the organiser — or, once the organiser has left, any remaining player;* [ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md)*)* |
| `LINE_UP_INCOMPLETE` · reader who **left the game** | §13's two sentences for a reader who left, read as *You left* | no | none |

**A reopened court is the half-built court again, and it is reached from the game**
([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md), 2026-09-12).
`POST /challenges/{id}/departure` is on the **game screen**, not here — the game carries its
`challenge_id` — and what it leaves behind is a `LINE_UP_INCOMPLETE` court whose seat reads `LEFT`,
which this table draws exactly as it draws one a decline reopened: the fill is the same fill, the
door is the same door. Two rows are added rather than the existing two widened, because one thing
differs: **the withdraw on a court that has been a game calls the game off**
([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), same day) — the same
route, the sheet reworded (`the-words.md` §22.3), and the control is the organiser's or, once the
organiser's own seat is open, any remaining player's. It was refused for the length of one record,
with `not_a_half_built_line_up`; that refusal is gone. The seat that left is drawn with its
answer, as a declined seat is.

**The door is drawn on every arm whose reader the room would hold** (2026-09-11). *Open the chat*
is ADR-0149 §3's client join over `GET /conversations`, and it **fails soft**: where the list holds
no room for this challenge — nobody has answered yet, the episode has ended — the arm draws
nothing, which is the *no door rather than a dead one* rule and is what the four rows marked *(the
door, below)* mean. Beside the join, the fold says whether **this reader** is in the room
(`readerIsInTheRoom`): a row that reads *none* is a reader who left or an episode that ended, and
the list — invalidated rather than patched by the reply that took them out — can hold their old
room for a beat; the unanswered invitee has said yes to none. A door is drawn only where both say
so.

**`I'm in` goes to the room.** Accepting is the one act whose whole point is a room to talk in —
the singles room with the person who challenged you, or the doubles room the people already in
are already talking in, its history included, because membership is derived and never cut at the
moment you joined. The reply is still the redraw (§2.4), and then the screen pushes the room. The
room is written by the teller off the outbox **after** the accept has answered, so the door is
**waited for** on a short bounded cadence rather than read once and missed; past the bound the
screen stays, and draws the door when the list next holds the room. **What is waited for is the
reply's to say**: `ON` means this yes completed the court and a game exists — opened inline with
the accept — while the room is told which a moment later and nothing nudges when it is, so the
wait is for the room to carry its game and the plan card is on screen when the room is. *Not this
time* goes nowhere.

**`AWAITING_ANSWERS` is three rows for the invitee, because the side alone cannot key it.**
`standing_of` holds this standing while **any** seat is awaiting, so a padel four sits in it with
the reader's own answer already given — accepted, or given and then released. This section used to
offer `I'm in · Not this time` to every invitee in it and to send them all §13's *They're waiting on
you*, and both were false for a reader who had already spoken
([#389](https://github.com/Raketa02/Raketa/issues/389)). The **controls** were already right in the
build — `challengeArm` gates them on *the reader holds a seat and nobody has answered for it*, so
`POST /accept`'s `seat_already_answered` is unreachable by tapping — and what was left was the
sentence, now [`the-words.md`](../matchmaking/the-words.md) §13.2's three readings. **Singles
reaches none of it:** the only invitee accepting takes the challenge to `ON`.

The `Card block` column reads `no` for the two who have **left**, which is §2.2's third level —
**per reader** — and is settled there rather than in this table.

**`ON` has an arm, and the inbox row is what reaches it.** An `ON` challenge **keeps its row in
`CHALLENGES` while it is news** — §1.1's *every one that ended in the last 24 h*, with the
**inbox's own `Record`** deciding that a completed line-up counts as ended, because nothing about
the arrangement can change again. Every row is a door, so the row opens this arm and the arm draws
the sentence with no card and no controls. A stale route resolves here too, and that is now the
second way in rather than the only one.

**What #324 ruled is narrower than this section used to claim, and the difference matters.** #324
took the **card** away — *"the game's standing owns the card the moment a game exists"*, upheld by
[ADR-0143](../../adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
§8 — and gave the **sentence** a home: *"§13's sentence for `ON` (`Everybody's in`) keeps its home
in the conversation, as the system line the first complete line-up writes."* §3.4 then **refused
that line**, on the rule that no system line announces a conclusion the record already implies, and
[`the-words.md`](../matchmaking/the-words.md) §23.1 lists `GamePlanned` among the six events that
publish nothing. So the home #324 named is gone, and a `SeatAccepted` line is written **only when
the room already existed** — on a singles two the one acceptance *is* the opening and writes
nothing. **§13's `ON` sentences are drawn on the row and on this arm, and by no system line**, so
the row is what makes them reachable at all — which is why extending *no card* to *no row* was this
section's own step and not #324's. Settled by
[#390](https://github.com/Raketa02/Raketa/issues/390).

> **The cost, stated rather than glossed: an `ON` challenge draws a row in both sections, and
> §1.4's argument does not cover it.** There it is *the challenge row is the obligation, the
> conversation row is the room* — and nothing about an `ON` challenge is anybody's obligation. This
> is news beside its room, and it is taken on that narrower ground.

**Every act is on this screen and none is on a row.** #324 §2 kept verbatim: every row is a door,
every act is on the surface behind it — Accept and Decline included.

### 2.2 The card block, and its three absences

**Drawn only in `AWAITING_ANSWERS` and `LINE_UP_INCOMPLETE`, and per seat as well as per
challenge** (ADR-0143 §8). The pair releases when a seat leaves, so a person who declined or lapsed
inside a still-open `LINE_UP_INCOMPLETE` gets no card either — *"that person is a stranger to you
once more the moment they leave."*

> **And a third level: per reader.** A reader whose **own** seat has **left** — declined or
> lapsed — is drawn no card block, in **either** live standing.

**The card is what a reader answers against.** It exists to price a person you are about to say
`I'm in` or `Not this time` about, so a reader who has already answered has nothing for it to do —
and drawing them a live, as-of-now valuation of those people serves no purpose this screen can
name. That is the rule; the pair supplies the second reason and is the stronger one, because the
pair **releases the moment a seat leaves**, so those people are strangers to this reader once
more and a live card of a stranger is ADR-0141's *"a directory with extra steps."*

**An accepted reader keeps their card**, and that is the one case the two reasons disagree about.
They have no answer left either — but they are still on the court and the pair still holds them,
which is the distinction this rule turns on, and it is what `LINE_UP_INCOMPLETE` has always done.
Settled on the pair rather than on the decision: *has this reader left*, never *has this reader
answered*.

**Recorded as an amendment on ADR-0143**, because §2 of that record is *the challenge is the gate,
and nothing is re-evaluated against the reader* — a permission decided once by the seat you hold.
This is not a permission gate; it is what the card block is **for**. The amendment says so, and
names the server half.

**The wire still sends these cards, and stopping that is
[#392](https://github.com/Raketa02/Raketa/issues/392)'s server half —
[#394](https://github.com/Raketa02/Raketa/issues/394).** ADR-0143 §8 states the per-seat rule and
the server's own `ReadChallenge._court` says how it is enforced — *"by not putting them in the
question — so there is no card computed, no photograph signed and nothing to leak"* — and a reader
who has left is owed the same: a client that declines to draw a signed
photograph URL has still been handed it. Both halves, and neither is redundant.

**One gap is stated rather than closed.** This reads the answer **the wire sent**, so a seat past
its window whose lapse has not been swept is not *left* yet and keeps the answering arm — card
block and both buttons. §2.4 already rules that acceptable, on *draw the clock, never obey it*; the
alternative is this side deriving a lapse from `answer_by` against `read_at`, which the client's
own `features/challenges/domain/challenge.ts` refuses in writing — *"the clock is not read here, and
that is deliberate"*. The sweep closes it.

What it draws, from `challenges`' own narrower schema:

| Block | Fields |
| --- | --- |
| **The person** | the whole handle, `photo_id` + `photo_url` (present exactly together, else the poster), `area_code`, `level`, `band`, `range`, and `player_score` |
| **The pairing** | the Fit, `distance_km`, the ranked scored terms with their evidence, `degraded_terms`, the concerns, the forecast, `at_stake` |

**Four things the design draws that this screen does not.** Each is a decision with a record
behind it, and each is written here so the mock is not built as drawn in six months:

1. **No bio.** `PlayerCardSchema` refuses free text *"ever"*, and ADR-0143 §6 holds the refusal is
   **stronger** here than where it was written: a searcher chose to look, an invitee was put in
   front of somebody without asking.
2. **`Score 91` is a segment, not a row.** A real published figure
   ([ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)),
   omitted where the platform has watched nothing — which is most people today. The segment
   **disappears rather than reading `Score 0`**.
3. **No *Why?* affordance.** The design prints a number and four reasons with nothing to open. The
   whole breakdown ships inline with the read, so a sheet is buildable and is not built here; what
   the screen prints is the top reasons and at most one concern, on the card's own caps.
4. **No countdown.** #327 refused one outright: the client has never carried the deadline, and a
   countdown would be the phone's clock deciding what the platform's clock owns. The deadline is
   **stated**, never obeyed — §2.4.

**Three answers when the pairing cannot be computed, and two of them draw the same thing**
(ADR-0143 §7): present; absent because there is **nothing to compute** — you hold no rating, no
declared intent or no committed profile in the sport you were challenged in; absent because it
**could not be read**. The arrangement always answers, because answering is not gated, and an
unrelated matchmaking outage must never become *you cannot answer your challenge*. **The codes are
the contract and the client writes both sentences.**

> **An invitee holding no rating in the sport they were challenged in has no pairing at all, and
> that is how the feature works rather than a corner of it.** The screen draws the arrangement and
> the handle, and does not apologise for it.

### 2.3 `AWAITING_ANSWERS`, invitee — the two answers

**One decision with two answers**, the design's own two buttons, and neither of them names a state
the act cannot produce.

- **`I'm in`** replaces the design's *Accept — game on*. #324 and #329 redefined *Game on* as *the
  plan is complete and the day is ahead*; accepting arranges nothing and draws ***Planning***, so
  the phrase is false the moment it is tapped. `I'm in` is what the standing says back —
  *You're in — everybody's in*, *You're in. {m} seats open…* — so the label and the confirmation
  are one sentence in two persons.
- **`Not this time`** is kept exactly as drawn. #221's own words.

**The organiser's side has no act, and that is ADR-0142's answer rather than an omission.** A
withdraw in Phase 1 buys hours of early pair release at the price of an unpoliceable
withdraw-and-resend, because `NobodyIsAskedTwice` is scoped to one aggregate and cannot see one.

### 2.4 What the two answers do

**Every act in `challenges` fails when offline and none is sent for you later** — #327's
feature-wide rule, one line at one site:

> **Nothing in `challenges` is sent for you later.** Accept, decline, withdraw and the seat fill
> all carry `networkMode: 'always'`, on the restated test: **is this act's meaning fixed by the
> moment it is tapped?**

**Offline draws the shipped pattern exactly** (`BuilderScreen`'s): **the pair greys out, and one
amber note sits above them** — not one per button, which would say the same thing twice about one
connection. The sentence is the shared `does-not-resume` value, unchanged, and **there is no third
value**: the two split on resumption, and a third keyed to the act would break the only distinction
the function has.

**Pending, never optimistic**, and **the reply is the redraw**. Both answer routes return the
challenge as it now stands, which *is* the server's derived standing, so writing it in is not
guessing. **The neighbours are fetched**: the accept that fills the last seat opens a game and a
conversation in the same transaction, and those live in caches the response says nothing about.

**A stale tap is a re-read, not a toast** — four arms on `sendRefusal`'s own shape, and **no new
copy**, because both sides of a closed window are already written and tested:

| Refusal | What the screen does |
| --- | --- |
| `answer_window_has_passed` | **Re-read and redraw.** The player lands on *Your day ran out*. |
| `seat_already_answered` | **Re-read and redraw.** Answered elsewhere — the two-devices case, and the first `409` here a well-behaved client can reach. |
| `challenge_not_found` | **Leave the screen.** It is gone, or it was never yours, and one code says both on purpose. |
| anything else | Say what it says, and read nothing. |

**The offer may expire under the finger, and it is let to.** The list sits at `staleTime: 0` with
the app's own `refetchOnWindowFocus`, so a refetch can redraw **Accept** away while the player is
looking at it. Play pins its ranked lists and the reason does not transfer: a pinned pool *is* the
record, where a challenge's standing is derived against a clock and genuinely goes false while you
look at it. A mis-tap prevented beats a mis-tap refused.

> **An affordance is never removed without the space saying what happened to it** — whether a
> refetch or a refusal took it. The buttons are **replaced by the sentence, never by nothing**.

This is #327 §7's rule in both directions, and it is the one obligation that ticket handed this
file by name. It binds every control on every screen in this document, not only these two.

### 2.5 `LINE_UP_INCOMPLETE`, and the reader who has left

**Three controls, in the order grow · talk · end** (ADR-0150), and only the organiser sees three —
on a court that was never a game. On a court that has been one, the third falls back
([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md) §1).

| Control | Who | What it does |
| --- | --- | --- |
| **⚡ Fill the seats** | any live member | runs the fill and **pushes a builder holding a full court and a fresh search** |
| **Open the chat** | any live member | `/chats/conversation/[conversationId]` |
| **Withdraw** | the organiser only | opens the sheet — §2.6 |
| **Call it off** | on a court that has been a game: the organiser, or once the organiser has left, any remaining player | the same route and the same sheet, reworded — `the-words.md` §22.9; the game is called off in the act |

**⚡ is the entry point, and items 1 and 2 of that ticket had one answer.** Pressing it is *Find a
game*'s own shape — press, the search runs, the builder arrives with a court on it — which
dissolves the *which search* crux, needs neither a stale `search_id` nor a reconstructed line-up,
and makes *Pick players myself* work on the first screen instead of after a mandatory ⚡. Nothing
outbound happens; the send is still a separate press, and it **pops back here**. The pool that
press opens draws the fill's **own** record, which since
[#407](https://github.com/Raketa02/Raketa/issues/407) carries the pool the four were drawn from
rather than the seated alone — this journey mints no shortlist, and that record is the only list
it has.

**An accepted seat is not a control.** No clear badge, no press, no pool — swapping is the only
thing that works on it, which **draws** *an acceptance is to the game, not to the side* rather than
writing it. *Start over* is **absent** on a court somebody has accepted: not disabled, not
redefined to mean *empty to these four*, which would be a second meaning for one label. AC-92's
named refusal is **never written**, because the state it refuses is unreachable — #324's *no copy,
no pill, no disabled control* is the rule it loses to.

#### The finding this screen had to close

**§13's `LINE_UP_INCOMPLETE` sentences assume the invitee is in, and one reader is not.**

Padel four: the organiser invites three, one declines, two accept. No seat is awaiting, so
`standing_of` yields `LINE_UP_INCOMPLETE` — and the player who declined still holds a seat, so
`GET /challenges` still returns it and their row is still drawn. Keyed on `(standing, side)` alone
they read ***You're in. {m} seats open, and the chat is already open***, which is false in both
clauses: they are not in, and the chat is not theirs.

**This is reachable the day the challenge screen ships**, and it is a consequence of ADR-0150's own
amendment rather than a rewrite of solved work — #331 ruled *rewriting* the five codes and ten
sentences out of scope, and #337 had already amended two of §13's rows.

> **The invitee sentence reads the reader's own seat, not only their side.** §13's
> `LINE_UP_INCOMPLETE` row gains two sentences for the reader who has left — [`the-words.md`](../matchmaking/the-words.md) §13.

**Why they are drawn no card block is §2.2's**, not this section's: the rule is the reader's and
spans both live standings, so it is argued once where the card block is defined.

**The row stays for the reader whose day ran out, and leaves at once for the reader who said no**
(amended 2026-09-11). `GET /challenges` is *every challenge you hold a seat in* and a departed seat
is still a seat, which is the reason [`the-words.md`](../matchmaking/the-words.md) §13.1 gives for
keeping the row — a row that vanished would take the only available explanation with it. That
argument is about an explanation, and it is what §1.1's shelf life is for: a row is kept to tell
the reader something they did not do. A **decline is the reader's own act**, so *You said no* tells
them nothing, and their row goes with the tap — on a singles court their no ended and on a doubles
court that carries on without them alike (`belongsOnTheInbox`); the organiser's row for the same no
keeps its day, because to them it *is* news. A **lapse** nobody chose, and *Your day ran out. They
are still filling the court.* is kept to be read exactly as before. The screen still resolves for a
declined challenge by its route (#390), and the record is untouched.

**And emphatically not because the pair rule still binds them** ([#393](https://github.com/Raketa02/Raketa/issues/393)).
It does not: the pair **releases the moment a seat leaves**. `open_pairs_among` folds
`players_in_it_at`, which keeps only seats that are `is_live_at`, so a departed invitee can be
challenged again immediately, in any sport, by anybody. What keeps them out of **this** challenge is
`already_asked_at` feeding `NobodyIsAskedTwice` — per aggregate, and not the pair rule at all.

### 2.6 The withdraw

**Whole-challenge, irreversible, organiser only, and in `LINE_UP_INCOMPLETE` and nowhere else.**
It destroys the conversation (ADR-0142), so it is the second irreversible act in this app that
reaches other people — and it takes the shape the first one already has. *Organiser only* holds
on a court that was never a game; on a court that has been one, the act calls the game off and
falls back to any remaining player once the organiser has left
([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md)).

**A sheet, on `SH.propose`'s exact shape**: a real modal (9.1) with `accessibilityViewIsModal`,
hidden siblings and Android back; a title naming the **moment** rather than the act, so the act is
named once by the control that carries it out; a dismissal **named by what it does**; and **focus
landing on the title rather than on the first action**, because that action is the destructive one
and landing focus there would make the worst outcome the cheapest to trigger (§20.6).

Its four sentences are [`the-words.md`](../matchmaking/the-words.md) §22.3.

**It fails when offline like every other act in this feature** (§2.4), and it is **pending, never
optimistic**: the route returns the challenge as it now stands, at `WITHDRAWN`, and the screen
redraws from the reply. The conversation is **gone**, not delisted, so the Chats list is
invalidated rather than patched.

---

## 3. The conversation

`/chats/conversation/[conversationId]`. **The place two people who have agreed to play talk about
it** — opened by the first acceptance, growing with each one, and destroyed once the episode *it*
names is over.

**The room is for the whole episode**: arrange the game, play it, find out what happened. That is
the sentence above read with *it* meaning the game rather than the arranging — and the reading is
**chosen rather than discovered**, the arrangement reading being coherent and simply left without
support ([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §1).
The room is destroyed at the **earliest** of:

- **`entry_closes_at`** — the instant *we played* stops being sayable;
- **`GamePlayed` plus `CONVERSATION_GRACE`**, which is **48 h**;
- **the challenge concluding without ever producing a game**, plus the same grace;
- **the withdrawal**, which destroys it in the same act and writes no line (§3.4).

**The end is derived and never stored**, from facts the room is already told — `Game.planned_at`
**is** `GamePlanned.occurred_at`, and §3.4 already has both reaching the room — so it costs no new
event, no new field and no new telling. **`CONVERSATION_GRACE` belongs to the Conversation context
and not to `games`** (ADR-0153 §4): `PLAN_HORIZON` stays in `games` because its interlock with
`ENTRY_GRACE` is the argument, and there is no such interlock here — this grace is about the gap
between app opens
([ADR-0151](../../adr/0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md)).

**The conversation is the one screen that stands the tab bar down, and it owns its own chrome**
([#400](https://github.com/Raketa02/Raketa/issues/400)). The composer replaces the bar for as long
as the player is in the room, so the keyboard and the stream get the whole screen rather than
sharing its foot with three stacked strips — the mock draws the bar simply absent, and it is
**not rendered** rather than hidden, because the bar is a flex sibling of the navigator and a
hidden one still takes its height and the bottom inset. The screen takes the top safe-area inset
the way every other screen does (`SafeAreaView`, `edges`, not inset arithmetic), and it takes the
**bottom** one too, on the same frame, because with the bar gone that inset has no owner — the one
exception to design-system 10.1's *the tab bar owns the bottom inset*, recorded there as a Part 16
amendment. The safe area sits **outside** the keyboard avoidance, so the composer lands on the
keyboard rather than a home indicator's height above it. The inbox the room is pushed over, the
challenge screen beside it and the game screen behind its own *Details* door all keep their bar;
§0.2's column stays lit throughout.

### 3.1 The header

**Back · the members' faces · their handles' stems · the sport and the game's state · Details.**

- **The faces are photographs or posters**, per §1.2. ADR-0148 made photographs affordable here
  where ADR-0143 refused them, because a conversation is destroyed rather than kept — *a difference
  between a record and a room, not a change of mind*.
- **The title is each handle's stem, comma-separated, and the spoken name is every handle whole**
  ([#401](https://github.com/Raketa02/Raketa/issues/401),
  [ADR-0157](../../adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)).
  `handleStem` is the handle up to its first word break — `Sergio.Sabater` drawn as `Sergio` — and
  it is not the first name ADR-0107 forbids: a prefix of the handle the person chose, cut at a
  character they typed, invents nothing, and §15 is what lets a box draw what a sentence may not.
  The list still gives way by **dropping whole names** at a
  separator and never by cutting one (§15); the stems are shorter inputs to that rule, so more
  names fit. §20.4 is the other half: the header's accessible name carries every handle whole,
  joined with a final *and*, then the sport, then the state — the row's own dialect (§24.2), one
  screen on. The budget the line is dropped against is counted at `h1`, which is what the title is
  set in.
- **The second line is the sport and the game's state, lower case — `Padel · planning` — and it is
  the same state as the card in Now.** This reverses what stood here, and the reversal is recorded
  in ADR-0157 rather than absorbed. What was refused was the prototype's subtitle — the sport plus
  the **card-state tag**, the twenty-state backend standing leaking into the chat, read by making
  the room ask `challenges` and `games` what it is (ADR-0148 §6). What lands is the **four-rung
  client-side ladder** and its endings, `gameCardName` folded from the two lists every room with a
  game already reads for its pinned plan card, in `features/plans`' own lower-case word. *Card
  name, never standing*; the row below keeps §6 in full. **A room with no game draws the sport
  alone** — `game_id` is nullable, a `LINE_UP_INCOMPLETE` room has no game and no plan, and no state
  is invented for it.
- **Details is drawn only when there is a game.** `GET /conversations` carries a **nullable
  `game_id`**, so a `LINE_UP_INCOMPLETE` conversation — which has no game and no plan — has no
  Details button and nothing to open. Drawing a dead control would be the disabled control #324
  refused.

### 3.2 The plan card is pinned, and it is the count, the chips and the lock

**The prototype's card is documented as pinned and is not** — it is emitted into the scrollable
content, and the chat opens scrolled to the bottom, so it is the first thing off-screen in any
conversation longer than a screen. That is #322's finding 1, and this file is where it is answered.

> **The plan card is pinned under the header. It is an eyebrow and a counter, the three slot
> chips, and *Lock the plan* — and nothing else.**

**Pinned**, because every chat opens at its newest entry (that is what a cursor is for), so a card
in the scroll is a card you have to hunt for — and the plan is the thing the room exists to fill.
**No panel**, because the panel that explains the slots is permanent chrome above a composer, and
ADR-0145 §6's panel already has a home: the game screen, where #336 §6 put it. This section said
*the chips alone* until [#403](https://github.com/Raketa02/Raketa/issues/403), which added the
two things a plan can now say about itself — how far along it is, and that somebody agreed it —
and left the panel exactly where it was.

```
┌────────────────────────────────────────┐
│ THE PLAN                    1 of 3 set │
│                                        │
│ [ Where ] [ Sunday ] [    Hour     ]   │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │          Lock the plan             │ │
│ └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**The eyebrow and the counter.** `THE PLAN` is an `eyebrow` — a region you are reading, never
`h2` — and `N of 3 set` sits opposite it in a muted pill, **mono and tabular** because it is a
number. The count is **derived on the client from the three fields and never sent**: the plan
schema's own docstring refuses a count on the wire as the one derived value that could disagree
with the three fields beside it. **Once locked, the counter reads `Locked`** — a word, because
the pill does not change colour and a colour would not be enough if it did.

**`Lock the plan`.** Greyed and not pressable while any slot is empty; coral and live once all
three are set, the one control on the card in 6.1's `primary`; **busy with its own word** while
the lock goes out; and **gone** once it has landed rather than 6.1's `settled` — a second lock
records nothing and answers `200`, so a control still offering the act would be one that provably
does nothing. **The label is `Lock the plan`, always**, with no reason appended: the note #324
owes every greyed control is the counter directly above it, which already reads `1 of 3 set`,
and a second sentence would be the same count in a second spelling. **The card's border is
`line` and never changes** — the mock's coral rectangle is a highlight the author drew, and
coral on a card already means pressed (design-system §5.1).

**Pending, never optimistic**, on the rule every slot chip follows: the lock writes a line other
people read, so the counter keeps saying `3 of 3 set` until the server has answered, and the
confirmation is the line itself — `{name} locked the plan`, through the stream like every
other entry. **And the card follows the line on every phone in the room**
([#405](https://github.com/Raketa02/Raketa/issues/405)): the nudge that brings *tomek.p set the
place* re-reads the plan beside the stream, so the chip, the counter and the lock say what the
line says with nothing pressed — one outbox tick after the tap, which is the line's own latency.
**And the card is born on the phone in the room** ([#406](https://github.com/Raketa02/Raketa/issues/406)):
the same nudge re-reads the game, so a court that completes while somebody is looking at the room
draws its card, its *Details* door and its state word there and then, rather than on the next
foregrounding. Each refusal is its own sentence by its **code**: `the_plan_is_not_complete`, which
the greyed button makes unreachable and the card handles anyway because the button is UX and the
server is the correctness mechanism; `plan_is_history`; `plan_not_found`; and `account_held`,
which is the room's one amber note over greyed controls and never a coral sentence on the card.

**One panel, one home; one plan, two primitives.** #338 §7: **`Chip`s here, where the plan is
edited; `Tag`s on the game screen, where it is read** — *a pressable pill is a chip*, *tags are
never pressable*. The vocabulary doing what it was split to do, and nothing new.

**A slot chip reads its value or its name**, in the order **where · day · hour** — ADR-0144's
order, the order people discuss them in and of decreasing negotiability.

| Slot | Empty | Filled | The input |
| --- | --- | --- | --- |
| **Where** | `Where` | the value | short free text, one line, capped at 120 — **no id, no lookup, no autocomplete, no reuse, no geocode** |
| **Day** | `Day` | the weekday | **seven chips, today + 6**, clamped to `planned_at + PLAN_HORIZON` and shrinking as the week runs out |
| **Hour** | `Hour` | the clock time | **30-minute steps, 06:00–23:00**, validated server-side |

**Any member may fill or change any slot, any number of times, and a lock does not stop that.**
There is no rate limit — **the line is the friction**, and every change writes a system line naming
who and what. **A slot is never emptied and a plan is never unmade.**

**There is a lock, and it is an act rather than a state**
([ADR-0155](../../adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
superseding ADR-0144's *there is no lock*). Once all three slots are set, any member may agree the
plan — `PUT /plans/{game_id}/lock` — and the whole of what that does is post `{name} locked the
plan` into the room, so the other three see the arrangement was agreed rather than merely
completed. **The count and the lock are two facts**: three filled slots is a plan everybody *could*
agree, and this says somebody did. The backend sends `locked_at` and no adjective.

**It freezes nothing, and there is no unlock.** Any member may still move any slot afterwards; the
plan stays locked and the move writes its own line. **`locked by everybody` stays deleted** — a
phrase the prototype's own data cannot support, since assent is recorded per act and not per
person, and a lock is one person saying *we are agreed* rather than four. §5.3's *a four cannot be
locked by two* is still unreachable, because there is no plan before the line-up completes.

**A combination already in the past is refused when the second of the two slots is filled**, in
written copy rather than by a disabled control, because the day and the hour are filled in either
order. [`the-words.md`](../matchmaking/the-words.md) §22.2.

**The clamp is why the day row can be empty.** Inside the 24-hour entry grace no day may be set,
and the only act left is *We played*. A row of no chips is the honest drawing of that, with the
refusal sentence beneath it.

**A plan's day and hour are wall-clock facts, drawn literally and never counted down** (ADR-0145
§7). Nothing expires at 18:00 — a card changing is a card changing, not a door closing.

### 3.3 The stream

**Two shapes in one ordered stream**, discriminated on the wire and **two components at the
surface** — a bubble and a system line, never one component with a branch. ADR-0146 refused the
shape on the wire and #338 §7 refuses it here for the same reason: one component with a branch
re-introduces at the surface exactly what the wire was shaped to prevent.

- **A message** is `seq`, `author_id`, `sent_at`, `text`, `client_message_id`. It has **no id of
  its own** — `(conversation_id, seq)` already identifies it.
- **A system line** is `seq`, `code`, `occurred_at`, nullable `actor_id`, `values` — and **`values`
  never repeats what the read already resolves**. The line carries `actor_id` and the client fills
  `{name}` from the response's `people` — the faces resolved for everybody it names, of which the
  members are a subset ([#408](https://github.com/Raketa02/Raketa/issues/408), ADR-0148 §4 as
  amended: the actor of a *seat left* line was never a member).

**The author's handle is drawn on a bubble only in a conversation with more than two members**, and
it is the **whole handle**. In a pair there is nothing to disambiguate; ADR-0107 forbids the
prototype's universal first name, which appears in fourteen of its twenty-two templates.

**No per-message timestamp, and a day separator between entries on different local days.** A room
lives at most a few days, so a clock beside every bubble is noise; the one time-shaped fact worth
drawing is *was this today*. **The separator uses the platform zone** — the same one the plan
converts through — so one conversation reads the same on every phone in it. A device zone would
put two people in one room on two different days.

**The stream opens at its newest entry and pages backward by cursor.** No offset, and **no
`has_more` anywhere**: ADR-0147's gapless sequence makes **`seq` 1 the beginning of the
conversation**, and a flag beside that is the same fact twice.

**No reader may infer loss from a gap.** The gaplessness is the server's promise and nothing is
permitted to depend on it.

### 3.4 The system lines

**Told by three contexts that do not know this one exists**, through the outbox (ADR-0146 §5). The
codes and their sentences are [`the-words.md`](../matchmaking/the-words.md) §23; what belongs here
is **which events reach the stream and which are refused**, because a builder reading only the
event list would write a line for each.

| Publisher | Event | Line |
| --- | --- | --- |
| `challenges` | `SeatAccepted` | ✅ — **only when the conversation already existed** |
| `challenges` | `SeatsInvited` | ✅ |
| `challenges` | `SeatDeclined` · `SeatLapsed` | ✅ — **one code, the answer as a value** |
| `challenges` | `ChallengeSent` | ✗ — no conversation exists yet |
| `challenges` | `ChallengeOpenedFromMutualInterest` | ✗ — it **is** the opening |
| `challenges` | `challenges.withdrawn` | ✗ — it **destroys** the room |
| `games` | `GamePlayed` | ✅ |
| `games` | `GamePlanned` | ✗ — the seats already imply it |
| `games` | `ResultProposed` · `Corrected` · `Countered` · `Accepted` | ✗ — `games` has its own conversation |
| `plans` | a place, a day, an hour recorded | ✅ — three codes |

**One rule covers three of the refusals: no system line announces a conclusion the record already
implies.** `challenges` and `games` both state it, ADR-0146 §6 applies it to this stream, and
ADR-0142 §3 gives the test that keeps it one — *an event may announce a conclusion only when no
arrangement of the seats could reach it*.

- **The room opening is not a line.** The conversation existing is the news, and `seq` 1 is
  whatever happens next. The first acceptor is a founding member, visible in membership; every
  later acceptance is a line. **One rule, three codes** — an acceptance, an invitation and a
  departure each write a line only when there was already a room to write it in.
- **There is no *Game on* line**, and the prototype writes that phrase four different ways.
  `GamePlanned` is refused on exactly ADR-0142 §3's test: everybody having accepted is an
  arrangement of the seats, so the line-up completing is reachable from the record. What a player
  sees instead is the **plan card appearing** and membership stopping — drawn, not announced.
  **The event still arrives**: §3's end is derived from its `occurred_at`, so a refused line is not
  a refused telling.
- **The withdrawal writes nothing**, because there is nobody left to read it. The room is
  destroyed in the same act; the news is on the challenge screen, in §13's sixth row.

**And two refusals are about where the argument lives, not about what implies what.** The four
result events are `games`' and `games` has its own eight-arm conversation for them. **That is the
whole reason** — one fact in one place, and ADR-0146's rename argument holds at any lifetime. It
used to rest partly on the room dying a day after the agreed point, and that half went with the
lifetime ([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §6);
the refusal did not move, because it never depended on the number.

**`GamePlayed` is the exception and earns it**: it is not the argument, it is the answer to the
question this room was opened to ask. It is also what closes #322's finding that four published
events get no sentence at all — ADR-0150 §9 closed `SeatLapsed`, and this closes the third.

### 3.5 The composer and the quick chips

**One block at the foot of the screen: the quick chips in a row above the field, and a coral
Send beside it** ([#402](https://github.com/Raketa02/Raketa/issues/402)). They were two strips the
screen emitted one after the other; the design draws them as one surface, on one ground, under one
hairline and one set of paddings, and `Composer` is the component that grew the row — everything
the block shares was already its. The chips post through the block's own send, so a chip send is an
ordinary send. The block sits on the screen's own `paper` under a 1pt `line` along its top — 2.1's
*`line` bounds a thing*, the tab bar's own edge, and not 5.3's `line2`, which is a fold inside one —
and takes no ground of its own, because the bottom safe-area inset is the frame's, under it (§3,
#400): a ground of its own would leave a band of paper above the home indicator, and taking the
inset itself would count it twice with the keyboard up. Send is 6.1 `primary` — `coralInk` under
white, Rule C — which is that variant's default, said explicitly. Every value is an existing step,
so there is no Part 16 row: nothing in the design system changed. The field's hint is `Message
about this game…` (§22.4) and its spoken name is still `Message` (§24.4). **A quick chip is never
`busy`**: it is the optimistic send, so there is no *on its way* for the word to name — the bubble
is the feedback — and 6.2's `busy` belongs to the plan card's slot chips, which write a line other
people read and wait for the answer.

**One line that grows to a cap, and Send.** `shared/ui` has **no text field at all** — the app's
only `TextInput` is `features/auth/components/AuthControls.tsx` — so the field arrives at a **new
Part 6 number with this composer**, and auth is refactored onto it in the same change or it is not
worth having (#338 §7).

**A message send pauses offline and resumes**, which is the app default and **not** `challenges`'
rule. That is why `client_message_id` is in the body rather than an `Idempotency-Key` header: the
value does **two jobs** — idempotency key and optimistic-send reconciliation key — so the client
renders immediately, replaces its own message when the real one arrives, and *a paused act is not a
failed one* cannot turn one message into two. A repeat answers `200` with the same message and the
same `seq`, recording nothing.

**Optimistic here, and pending everywhere else in this map.** The send returns the created message,
so **the sender's own message never waits for a nudge round trip** — the one place ADR-0147's
two-round-trip cost can honestly be avoided. It is safe because a message reaches other people and
cannot be *wrong*: there is no derived standing to guess at, which is what makes the accept
pending.

**The quick chips are 6.2 `Chip`s in the row above the field, inside the block, and a chip posts
words and nothing else.** ADR-0144's rule: *"Saturday works?"* is a question, and a chip that also filled the day slot
would record an agreement nobody had yet — the one thing the card must not do. The prototype's two
*actions wearing a message's clothes* were both ownership and money, and both died with Decision 3.

> **One chip per unfilled slot, in slot order, plus `On my way` when the agreed day is today.**

**The fallback is conditional, and that is a correction to #329.** That ticket collapsed the rule to
*one chip per unfilled slot plus the unconditional fallback, which never reaches the four-chip
cap* — three unfilled slots plus an unconditional fallback is **exactly** four, and *On my way* on a
Monday for a Saturday game is nonsense besides. Conditional, the maximum is three: all three slots
open and the day not today, or at most two open on the day plus the fallback.

**And the chips name nothing.** The prototype's three are hard-coded content — a weekday, a part of
day and one fixture venue — and §5.1's part of day is deleted. Each chip asks the question its slot
is about; the sentences are [`the-words.md`](../matchmaking/the-words.md) §22.4.

### 3.6 Not live, held, and somebody is typing — the three states the records made reachable

**All three were decided as rules and left undecided as screens.** ADR-0147 §8 made *not live*
reachable and honest; ADR-0148 §9 made *held* reachable inside a conversation; ADR-0156 built the
typing indicator and left the drawing here. The map's *Not yet specified* handed the first two
here, as two lines rather than a ticket, and the third joins them.

#### Not live

**A severed stream, a dead subscriber, a Redis outage and a phone with no signal all produce the
same thing**: a chat that is not live, whose ordinary read path still works and whose composer
still works.

> **One line above the composer, `amber`, present only in the foreground and only after a connect
> attempt has failed.**

- **Not a disabled composer.** Sends are ordinary authenticated `POST`s and the channel is
  unidirectional by construction — writing is unaffected. Disabling it would state something false
  about the half that still works.
- **Not an indicator.** The fact a player needs is in two parts — *what you send still goes, and
  what they send arrives when this reconnects* — and only a sentence carries two parts. Part 13's
  *never colour as the only signal* refuses the dot on its own in any case.
- **Not on a cold open.** Drawn only after a failure, or every open flashes it. `react-native-sse`
  behind the `LiveStreamPort` is what knows; the screen reads a state, not a socket.
- **`amber`**, on 1.3's reading — *watch this — reversible, not yet wrong* — the same token and the
  same argument as the row stripe.

**Reconnect runs every fifteen minutes in production** because the stream closes at the access
token's `exp`, so this line is a thing players will see routinely and briefly. That is the
dividend ADR-0147 named: the hardest-to-test path in the design cannot rot unnoticed.

#### Held

**A hold stops you writing anywhere another player sees it, and never stops you reading**
(ADR-0148). Inside a conversation that means: the stream reads, the plan reads, and **the composer,
the quick chips and the three slot chips all refuse**.

> **The composer and every chip grey out, and one amber note sits above the composer.**

That is `BuilderScreen`'s shipped pattern and #327's copy of it, applied a third time: **greyed
controls, one note, pre-emptive** — you never tap into silence and you are never told off for
having tapped. A greyed text field is acceptable **only** because the note is above it and arrives
first; absent the note it would be exactly the dead end #324 refused.

**One note for all of them**, not one per control: it is one fact about the account, and saying it
five times on one screen is the failure §1.6 names about counts. The sentence is
[`the-words.md`](../matchmaking/the-words.md) §22.5.

**A hold never removes the room.** It sits beside ADR-0143 §7's forward-looking block without
contradicting it — that one is about a pair, this one is about a person — and a hold that erased an
arrangement other people are already inside would be the blast radius pointed the wrong way.

#### Somebody is typing

**The only presence this product has** (ADR-0156), and it is narrow on purpose: inside a room, about
people who have already agreed to play, true for the five seconds somebody's finger is actually
moving. There is no online, no last-seen and no read receipt anywhere on this map, and none is
coming.

> **Three pulsing dots in the other side's bubble, at the newest end of the stream, present only
> while the `typing` frame's `player_ids` is non-empty — and named by a sentence.**

This section said *one `muted` line* until [#404](https://github.com/Raketa02/Raketa/issues/404)
drew it; the design is a bubble, and the design wins (#397). What the sentence became is the
element's spoken name.

- **It sits in the stream, not in the header.** It is a fact about *now* in a room being read from
  the bottom, and a header is where the facts that outlast the screen live. It takes the place a
  next bubble would — the newest end — and scrolls with the backlog. It is **always the other
  side's bubble**: `surface` bounded by `line` with the speaker's corner dropped, never the reader's
  `night`, because the reader is not who it is about.
- **The dots are the drawing and the sentence is the name, and they are one element.** Part 13's
  *never colour as the only signal* is met by shape and motion for the eye and by §22.5's sentence
  for the ear — [`the-words.md`](../matchmaking/the-words.md) §24.6 — and the region is polite.
  **The motion is the whole signal**: three still dots are indistinguishable from a message that
  says `...`, which is why this is the one thing that animates although design-system §1.5 says
  nothing has to (Part 16). Under reduced motion the dots are drawn still and the name stays.
- **A separate component, not a branch inside the bubble.** ADR-0146 refused one shape with a
  `kind` on the wire and §2.1 refuses it at the surface: a typing indicator has no author, no text,
  no `seq` and no place in the stream's ordering, and it is never an entry the list's data knows.
- **The names come from the members you are already holding**, exactly as every system line does.
  The frame carries `player_ids` and nothing else, so a corrected handle fixes the indicator for
  free.
- **Never you.** The server filters the reader out of their own room's frame, **and the client
  filters again** — a composer drawing an indicator for the person using it is the most visible
  possible bug, and a set difference is what the second guard costs (#404).
- **It goes away on its own, and that is the design.** No *stopped* is sent by anybody: the server
  reports whoever's heartbeat has not expired, so a killed app, a lost signal and a dropped request
  all clear the line within seconds. The frame carrying an empty list *is* the clear, and **it is
  sent when the answer changes and never on a tick** — so the client keeps **no clock**: a timer
  from the last frame would clear the indicator on exactly the person it exists for, somebody typing
  a long message, and nothing would ever re-draw it. **The client's own net is the channel**: a
  roster is only as live as the stream that carried it, so it is dropped the moment the channel is
  not live — severed, backgrounded, or offline — and never remembered across a reconnect, because
  the server re-announces anybody still typing on its first check. **What that net does not cover
  is stated**: a stream that dies without the port noticing — half-open, no error, no close, the OS
  still saying online — reads `live`, and a roster on it stands until the token's `exp` closes the
  stream, about fifteen minutes. It is the blind spot a nudge already has on that channel, bounded
  by the same deadline; a last-resort clock would close it at the price of clearing a real typist,
  and the guess is not taken.
- **Typing is not query cache state.** A typing frame invalidates nothing, advances no cursor and
  touches no page; it is held as the room's own state and drawn.
- **Polite is two mechanisms.** Android's `accessibilityLiveRegion="polite"` is genuinely polite
  there and nothing on iOS; the app's queued announcement is polite on iOS and interrupts on
  Android. The bubble uses each where it is polite, and it goes still under a running screen reader
  as well as under reduced motion, on the app's own `useCollapsedPresentation` rule.

**The client's own half is a heartbeat and nothing more.** Post `/typing` every ~3 s while the
composer has focus and the text is changing, and **stop posting when it stops** — there is no call
that says *stopped* and adding one is not available. The cadence must stay under the server's
five-second expiry or the other side's indicator flickers on somebody who never paused.

**A held player still sees it and cannot cause it.** The heartbeat is on the send's side of ADR-0148
§9 — an indicator is drawn on other people's screens, which is reach — so it is refused with the
same `account_held` the composer is, and the greyed composer above already says why.

### 3.7 A conversation that has ended

**Destroyed, not delisted.** The row leaves `CONVERSATIONS`; the screen behind it answers
`conversation_not_found`, which is **one code for two cases** on `challenge_not_found`'s argument
verbatim — separating them would answer *is this id real* about a stranger's evening.

**And one code for a third case, on the same argument.** Past its end a conversation answers
`conversation_not_found` **whether or not a sweep has run** — the sweep exists to make the
destruction real, not to make the answer right, which is the rule `challenges`' `lapse` and
`entry_closes_at` both already state
([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
§5). Never existed, destroyed, and past its end but not yet swept are one answer, and the client
cannot tell them apart because there is nothing it should do differently.

**A client holding a cursor into a destroyed conversation leaves the screen**, on
`challenge_not_found`'s own arm in §2.4's table. It does **not** retry, and the deletion is **not
inferable from a gap in the sequence**, because there is no sequence left to have a gap in.

---

## 4. Now

`/`. **Games only.** Challenges have one home and it is Chats — two inboxes is how a challenge gets
answered twice. Decided on `prototype/now-and-game-screen` by
[#336](https://github.com/Raketa02/Raketa/issues/336).

### 4.1 A rail, not a list

**`YOUR GAMES · n`, one card, swipe.** `GamesSection` refuses shelves in writing — *"a game
awaiting an entry, one awaiting an answer and one that never happened are one thing at three
moments of its life"* — and a rail keeps that refusal by not being a list at all.

**The card is the content width**, not 7.7's `0.74`. That moves a design-system number, so it
arrives as a Part 16 amendment scheduled by #338 §2: 7.7 gains a `1.0 × content` geometry and keeps
`marginTop: auto`, **and the dots become 7.18** — a new section, because a full-width card has no
peek, so the dots stop indicating and **become** the affordance, tracking the scroll. Not pressable,
on 7.9's own `hitSlop` arithmetic.

**The order is the server's — newest arrangement first.** On a rail you page through everything, so
*which is first* carries far less weight than in a scannable list, and newest-arrangement-first is
**stable** where a clock sort silently re-orders a player's cards between sessions. **The cost is
stated: a game arranged this morning for next Saturday sits ahead of one arranged last week that
is tonight.**

**Endings keep a card for 24 h and then leave** — #335's number and #335's argument one tab over.
It also keeps the day line honest: inside 24 h a weekday is only ever *Today* or *Yesterday*, so
the format never grows a fallback for a game ten days old. **Cost: after 24 h a finished game and
its score are unreachable in this build.** That is a history surface, it belongs to You, and it is
on the map's fog rather than built here.

### 4.2 The card

**Header · slots + court · footer, on a dark shell** — the design of
[#410](https://github.com/Raketa02/Raketa/issues/410), built by
[#413](https://github.com/Raketa02/Raketa/issues/413), and the Planning card is the first one drawn
for real. Where this disagrees with what stood here before, **the design won and the record is
amended**; the old anatomy — *tag · eyebrow · figure · line · gloss · court · footer* — is kept
below only as what each slot replaced.

```
┌──────────────────────────────────────────────────┐   night, radius 15
│ (● Planning)                              PADEL  │   tag on-dark, dot = the STAGE · sport word
│ ▌ WHERE                          ┌────────────┐  │   ▌ bright bar = settled
│ ▌ Zabłocie Sport                 │ (ON)  (ZB) │  │   │ dim bar    = not agreed
│ │ DAY                            │────────────│  │
│ │ Not agreed yet                 │ (TK)  (KW) │  │   (TK) has the volt ring — you
│ │ TIME                           └────────────┘  │
│ │ Not agreed yet                                 │
│ ┌──────────────────────────────┐  ┌────┐         │   the wide door · the bubble
│ │       Finish the plan        │  │ 💬 │         │
│ └──────────────────────────────┘  └────┘         │
└──────────────────────────────────────────────────┘
```

| | |
| --- | --- |
| **Tag** | #324's card name, on 6.4's `on-dark` pill. Affordable here because ADR-0148 §6's refusal was about a **cross-context read**, and a game card reads its own standing. **The dot is the stage's** — `arranging` while the game is in the players' hands (Planning, Needs result, Confirm the result), `mint` where it is settled (Game on, Today, Counted), the quiet hairline on the two endings nobody scored — and it is legal because the sport is the **word** beside it. *Replaces*: the sport dot and the pill's `warn` / `ok` variant |
| **Sport word** | `PADEL`, `PADEL · FRIENDLY`, top right, uppercase, muted on dark. `FRIENDLY` is the marked case (ADR-0150). **Nothing writes *singles* or *doubles*: the court says the format.** *Replaces*: the eyebrow — `SINGLES` / `DOUBLES` went with the court saying it, `YOU OWN IT` went with ownership |
| **Slots** | Three rows in the app's own order — **where · day · hour** (`slots.ts` is the one place that order lives) — each a 3pt bar, a label (`WHERE` / `DAY` / `TIME`) and a value. **A settled slot draws its value big and white with a bright bar; an unsettled one draws `Not agreed yet` small and grey with a dim bar.** The card fills with brightness as the plan does. WHERE is `placeWithoutTheCourt`, one line, tail-ellipsised, spoken whole; DAY is the weekday whole and **the date beside it** — `Sunday` `9 Aug` — which §5.4 #6 refused and the design reinstates; TIME is `plan.hour`, mono, and nothing else — no duration exists. *Replaces*: the figure, the line and the gloss (§4.3) |
| **Line** | One small line under the slots, kept so no card loses a fact it drew before: ***Needs result*'s window** — `{duration} left`, folded from `entry_closes_at` against `read_at`, obeying nothing — and **the endings' standing**, `gameStandingLine`'s own sentence. Nothing on the three plan-led rungs: the slots are their whole account |
| **Court** | 7.12 at `card` **88**, measured against the mock at 1×, beside the slots. **Each seat is the person's photograph** where the room has one and the generated poster otherwise; **three letters under every seat, yours included** — the `volt` ring is the only *this is you* mark, so the `you` caption went. No sport caption on the ground: the sport is the word in the header |
| **Footer** | **The wide door** — the next thing to do, and its wording changes with the stage: `Finish the plan` on Planning, `Open` on Game on, `We played` on Today and Needs result, `Confirm the result` on the argument, and **none on an ending** — in the card's accent, `volt` on Planning and mint on everything else, over 7.7's `marginTop: auto` with no hairline. **The bubble** beside it opens the room, only where there is one. *Replaces*: the named door over a hairline, and the ✉ |

**The card body is not pressable.** The two buttons are the only doors, which reverses §5.2's *the
card body goes wherever the button goes*: there is nothing left for a body door to agree or
disagree with. The body is **one accessibility element with no action** — the tag, the sport and
the three slots as sentences (§24.5) — and the two doors follow it as elements of their own, so
the wide door's verb is no longer part of the body's name.

**Every other card is drawn by the same shell, softly.** The real look of the other eight cards is
not in #410; until the author supplies it, every name draws the shell on soft defaults — mint bars
and a mint wide door, the stage dot as above — so the rail does not mix two visual languages and a
game flipping to *Game on* under your thumb does not jump layouts. When a name's design arrives it
is a row in the tables (`STAGE_DOT`, `ACCENT`, `doorLabel`) or per-name content inside one shell,
never a tenth card.

**The faces need no backend.** A game's seat carries a handle and nothing else about the person in
it (ADR-0141), but the conversation rows the rail already fetches for the bubble carry every
member's `photoUrl` — so the same join, keyed on the challenge, hands each card the faces for its
own room. It fails soft: no room is no bubble **and** posters in every seat.

**The seats' posters need no new token.** ADR-0134 makes a poster **a fact about an id**, so the
design's coloured tile with initials **is** the app's poster plus 7.12's three-character caption,
with `?` for a seat `users` can no longer answer for.

### 4.3 The gloss — retired, and what the bars say instead

**The four `AWAITING_ENTRY` rungs had one sentence each on the card** — *Still to agree: where*,
the next unfilled slot in slot order, with *Nothing left to agree* once there was none and *Needs
result* overriding with the time left — and #413 retired it: the three slot rows draw **all
three** slots, and an unfilled one draws `Not agreed yet` under a dim bar, so the sentence would
now be the column said again in prose.

| Rung | What the card says instead |
| --- | --- |
| **Planning** · **Game on** · **Today** | the three slots, bright where agreed and dim where not — nothing under them |
| **Needs result** | the slots, and `{duration} left` under them, folded from `entry_closes_at` against `read_at` |
| **Needs a player** | the slots, and nothing under them — the **empty seat on the court** is the whole of what this rung adds, and the spoken name says `An open seat` after the sport ([#418](https://github.com/Raketa02/Raketa/issues/418)) |
| everything that is not a rung | the slots, and `gameStandingLine`'s sentence under them |

**The fifth rung, and it is above the clock**
([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md), #411 rule 5,
built by [#418](https://github.com/Raketa02/Raketa/issues/418)). A seat somebody left is a fact
about the **court** and not about the plan, and the game cannot be played — or recorded — until
somebody is in it; so `rungOf` reads the court before the clock, and **Needs a player** outranks
*Needs result*, *Today* and *Game on* alike. Nothing on the wire names it: the standing stays
`AWAITING_ENTRY` and the seat is `player_id: null`, and the ladder is the one place the two are
read together. The server's own *Never played* still wins — a window that closed on a short court
closed all the same. The tag is `Needs a player`, the dot is `arranging` (the game is back in the
players' hands), the wide door is **`Fill the seat`** — the challenge screen's own fill, run from
the card and landing in the builder ([#419](https://github.com/Raketa02/Raketa/issues/419)), drawn
**only while the agreed moment is ahead** because nobody may be seated into a game whose moment is
gone; past it the card has the bubble alone — and the empty seat is drawn as the builder draws
one: a dashed outline, no plus, no caption, no ring.

**Called off** ([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), built by
[#419](https://github.com/Raketa02/Raketa/issues/419)) is the fourth ending on the same shell: the
tag `Called off` with the quiet hairline dot, the line `Called off` under the slots, no door, and
**shelved a day from `called_off_at`** — read before the window and the entry, because
`entry_closes_at` is `null` on it and `played_at` never is. Nobody is named: the room went with
the act.

**What survives is the override and the citation.** *Needs result* keeps its window because a
passed agreement makes the unfilled slots irrelevant and the entry window is the only live fact
left; it still **obeys nothing**, because `standing_of` gates entry on `entry_closes_at` and the
server derives the standing. The endings keep `features/games`' own sentence, the same one the
screen behind the card says. The checklist on the game screen (§5.3) is unchanged and is still the
one place the whole list is printed as prose.

***Today*'s alarm survives in a different shape.** #324's second amendment dropped *Today*'s
three-slot requirement, so a *Today* card may genuinely have no hour — and a dim `TIME` bar on the
morning of the game says so more loudly than four words did.

### 4.4 The empty state

**Now stops being a placeholder, so `PLACEHOLDER_COPY.now` dies — and an empty Now would then be a
blank screen**, which is worse than the citation it replaced. The line is present-tense, says what
the tab **is**, and points at the act.

**The test moves rather than being deleted.** Whatever the sentence becomes,
`shellCopy.test.ts`'s *never says nothing is happening* must still go red if it asserts emptiness. A
guardrail that silently stops matching is worse than none.

---

## 5. The game screen

`/games/[gameId]` under Now and `/chats/conversation/[conversationId]/details` under Chats — **one
component, two routes** (§0.2). **`ResultScreen` becomes `GameScreen`**, and `GAME_ROUTE`'s docblock
stops calling it *"the result conversation for one game"*; everything `features/games` already owns
keeps its name, because the result argument is still most of that screen.

**Grown, not replaced.** `ResultScreen` already **is** a state-keyed detail surface with ten arms,
two of them pre-result. It gains the three plan arms rather than a second screen linking into it,
because a hand-off in the middle of one standing's life gives a player two different screens for
the same game depending which day they tap it.

### 5.1 The arms

| Arm | What it shows | Primary act |
| --- | --- | --- |
| **Planning** | the card at the top, the court's pairing, the plan **editable** — chips, counter, lock, the panel inside | **Open the chat** |
| **Game on** | the same layout, the plan whole and the lock live | **Open the chat** |
| **Needs a player** | the same layout with the empty seat on the card and an *Open seat* row on the players card, no forecast (the pairing omits it), the plan still editable — and **no *We played*** while the seat is open ([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md), #418); **Fill the seat** where *We played* would be, **Call it off** for whoever holds the exit ([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), #419) | **Fill the seat** — while the agreed moment is ahead; **Open the chat** otherwise |
| **Today** | the plan, whole, in `Tag`s | **We played** |
| **Needs result** | the plan, and how long is left to say you played | **We played** |
| **Confirm the result** ×4 | built — #314, untouched | built |
| **Counted** | the agreed score, the outcome, the worth line | none |
| **Uncounted** | *an evening, not evidence* | none |
| **Never played** | *It never happened* | none |
| **Called off** | *It was called off* over the line *Called off*, and the ghost's own body — *Nobody is marked for that* — with no plan, no doors and no act on the court; drawn as *Never played* is ([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), #419) | none |

**The plan-lead layout, since [#414](https://github.com/Raketa02/Raketa/issues/414)** — the two
rungs whose card door says *Finish the plan* / *Open*, redrawn to #410's design:

```
‹  DOUBLES · COUNTED                         ← the eyebrow, and no title (10.3 as amended)
┌ the Now card, doors={false} ───────────────┐   the tag, the sport word, the slots, the court
└────────────────────────────────────────────┘
┌ BALANCE FORECAST ──────────────────────────┐   the court's pairing, §5.5 — absent entirely without a forecast
│ 2,70            gap −0,01            2,71  │
│ [ You + Zofia ▓▓▓▓▓░░░░░ Kuba + Ola ]      │
│ 90%  Very even · A counted game — …        │
│ [ If you win +0,08 ] [ If you lose −0,08 ] │   two tiles or none
└────────────────────────────────────────────┘
┌ PLAYERS ───────────────────────────────────┐   always drawn — your side first, you first
│ (TK) tomek.p (you)                         │   a row is a button: tap opens the record
│      2,71 · Established · likely … · 74% sure
│ …                                          │
│ Tap anyone for their record — …            │
└────────────────────────────────────────────┘
┌ THE PLAN ─────────────────────  1 of 3 set ┐   the chat's PlanCard, editable
│ [ Where ] [ Saturday ] [ Hour ]            │
│ ┌ ⓘ Agreed between you — nothing is booked ┐   PLAN_PANEL, inside the card, between the chips and the lock
│ └──────────────────────────────────────────┘
│ [ Lock the plan ]  (greyed below three)    │
└────────────────────────────────────────────┘
[              Open the chat                ]   ← Button dark, lg — in the scroll, nothing pinned
[                We played                  ]   ← Button secondary — withheld while a seat is open
[             Fill the seat                 ]   ← Button primary, lg — Needs a player only, while the moment is ahead (#419)
[              Call it off                  ]   ← Button secondary — Needs a player only, for whoever holds the exit (#419)
[            Leave this game                ]   ← Button secondary, last — while the agreed moment is ahead (#418)
(the star card, when a rating is waiting)
```

**The eyebrow is the format and the kind** — `DOUBLES · COUNTED`, `SINGLES · FRIENDLY` — read off
the seats and the `GameKind`, with **no title under it**: the card names the people and the plan
names the day, so `Padel · with … · arranged n ago` would be the same facts twice. `COUNTED`,
never `COMPETITIVE` (§5.4 #8 stands). The standing line and the checklist (§5.3) go on this lead —
the card's bars say what is agreed and the counter says how much. **The plan is edited here**
([ADR-0149 §4 as amended](../../adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)):
the chat's card reused as it is, with `PLAN_PANEL` drawn inside it through the one `note` slot the
room leaves empty. **Nothing is pinned while the grid is closed**; *We played* opens it over the
plan and the pinned footer comes back with the send and the way out.

**On the score lead the plan is drawn read-only, in `Tag`s, and edited in the chat** — so the
chat door there is a door to where the plan is changed; on the plan lead it is a door to where a
change is *seen*, since every write posts a line into the room. On both it is **always drawn,
whichever door you came in by**. Arriving from Now it is the whole point; arriving from
**Details** it is the way back. Drawing it conditionally would make the surface depend on its
door, which is the one thing Decision 7 bought by having only one. It fails soft on there being
no room (ADR-0149 §3), on both leads.

***We played* is available in every `AWAITING_ENTRY` arm**, not only the two that lead with it.
`standing_of` gates entry on `entry_closes_at` and on nothing else, so four people can arrange a
game at six and play it at eight without ever filling a slot. Strict one-action-per-state buys a
tidy table at the price of the app declining to hear the one fact the whole loop exists to collect.
**One exception, since [ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)**:
*We played* is **withheld while a seat is open** (#411 rule 5) — the server refuses a result on a
short court, and a game with a gap in it is not one anybody could have played. It is the domain's
answer (`actsOffered`) rather than the screen's, so the card's door and the screen's control cannot
disagree about it.

***Leave this game* is the last thing on the plan lead**
([#418](https://github.com/Raketa02/Raketa/issues/418), #411 rules 1 and 8): a `secondary` control
under *We played*, behind a sheet on the withdraw's shape (`the-words.md` §22.8), drawn **only while
the agreed moment is ahead** — the server refuses a departure past it with `game_moment_has_passed`,
and the client mirrors the rule off the same instant rather than offering a control the act would
refuse. The rung alone cannot say it, because *Needs a player* outranks *Needs result*. It is a
**challenge** act reached from a game — the seat that reopens is the challenge's — so the control
is `features/challenges`', composed by `features/plans` into a fourth slot on the screen
(`courtActs`), the shape the chat doors already take; *Fill the seat* and *Call it off* sit in the
same slot. Pending, never optimistic; on success the games, the plans and the rooms are
re-read and the screen goes back — the card is gone from the rail because the server no longer
lists it. A stale tap re-reads the games list and says nothing; `challenge_not_found` leaves;
`account_held` is said as every write in that feature says it. Not on the card, not in the chat.

**On *Needs a player* the slot holds two more, and they are the reopened court's whole account**
([#419](https://github.com/Raketa02/Raketa/issues/419), #411 rules 3 and 4,
[ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md)). ***Fill the seat*** is the
arm's primary act, drawn where *We played* would be: it runs the challenge screen's own fill —
`POST /lineups` naming the challenge and nothing else, the people **the game's seats** hold read as
accepted — and pushes the builder under the challenge, whose send pops back to this screen; the
newcomer's yes re-seats the same game, and the nudge re-reads it. Drawn only while the agreed
moment is ahead, with the leave, because nobody may be seated into a game whose moment is gone. It
is the same control as the card's wide door — `features/challenges`' `FillTheSeat`, composed by
`features/plans` into both — so the two cannot say two things about one press. ***Call it off*** is
the withdraw grown to a reopened court: `secondary`, above the leave, behind the withdraw's sheet
reworded (`the-words.md` §22.9), for **the organiser — or, once the organiser's own seat is open,
any remaining player** — a challenge fact, joined off the challenge list the tab bar already holds
(ADR-0149 §3's shape; nothing is added to `GET /games` for it), failing soft into no control. Only
while a seat is open, and **not** only while the moment is ahead: the withdraw is not guarded by
the moment, so on a short court past it this is the one act left. Pending, never optimistic; on
success the games, the plans, the rooms and the challenges are re-read and the screen **stays**,
re-folding into the *Called off* arm off the games list. A stale tap re-reads and says nothing;
`challenge_not_found` leaves; `account_held` is said.

### 5.2 Which door each card opens, in full

**#336 §4 fixed the rule and left the table here.** The rule is that **the button is a named door**
— it carries the act's verb, it navigates, and it never writes — and **the destination is the
state's**. *The card body goes wherever the button goes* was the rule's second half, on the
argument that a body always opening the details screen would be a second, quieter door disagreeing
with the first; **[#413](https://github.com/Raketa02/Raketa/issues/413) reversed it the other way
round — the body is not a door at all**, and the two buttons on the card are the only doors. The
consequence is stated rather than hidden: **an ending's card offers nothing and opens nothing**,
and the room behind it is destroyed (ADR-0153), so a finished game's screen is not reachable from
the rail — the card is the record for the day it stays.

| # | Card | From | Button | Lands on |
| --- | --- | --- | --- | --- |
| 1 | **Challenge sent** | Chats row | — | `/chats/challenge/[id]`, `AWAITING_ANSWERS` organiser |
| 2 | **Challenge for you** | Chats row | — | `/chats/challenge/[id]`, `AWAITING_ANSWERS` invitee |
| 4 | **Line-up incomplete** | Chats row | — | `/chats/challenge/[id]`, `LINE_UP_INCOMPLETE` |
| 17 | **Declined** | Chats row | — | `/chats/challenge/[id]`, `DECLINED` |
| 18 | **Expired** | Chats row | — | `/chats/challenge/[id]`, `LAPSED` |
| — | **Withdrawn** | Chats row | — | `/chats/challenge/[id]`, `WITHDRAWN` |
| 5 | **Planning** | Now card | `Finish the plan` | `/games/[gameId]`, the Planning arm — the same door as Game on's, under the word for the errand |
| 3 | **Game on** | Now card | `Open` | `/games/[gameId]`, the Game on arm |
| 11 | **Today** | Now card | `We played` | `/games/[gameId]`, the score grid |
| 12 | **Needs result** | Now card | `We played` | `/games/[gameId]`, the score grid |
| 13 | **Confirm the result** ×4 | Now card | `Confirm the result` | `/games/[gameId]`, the confirm arm, both controls inline |
| 14 | **Counted** | Now card | — | nowhere — no door, and the body is not one |
| 16 | **Uncounted** | Now card | — | nowhere |
| — | **Never played** | Now card | — | nowhere |
| — | **Called off** | Now card | — | nowhere — shelved a day from `called_off_at`, which `GameSchema` carries beside `played_at` for exactly this; `entry_closes_at` is `null` on it, so a card that read the window would stay eight days ([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md)) |
| — | every live card | Now card | the bubble | `/chats/conversation/[conversationId]` |
| — | the conversation | Details | — | `/chats/conversation/[id]/details`, the arm the standing derives |
| — | **Planning** · **Game on** | the game screen | `Open the chat` — `dark`, `lg`, full width | `/chats/conversation/[conversationId]` — the join, failing soft |
| — | **Planning** · **Game on** | the game screen | `We played` — `secondary`, beneath | the score grid, opened over the plan; the pinned footer returns with it |
| — | **Needs a player** | Now card | `Fill the seat` — while the agreed moment is ahead; none past it | the fill (`POST /lineups`, naming the challenge), then `/chats/challenge/[challengeId]/fill` — the builder, whose send pops back to the rail. **The one door that runs something before it navigates**, and it still reaches nobody ([#419](https://github.com/Raketa02/Raketa/issues/419), [ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)) |
| — | **Needs a player** | the game screen | `Open the chat` — and **no `We played`** while the seat is open | `/chats/conversation/[conversationId]` |
| — | **Needs a player** | the game screen | `Fill the seat` — `primary`, `lg`, where *We played* would be, while the agreed moment is ahead | the same fill and the same builder, popping back to the screen (#419) |
| — | **Needs a player** | the game screen | `Call it off` — `secondary`, above the leave, for whoever holds the exit | the sheet, then `POST /challenges/{id}/withdrawal`, then **stays** — the screen re-folds into *Called off* off the re-read ([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), #419) |
| — | **Planning** · **Game on** · **Needs a player** | the game screen | `Leave this game` — `secondary`, **last**, while the agreed moment is ahead | the sheet, then `POST /challenges/{id}/departure`, then back — **not a door: it writes**, like the plan's chips above it ([#418](https://github.com/Raketa02/Raketa/issues/418)) |

**Fourteen cards, one route each side of the seam, and no deep-link parameter.** *The grid is the
screen*: `GameScreen` is state-keyed, so the verb names what you arrive at and the standing
guarantees you arrive there. That is a finding rather than a shortcut — three of the four Now
destinations cost **one** route because the screen was already built this way.

**Two of the twenty are not in the table and both are deliberate.** *Played · friendly* is not a
state — it is `GameKind.FRIENDLY` riding any played state, and it is the worth line on the screen.
*Game on* as the source means *everybody accepted*; here it means the plan is complete and the day
is ahead, which is what the phrase is actually for. **`ON` draws no card at all**, because the
game's standing owns it the moment a game exists.

**The seven refused states get nothing at all** — no state, no copy, no pill, no disabled control.
*Needs an owner*, *Being booked*, *Booked*, *Settle up*, *Payment overdue*, *Cancelled* and
*Reported* do not exist, and the *Settle up* pill the Chats design draws on a conversation row is
deleted with them. This is `CHALLENGE_SENT`'s argument about notifications applied to seven states
instead of one: **the app does not name a thing it cannot do.**

### 5.3 The checklist

**Three lines, capped, in one order — what is true now, what is still to agree, what it moves.** The
game screen's, never the card's, and drawn **on the two score-lead arms only** since
[#414](https://github.com/Raketa02/Raketa/issues/414): on the plan lead the card at the top carries
the first two — its bars say what is agreed and the counter says how much — and the third is the
kind word in the eyebrow. It was drawn on all four `AWAITING_ENTRY` arms until then; the ended arms
and the four `AWAITING_ANSWER` arms are built and untouched.

| | Line | Where it comes from |
| --- | --- | --- |
| 1 | what is true now | [`the-words.md`](../matchmaking/the-words.md) §22.6 |
| 2 | what is still to agree | §22.6 — **the full list**, in slot order, which is what the card's gloss defers to |
| 3 | what it moves | **cited, not written** — `worthLine`'s built and tested sentence |

**The third line is the whole of what survives ADR-0143 §8's refusal**, and it is already shipped.
Every line the design drew was about an owner, a booking or a part of the day, and all three are
gone.

### 5.4 Eight corrections to the details design

Drawn to `details1.png` / `details2.png`, which is the **pre-ADR product**. Each correction is a
record read out, and they are listed here because the mock will outlive this map:

1. ***Part of day* is not a slot.** The three are **where · day · hour**, and ADR-0145 §2 deleted
   the part-of-day bands *"deleted, not repurposed"*.
2. ***Lock it in · set all three first* is deleted.** Filling the third slot **is** the lock.
   **Amended by #403 and #414**: there is a lock, and it is an act with its own control —
   `Lock the plan`, greyed below three under the counter that says why — and since #414 that
   control is on the game screen's plan lead too, **via the reused card, as the chat decided it and
   not as the prototype drew it**: no *set all three first*, no coral outline, the counter as the
   reason.
3. **The coral outline around the plan goes with it** — it was the locked state's border, and 5.1
   already spends a coral outline on the *pressed* state.
4. **The *No clock time yet — on purpose* panel inverts.** It stops explaining an absence and names
   one: a player seeing *Zabłocie Sport · Saturday · 18:00* inside an app may reasonably assume the
   app did something about it. It did not. [`the-words.md`](../matchmaking/the-words.md) §22.2.
   Since #414 it is drawn **inside the plan card**, between the chips and the lock.
5. **The three slots are `Tag`s on the score lead and `Chip`s on the plan lead** (#414, ADR-0149 §4
   as amended). The tags stay where the plan is read beside a score and *a control that cannot be
   operated must not offer the affordance of one*; the chips are the chat's own, on the two rungs
   whose door promised *Finish the plan*.
6. ***Sun 9* is a date**, and this app had none — the horizon is seven chips, so a weekday is
   exact. **Amended by #413: the Now card draws the date beside the weekday** (`Sunday` `9 Aug`),
   because the design wins — and since #414 that card heads the game screen's plan lead, so a date
   is drawn there too, on the card; the plan's chips and tags still draw the weekday alone.
7. ***60 min* is a duration nothing in this build holds** — no booking, no court, no slot length.
8. ***COMPETITIVE* is a search's mode.** A game carries a `GameKind`, and `FRIENDLY` is the marked
   case.

**And *press and hold anyone for the full record* is gone.** `CourtSeat.tsx` deleted that shortcut
on #285's argument — *"a hold is a gesture with no affordance, no announcement, and no equivalent in
the accessibility API at all, so it was never reachable by the people who most needed the route."*
**Still gone since [#415](https://github.com/Raketa02/Raketa/issues/415) put the record behind the
players card**: the gesture is a **tap**, on the whole row, which is a `button` with a name — so the
route #285 was arguing for is the one that exists, and the footer says *tap* because that is what is
there. The design's sentence said *press and hold*; honouring #285 is not reversing it, it is
drawing the affordance the hold never had.

### 5.5 What this screen refused, and the reversal that was taken

**ADR-0143 §8 refused this screen's two richest blocks by name**, and a game exists only after `ON`,
so that clause was read as being about exactly this screen:

> **`ON` draws neither. The game's standing owns it the moment a game exists, and that game's seats
> carry handles under ADR-0141; a card here would be a second, worse copy of the game screen.**

The **Balance forecast** and the `Tennis 3,10 · band 2,88–3,32 · 58%` rows are that card. This
file upheld the refusal, on an argument of its own — *a forecast exists to help you decide whether to
play somebody, and on this screen you have already decided* — and filed the reversal as
[#346](https://github.com/Raketa02/Raketa/issues/346), which closed *wontfix*.

**Reversed by [ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md)**, on the
argument #346 itself named as the one that would win: **a Planning game has not happened, which is
exactly why the challenge screen is allowed a forecast.** ADR-0143 §2's test is stated on the
*values* — they are admissible because they *mean exactly what a card means* — and *you have already
decided* governs the card's lifetime on the **arrangement**, not a different screen about a different
record. So `ON` still draws no card on the *challenge*, and the game it became draws a pairing of its
own: `GET /games/{game_id}/pairing` — the forecast, the split, what is at stake and each seat's
Level, computed for the reader, only for somebody on the court, and only while the game is
`AWAITING_ENTRY`. **Nothing goes on `GET /games`**: the seat there still carries a handle and nothing
else, and the pairing is read *beside* the game through a port `games` publishes and the matcher
signs. What §5.5 priced is paid rather than argued away — the port exists, and ADR-0143's apparatus
is reused rather than built a second time, which is why the challenge card and the game screen come
to one number for one court. The forecast block is
[#415](https://github.com/Raketa02/Raketa/issues/415)'s; `worthLine`'s sentence survives beside it.

**The client shape** ([#415](https://github.com/Raketa02/Raketa/issues/415)) — two blocks in the
plan lead's `court` slot, over one read:

- **The read is the game's.** `features/games` owns `GET /games/{game_id}/pairing` end to end —
  `api/pairingApi.ts`, `mappers/pairingMappers.ts` (the wire boundary), `domain/pairing.ts`,
  `hooks/usePairing.ts` under `gameKeys.pairing(gameId)` — and the slot is filled by that feature's
  own `CourtPairing`, composed by `GameScreenWithPlan` because the faces come off the room join it
  already holds. **The read is enabled on `AWAITING_ENTRY` and made on the plan lead alone**: the
  slot is drawn on the two plan-lead rungs and nowhere else, and the route refuses by name after
  the game has happened, so a result arm never asks. The three refusals — `game_not_found`,
  `pairing_is_history`, `account_held` — are folded to *no pairing* **by code**, an answer rather
  than an outage; anything else is the failure it is.
- **No arithmetic on the client.** The gap, the percentage, the deltas and the range are printed as
  served; the bar takes the signed gap as its `advantage` on 7.11's one fixed scale, exactly as the
  builder's forecast card feeds it. The words and the bar are Play's, cited across a declared
  `games → play` edge rather than copied (`eslint.config.mjs`, and `pnpm test:boundaries` asserts
  the edge stays open).
- **The forecast block's anatomy** (mock 7): `BALANCE FORECAST` · the two side strengths in `num.l`
  with `gap` and the signed gap between them · the balance bar at `md`, labelled with **stems** —
  `You + {partner}` / `{stem} + {stem}`, or `You` / `{stem}` in singles · the percentage in the
  tone's ink beside §B9's word · the sentence about what a score does · the two stake tiles, the
  win tile tinted mint (7.14 as amended). **Absent entirely when the pairing carries no forecast**
  — somebody unrated, a refusal, a read in flight or failed — with no sentence saying why; the tiles
  go with it. Two tiles or none.
- **The players card's anatomy** (mock 8): `PLAYERS` · one row per seat, **your side first — you,
  then your partner — then the other side** (`courtForReader`, the one re-ordering) · the face off
  the room join at the Chats row's 38, the poster failing soft · the **whole handle**, `(you)` after
  yours, `?` for a seat `users` cannot answer for · the level row `{level} · {band} · likely {low} –
  {high} · {n}% sure` in mono, or **nothing under an unrated seat** · **no chip on anybody** · the
  footer. Always drawn — it does not depend on the forecast.
- **Tap, not hold.** The whole row is a `button` named for the record it opens, and it opens
  `PlayerRecordSheet` for that player with the sport the reader arrived from and nothing else — no
  distance, no overlap, no pairing row, because no search stands behind this screen. The read
  behind the sheet admits somebody you share a game with, so nothing on the backend moved for it.

---

## 6. What the player app owes, across all five surfaces

Standing obligations, none of which expires on being satisfied once. They are the counterparts of
[`the-play-screens.md`](../matchmaking/the-play-screens.md) §11 for this map's surfaces.

1. **An affordance is never removed without the space saying what happened to it** — whether a
   refetch or a refusal took it (§2.4). The buttons are replaced by the sentence, never by nothing.
2. **Nothing in `challenges` is sent for you later**, and a message send pauses. Two `networkMode`
   values across two features, both deliberate, both argued at their site.
3. **Draw the clock, never obey it.** Deadlines are stated from the standing the server sent and
   folded against `read_at`; no countdown gates any control, on any screen.
4. **A plan is drawn literally and never counted down.** The complement of the rule above, and the
   reason `durations.ts` is narrowed rather than deleted.
5. **No client-side state machine and no status column**, on either side
   ([ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md)). Every card name in
   §5.2 is folded from a standing, the plan's slot count and the clock, at read time.
6. **No familiar form derived from a nickname**, anywhere — a bubble's author label, a row's handle
   list, a seat's caption. The whole handle or nobody (ADR-0107).
7. **The conversation reads nothing about a standing.** ADR-0146 forbids it, and ADR-0148 §6 makes
   it unnecessary: the last entry is what a pill would have said.
8. **`features/plans` may import `features/games`, and `features/games` never learns a plan
   exists** (ADR-0149). That is the client half of ADR-0145 §4, and it is a grep rather than a
   judgement.
9. **No system line announces a derived standing** (§3.4). There is no *Game on* line.
10. **Every state on every screen is reachable by `make seed`.** No `__DEV__` data path, no mock
    module, no fixture imported by a screen (ADR-0029).
11. **An open seat is drawn, never dropped**
    ([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)). A game's
    seat with `player_id: null` is a seat somebody left: it keeps its place and its side, the
    court keeps its size, and *Needs a player* is folded from it on the client — nothing on the
    wire names the rung. Every screen that draws a court draws the empty seat, and *We played* is
    withheld while one is open.

---

## 7. What this file does not decide

- **What each surface says** — [`the-words.md`](../matchmaking/the-words.md), which this ticket
  grows by six sections. Every sentence and every accessible name is there and nowhere else.
- **Where one component stops and the next begins** —
  [`the-loop-components.md`](the-loop-components.md).
- **What any of it looks like** —
  [`design-system.md`](../../../frontend_player/docs/design-system.md), and the six Part 16
  amendments plus one new section that #338 scheduled onto
  [#340](https://github.com/Raketa02/Raketa/issues/340). **Each chat-screen build ticket carries its
  own amendment**, which is #338 §1's stated price: the chat screen has never been drawn on a phone,
  so ownership is decided for everything and a number is written only for what a device drew.
- **The sport filter the Now design draws.** *All · Padel · Tennis · Squash · Badminton* over the
  rail. Real work nobody has scoped, and it collides with the reason #326 refused a sport-filtered
  badge — *the bar has no sport*, and `challengeKeys.list()` is *not keyed by sport: the pair rule
  crosses all four*. A games list **could** be, which is exactly why it needs deciding rather than
  assuming. On the map's fog.
- **A history surface, on You.** §4.1's 24-hour tail makes a finished game and its score
  unreachable after a day. Whether that is acceptable at launch is a question for the You tab and
  not for Now. On the map's fog.
- **Replies.** §5.2 of the source names them and nothing draws them. They no longer wait on the
  transport — ADR-0147 made every entry ride one sequence — so a reply is a question about a
  *message's shape*. On the map's fog.
- **The unread mark inside a conversation.** Out of scope, and it is **not** `read_at` — that field
  is the fold instant and means the opposite. ADR-0147's gapless sequence leaves it buildable as a
  **position** rather than a boolean.
- **Typing indicators and presence.** Out of scope: the only things here with no event and no
  record, needing a second non-durable channel with different rules.
- **A pairing forecast on this screen** — decided since, the other way: §5.5 and
  [ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md). The read is the
  backend's; the block is [#415](https://github.com/Raketa02/Raketa/issues/415)'s, and §5.5
  holds its client shape.
- **Push, and any out-of-app reach.** Out of scope. The loop closes without it, because every step
  after the first acceptance is between people who opted in by answering.
