# ADR-0153 — A conversation is for the episode, and its end was already on the wire

- **Status:** Accepted — **§3 superseded 2026-09-13 by [ADR-0164](0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md) §6**: a room without a game has
  ended exactly when its challenge is over, and not a grace after its last departure. §2's clock
  for a room with a game, and §4's grace after *we played*, stand.
- **Date:** 2026-09-07
- **Answers [#347](https://github.com/Raketa02/Raketa/issues/347)**, which
  [ADR-0149](0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md) §3 filed as a
  cost it could not pay: *"the chat door disappears before the loop closes, and this record does
  not fix it."*
- **Moves the lifetime [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  gave the conversation**, and leaves *destroyed, not delisted* exactly where it stands. What
  changes is the anchor and the number; the mechanism is untouched.
- **Does not move the entry window.**
  [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md) §5's refusal to
  re-date it off an agreed hour stands, and is put to a second job here.
- **Second application of [ADR-0151](0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md)'s
  rule** — *a window must exceed the gap between app opens, not equal it* — and the first outside
  a challenge.
- **Closes the case ADR-0145 named and declined**: a conversation with no plan, no game and no
  withdrawal.
- Rewrites [#359](https://github.com/Raketa02/Raketa/issues/359)'s acceptance criteria **before**
  it is built.

## Context

ADR-0142 gave the conversation an end: 24 h after *the moment it was arranging* — the plan's agreed
point, or the game settling, whichever comes first — and then **destroyed, not delisted**. The
entry window is `planned_at + PLAN_HORIZON + ENTRY_GRACE`, eight days, and ADR-0145 §5 deliberately
refused to re-date it. So a game sits at `AWAITING_ENTRY` with no conversation at all, at exactly
the moment two people most want to ask *did we play?*

**The two arguments holding that up are holding each other up.**
[`the-words.md`](../specs/matchmaking/the-words.md) §23.1 refuses `ResultProposed` · `Corrected` ·
`Countered` · `Accepted` a system line partly on the lifetime — *"a room dated to die one day after
that point would carry the first two turns of an eight-day argument and then vanish mid-sentence,
which is worse than carrying none"* — while #325 called 24 h safe *because* the score is argued on
`games`' own conversation. Each half is the other's support. Neither is independently load-bearing,
and the hole is what you get when a circular pair is mistaken for a decision.

**The hole is not eight days wide in the ordinary case, and that matters.** ADR-0144 clamps the
plan's day chips at `planned_at + PLAN_HORIZON` and entry closes one `ENTRY_GRACE` later, so
`agreed point + 24 h ≤ entry_closes_at` **always** — the interlock ADR-0145 named. The gap runs
from 24 h, for a plan on the last plannable day, to eight days, for a plan for this evening. It is
widest exactly when people arrange furthest ahead.

**And one arm of the rule was never buildable.** *The game settling* is a derived standing —
`SETTLED = {NEVER_PLAYED, CONFIRMED, UNSCORED}`, computed by `standing()` from `played_at`, the
proposals, the acceptance and `now`
([`standing.py`](../../backend/app/modules/games/domain/standing.py)). There is no `GameSettled`
event. [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §5 says a
conversation is **told**, through the outbox, by contexts that do not know it exists, and §6
refuses a line for a derived standing. A room cannot learn that a game settled without re-deriving
`games`' standing inside the chat context. The arm reads well in prose and has no mechanism.

## Decision

### 1. The room is for the episode, not for the arrangement

A conversation exists for the **whole episode** — arrange it, play it, find out what happened — and
not for the arranging alone. The screen spec already says so and was not being read that way:
[`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §3 calls it *"the place two people
who have agreed to play talk about **it**"*, and *it* is the game. `CONTEXT.md` calls a
Conversation *"one purpose-bound thread"* and never names the purpose.

This is the sentence the rest of the record hangs on, and it is chosen rather than discovered. The
arrangement reading is coherent; it simply has no support once the circular pair above is taken
apart, and it produces a product in which two people who arranged a game stop knowing each other
the day after, while the app goes on asking one of them for a score for another week.

### 2. The end is `entry_closes_at`, or a grace after `GamePlayed`, whichever comes first

A conversation is destroyed at the **earliest** of:

- `entry_closes_at(planned_at)` — the instant *we played* stops being sayable and the game becomes
  a ghost;
- `GamePlayed.occurred_at + CONVERSATION_GRACE`;
- the challenge reaching a conclusion that yields no game, plus the same grace (§3);
- a withdrawal, which still destroys the room **in the same act** and writes no line.

> **The fourth arm is amended 2026-09-12 by
> [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md).** A withdrawal now reaches a court
> that has been a game — a reopened court is called off through it — so the room it destroys may
> already hold its `game_id`. The arm does not read it: `_withdrawn` looks the room up by
> challenge and destroys whatever it finds, and nothing here moves the end later. `GameCalledOff`
> itself reaches the room not at all.

**Both anchors are facts the room is already told, and this is the windfall.**
`Game.planned_at` **is** `GamePlanned.occurred_at` — `game.py:406` sets it from that event and
nothing else — and `the-words.md` §23.1 already lists `GamePlanned` among the events the room
receives and draws no line for, *"the seats already imply it"*. `GamePlayed` is system-line code 4.
So the anchor costs **no new event, no new field and no new telling**; being told without drawing a
line is the shape `ChallengeOpenedFromMutualInterest` and `challenges.withdrawn` already have.

**Anchoring on `planned_at` rather than on the agreed point is deliberate, and reuses ADR-0145 §5's
argument.** A plan is editable by any member at any time. Dating the room's end from the agreed
point would let two people walk their own room forward by tapping a chip, which is the precise
shape §5 refused for the entry window — *"an entry window a player can extend by tapping"*. That
refusal now does a second job: it keeps the room's end fixed at birth, so the end never moves later
than it was, only earlier.

### 3. The room that never becomes a game gets the same number, and stops living for ever

> **Superseded 2026-09-13 by [ADR-0164](0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md) §6.** The number went, because the anchor read the *order* the
> answers came in — `B yes → D yes → C no` closed the room two days later while three people were
> talking in it, `B yes → C no → D yes` never did — and it only ever fired on rooms that still had
> accepted players in them. A room without a game now has ended exactly when its **challenge** is
> over, derived on every read from the challenge's own standing; what ends a challenge that never
> becomes a game is [ADR-0165](0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md) §3. The room still stops living for ever, and no longer by a clock.

ADR-0145 named the case and declined it: *"a conversation opened on a first acceptance whose
challenge then lapses or is declined to death has no plan, no game and no withdrawal."* #359 was
going to ship it as a comment in the module.

It is not a curiosity. It is a room with **no anchor at all**, and therefore one that is never
destroyed — already a breach of the rule ADR-0142 wrote to prevent a conversation becoming a record
with no end. It is closed here, on the same grace and from the challenge's own conclusion: the room
is told every departure (code 3, `SeatDeclined | SeatLapsed`), so the fact is in hand and only the
instant was missing. One number for both arms, because they are one question — *the thing this room
was opened for is over*.

### 4. The grace is a stated 48 hours, and it does not claim to outlive settling

`CONVERSATION_GRACE` is **48 h**, on ADR-0151's rule: the default here is destruction, what it
costs is the room, and 24 h *equals* the gap it has to outlast. That is the same boundary condition
0151 found in `ANSWER_WINDOW`, and this is its second application.

**It is stated, not derived, and the reason is worth recording because the obvious derivation does
not exist.** A correction **re-dates** the proposal — `standing.py`'s *"`at` is the proposal's own
or the correction's that re-dated it"* — and correcting is free until the other side responds
(`errors.py`). A side that keeps correcting into an unanswered window pushes `proposal_closes_at`
out indefinitely, so **settling has no upper bound** and no number can be shown to outlive it. This
record therefore **declines to claim** that the room survives `games`' conversation. It does not
need to: §6 leaves the score argument where it is, and the grace exists for the human question, not
for the argument.

Saying otherwise would be the failure ADR-0151 §3 named — *"an argument that points at a fact which
has changed is worse than no argument"* — committed in advance.

**The constant belongs to the Conversation context**, not to `games`. ADR-0148 kept `PLAN_HORIZON`
in `games` *"because its interlock with `ENTRY_GRACE` is the argument"*; there is no such interlock
here. This grace is about **app opens**, which is `ANSWER_WINDOW`'s argument and not a games
window's.

**Falsifier, named rather than implied:** messages sent after `GamePlayed`, against time since it.
If nothing is ever said in the second day, the second day is not being used and the number comes
back down.

### 5. The end is derived, the sweep is for the record, and the read is the truth

The instant is **derived**, never stored. It moves as the room is told things — a game played on
day 1 ends its room on day 3, six days before `entry_closes_at` — so a stored `ends_at` would have
to be rewritten on every telling. That is the second-copy problem ADR-0146 §7 refused for
membership, in a column whose first copy going wrong decides whether a room exists at all.

**Past its end, a conversation answers `conversation_not_found` whether or not the sweep has run.**
The sweep exists to make the destruction real, not to make the answer right. This is not a new
pattern: `challenges` states it — *"the sweep (`lapse`) exists for the record, not for
correctness"* — and so does `entry_closes_at`'s own docstring, *"the game reads as never played
whether or not anything swept it, which is what makes the answer to* did this happen *the same at
every instant."*

#359's *one code for two cases* survives untouched, and gains a third: never existed, destroyed,
and past its end but not yet swept all answer the same thing, for the same reason.

### 6. The result argument stays on `games`, and its stated reason is rewritten

§1 removes the lifetime half of `the-words.md` §23.1's refusal — under §2 the room is alive for as
long as anybody is likely to be arguing. **The refusal stands anyway, on scope alone**: one fact in
one place, and ADR-0146's rename argument holds at any lifetime — *"two things called conversation
in one codebase is how somebody eventually subscribes the wrong one."*

But the sentence carrying the dead half is **rewritten rather than left standing**, for §4's
reason. A reader who finds a refusal justified by a lifetime that no longer exists will conclude
the refusal has lapsed with it.

### 7. The three 24-hour numbers are a coincidence, and they do not travel

[#335](https://github.com/Raketa02/Raketa/issues/335)'s ended-challenge row and
[#336](https://github.com/Raketa02/Raketa/issues/336)'s ended Now card also leave after 24 h, and
**neither moves.** They are shelf lives on an inbox, where the record survives and only the row
departs — `the-loop-screens.md` §2 says it outright: *"nothing is lost and nothing lies, because
the list still holds them."* This one destroys an aggregate.

Three numbers that agree today, for three different reasons, are three numbers. This is written
down so that the next reader does not tidy the inconsistency away in either direction.

## Consequences

- **The fix is worth nothing to the people who arrange latest, and everything to the people who
  arrange earliest.** The interlock means a plan on the last plannable day already had
  `agreed point + 24 h = entry_closes_at`, so for that pair the room's life is unchanged. The gain
  scales with how far ahead people plan, which is the opposite of how the hole reads in #347 and is
  the honest description.
- **Two rooms about one game are now simultaneously alive**, briefly and by design: this
  conversation and `games`' result conversation. §6 keeps the score in one of them, but nothing
  stops two people typing *was that 6-4?* in the wrong one. That is the cost of leaving the
  argument where it is, and it is smaller than the cost of moving it.
- **A room outlives the arrangement, so `Member`'s wording stops being true while its rule stays
  true.** Membership after the line-up completes is the game's frozen line-up, and a game outlives
  the agreed point by the whole entry window — the derivation never loses its source. Only the
  clause *"whichever record is currently arranging"* becomes false, and it is reworded in
  `CONTEXT.md` in the same commit as this record. ADR-0146 §7's *one rule rather than two* is
  untouched.
- **ADR-0148's argument for `read_at` on the conversation envelopes goes stale and the field does
  not.** It earned the field by the destruction rule — *"its very membership is a fold… destroyed,
  not delisted, 24 h after the moment it was arranging"* — and membership is still a fold, against
  a different instant. Per ADR-0145's precedent, the record is not retro-edited; the sentence is
  named here as stale.
- **ADR-0149 §3's cost paragraph and `the-loop-screens.md`'s fog entry become historical.** The
  first is a record and stays as written; the second is a living spec and is deleted by the ticket
  that builds this.
- **Nothing on the wire moves and no client regenerates.** The lifetime is internal, the
  conversation list and detail shapes are unchanged, and `read_at` keeps its meaning. What changes
  is which rows the list returns.
- **A game nobody ever enters keeps its room for the full eight days**, including a pair whose
  arrangement quietly evaporated. That is the deliberate reading of §1: the room is for the episode,
  and *nobody ever said whether it happened* is part of the episode.
- **#359 is blocked on #347 and its criteria are rewritten before it is built.** Three of its
  acceptance criteria carried the old number, one carried an arm with no mechanism (§Context), and
  one recorded the unanchored case as folklore that §3 now closes.
- **`local` is the only environment that runs**, and the Conversation context is unbuilt, so there
  is no data to migrate and nothing to backfill. This record lands in the specification, not in a
  release.
