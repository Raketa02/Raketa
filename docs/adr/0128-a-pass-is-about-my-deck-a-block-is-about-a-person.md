# ADR-0128 — A pass is a statement about my deck; a block is a statement about a person

- **Status:** Accepted — **the Context's *there is no Show them again* and §4 superseded
  2026-09-14 by [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)** §5: a route clears a sport's pass suppression, dealt memory and
  cool-off at once; the durable record stays. §1–§3 and §5 stand.
- **Date:** 2026-08-27

## Context

[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) settled the Block:
a **directed record with a symmetric effect**. `A → B` and `B → A` are independent records, and
each one removes both people from **every surface that shows one player to another**, failing
closed.

The Pass looks like the same shape. It is a *not today* on a deck card, it suppresses, and
[`the-play-screens.md`](../specs/matchmaking/the-play-screens.md) §7 already makes it
write-only, Origin-keyed, and returned by no route in any form. What it never had is a boundary:
`PASS_SUPPRESS` was a number in fog, and **three questions were never ruled on** —

1. does the suppression reach **search**, or only the deck;
2. does a **second** pass on the same person mean more than the first;
3. does it bite **their** deck too, as a block does.

§9.5.1 pushes toward the block's answer on the second: *"repeated passes on the same person are
a soft signal respected quietly."*

**Four things bear on it.**

**A pass is invisible to everyone, including the passer.** No route returns one, not as a card,
not as a count; §21 refuses it, and there is no *Show them again* — that button was struck for
making the suppression a suggestion. So an escalation could not be seen, disputed or undone by
anybody, and its effect would arrive as an unexplained absence.

**A quiet soft signal has nowhere to live.** [ADR-0123](0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)
closed the silent roster and budgeted it per player at `MOVE_NOTICE`. *Respected quietly* is by
construction a silent score, so adopting it means reopening a closed union for a signal that can
never print — which is exactly the move
[ADR-0126](0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md) refused for
the diversity stage.

**The pool is thin.** At launch density, 63% of searches return under five candidates. A
suppression that reaches search removes somebody from a *question about the city* for 30 days,
on one tap, in a city that has barely enough people to answer the question at all.

**The escalation already exists, under its own name and with consent.** A Block is symmetric,
deliberate, reversible, and glossed. A pass that hardens toward permanence is a block nobody
agreed to, arrived at by tapping.

## Decision

**We will set `PASS_SUPPRESS = 30 days` and give the pass three boundaries, all of which are the
opposite of the block's — because the two say different things.**

**A pass is a statement about my deck. A block is a statement about a person.**

### 1. Deck only

A pass never reaches the shortlist, the line-up, or a forecast. The deck's exclusions
(`the-engine.md` §10.3) are the deck's; a passed player is a full candidate everywhere else,
immediately.

> **Read on one more surface 2026-09-16 by [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §4.** A
> pass may be *given* from the radar's record sheet; it is the same pass, about the same deck,
> and the radar itself hides nobody for it — Magda, passed on Monday, is drawn on Tuesday's
> radar and dealt on no deck for thirty days.

The deck is a **judgement surface** — one person, yes or no, *not tonight*. A search is a
**question about the pool**, and a search that hides people because of a swipe is a search that
lies about the city. That is the same reason
[ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md) makes the empty response carry a
**post-gate** count: a number about the city has to be true about the city.

### 2. One-directional

My pass suppresses in **my** deck and nowhere else. §9.5.1's own promise — a pass *"costs the
other person nothing"* — is kept **literally**, where a symmetric pass would spend their pool on
my tap and they would never learn why.

This is where it parts company with ADR-0095, and the reason is the thing being said. A block
has to be symmetric or it is worth nothing: *I do not want to be near this person* is false if
they can still see me. A pass says *not this card, tonight*, which is a fact about one deck and
carries no claim about the other person at all.

### 3. Never escalates

A second pass on the same person suppresses for the same 30 days and no more. §9.5.1's *soft
signal respected quietly* is **struck**: it cannot print, it cannot enter ADR-0123's closed
silent roster, and its destination — a person who effectively never returns — is a Block, which
the product already has and which requires somebody to mean it.

Note when a second pass is even possible: only after the first suppression has lapsed, 30 days
later. A player who passes twice across two months, and wants more than that, has a gesture
available and it is not this one.

### 4. `PASS_SUPPRESS` crosses in no shape at all

It is the only ruleset number the deck's three decisions produced with **zero contract surface**
— no field, no code, no timestamp. The wire is untouched by this record.

### 5. It is five-numbers-shaped

Named owner `RobertConstantin02`, and any change lands as an ADR naming who moved it
([`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md)). In a thin pool it is one of
the few things that can turn a non-empty pool into an **empty deck**, and — §4 — nobody can see
it doing so, the player whose taps caused it least of all.

## Consequences

- **You can pass on somebody tonight and find them third in your shortlist tomorrow.** Named
  rather than hidden: it is the price of not letting a swipe edit a search, and the two surfaces
  mean different things about the same person. If it turns out to read as the product ignoring
  you, the fix is a *sentence on the deck about what a pass does*, never a wider suppression.
- **Somebody who wants a person gone must block them.** That is a heavier gesture, and it is
  meant to be. The alternative on offer — a pass that silently hardens — gets to the same place
  while letting nobody say they intended it.
- **The block keeps its weight.** One permanent instrument, deliberate and reversible, rather
  than two mechanisms converging on the same effect from opposite ends of the intent scale.
- **The falsifier is already paid for**, which is more than any of the five numbers can say. The
  **Origin key** on `POST /passes` exists precisely so *pass rate on re-shown profiles* is
  measurable. Two demands follow, in
  [`search-telemetry.md`](../specs/matchmaking/search-telemetry.md): per card, whether the
  pairing had a **lapsed** suppression — without it only plain pass rate is computable, never
  *re-shown* pass rate — and per deal, **how many cards a live suppression excluded**, which is
  the only thing that distinguishes *your own passes emptied your deck* from *the pool is
  empty*.
- **Nothing here bounds how many people a player may pass on.** There is no pass cap and none is
  proposed: passing is the deck working, and the deck's own exhaustion plus a fresh deal is the
  answer to a player who passes on everybody.
