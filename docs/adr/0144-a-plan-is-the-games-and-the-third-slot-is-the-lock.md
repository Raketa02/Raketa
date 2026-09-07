# ADR-0144 — A plan is the game's, and the third slot is the lock

- **Status:** Accepted
- **Date:** 2026-09-07
- **Extends [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)**, which drew the
  line this record stands on: `games`' subject is *everybody accepted* to *there is nothing more
  to say about this evening*, and *"there is no booking, no calendar and no date field anywhere."*
  A plan is the calendar-shaped thing that sits **beside** that context without being let into it.
- **Cites [ADR-0100](0100-challenge-window-derived-never-chosen.md)**, which made a `Window`
  *derived, never chosen* and refused a window picker anywhere. This record names a day and an
  hour for the first time in this product, **after** everybody has accepted, and does not turn a
  window into a picker: the two live at opposite ends of the same evening.
- **Does not decide what the hour costs.** What replaces documentation §5.1's argument, what the
  design's *"No clock time yet — on purpose"* panel says instead, and whether the result-entry
  window is re-dated off an agreed hour are owed to
  [#330](https://github.com/Raketa02/Raketa/issues/330) and are deliberately absent here.
- Settles [#329](https://github.com/Raketa02/Raketa/issues/329) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

**Nothing in this platform holds a plan.** The root `CONTEXT.md` has no *plan*, no *owner* and no
*conversation*. `challenges` states *"no day, part of day, hour or place is ever attached"*;
`games` states *"there is no booking, no calendar and no date field anywhere, so the moment a
player says it is the moment it was."* Four people accept a challenge, a game opens, and the
platform holds no fact about when or where they will meet.

The source documentation's answer is a **plan card** in the chat with three slots — day, part of
day, roughly where — and a **Lock it in** button that activates when all three are set. The map
has already replaced the slots (a day, an **hour**, and a club) and put **ownership, the court,
the booking and the money out of scope**. So the card arrives here with its slots changed and the
thing its button unlocked deleted.

### Three facts already decided, which do most of the work

- **The card records an agreement; it does not negotiate one.** The players agree in words, in the
  chat, and *then* any of them writes the slot down. Nothing requires the person who fills a slot
  to be the person who proposed it.
- **[#324](https://github.com/Raketa02/Raketa/issues/324) keys three cards on the slot count and
  never on a lock.** *Game on*, *Planning*, *Today* and *Needs result* are one code —
  `AWAITING_ENTRY` — read against *how many of the plan's three slots are filled* and the clock.
  The counter appears under a **game** standing and under no challenge standing at all.
- **[#325](https://github.com/Raketa02/Raketa/issues/325) already spends the plan's agreed
  moment.** A conversation ends 24 h after *the moment it was arranging* — the plan's agreed day
  and hour, or the game settling, whichever comes first, or the withdrawal.

### And one that had been overlooked

**`slot_start` is already written and has no caller anywhere in `app/`.** It converts *(anchor,
day offset, minute of the local day, zone)* to an `Instant`; it resolves the autumn overlap at
`fold=0` *"always, on every call, so two people booking the same slot get the same slot"*; it
returns a typed `NonexistentLocalTime` for the spring-forward gap, with the round-trip idiom and
the comment explaining why the obvious check detects nothing. It was written for the booking grid
the 2026-08-25 reset deleted, and it survived. **A day slot and an hour slot are precisely its two
coordinates.**

## Decision

### A plan is the game's, it is its own context, and it is born by being used

**We will make a Plan the plan of one game, identified by that game's id.** One plan per game for
ever; a second id would be a second name for the same thing. It is **its own bounded context** —
`challenges`' subject ends at *everybody has answered* and `games`' begins at *played*, and both
say so in writing.

**A challenge that has not completed its line-up therefore has an open conversation and no plan.**
Two of four may not write down Saturday at 18:00 while two seats are unanswered, because the
people who would have to keep that promise have not agreed to be anywhere.

**Nothing is written at birth.** The plan is created by its first fill, and *no plan* is what the
game screen draws as *the plan empty*. This context has no opening event of its own, no subscriber
to `GamePlanned` and no outbox hop.

### There is no lock. Filling the third slot is the lock

**We will not ship §5.3's *Lock it in*.** With ownership and booking out of scope, the only thing
the lock did is gone, and what remains of the prototype's locked state is a border colour, a
removed button, and a pill reading `locked by everybody` that **its own data cannot support** —
no assent is recorded anywhere, and a slot is set by whoever tapped last.

Two consequences are stated rather than left to be found:

- **§5.3's guard — *a four cannot be locked by two* — is not implemented, because it cannot be
  reached.** There is no lock to guard and no plan before the line-up completes. The prototype
  needed the guard only because its `planReady` never looked at the line-up.
- **§5.3's second sentence is deleted, not rewritten.** *"Somebody has to book the court — whoever
  does becomes the owner"* has no moment left to be posted at.

### Three slots: where, then the day, then the hour

That is the reading order — the order people discuss it in, and the order of decreasing
negotiability.

- **Where** is short free text, one line, capped, and labelled *Where*. This context refuses, in
  writing: **no id, no lookup, no autocomplete, no reuse, no geocode, and nothing anywhere reads
  it.** It is a note between the people on the court and it is never a place the platform knows.
- **The day** is **seven chips, today + 6**, clamped to end at `planned_at + PLAN_HORIZON` so the
  row shrinks as the week runs out. It stores a **local date**, resolved at the tap. The
  challenge's overlap is drawn beside the chips as context and is never the input.
- **The hour** is **30-minute steps, 06:00–23:00**. It stores a minute of the local day.

**One platform zone — `Europe/Warsaw` — recorded as a locale assumption and not as a constant to
tune**, in the shape `availability.py`'s `_WEEKEND` already uses. **Its falsifier is the first
shard whose players are somewhere else.**

**The conversion goes through `slot_start` and nowhere else**, so the DST refusal is inherited
rather than rewritten.

### Who writes, what a slot does, and what stops it

**Any member of the line-up may fill or change any slot, any number of times**, and every change
writes a system line naming who and what. Last write wins; there is no history beyond the lines
and no rate limit — **the line is the friction.**

**A slot may be changed but never emptied.** Once the four have written down a day, the plan holds
a day: you can move it, you cannot un-write it. **A plan is never unmade** — nobody turns up, and
the game ghosts at `NEVER_PLAYED`.

**The game leaving `AWAITING_ENTRY` is the only thing that freezes the slots**, and it is not a
lock: once somebody has said *we played*, the plan is history. It is a fact this context reads
through **one port asking one question** — *is this player on this game's court, and is that game
still open to planning* — in the shape `challenges` asks all six of its own.

### Three events, and no event that announces a conclusion

**A place recorded, a day recorded, an hour recorded** — each carrying the value, the player and
the moment. **Setting a slot and moving one are the same event told with two sentences**, separated
by the fold rather than by a second class.

**There is no completion event and no cancellation.** The third recording *is* the completion, and
a line announcing it would be a conclusion the record already implies — `challenges`' rule and
`games`' identical one. *Calling the game off* is out of scope: `games` opens one game per
arrangement for ever, and a cancel would need it to grow the state ADR-0137 refused.

### The record is event-sourced and stores nothing it can derive

The system lines the conversation draws **are** this context's history; a three-column table would
need an audit log beside it to write them, and that log would be the second place the same fact is
true. **The slot count is derived. The agreed instant is derived, and exists only when the day and
the hour are both recorded.** And **the plan never writes to `games`**: `planned_at` keeps meaning
*when it became a game*.

## Consequences

**A day alone is not a moment, and #325's clock has to cope with that.** The conversation's anchor
is the *agreed instant*, so a plan holding a day and a place anchors nothing and the rule falls
through to its next arm — the game settling, which `NEVER_PLAYED` and `UNSCORED` both are. One
case is left with no anchor at all and belongs to whoever owns the conversation's record: a
conversation opened on a first acceptance whose challenge then lapses or is declined to death has
no plan, no game and no withdrawal.

**[#324](https://github.com/Raketa02/Raketa/issues/324)'s card table is amended by one row.**
*Game on* was *no slot filled* and *Today* is *three slots filled and the agreed day is today*,
which left three slots filled with the day still ahead drawing nothing — and with no lock that is
where a fully agreed plan sits for most of its life. So ***Game on* widens to *the plan is complete
and the day is ahead*, and *Planning* covers nought to two slots.** *Needs result*'s trigger
sharpens from *the agreed day has passed* to *the agreed moment has passed*. No fifteenth card.

**The plan can be moved under somebody who has already read it, and that is accepted.** Last write
wins with no history, so a player who saw *Saturday 18:00* and comes back to *Sunday 09:00* learns
it from the conversation's lines and nowhere else. The alternative — a proposal each person
accepts — is the negotiation the card exists not to be, and it would need an assent record the
source's own `locked by everybody` pretends to have and does not.

**The clamp costs a legitimate arrangement.** Two people who complete a line-up on Monday and
genuinely want to play a fortnight out cannot say so: the day row stops at
`planned_at + PLAN_HORIZON`. The alternative was worse — a plan naming a Saturday on which
*we played* is no longer sayable, and a card walking from *Game on* to *Never played* while the
plan still read *next Saturday*. Whether the horizon should instead re-date off an agreed hour is
[#330](https://github.com/Raketa02/Raketa/issues/330)'s.

**One zone is wrong the first time two players are in different ones**, and the assumption is
recorded so that the day it breaks it is found rather than debugged. Per-device zones were refused
because they would show two people on one court two different hours for one agreement, and there
is no club record to hold the true one.

**A free-text *where* will be spelled four ways for the same club**, and nothing will notice. That
is the price of refusing a venue record, and it is the refusal that keeps *the court* out of a
build that has no booking, no inventory and no owner.

**The client gains its first date and its first clock time**, against `durations.ts`'s written
claim that *"there is no date and no clock time in it, and that is the product rather than an
omission… a duration is the only time-shaped thing these screens are entitled to draw."* That
sentence now has an exception, and rewriting it is
[#330](https://github.com/Raketa02/Raketa/issues/330)'s, not this record's.

**A dead function comes alive.** `slot_start` acquires its first caller in `app/`, and its
docstring's *"Delete this and the booking grid offers an hour that has no minutes in it"* becomes
a live claim about a shipped surface rather than a note about a deleted product.

**Nothing is written into the root `CONTEXT.md` yet**, on
[ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)'s
precedent: Part 1 documents *implemented* bounded contexts, and this is a decision rather than a
behaviour. The context's name, its events' spelling and what it refuses in the glossary's own
voice are owed to [#332](https://github.com/Raketa02/Raketa/issues/332).
