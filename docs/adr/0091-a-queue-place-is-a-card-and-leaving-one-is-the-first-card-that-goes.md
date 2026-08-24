# ADR-0091 — A queue place is a card on the strip, and leaving one is the first card that goes

- **Status:** Accepted
- **Date:** 2026-08-24
- **Resolves:** [`Raketa02/Raketa#81`](https://github.com/Raketa02/Raketa/issues/81)
- **Completes:** [ADR-0087](0087-leaving-standby-is-the-seventh-act.md), by giving its act a card to sit on
- **Discharges:** [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md)'s *"the one-card answer must be able to say **this card is no longer on your screen**"*
- **Narrows:** [ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md)'s enrolled strip, from three memberships to four

## Context

[ADR-0087](0087-leaving-standby-is-the-seventh-act.md) added a seventh act, `leaveStandby`, on the
rule [ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md) wrote the door for: *an act
arrives **with the surface that receives it**, never ahead of it.* It shipped the wire enum, the
copy table on the phone, and a decision that the surface would be a bare `DELETE`.

Building that `DELETE` (`#81`) turned up two things the ADR did not have to answer and this one
does.

**Nowhere on Now can hold a `waitlisted` card.** ADR-0087 calls it *"the one card where silence was
worst"* and gives it a primary button; ADR-0083 lists it among the twenty-seven Now cards that name
nothing, so both read as though the card were already on the screen. It is not, and could not be:

- the **enrolled strip** answers *a seat that names her, or a departure that does*
  ([ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md)), and a queued
  player holds neither;
- the **offers region** is seats offered to her ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md)),
  which is a different rung and a different fact;
- the **ranked shelves** exclude a match she is queued for, by the `NotOnStandby` rule
  ([ADR-0051](0051-now-is-ordered-not-drawn.md)) — deliberately, so the screen never suggests her
  the match she has already asked about.

The prototype agrees and says so: *"a waitlisted match cannot appear on Now. The strip filter
requires `mySeat(m)`… `waitlisted` is reachable only through the gallery and the match detail
screen."* Both of those are out of scope, and ADR-0083's answer to a missing match screen was to
remove **buttons**, never cards.

So the seventh act was shipped onto a card that renders nowhere. A button on a card nobody can see
is the same defect as a button whose destination is unbuilt, arriving from the other direction.

**And nothing in the product could remove a card.** ADR-0070 requires it — *"the one-card answer
must therefore be able to say **this card is no longer on your screen**, not only here is its new
content"* — and the shape shipped without it, honestly, because nothing could produce one:
[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) keeps a leaver's card until her outcome
settles, so the only action off Now at the time changed a card and never took one away. The domain
type recorded the gap and named `#83` as the expected first producer.

## Decision

**We will put a standby place on the enrolled strip as a fourth membership, and make leaving one the
first act that removes a card.**

### The strip has four memberships, and the fourth confers nothing

A card reaches the enrolled region when the viewer holds **a seat, a departure, a live seat claim,
or a standby place**. The first three are unchanged. The fourth is the only one that confers nothing
at all — `CONTEXT.md` is explicit that standby is *priority, not a place* — and it is there for one
reason: it is the only region on Now that could hold the card, and a card that renders nowhere
cannot carry a button.

**This is a narrowing of ADR-0073's *"committed"*, and it is stated rather than smuggled.** The
region's own copy for that card reads *you are queued, not committed*, which is the region admitting
the exception in the sentence it prints. The alternative — a fourth region — would give the screen a
row that is empty for almost every player on almost every screen, which is the thing ADR-0070 gives
shelves the *absent when empty* rule to avoid, and would then need its own order, its own cap and
its own place in the composition.

**The kernel already assumed this.** `situation()`'s played rung carries the comment *"a standby
player and a leaver both resolve to the post-play situation, and the affordance to enter a score is
what is withheld from them, downstream"* — a sentence that is only meaningful if a standby player
reaches a composed card. The ladder has been ready since it shipped; what was missing was a store
and a membership.

**The queue is not part of the `Match` aggregate.** It is a table keyed `(match_id, player_id)` with
no version and no events. A join changes nothing a rung reads about the *match* — the kernel takes
it through `Viewer`, which is a fact about the person looking — so routing it through the aggregate
would bump [ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)'s version column, serialise
joins against seat payments, and invalidate the scoring-context cache keyed `matchId : recordVersion`
every time somebody queued.

