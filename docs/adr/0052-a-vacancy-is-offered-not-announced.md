# ADR-0052 — A vacancy is offered, and how loudly depends on how soon the match is

- **Status:** Accepted
- **Date:** 2026-08-20
- **Amended by:** [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md) —
  the **exclusive offer does not ship**. The two modes, the one-hour hold, the three-offer cap,
  the twelve-hour backstop and the *in context, not at launch* permission rule below are all
  superseded; the ordering principle, the channel rules and the screen rules stand. Read 0061
  before implementing the cascade — but read this one first, because it holds the reason the
  open-call wording is not optional.

## Context

A **vacancy** — the unfilled seat a departure leaves — is *"the thing the rescue cascade works"*.
Until now nothing said how a player learns that the cascade reached them. Standby exists as a
situation (`waitlisted` is the one situation only a viewer can be in), and the specification
sketches a position line — *"you are 2nd on the standby list"* — but no mechanism carries a freed
seat from the cascade to a person.

Push notifications were ruled out of this effort **twice**: once for want of a stated requirement
([ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md)), and again on
`Raketa02/Raketa#19` against a stated one, with the cost named and accepted — *a backgrounded app
learns nothing until next open*. What made that affordable was explicit: **the 24-hour deadline,
not a claim that anything is fast.**

An offered seat is the first thing on Now that **expires in under a day**, and the first that is
**contested** — one seat, many eligible players. Both properties break the reasoning that made
deferral safe, and neither can be repaired inside the app: a phone cannot set its own alarm for a
cancellation it has not heard about. The product owner has accepted the provisioning cost and
scoped the channel to this one message.

The mechanism itself has one hard constraint from the product owner: **a seat that is gone must
never be presented as an exceptional card.** That rules out the simplest design — tell everybody
eligible, first to tap wins — under which the exceptional card is a lie for everyone but one
person, every time.

## Decision

**We will treat a vacancy as something offered to a named person, and let the match's own start
time decide how exclusive that offer is.**

### Finding is immediate; telling is scheduled

The cascade runs the instant a departure is recorded, at any hour. **Nothing is dispatched by the
act of finding.** Delivery is a separate, scheduled act, shaped by when the match is and by
whether the recipient can act. This is what removes the pathology of a 02:40 search waking
somebody for a match on Tuesday and expiring while they sleep — the search still runs at 02:40
and the offer waits for 08:00.

### Two modes, chosen by the clock, and the card's wording follows

- **More than 24 hours to the match — an exclusive offer.** One player at a time. The seat is
  genuinely reserved: nobody else can take it, and the card may say so — *a seat is being offered
  to you*. **One hour from delivery**, then it passes to the next person.
- **Inside 24 hours — an open call.** No reservation. The card says what is true — *a seat just
  opened, first to take it* — and is dispatched in **waves**: the top three eligible immediately,
  the next five after ten minutes, then everyone. A 21:00 seat freeing at 20:15 still fills by
  20:40, and because most vacancies are taken in the first wave, the many-disappointed case
  becomes rare instead of routine.

The mode is picked by the match's start time and never by a judgement call. **The exclusive
wording is used only when the seat really is exclusive**, which is the whole discipline: two
wordings exist so that neither has to lie.

### The clocks

- An exclusive hold runs **one hour from delivery to the device**, not from the moment the seat
  freed — a fixed window from the vacancy would routinely be spent entirely asleep. A phone that
  is off or out of signal would freeze the seat, so there is a backstop: **the seat releases to
  everyone at the latest twelve hours before the match**, whichever comes first.
- **Delivery is held overnight to 08:00 local, unless the match starts within twelve hours**, in
  which case it goes immediately. One rule and one exception, both sayable to a player: *we do
  not wake you unless you would miss the game.*
- **Accepting and paying are two acts.** Accepting stops the offer clock and makes the player
  provisionally in; a short second window covers payment, and the seat releases if it is not
  completed. The money mechanics — when a seat is charged, what a failed payment does, what is
  refunded — belong to the money chain and are not settled here; what is settled is the **shape**,
  because the offer clock cannot be specified without knowing whether it must also cover a card
  authorisation.

### Who is offered it, and in what order

**Standby first, ordered by fit within standby; then everyone else eligible, ordered by fit.**
Asking gets a player into the front group; fit picks the order inside the group.

