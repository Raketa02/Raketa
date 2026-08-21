# ADR-0087 — Leaving standby is the seventh act, and it arrives with the write that receives it

- **Status:** Accepted
- **Date:** 2026-08-22
- **Resolves:** [`Raketa02/Raketa#59`](https://github.com/Raketa02/Raketa/issues/59), with [ADR-0086](0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md)
- **Opens:** [ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md)'s closed enumeration, in exactly the manner that ADR prescribed

## Context

[ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md) closed the act enumeration at
six and left a door in the wall: *"A seventh act arrives **with the surface that receives it**,
never ahead of it — which is precisely how the removal act will come back."* It listed `waitlisted`
among the twenty-seven cards that name nothing.

[`#59`](https://github.com/Raketa02/Raketa/issues/59) put leaving standby beside leaving a match, on
the strength of a shared word. They share nothing else. `CONTEXT.md`:

> **Standby** — the players who asked to be told if a seat frees on a particular match. It confers
> **priority, not a place** … a standby **position** is not a fact the platform will show — it can
> rise.

No seat, no money, no cascade, no outcome, nothing to settle, and — decisively — **no position to
forfeit**, because the model already refuses to show one. There is no consequence for a screen to
state, which is the whole reason ADR-0086's act needed a route. This one needs a write.

`waitlisted` is also the one card where silence was worst. It is the single situation only a viewer
can be in ([ADR-0040](0040-one-ladder-resolves-a-situation.md)), it says *you are queued, not
committed* — and today nothing takes a player off it.

## Decision

**We will make leaving standby the seventh act, take the `waitlisted` card's primary button with
it, and receive it on a write that asks nothing.**

### `leaveStandby`, and the table becomes seven rows

| Code | Receiving surface | Who gets it |
|---|---|---|
| `leaveStandby` | `DELETE /api/v1/matches/{matchId}/standby` | `waitlisted` |

The twenty-seven cards that name no act become **twenty-six**. ADR-0083's rule is unchanged and is
satisfied rather than bent: *a card names an act when the viewer can take it now and a v1 surface
can receive it.* The viewer can, and the surface ships with this decision — which is the condition
that ADR wrote the door for.

**ADR-0083's reassurance argument does not reach it.** That argument was about *Cancel my position*
being the loudest thing on a match a player is looking forward to. A standby place is a queue
position on a match the player does not hold a seat in; the loudest thing on that card is the only
thing they can do about it.

The label stays the client's, per
[ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md). The client's
code → sentence table becomes seven rows and stays total.

### No confirmation, and no warning

Nothing is lost. No money moves, no Player Score is touched, and there is **no place to lose** — a
standby position is not a fact the platform shows, precisely because it can rise. Rejoining costs
what joining cost, which is nothing.

**A confirmation here would imply a cost the model says does not exist.** That is worse than a
mis-tap, because a mis-tap is one tap to undo and a false warning teaches a player that standby is
something they are giving up.

### Its own write, returning Now's update

`DELETE /api/v1/matches/{matchId}/standby`, and the response carries ADR-0070's update shape like
every other action off Now
([ADR-0074](0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md)).

**Not folded into ADR-0086's departure route.** A route exists to hold a consequence; this act has
none, and giving it one would be building the screen this ADR just argued it does not need. And a
match a player is only on standby for is a match they hold no seat in, where `mayDepart` is false —
so the two acts never appear together on one card.

**No idempotency key.** ADR-0030's command log is for **destructive** commands, and a repeated
delete of a standby place a player no longer holds is the state they asked for. The route is
idempotent by its own nature, which is the case a key exists to manufacture.

## Consequences

**Easier**

- The one situation only a viewer can be in stops being a place a player cannot leave.
- The enumeration's opening rule has now been exercised once, and it worked as written: the act
  arrived attached to a surface, and the question *does this card get a button* was asked about a
  surface rather than about a situation.

**Harder**

- **The act enumeration is no longer six**, and *"closed at six"* is a sentence in ADR-0083 that a
  future reader will find and have to reconcile. It was closed against per-situation judgement, not
  against growth; growth still costs a surface.
- **A `waitlisted` card now has a primary button and a `⌘` that is wrong**, since ADR-0083 already
  found the Getting-in sheet *"visibly wrong"* on a match you have not joined. This decision does
  not fix that — it is a card-anatomy question — but it puts a correct control next to an incorrect
  one, which makes the defect easier to see and harder to leave.