**It announces nothing**, which is the one place Matches departs from that ADR's *every change is its
own named event*. That obligation exists because the outbox is the only trail a support agent has for
a game somebody **paid for**. A queue place moves no money and confers no place, and it has exactly
one reader — the invitation cascade
([ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)), which reads the list when a
seat frees rather than following it. An outbox row nothing subscribes to is
[ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md)'s field with no reader,
written once per tap.

**A place is deleted rather than ended**, which is the opposite of every other child table in the
context and is the decision rather than an oversight. A vacancy, a departure and a seat claim are all
kept because *what happened at 18:03* is a support question about money or about a seat somebody
could not take; neither is true here. ADR-0087's *"rejoining costs what joining cost, which is
nothing"* is only true if the platform is not quietly keeping a record of every time she changed her
mind.

### Now's update is one card in one of two forms

`NowUpdate` becomes a discriminated union: **the card, changed in place**, or **the card, gone**.

Leaving standby produces the second, because the queue place is the whole of what put that match on
her strip. That makes it ADR-0070's first genuine producer, arriving before `#83`'s offers region
rather than after it — the domain type's own note named the wrong ticket, on the reasonable ground
that a departure cannot remove a card.

**A union and not a nullable card.** This is [ADR-0072](0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md)'s
rule for the leaver's money applied to the update: *it is gone* and *this build sent none* are
opposite sentences and a blank cannot tell them apart. Reading a card off the wrong form is a
narrowing error on both sides of the wire.

**The gone form carries the match id and no card.** There is nothing to carry: the viewer is nothing
to that match now, and composing an emptied card would be answering *what is this match doing* for
somebody who is not asking.

**The two region slots are still not here.** ADR-0070 puts a region in an update when its *contents
or order* change, and a single card leaving is expressed by the form above rather than by re-sending
the region it left — which also keeps the update independent of the sport chip, where a region is
not. The first act that moves a region's order is taking a seat (`#89`).

### The route refuses nothing but an address

`DELETE /api/v1/matches/{matchId}/standby` has **no membership gate**. Anybody may queue for any
match, so there is nobody to be a stranger to, and the acceptance criterion — *deleting a standby
place the viewer does not hold returns what a success returns* — is satisfied by having nothing to
check rather than by catching a refusal and dressing it as a success. The only 404 is a match id that
names nothing, and it is about the address rather than about the act.

**A queued viewer's departure route resolves** rather than 404ing, and answers `mayDepart: false`. She
is something to the match, so the screen opens and offers nothing — the same answer a leaver gets. The
two controls never appear together, which is ADR-0087's own reason for keeping the two acts apart.

### Joining has no surface, and that is v1

The waitlist toggle is a match-screen control and the match screen is out of scope, so **nothing a
player taps puts her on a standby list**. The write exists as a use case, with the seed catalog as its
only caller — the same shape the four private-owner situations already take
([ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md)'s *"reachable only from seeded
data in v1"*). The named future caller is the **standing rule** that auto-joins matching lists, which
`CONTEXT.md` already describes and nobody has built.

## Consequences

**Easier**

- The seventh act has a card, so ADR-0087's rule about how the enumeration grows held end to end
  rather than half-way.
- `NotOnStandby` can fire for the first time. It has been written, evaluated and tested since the
  funnel shipped, against an adapter that answered the empty set for everybody — and the swap really
  was the one line in the composition root that adapter's docstring predicted.
- The invitation cascade (`#82`) has the store its rung 1 needs. That rung is *"asked for **this**
  match"*, and it is what makes standby worth joining.
- ADR-0070's removal form exists, so `#83`'s offers region inherits it rather than authoring it on the
  busiest write in the product.

**Harder**

- **The enrolled strip is no longer describable as *what you are committed to*.** Four memberships,
  one of which confers nothing, and the region's name now needs the exception said out loud. A fifth
  would be the point at which the region is really two.
- **A queue place with no join surface can only be seeded**, so the demo week is the only place the
  card is reachable, and a bug in the composition would be invisible outside it until `#82` lands.
- **`NowUpdate` is a union on both sides of the wire.** Every future reader narrows, and a client that
  fails to is a type error rather than a blank line — which is the intent, and is still a cost paid by
  a client that only ever wanted the card.
- **A queued player's card is a card about a match she has no stake in.** It counts seats and prints a
  price she has not paid, because it is the match's card rendered for a fourth audience. That is
  ADR-0030's leaver argument applied one membership further out, and it is the reading most likely to
  be revisited.
