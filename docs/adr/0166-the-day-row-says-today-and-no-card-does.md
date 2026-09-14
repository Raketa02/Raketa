# ADR-0166 — The day row says *Today*, and no card does

- **Status:** Accepted
- **Date:** 2026-09-14
- **Amends [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md) §3**
  — the card ladder loses its second rung, *the agreed day is today → Today*, and §3's argument
  for it is answered rather than overruled (§1 below). Everything else in that record stands: the
  hour is the agreement, the agreed point is defined whenever a day is, the clock still outranks
  the checklist, and *Needs result* is still the rung it was.
- **Amends [ADR-0157](0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)**
  on one example: *"two of the four rungs are facts about the clock"* becomes one of four. The
  argument it was an example of — a rung is a reading of the plan against `read_at`, which a
  stream of acts cannot hold — stands, on *Needs result* alone.
- **Leaves standing [#324](https://github.com/Raketa02/Raketa/issues/324)'s rule that the tag
  is the card's name**, and [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)'s
  rung above the clock. Nothing on the wire moves: no field, no enum, no `make gen-api`.

## Context

**The Now card had a state named after the calendar.** ADR-0145 §3's ladder read *Needs result*,
then **Today**, then *Game on*, then *Planning*, and its test for the second was the simple one —
*the agreed day is today* — placed above the checklist on purpose: *"the purchase of this whole
record is that a plan makes the clock drawable. Refusing to draw Today on a day four people agreed
hands that purchase straight back."* #324's second amendment had already dropped the three-slot
requirement from it, so a *Today* card could genuinely have no hour and no place, and §3's own
cost statement said so: *"a game today whose club nobody typed says Today while the club line is
still empty — correctly."*

**Walking the rail on the day of a game says otherwise.** A card tagged *Today* in the settled
colour, leading with *We played*, over a plan whose `TIME` bar is dim, is a card announcing the
game as settled because of what day it is. The tag, the dot and the door all say *go and play*;
the slots under them say *you have not agreed when*. Two readings of one card, and the one in the
tag is the one that happens to be about the calendar rather than about the plan. The same card
on the same plan a day earlier reads *Planning*, volt, *Finish the plan* — which is what the plan
is on both days.

**And the day was already drawn on the card.** Since #413 the day row prints the weekday whole
and the date beside it — `Monday` `14 Sep` — so *Today* as a tag was the day row's fact said a
second time, in the one slot on the card that is supposed to name the **stage**. ADR-0145 §3's
purchase — the clock is drawable — is real; what this record disputes is that the tag is where
to draw it. `Today 14 Sep` in the day row draws the same clock, under whichever tag the plan has
earned, and says less that is not true.

**What nothing else on the card could tell apart.** *Game on* is three slots agreed and the moment
ahead; *Today* was the agreed day, whatever the slots. So a game with a full plan on its own day
and a game with a day-only plan on its own day drew the same tag, and the difference between
them — the whole of what the card exists to say — was in the bars only.

## Decision

### 1. The ladder is four rungs, and the calendar is not one of them

**We will read the card ladder as: a seat is open → *Needs a player*; the agreed point has passed
→ *Needs result*; all three slots filled → *Game on*; otherwise → *Planning*.** A game on the day
it is to be played is *Game on* or *Planning* by its slots, exactly as a game on any other day is.
ADR-0145 §3's ordering stands — the clock outranks the checklist — and it now has one clock rung
to outrank it with, which is the one that reads an instant rather than a date.

The answer to §3's argument is that the purchase is kept and moved: a plan still makes the clock
drawable, and the day row is where it is drawn (§2). What §3 feared — *refusing to draw Today on a
day four people agreed* — does not happen; what stops happening is drawing it as a **stage**.

### 2. The day row says *Today*, on the Now card and nowhere else

**We will draw the card's day row as `Today` and the date, in place of the weekday and the date,
when the plan's day is the platform day of the games list's `read_at`.** The word takes the
weekday's role — `h2`, with the date in `tiny` beside it — and it is spoken the same way: *Day,
Today 14 Sep*. The test is the one the rung used, `plan.day === platformDay(readAt)`, folded
against the games list's instant and never the phone's clock or zone (ADR-0148 §10), and it is
defined **once**, in `features/plans/domain/slots.ts`, with two readers: the day row, and the
quick chips' *On my way*, which had its own copy of the same comparison.

**Only the card.** The plan chip in the room and the read-only tag on the game screen keep the
weekday. The card is the one surface that draws a date beside the weekday and the one that folds
against an instant, so it is the one that can say the day has come; a chip that says *Today* in a
row of `Mon Tue Wed` is a different kind of word in a row of one kind, and the chip is also the
control that opens that row.

**Only *Today*.** No *Tomorrow*, and no *Yesterday* on an ended card. This record folds a *state*
into the day row; *Tomorrow* was never a state, and `Tuesday 15 Sep` already says it. One word,
so the row cannot grow a vocabulary the tag was just relieved of.

### 3. *We played* leads only once the agreed point has passed

**We will land the card's wide door, and the game screen's entry arm, on the plan for every rung
but *Needs result*.** *Today* was the one rung that led with *We played* before its moment; with
it gone, a game on its own day reads `Open` (or `Finish the plan`) and lands on the plan lead,
where *We played* is the quiet door under *Open the chat*, exactly as it is on any other day. Once
the agreed point is behind the fold the card reads *Needs result* and leads with *We played* on
its own — the hour for a plan with one, the start of the next day for a plan without.

This is the one behaviour a player will notice, and it is accepted rather than worked around:
leading with *you played* at 09:00 for a 16:00 game was the wrong lead, and the screen still
offers the act on every entry arm (`GameScreen.tsx`: *it changes what leads and never what is
offered*). A *Game on* card that led with *We played* when the day is today would be the *Today*
state again under another name.

### 4. What is not decided here

No card is renamed, no dot or accent changes meaning, and the rail's order is still the server's.
The two transcriptions of the ladder in the backend — `app/seeds/loop.py` and
`tests/api/test_the_loop.py` — drop the rung with the client, and the seed's fixture that reached
*Today* now reaches *Planning* on the day of its game, which is the card this record is about.
`the-loop-components.md` §3.3, `the-loop-screens.md` §4–§5, `the-words.md` §22 and
`frontend_player/CONTEXT.md` are corrected with it.

## Consequences

**A card has one less thing to say, and says it with the slots.** A day-only plan on the morning
of its game is *Planning*, volt, with `Today 14 Sep` under a bright bar and `Not agreed yet` under
a dim one — which is the alarm #324's second amendment wanted, said by the plan rather than by a
name. A full plan on its own day is *Game on*, mint, `Today 14 Sep` — a settled game, today.

***We played* is one press further away on the day of the game, until the hour.** Four people who
arrange 16:00 and play at 14:00 find `Open` on the card at 15:30 and *We played* on the screen
behind it. The cost is stated and small; the alternative was a card that led with a score before
anybody could have one.

**The word is judged against `read_at`, and a stale list says *Today* a day late.** This is the
same staleness the *Today* tag had — the same instant, the same comparison — so nothing is worse;
it is named because the word is now in a row that otherwise prints calendar facts, and a reader
may take it for one. A refetch corrects it, and a game whose day has passed reads *Needs result*
on the same refetch.

**ADR-0145 §3 keeps a sentence this record contradicts, and the scope note is what stops a reader
re-deriving the rung.** Its argument is good — the clock must be drawable — and will keep leading
readers to the same tag unless the note says where the clock went.

**Ten card names rather than eleven**, and every `Record` over the union lost a row in one commit;
a table that grows *today* back fails `pnpm typecheck` in `nowPresentation.ts` and a test in
`nowPresentation.test.ts` that holds the name absent by name.
