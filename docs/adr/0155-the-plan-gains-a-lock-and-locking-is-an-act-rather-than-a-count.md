# ADR-0155 — The plan gains a lock, and locking is an act rather than a count

- **Status:** Accepted
- **Date:** 2026-09-10
- **Supersedes [ADR-0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)'s
  *There is no lock. Filling the third slot is the lock*** — that section and **nothing else in
  that record**. Its three slots, its birth-by-being-used, its *a slot may be changed but never
  emptied*, its freeze and its *the line is the friction* all stand exactly as written, and this
  record leans on every one of them. ADR-0144's **title** is left alone: renaming a file breaks
  links from thirteen other records, and a title that has been superseded in one clause is a
  smaller lie than a link that goes nowhere.
- **Applies [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  §3's test** — *an event may announce a conclusion only when no arrangement of the seats could
  reach it* — for the second time, and from the other side: `GamePlanned` fails it and
  `PlanLocked` passes it. §2 below is that argument.
- **Does not touch [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)
  §5.** *There is no un-agreeing to fear, only re-agreeing, and any member may do that at any
  time* is what makes a lock safe to ship rather than something the lock has to work around.
- **Does not move the game.** Locking does not put a game into *Needs an owner* or any other
  standing, and nothing in `games` reads a plan. Out of scope for
  [#397](https://github.com/Raketa02/Raketa/issues/397) entirely.
- Settles [#398](https://github.com/Raketa02/Raketa/issues/398).

## Context

ADR-0144 refused §5.3's *Lock it in*, and the argument was sound at the time:

> **We will not ship §5.3's *Lock it in*.** With ownership and booking out of scope, the only
> thing the lock did is gone, and what remains of the prototype's locked state is a border
> colour, a removed button, and a pill reading `locked by everybody` that **its own data cannot
> support**.

Every clause of that is a statement about a **destination**. The prototype's lock existed to
hand a court booking to an owner; with no ownership and no booking, the button pointed at
nothing, and a locked *state* was a border colour with no fact behind it. The record was right to
refuse a feature whose only remaining content was a decoration.

Three things have landed since, and together they give the lock somewhere to go.

**The room exists.** ADR-0146 built a conversation per challenge, and ADR-0148 put the plan
beside the game in it. Every slot write already posts a system line naming who and what.

**The lines are what this context has instead of history.** ADR-0148 §8 refused `set_by` and
`set_at` on a slot precisely because *those lines are this context's history*. So a fact about
who did what, and when, already has a place to live that is not a column.

**Nothing anywhere says the plan is agreed.** Three slots being filled is the most a reader can
learn today, and it is strictly less than what people mean when they stop discussing it. Four
people can be looking at a complete plan that two of them have not read and one of them intends
to move. There is no moment on the record that says *we are done arranging this*.

That last one is the gap. It is not a decoration and it is not derivable: **nobody wrote it
down.**

## Decision

### 1. We will ship a lock, and its destination is a system line

**We will add `PlanLocked` to the Plan context and a `PLAN_LOCKED` system line to the room.**
`PUT /api/v1/plans/{game_id}/lock` takes no body and answers the plan; the event carries the game,
the player and the moment; the room draws `{name} locked the plan`.

**The line is the whole of what the lock does**, and that is the answer to ADR-0144's objection.
The prototype's lock reached for ownership and booking, and both are still out of scope — this
one reaches for the room, which is where every other fact about arranging a game already goes.
Every member sees that the plan was agreed rather than merely completed, in the same backlog,
in the same shape, filled from the same membership.

**It carries no value.** The value is the three slots and they are already recorded; a copy on
this event would be the second place that fact is true, and the first thing to disagree with the
slot line above it after a later move. `values` is empty — the one plan line for which it is.

### 2. Announcing it passes the test `GamePlanned` fails

ADR-0142 §3 wrote the rule an event has to pass before it may announce a conclusion:

> *an event may announce a conclusion only when no arrangement of the seats could reach it.*

`GamePlanned` fails it, which is why `the-words.md` §23.1 refuses a *Game on* line: everybody
having accepted **is** an arrangement of the seats that reaches *the game is on*, so a line
saying so would be a second place for a folded standing to be true, and it would be the one that
got believed.

**`PlanLocked` passes it, and passes it cleanly.** Fold the whole plan — three values, the count,
the agreed point, the moment each was written — and *these people have agreed* is nowhere in it.
The stream says what was written down and by whom; it does not say that anybody stopped. There is
no arrangement of the three slots that reaches this fact, because **nobody wrote it down**. So
the event is not a second place for the fact to be true, it is the **only** place, and the fold
reads it exactly as it reads a recording.

This is the second use of that exemption and it is still self-policing: the test is about
reachability from the record, not about how useful a line would be.

### 3. The count and the lock are two facts

ADR-0144 folded them together — *filling the third slot is the lock* — and that sentence is what
this record takes back.

**A complete plan is one everybody *could* agree. A locked plan is one somebody did.** They are
not the same claim and the gap between them is where the arranging actually happens.

Structurally this is one rule and it is enforced in one place: `is_locked` is
`locked_at is not None` and is **explicitly not** `slot_count == SLOTS`. `SLOTS` says how far
along a plan is and is what the lock is guarded on; it is never what `is_locked` reads. A
property that read the count would put ADR-0144's folded-together version back in the one place
that would then be believed.

The two refusals that fall out are **deliberately different shapes**, and the asymmetry is the
decision:

- **Locking an incomplete plan raises** — `the_plan_is_not_complete`, a **409**, because nothing
  was sent and what is wrong is the state of the plan rather than a field in a body. A silent
  `200` here would leave a client believing it had agreed one.
- **Locking an already-locked plan records nothing and answers `200`** — this repository's
  idempotency language applied to an **act** rather than to a value, and the first lock's moment
  is the one that stands. It is not a refusal, because the caller asked for a state the plan is
  already in.

### 4. The lock freezes nothing

**After a lock, any member may still move any slot, and each move writes its own line as it does
today.** The plan stays locked; a slot write does not read `locked_at` and never will.

The reason is ADR-0145 §5, unamended: *there is no un-agreeing to fear, only re-agreeing, and any
member may do that at any time.* Nothing on this platform will ever hold a court, so nothing can
contradict a plan — which means a lock that froze a slot would be protecting an agreement against
the only people entitled to change it, and would do it by making them worse off than the pair who
never locked.

**The game leaving `AWAITING_ENTRY` is still the only thing that freezes a slot**, exactly as
ADR-0144 wrote it. The lock is not a second freeze and there is no third.

**Moving a slot after a lock does not clear the lock.** The friction is the line trail, as it
already is for every change: the room shows the lock, and then it shows the move, in order, with
names on both. A lock that cleared itself would make *the plan was agreed and then somebody
changed the time* unsayable, which is precisely the thing the other three people want to know.

### 5. There is no unlock

**There is no `PlanUnlocked`, no route and no way back to `null`**, for the same reason there is
no clearing event and no cancellation: **the lock is a thing that happened.** A record of an act
does not get taken back; §4 is what makes that cheap rather than restrictive, because re-agreeing
is free and un-agreeing was never what anybody needed.

An unlock would also be a line the room could not write honestly. *Never mind* is not a fact
about the plan — the three slots are unchanged — and it is not a fact about the game. It is a
fact about somebody's confidence, which this platform does not model anywhere.

## Consequences

**A plan gains one field on the wire and one route.** `PlanSchema.locked_at` is additive and
nullable, and `PUT /plans/{game_id}/lock` is new. Nothing is removed or renamed, so no shipped
client breaks; the client draws the locked state off `locked_at` and needs nothing else, since
there is no locked *behaviour* to describe.

**`locked_at` is the one non-slot value on `PlanSchema`, and ADR-0148 §8 survives it.** *A slot
carries its value and nothing else* is a rule about slots. The lock is not a slot: it is an act,
and its moment is the only thing a client can draw it by. **Who** locked it is still on the line
in the room, exactly like every other attribution in this context — the schema gains no
`locked_by`.

**The Plan is now the one context on `telling.py` where four out of four events draw a line**, and
the fourth is the first one there that is an act rather than a value. The eighth `SystemLineCode`
is the first with an empty `values` on the plan side.

**A stream can now hold a lock before its third slot, and the fold will read it.** `lock()` cannot
produce one, so such a stream would be a bug upstream — and the fold deliberately **re-runs no
refusal**: replaying it loudly would take the arrangement away from the four people who can see
it, which is a worse outcome than a plan that reads as locked a little early. The refusal lives at
the act, once.

**The lock is not on the Now card ladder and this record does not put it there.** What a card says
about a locked plan, and whether `locked_at` moves a game to *Needs an owner*, are #397's and the
client's; nothing here reads `locked_at` except the wire.

**A lock is reach, so a hold refuses one.** It writes a line other people read, which is ADR-0148
§9's own test, and it is refused **after** the gate like every other plan write — a stranger is
told there is no such plan rather than that their account is held.

**What this costs.** A second person can lock a plan the first person is about to move, and the
room will show both, in order, and neither is wrong. That is the same last-write-wins trade
ADR-0144 already took on the slots, and it is taken here for the same reason: the alternative is a
proposal each of four people accepts, which is the negotiation this card exists not to be.
