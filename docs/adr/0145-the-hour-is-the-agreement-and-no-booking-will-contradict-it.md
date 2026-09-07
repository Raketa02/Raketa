# ADR-0145 — The hour is the agreement, and no booking will ever contradict it

- **Status:** Accepted
- **Date:** 2026-09-07
- **Extends [ADR-0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)**, which
  decided the Plan's shape — three slots, *where · day · hour* — and said in as many words that
  it *"does not decide what the hour costs."* This record is that cost.
- **Cites [ADR-0100](0100-challenge-window-derived-never-chosen.md)**, whose refusal — a `Window`
  is *a label on the search*, **never a proposed time** — is why the headline ladder loses two
  rungs rather than one.
- **Scopes one sentence of [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md).**
  *"There is no booking, no calendar and no date field anywhere"* becomes a claim about
  **`games`' record** — which is what it was always about, and is still true of.
- **Cites [ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)**,
  which fixed a Player Score at what the platform watched. An agreed hour is not something the
  platform ever watches anybody keep.
- Settles [#330](https://github.com/Raketa02/Raketa/issues/330) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

### §5.1 is an argument, and the whole product leans on it

Documentation §5.1 is titled *Why there are no clock times before a court exists*, and it opens:
*"A player cannot know what court is free next Saturday, so any hour agreed before booking is a
guess that later has to be un-agreed."* Three rules follow from it — **a challenge asks one
question** and has no *when* at all; **the plan has three slots, none of them a clock**, being
day · part of day · roughly where, with the bands fixed at 08:00–12:00, 12:00–17:00 and
17:00–22:30; and **"the exact hour appears only when the owner writes in what they booked."**

The chat design argues §5.1 back in its own panel, which is the sharpest evidence that the
absence is deliberate rather than an omission: *"No clock time yet — on purpose. Nobody can
promise 18:30 before a court exists. Agree the day and the part of the day here; the exact hour
is written in by whoever books, once they have booked."*

ADR-0144 put an hour in the plan anyway. That was a product call, made deliberately, and this
record is not a re-litigation of it — it is what it costs, and what replaces the argument it
displaced.

### The argument has two halves, and only one of them was ever true

**The fact is true, and this build does not make it less true.** Nobody can promise 18:30 before
a court exists. Decision 3 on the map put ownership, the court, the booking and the money out of
scope, so nothing in this product will ever hold a booking, and nobody using it can promise a
court either.

**The conclusion carries a hidden premise, and §5.1's own next sentence names it.** *An hour
agreed now later has to be un-agreed* is only true if **something else will eventually say what
the hour is** — and §5.1 says what: *"the exact hour appears only when the owner writes in what
they booked."* Take the owner away and there is no second authority anywhere. Nothing in this
platform will ever hold a booking, so **nothing can ever contradict an agreed hour**. There is no
un-agreeing left to fear; there is only re-agreeing, and ADR-0144 already ships it — any member
may change any slot, any number of times, and every change writes a line naming who and what.

So §5.1 was not wrong about courts. It was wrong about **who is the authority on when you play**,
in a product that deleted the other candidate.

### A hole neither #324 nor #329 noticed

[#324](https://github.com/Raketa02/Raketa/issues/324) keys *Today* on **three slots filled and
the agreed day is today**. [#329](https://github.com/Raketa02/Raketa/issues/329) sharpened *Needs
result* to **the agreed moment has passed**, and defined that instant as existing **only when the
day and the hour are both recorded**.

A plan holding a day and nothing else therefore satisfies neither. It reads *Planning* on the day
four people play, and *Planning* the week after. Neither ticket was wrong: the two rules were
written against different halves of the plan, and their overlap was never checked.

## Decision

### 1. The hour is the agreement, not a guess at a booking

**We will strike §5.1's conclusion and keep its fact.** The replacement argument is one sentence:
**the people are the authority on when they play, and the platform will never learn anything
else.**

An agreed hour is not a prediction of a booking that a booking will later correct. It **is** the
agreement — the only statement about when this game happens that will ever exist. That is
precisely what makes it writable: a value nothing can contradict cannot be made stale by anything
except the people who wrote it, and they have a control for that.

This is recorded rather than left implicit because the fact §5.1 opens with is *permanently true*
and will keep leading readers back to §5.1's conclusion. The next person to notice that nobody
can promise 18:30 must find this record, not that paragraph.

**Only the plan half of §5.1 is overturned.** *A challenge asks one question* stands, unchanged
and unchallenged: `POST /challenges` carries no window, no day and no hour, ADR-0100 refuses the
picker, and *"when exactly — in the chat, if you accept"* is still exactly what the receiving
screen says. The two halves were argued together and only one of them depended on the owner.

### 2. The headline has two rungs, and a `Window` is not one of them

Documentation Part 4 gives each card *"a headline — the exact hour if a court is booked, otherwise
the part of day, then the day, then the rough window."* Four rungs, of which rung 1's condition
is deleted and rung 2's unit no longer exists. **We will keep two.**

- **The agreed moment**, when the day and the hour are both recorded — *Saturday 18:00*.
- **The agreed day alone**, when only the day is — *Saturday*.
- **Below that there is no time at all**, and the card leads with **who is on the court**.

**A `Window` is never a headline.** ADR-0100 made it *a label on the search, never a proposed
time*, and `availability.py` holds the standing refusal that **the grid is never rendered to
anybody as a calendar**. Headlining one would turn a label on a search into a proposed time in
the one place a player would read it as a plan, and it would be blank half the time anyway — a
mutual-born game has no window at all. It costs nothing to refuse: `GameListResponse.window`
ships today and **no component reads it**.

**And the three part-of-day bands are deleted, not repurposed.** With an exact hour recorded,
rendering 18:00 as *Evening* discards the thing four people agreed in order to print a coarser
version of it. The bands go with the rung they were the unit of.

The ladder has also changed character, which is worth saying because the shape looks similar. The
old one **climbed toward precision as a booking arrived**. The new one prints what the people have
written down so far and nothing else ever sharpens it.

### 3. A plan has an *agreed point*, and it exists the moment a day does

**We will define the plan's agreed point as the agreed instant when the hour is recorded, and the
start of the following local day when it is not.** No day recorded, no agreed point at all.

This **amends ADR-0144**, which scoped the derived instant to *day and hour both recorded*. One
value, defined whenever the day is, coarsened rather than absent when the hour is missing — and
coarsened **later, never earlier**, so nobody is ever asked for a result before they could have
played. It needs no new arithmetic: the coarse case is `slot_start` at the next day's offset and
minute zero, which is the same function ADR-0144 already routes every conversion through.

**The card ladder becomes four rungs read in order, and the clock outranks the checklist:**

1. the agreed point exists and has passed → **Needs result**
2. the agreed day is today → **Today**
3. all three slots are filled → **Game on**
4. otherwise → **Planning**

*Today*'s own test is the simple one — **the agreed day is today** — and it needs no instant.
Rungs 3 and 4 are reached only when the point has not passed and the day is not today, so
#329's *"and the agreed moment still ahead"* is implied rather than restated.

The purchase of this whole record is that a plan makes the clock drawable. Refusing to draw
*Today* on a day four people agreed hands that purchase straight back, and keeping #324's
three-slot rule lets **a free-text note about a venue gate the card that says go and play** —
which inverts ADR-0144's own ordering, where *where* is the most negotiable of the three.

### 4. A planned moment and a played moment never reconcile, and `games` cannot read a plan

**We will require no agreement between them, ever** — no warning, no clamp, no nudge, and no read
in either direction. People arrange 18:00 and play at 19:30. **The entry is the record that the
game happened** and it carries its own moment (ADR-0137); a plan is an agreement about a future.
Two records, two subjects, and nothing to reconcile.

**ADR-0137's sentence is scoped, not deleted.** *"There is no booking, no calendar and no date
field anywhere, so the moment a player says it is the moment it was"* becomes a claim about
**`games`' record** — where it is still exactly true, and where it was always aimed. The sentence
was never a statement about the platform; it was a statement about **which record carries the
moment**, and that answer has not changed. This is ADR-0144's *"beside that context without being
let into it"* made checkable: if `games` ever imports the Plan, this clause has been broken.

Its two copies — the root `CONTEXT.md`'s **Result** entry and `frontend_player/CLAUDE.md` — carry
the scoping when they are next touched. **Nothing is written into the root `CONTEXT.md` by this
record**, on ADR-0142's and ADR-0144's precedent: Part 1 documents implemented bounded contexts,
and the context this distinguishes `games` from does not exist yet. The glossary work is
[#332](https://github.com/Raketa02/Raketa/issues/332)'s.

### 5. The entry window is not re-dated off an agreed hour

ADR-0144 left open *"whether the horizon should instead re-date off an agreed hour."* **It does
not.** `entry_closes_at` stays `planned_at + PLAN_HORIZON + ENTRY_GRACE`, dated from *when it
became a game*, and `games` never learns that a plan exists.

The alternative fails on something worse than an uneven window. **A plan is editable by any
member at any time**, so re-dating would make a derived standing depend on a value a player can
move: a game reading `NEVER_PLAYED` would **walk backwards** to `AWAITING_ENTRY` when somebody
touched a chip, and the entry window would become a thing you extend by tapping. ADR-0137's whole
point is that *did this happen* has the same answer at every instant.

**The unevenness is smaller than it looks, and it is the designed case rather than an accident.**
ADR-0144 clamps the day chips at `planned_at + PLAN_HORIZON`; entry closes one `ENTRY_GRACE`
after that. So **every plannable day leaves at least twenty-four hours to say *we played***, and
`ENTRY_GRACE` was chosen to be exactly that: *"a day is what this platform already asks of a
person it needs an answer from — the challenge's own answer window."* The clamp and the grace
already interlock; nothing needed adding.

What remains is a real asymmetry and it is stated rather than fixed: a game played the evening it
was arranged has eight days to be entered, one planned for the last available day has one. **The
clock has always run from the arrangement, and the plan does not get to move it.**

### 6. The panel inverts: it stops explaining an absence and starts naming one

The design's info panel is false in both its sentences, and it existed to explain **an absence**
that no longer exists. It is not deleted, because one thing a player genuinely cannot infer
survives: seeing *Zabłocie Sport · Saturday · 18:00* inside an app, they may reasonably assume
the app did something about it. **It did not.**

So the panel says what is true and what is missing, in that order — the claim being settled here,
the wording open to the design pass:

> **Agreed between you — nothing is booked**
> Raketa does not hold courts. This is the note you are keeping between you: anybody here can
> change any of it, and everybody sees who changed what.

The reason for the three slots survives its old justification. They are **a shared note, not a
reservation**, and that was always what they were — §5.1 just described them by what they
refused to say.

### 7. `durations.ts`'s claim narrows, and the plan is drawn literally

`durations.ts` states: *"There is no date and no clock time in it, and that is the product rather
than an omission… a duration is the only time-shaped thing these screens are entitled to draw."*
ADR-0144 sends the rewrite here.

**The general claim is now false and is narrowed to what it was protecting** — the games
contract's deadlines — rather than left standing as a lie that reads like a rule. Its discipline
is untouched and stays whole: **a deadline is measured from `read_at`, never from this phone's
clock.**

And its complement is decided for the plan: **a plan's day and hour are wall-clock facts, drawn
literally, and never counted down.** Nothing expires at 18:00 — the card changing is a card
changing, not a door closing. This is [#327](https://github.com/Raketa02/Raketa/issues/327)'s
*draw the clock, never obey it* arriving from the other side: there the client holds a deadline
it must not act on, and here it holds a time that **is not a deadline at all**.

### 8. An agreed hour is never evidence about a person

**We will never read the gap between an agreed moment and an entry as punctuality**, and no
strand, signal or flag is derived from one.

The temptation is real — two agreed moments and a played moment look like a *turns up when they
said* strand, and Player Score has three strands still unsourced. It is refused on ADR-0140's own
argument: a Player Score is **what the platform watched**, and the platform does not watch
anybody turn up. It watches somebody type. The distance between an agreed 18:00 and an entry at
22:00 is the distance between a plan and a keyboard, and filing it as lateness would charge a
slow phone as a character flaw — which is the failure #217's Decision 3 refused when it declined
to fake the missing strands.

Recorded now, because it is free to refuse today and expensive to remove after somebody has
built it.

### 9. The calendar is still refused. The clock is not

The refusals that do **not** move, each stated plainly so the next reader can tell what changed
from what did not: **no court record**, **no booking**, **no inventory**, **no price**, and
**nothing anywhere reads the *where* slot** (ADR-0144).

The one that narrows is *there is no date picker anywhere in this app*. **The line is now: bounded
chips the platform offered, never a free instant.** Seven day chips ending at a horizon is not a
date picker, and thirty-minute steps between 06:00 and 23:00 is not a time picker — neither can
name an arbitrary instant, and both are bounded by a window the platform derived rather than by a
month the player scrolled.

**`availability.py`'s invariant is untouched**, and the distinction is worth having in writing:
*"the grid is never rendered to anybody as a calendar… overlap is a fact about a pair where a
calendar is a fact about a person."* A plan's day chips are neither — they are anchored on **the
game**, seven days from `planned_at`, and they show nobody's availability to anybody. A calendar
is a fact about a person, an overlap is a fact about a pair, and **a plan is a fact about a court
full of people who have already agreed to be on it.**

## Consequences

**§5.1's fact outlives its conclusion, and will keep producing the same objection.** Nobody can
promise 18:30 before a court exists — that stays true for as long as this product has no booking,
which is for ever on current scope. Every future reader who notices it will reconstruct §5.1's
argument unless they find §1 first, which is why §1 states the hidden premise rather than only
the answer.

**The clock now decides a card, and a free-text note no longer can.** *Today* draws on a
one-slot plan, and a plan holding only a day stops reading *Planning* a week after the day passed.
The cost is that `Game on` becomes a narrower card than the phrase suggests, and a game today
whose club nobody typed says *Today* while the club line is still empty — correctly.

**One derived value gets two definitions of precision.** An agreed point is an instant when the
hour is there and a whole day when it is not, and a reader who sees *the agreed point has passed*
has to know which. The alternative was two values that disagree in two places, and this one is at
least defined everywhere a day is.

**#325's conversation lifetime gains an anchor it did not have.** A conversation on a day-only
plan currently falls through to *the game settling*, eight days out; on §3 it anchors on the
agreed point and ends twenty-four hours after the day it named. **One case is still unanchored**
and it is not this record's: a conversation opened on a first acceptance whose challenge then
lapses or is declined to death has no plan, no game and no withdrawal.

**A plan can name a day that leaves twenty-four hours to enter a result, and nothing warns.** §5
declines to fix it, so a group who arrange on Monday for the following Monday get the tightest
entry window the product offers, with no sign that they chose it. The alternative was an entry
window a player can extend by tapping a chip.

**Nothing reconciles a plan with what happened, and that will look like a bug.** A card can read
*Saturday 18:00* beside a result entered at 21:40 on Sunday, and the app will say nothing about
the difference — because the two facts have different subjects and only one of them is the
record that the game happened. Somebody will file it; §4 is the answer.

**Two written claims in the codebase become stale on this decision and are not edited by it.**
`durations.ts`'s *"no date and no clock time"* and the two copies of `games`' *"no booking, no
calendar and no date field anywhere"* are decided here and rewritten by the build tickets that
touch them. **A record that decides a sentence's fate without changing it is a bet that the
ticket lands** — the bet is made deliberately, because this map writes no feature code.

**The refusal list is now the load-bearing part.** With an hour, a day, a place and a clock in the
product, *no court, no booking, no inventory, no price, no free instant* is what keeps the next
request for a month view, a venue lookup or a reminder answerable — and §9 is where a reader is
sent to be told which of those is a scope call and which is a decision with an argument behind it.