Strict standby-join order was refused: three weeks of waiting is not evidence somebody will turn
up on Tuesday, and a queue that ignores fit fills matches with worse games. Pure fit across
everybody was refused too: if strangers are ranked alongside the people who asked, joining
standby buys nothing and nobody will.

**The consequence is that a standby *position* is not shown.** *"You are 2nd in line"* can rise —
a better-fitting player joining standby overtakes you — and a number that goes up reads as a
promise being broken. The card says **you are on the standby list** and nothing more. A literal,
monotonic position is available only under strict join order, and that is the fill rate it costs.

### On the screen

- **Offers sit above everything**, in their own block at the top of Now — above the shelves and
  above the enrolled strip. An offered seat is not a match the player is in, so it does not belong
  in the strip; it is not a suggestion, so it does not belong in a shelf. It is the one thing on
  the screen that expires.
- **Several offers show as a side-scrolling row, ordered by which expires first** — never by
  which fits best. Hiding an offer somebody waited weeks for because another is sooner costs them
  a game to save a scroll.
- **The row is uncapped, but a player may hold at most three exclusive offers at once.** Beyond
  that, the cascade moves to the next person rather than reserving a fourth seat. Otherwise one
  very active player silently freezes a share of the city's vacancies while they decide, and the
  reservations are invisible to everybody but them.
- **An offer on the screen silences the coral badge**
  ([ADR-0051](0051-now-is-ordered-not-drawn.md)).

### When it is gone, it is withdrawn — silently

The moment somebody else takes the seat, **the delivered notification is removed from the lock
screen and the card disappears from Now.** No second notification. A retraction buzz would mean
every rescue produces one welcome interruption and up to seven unwelcome ones, and the unwelcome
one is the one most players receive most often — which is how a channel gets switched off, and a
player with notifications off cannot be offered seats at all. **A line is written to Inbox** so
the history exists for anybody who goes looking, without interrupting anybody who does not.

### The channel

- **Push is built for exactly one message: a seat you asked for is free.** Nothing else may use
  it in v1. *What else is worth interrupting somebody for* remains a product question that
  scoring must not answer alone, and it returns as its own effort.
- **Several offers dispatching together produce one notification, not one each** — *"3 seats are
  free for you"*, opening Now, where each card keeps its own clock. Three buzzes in one second
  reads as a malfunction.
- **What the notification says: the time and the urgency, never the venue** — *"A seat is free —
  Tue 19:00. Yours for an hour."* The venue is the part that is genuinely sensitive on a lock
  screen read over somebody's shoulder, and it is the part least needed to decide whether to open
  the app.
- **Permission is requested in context, not at launch** — the first time a player joins standby,
  where the reason is self-evident. **If permission is refused, no offer is made to that player at
  all**: the seat goes straight to the open pool and they compete for it like anybody else.
  Holding a seat for somebody who will never learn of it costs the match a fill and gives them
  nothing.

## Consequences

**Easier**

- Standby becomes a real product rather than a list: joining it changes what happens to you when
  a seat frees, which is the thing it always claimed and never did.
- Late cancellations become fillable at all. The alternative was a seat that frees at 20:15 and is
  found by whoever happens to open the app.
- Both routes to the top block — standby, and the future opt-in alerts feature — feed **one
  shape**: *a seat is being offered to you*. Alerts, when built, are a new **source**, not a new
  thing on the screen.

**Harder**

- **Push is now a dependency of Now**, which it deliberately was not. Apple and Google
  provisioning is human work an agent cannot do, and the channel will exist long before the
  policy about what may use it does.
- **The one-message discipline has no enforcement.** Every feature built after this will have a
  reason why its notification is the exception, and the only thing holding the line is this
  record.
- **Two wordings and two modes are four things to keep straight**, and an exclusive wording used
  in open-call mode is a lie the player will discover by losing a seat they were told was theirs.
- **Silent withdrawal can read as a phone glitch.** A notification that vanishes is exactly what a
  malfunctioning app looks like, and the Inbox line is a weak answer because most people will not
  look.
- **A standby position cannot be shown**, and the specification sketched one. Somebody will ask
  for it, and the honest answer is that it would be a number that rises.
- **The twelve-hour backstop can take a seat away from somebody who never saw the offer** — a flat
  battery on Friday costs a Saturday-morning game. The alternative was a dead seat, and this is
  the side of the trade the match needs.

**Neutral**

- The cascade's own logic — who is eligible, what makes a vacancy — is unchanged. This record
  governs how the result of that search reaches a person.
