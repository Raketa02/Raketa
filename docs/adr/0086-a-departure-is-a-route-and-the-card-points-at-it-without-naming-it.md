# ADR-0086 — A departure is a route off Now, and the card points at it without naming it

- **Status:** Accepted
- **Date:** 2026-08-22
- **Resolves:** [`Raketa02/Raketa#59`](https://github.com/Raketa02/Raketa/issues/59)
- **Completes:** [ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md), which ruled the removal act out of the primary slot and filed *where it does live* rather than answering it
- **Copies:** [ADR-0074](0074-the-result-route-reads-four-facts-and-an-action-off-now-hands-now-its-update.md), field for field — the pattern it promised every later action off Now
- **Narrows:** [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) — *"the owner cannot leave"* now also means the owner's **booking cancellation** is not built in v1

## Context

[ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md) closed the act enumeration at
six and named its own sharpest cost: **nothing a player does can trigger the cascade**, so
`replacement`, `replacementTransfer`, `rescue`, `rescueLate`, `cancelledCheckpoint` and the entire
leaver audience are reachable only from seeded data. It refused the primary slot to the removal act
on a stated ground — *"Cancel my position as the loudest thing on every match a player is looking
forward to inverts a screen whose job is reassurance"* — and deferred the surface question here,
because the act needs the money line the prototype's `leaveOutcome` prints and **a card
demonstrably cannot give it that room**.

The ticket named three acts. Walking them found that they are not three of a kind, and that one of
them is not ours to build.

- **Leaving a match** is [ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)'s
  granted right: *"a marketplace player may withdraw freely before the lock at no cost to the
  owner."* It vacates a paid seat, starts the cascade, and has four money outcomes.
- **Leaving standby** shares the word and nothing else — no seat, no money, no outcome. It is
  decided in [ADR-0087](0087-leaving-standby-is-the-seventh-act.md).
- **Cancelling a private court** is a thing this model has already refused to call a departure.
  ADR-0030: *"The owner cannot leave. Leaving is vacating a seat while the match survives; an owner
  vacating orphans the guarantee that is the match's court. This is the one departure the model
  refuses. **Cancelling the whole booking is a different act, governed by club terms.**"*

Three further facts arrive already settled, and between them they do most of the work.

- **`Withdrawal` is taken.** `CONTEXT.md` defines it as *an offer ending because the seat went
  elsewhere* — a fact about a **seat offer**, not about a player. The act here is a **Departure**
  and the player is a **Leaver**, both already in the glossary, both named by ADR-0030. A route
  called `/withdrawal` would be the rival vocabulary [ADR-0040](0040-one-ladder-resolves-a-situation.md)
  exists to prevent, shipped by accident.
- **The command's shape is half-decided.** `CONTEXT.md` defines **Quote** as *"the outcome label a
  player was shown before they chose to leave, carried on the leave command. If the outcome
  recomputed at apply time is strictly worse than the quote, the command is refused and the player
  is re-presented."* So a departure is definitionally a two-step act, and the surface is the step
  that produces the quote.
- **The outcomes are a closed set of four** — *reversed*, *refunded in full*, *refunded half*,
  *forfeited*; on a private court only the second and fourth are reachable. The prototype's
  five-row table is not that set: one row is a **transfer** (out of scope with the invite flow) and
  one is *the club or the weather cancels*, which is `cancelledClub` overriding the match rather
  than an outcome of leaving it.

And one thing nobody had noticed. `freeCancelHours`, the field the ticket names as the private
owner's bound, ships with **no v1 reader** —
[ADR-0078](0078-club-policy-is-eight-fields-and-two-of-them-ship-dark.md) records that its *"only
two consumers are the owner messages ruled out of scope"*. There is no private-booking flow, so a
private court in v1 arrives only from seed; cancelling a real reservation means reaching a club, and
no such channel exists. The act had a bound nothing reads, a subject nothing creates, and a
recipient nothing can reach.

## Decision

**We will serve a departure as one route off Now that states what leaving is worth right now and
what it could still become, and we will reach it from a control that is not the card's act.**

### The route

**`GET /api/v1/matches/{matchId}/departure`**, and the write under the same path. This is
ADR-0074's shape, deliberately and without variation — that ADR closed by recording that *"every
future action taken off Now now has a pattern to copy rather than a question to reopen"*, and this
is the first one to take it up.

- **It embeds the match's spine verbatim** — the same object `GET /api/v1/now` sends.
- **It is not a card.** No fit badge, no emphasis flag, no card stamp.
- **It carries the situation off the same ladder.** One reader, several renderings, per ADR-0040.
- **A refusal is not a second shape** ([ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md)):
  a departure that no longer applies returns what a success returns — what is true now.

### It prints all four outcomes, always, each with a marker the server sends

Not only the reachable ones. **A table that quietly drops *forfeited* once it is unreachable is
also a table that never showed it while it was**, and the entire reason this act got a route
instead of a card was room. Each outcome carries a server-composed marker of its standing —
searching, still possible, opens at a stated moment, or spent. The phone derives none of them
([ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md)).

On a private court the table is **two rows**, because `CONTEXT.md` already fixes that only
*refunded in full* and *forfeited* are reachable there. That is the glossary being read, not a
second rule.

### It carries the facts behind the outcome, and refuses to name a phase

The commitment deadline **as a moment** — the phone subtracts, and derives nothing else — the
seat's amount, and how full the match is. All facts the card or the spine already holds.

**No `phase` field.** The prototype names four (*free cancellation · full-price search · 50/50
Rescue · past the checkpoint*), and the four outcome markers already say which one you are in. A
phase name is a second vocabulary answering a question already answered, which is the shape ADR-0040
refuses.

### `mayDepart` is a server boolean, false in exactly three places

The server states it; the phone derives none of it, exactly as ADR-0074 states `mayEnter`,
`mayAccept` and `mayCounter`.

1. **After the match starts.** There is no departure to make — you played, or you did not, and that
   is `playedNoShow`.
2. **Under [ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md)'s lock**, once
   a converted private court is full and past the club's cancellation deadline. Unchanged.
3. **For a leaver who has already left**, and the route **resolves** rather than 404ing — mirroring
   ADR-0074's own hardest case. A 404 tells a leaver their match never existed, which is the class
   of defect ADR-0030 was written against.

A viewer holding a live **seat claim** has `mayDepart` false, because
[ADR-0081](0081-a-seat-is-never-taken-until-it-is-paid.md) fixes that they hold no seat yet.
Abandoning a claim is already one of the three ways that ADR ends one; it is not a departure and
must not grow a second mechanism.

### The quote is the one live outcome, not the set

*Reversed* before commitment, *refunded in full* while the full-price search is running, *refunded
half* once Rescue has opened. The other rows are shown as possibilities and are **not** quoted.

Quoting the whole table would make the refuse-if-worse rule compare sets, and `CONTEXT.md` defines
the ordering over single labels — *refunded in full > refunded half > forfeited = nothing
returned*. The rule then reads plainly: **if the live outcome at apply time is worse than the one
you were looking at, we refuse and show you the new one.**

### The route is the confirmation

One primary button, carrying the quote. **No third step.** A confirm dialog over a screen whose
entire job is to state the consequence asks the same question twice, and the refuse-and-re-present
rule already gives the player the only correction that matters — what is true now, rather than a
sentence about a rule.

### An idempotency key crosses the wire, and it is not the thing ADR-0074 refused

ADR-0030 requires destructive commands to carry a command log keyed `(command, idempotency key)`
with a 24-hour expiry. The client generates the key and sends it.

ADR-0074 refused a client-held **version** because it *"would make the phone hold a rule about its
own staleness"*. A key encodes no rule and states no belief about freshness. It answers one case
that a version could not: a phone that loses its answer to a departure it already made, whose naive
retry charges the cascade twice.

### The write returns Now's update, and the card changes audience in place

ADR-0074's rule, unchanged: the response carries its own screen's answer **and** ADR-0070's update
shape — the one card that changed, plus either viewer-owned region whose contents or order moved.

**This is the first mid-session audience change in the product**, and it is recorded here so nobody
discovers it. Before the write the viewer is *in the match*; after it they are a **leaver**, and
ADR-0030 keeps the card until the outcome settles under the predicate *"I hold a seat, or I held one
and its outcome is not yet settled."* So the card is returned **changed, in place** — same match,
same region, new rendering. Nothing is removed and no region moves.

[ADR-0072](0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md) fixed that an
audience changes a card's words and which money it names and never its situation. This is where that
becomes a thing a client can watch happen, and it is why **no client may cache a card keyed on the
audience that composed it**.

### The card reaches it with a third control, and names no act

**A member-only control in the action row, and not the primary slot.** ADR-0083's ruling stands
verbatim; this does not reword it into an objection about a label.

- **It is a spine boolean, not an act code.** Putting it in `cta` would reopen an enumeration
  ADR-0083 deliberately closed, for something that is not the card's act, and would give one card
  two act codes. The spine is where ADR-0070 puts the composition's judgement about *this viewer*,
  which is exactly what *may this person leave* is. **This is the third entrant to that
  screen-facts slot**, after the debt line and the seat claim, and ADR-0070's warning — *"the slot
  is not an invitation"* — is honoured by making the argument rather than assuming it: the client
  is forbidden by ADR-0053 from deriving *I hold a seat*, so either the server says or the control
  cannot be drawn at all.
- **An exit glyph from the stock outline family**
  [ADR-0082](0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md) locked.
  `⋯` was refused: it promises a menu and opens a route.
- **It carries a real accessibility label**, which `✉` and `⌘` still lack — `UI` §1087 records that
  both have **nothing**.
- **44 × 44 hit slop**, per `UI` §1153's `Button.iconOnly`. The action row's controls are 40 × 34
  and the spec flags them *"under 44 in both axes"*; the third control inherits the prescribed fix
  rather than deepening the defect.

**This departs from a UI authority, and the departure is the same shape ADR-0083's was.** The two
UI documents always draw a primary button, so they never draw a row of three icons; they are final
on what a card looks like and silent on a control whose destination they assumed existed. Read it
as ADR-0083 asked its own departure to be read — a forced consequence of an out-of-scope ruling,
not a licence to redraw the card.

### Two things are ruled out of scope rather than half-built

- **The private owner's cancellation.** It needs a booking flow to have made the reservation, a
  channel to the club to cancel it, and `freeCancelHours` to have a reader. It has none of the
  three, and ADR-0030 already holds that it is *a different act, governed by club terms*. It
  returns with the private-booking effort, whole.
- **Transfer my seat.** It is the leaver's **best** outcome — a named person always pays full
  price, so the leaver gets 100% where the cascade might return half or nothing — and it is the
  invite flow, which this map rules out and whose ladder
  ([ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)) is declared and dark.
  **The route says nothing about it.** Advertising a door that is not there is worse than the gap.

## Considered options

- **The primary slot with a neutral label** — the prototype's own screen title is *"I can't make
  it"*, not *Cancel my position*, and the slot is vacant on all twenty-seven silent cards. Refused:
  ADR-0083 is explicit that *"none of them may take the primary slot"*, and reading a ruling about
  the slot as a ruling about the wording is rewriting it one day after it was made. It remains the
  strongest alternative, and if it is ever taken it must be recorded as a genuine override.
- **A sheet, like Getting in.** Refused: `UI` §C6's sheet is a door code and a QR. This screen
  states a consequence a player must read before an irreversible act, and it is the one thing
  ADR-0083 said a card could not give room to.
- **A general `GET /matches/{id}`.** Refused again, on ADR-0074's grounds — it authors the
  match-detail screen's contract inside a ticket that is not about it.
- **Printing only reachable outcomes.** Refused above.

## Consequences

**Easier**

- **The cascade has a trigger.** ADR-0083's sharpest cost is discharged: `replacement`,
  `replacementTransfer`, `rescue`, `rescueLate`, `cancelledCheckpoint` and the leaver audience stop
  being demo-only, and half this map's most carefully modelled machinery becomes reachable by
  something a player does.
- Nothing about the route is a new idea. Spine, situation vocabulary, update shape, refusal shape
  and permission booleans are all ADR-0074's, which is the second proof that pattern was worth
  writing down.
- The quote rule has one meaning instead of two plausible ones, and it is a comparison of labels.

**Harder**

- **A third fact enters ADR-0070's screen-facts slot**, and the next thing proposed for it must
  make its own argument. That warning has now survived three entrants, which is the point at which
  it starts to look like a formality — it is not.
- **A member's action row now holds three controls in a 268 px card**, where `UI` §B6.3 records one
  variant and ADR-0083 added a second. A client treating the row's shape as a boolean now needs a
  third condition.
- **The private owner's card is silent in both directions.** ADR-0083 already left it naming no act
  because inviting has no screen; it now also offers no way out. All four private situations arrive
  only from seed in v1, so nobody meets this — but the seeded demo will show it.
- **`freeCancelHours` loses its last prospective v1 reader.** ADR-0078 shipped it dark on the
  ground that the fact is cheap to capture and expensive to backfill; that argument is unchanged,
  but the field is now dark for two reasons rather than one.
