# ADR-0062 — A notification is a prompt to look, and Now is the only surface that states what is true

- **Status:** Accepted
- **Date:** 2026-08-21
- **Amends:** [ADR-0052](0052-a-vacancy-is-offered-not-announced.md) — its **silent
  withdrawal** rule (*"the delivered notification is removed from the lock screen"*) and its
  **Inbox line**. Its screen rules, its ordering and its channel discipline stand.
  Also amends [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)'s
  notification **wording** and its *"several offers dispatch as one notification"* rule, which
  is widened from one dispatch to one **live** message per player.

> **Scope note.** [ADR-0067](0067-the-quiet-replacement-is-evidenced-and-the-extra-message-waits.md)
> **lifts the provisional rule below.** `passive` silencing a collapse *replacement* has since
> been measured through the field Apple documents a remote `apns-collapse-id` becomes, and this
> record is no longer conditional on anything. Read two corrections with the *"This is
> provisional on one measurement"* paragraph: its recorded fallback — *"if it buzzes, every
> replacement buzzes"* — was **replaced** by
> [ADR-0065](0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md),
> and its *"Apple switches that off during testing"* worry cites the **silent-push power
> budget**, which has no `interruption-level` equivalent. The measurement it carries on
> [#26](https://github.com/Raketa02/Raketa/issues/26) moved to
> [#37](https://github.com/Raketa02/Raketa/issues/37) when that ticket split. Everything else
> here stands as written.

## Context

[ADR-0052](0052-a-vacancy-is-offered-not-announced.md) made withdrawal silent, and rested it
on one sentence: **"the delivered notification is removed from the lock screen."**
[Raketa02/Raketa#25](https://github.com/Raketa02/Raketa/issues/25) established that the
capability does not exist.

**No platform offers server-side removal of a delivered alert as a guarantee.** Apple
documents *replacement* and documents removal **nowhere** — the only lock-screen retraction in
its docs is Live-Activities-only. The one path that removes is a silent push waking the app,
and Apple attaches to it *"the system doesn't guarantee their delivery"*, a two-or-three-per-hour
ceiling, death on force-quit, and the line that decides it: **"These limits are disabled when
testing your app from Xcode."** A withdrawal built that way passes every manual test and fails
in the field, invisibly. Android can cancel, but only by posting the offer **from the app
process** rather than letting Play services display it — which makes the offer die with the
app and puts the sender on a seven-day deprioritisation window. Offline is worse than either:
APNs may reorder, stores one notification per bundle id, and says last-write-wins *"isn't
always guaranteed"* — so a retraction can be evicted **by** the offer it was sent to cancel,
leaving a stale offer on a lock screen indefinitely.

Two things about the surrounding design made this bigger than a mechanism swap.

**The constraint was written for one surface and applied to two.** ADR-0052's hard rule — *a
seat that is gone must never be presented as an exceptional card* — holds for the card, because
Now re-reads. The lock screen is a copy the server cannot reach. The record reasoned about one
surface and shipped two.

**[ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md) multiplied the
cost.** With the exclusive offer gone, every eligible player is told at once, so one filled seat
leaves **N−1** stale notifications rather than one. Any mechanism that produces a second buzz
now produces thirty-nine of them — the exact interruption ADR-0052 spent its whole withdrawal
design to avoid.

## Decision

**We will stop trying to take a notification back, and stop it ever making a claim that can go
stale.** A notification is a **prompt to look**; **Now** is the only surface that states what is
currently true.

### The wording carries the retraction

The lock screen says what **happened**, never what **is**: *"A padel seat just opened — Tue
19:00, 20 min away. First to take it."* That sentence was true at 16:42 and is still true at
midnight and is still true after somebody else takes the seat. There is nothing to withdraw,
because nothing was claimed.

This is the same move ADR-0061 made for the card. The product owner's constraint is kept by the
**wording** on both surfaces — the only difference being that Now can also keep it by re-reading,
and the lock screen cannot keep it any other way.

**The consequence is that our messages accumulate rather than expire.** Ania's Tuesday line is
still on her lock screen on Wednesday, after the match has been played — true, and dead. Nothing
on either platform lets us clear it; the only tool is another message. Sweeping it would cost a
notification per player per match that ever offered them a seat, to fix something a swipe fixes.
**We live with it.** The collapse rule below is the only thing that ever cleans up.

### One live message per player

We occupy **one line** on a player's lock screen, ever. A new seat's message **takes the previous
one's place** rather than stacking beside it. With no frequency cap in v1, this collapse **is**
the frequency control.

**Which seat the line names: a seat the player asked for outranks one we chose for them;
soonest-to-expire decides inside each group.** The rest are a count — *"+2 more"* — and the
opening clause (*the seat you asked about* · *a match you looked at* · *a seat near you*) belongs
to whichever seat is named.

This **deliberately differs** from the offers row on Now, which is ordered soonest-to-expire and
nothing else ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md)). The two are doing different
jobs: the row shows **every** offer, so its order only decides how far somebody scrolls; the lock
screen shows **one** and hides the rest, so its order decides which seat they learn about at all.
Ranking purely by urgency is right when nothing is hidden and wrong when everything else is.

### Only a seat you asked for may buzz

- **A standby seat interrupts.** It buzzes, every time, and it takes the line — so the
  interruption's cause is always the thing on the screen it produced. An interruption whose cause
  is hidden behind *"+2 more"* is a broken interruption.
- **A seat we picked for the player updates the line silently** — rungs 3–7, the players who
  never asked. The count changes; the phone does not light up.

**Asking is what buys the interruption.** A standby player's head start is ten minutes and nothing
on the screen shows it; this is the second thing joining a list actually buys.

**This is provisional on one measurement, and only this rule is.** Apple documents
`interruption-level: passive` and documents `apns-collapse-id`, and **never documents the two
together**. Whether a passive collapse-*replacement* is genuinely silent is a fact about devices.
Before this ships, one message goes to one real iPhone with both set and somebody watches whether
it buzzes. **If it buzzes, the fallback is that every replacement buzzes** — noisier, but every
buzz is still a real seat, and it needs nothing measured. What we may not do is assume it works:
that assumption is one Apple switches off during testing, so it would pass every check we run and
fail on the player's phone. Carried on
[#26](https://github.com/Raketa02/Raketa/issues/26).

### The tap re-reads, and the app says so once

**The notification carries no truth.** A tap re-evaluates the match's live state, and the seat is
simply joinable or not.

**When it is not: one plain line at the top of Now — *"That seat has gone."*** Not a card, no
action, no tap target; it fades. A card is what a takeable seat wears, and a gone seat in card
shape is exactly what the constraint forbids.

**One rule covers every way a player meets it:** *the first time they arrive on Now after a match
they were told about has no room for them, they get the line — once.* The notification tap, the
cold open two hours later, and the card evaporating mid-scroll are the same rule firing at
different moments. A seat they were **never** told about produces nothing, ever.

### What they were told about is the match having room, not one seat

Marek's seat and Zofia's seat are not distinguishable to somebody who was told *"a padel seat just
opened"*. So **the line fires only when the match has no room left for that player** — if a second
seat freed while they were away, they get the live card and nothing else.

Greeting somebody with a disappointment stacked on top of a seat they can take right now is a lost
fill and reads as a malfunction. This is what the past-tense wording implies: we describe an
**opportunity**, not an object.

### Both platforms do the same thing

Android can genuinely cancel a delivered message and we **decline to use it**. The capability costs
an offer that dies when the app is swiped away, and it buys a second behaviour to keep straight
forever. Past-tense wording behaves identically on every phone, so after this record there is
nothing left to diverge about.

### No Inbox line

[ADR-0052](0052-a-vacancy-is-offered-not-announced.md)'s Inbox line was written to be the **only**
trace, and its own record called it *"a weak answer, because most people will not look"*. It is not
the only trace any more. **It does not ship.** Inbox holds what other people and clubs are asking of
you; a seat you did not get is nobody asking you anything, and a screen quietly filling with losses
nobody requested is a worse artifact than no record at all.

## Consequences

**Easier**

- **Withdrawal stops being a mechanism.** No silent pushes, no cancel calls, no reconciliation for
  a retraction that raced its own offer. The N−1 fan-out ADR-0061 created costs nothing, because
  nothing is sent.
- **One channel behaviour for both platforms**, and it is the one that survives a flat battery, a
  force-quit and an offline queue — the three cases every removal design fails.
- **The lock screen can never lie**, so it can never be the surface that breaks the no-gone-seat
  constraint. That question is closed rather than mitigated.
- **The frequency problem was solved by the same rule as the staleness problem.** One live message
  is both.

**Harder**

- **Our notifications accumulate.** A player who is offered seats all week and swipes none carries
  a true, dead line for a match that has already been played. We have no way to clear it and have
  chosen not to spend a message trying.
- **The silent update rests on an undocumented combination**, and the fallback is a noisier product.
  This is the one thing on this record that ships provisionally.
- **The collapsed line hides seats.** Three live offers, one named: two seats exist that the player
  learns about only by opening the app. Under the old stacking behaviour they would have seen all
  three — and would have been buzzed three times.
- **The lock screen and the offers row order differently**, which is two rules where there was one,
  and somebody will read it as an inconsistency before they read the reason.
- **A player who loses a seat learns nothing until they next open Now**, and then only once. There
  is no durable record anywhere that they were offered a seat and missed it.

**Neutral**

- The ladder, the pool, the two dispatches, the 08:00 hold, the fit floor and the price phases are
  untouched. This record governs **what a notification may claim and what happens to it afterwards**.
- The transport choice is untouched: everything here — collapse ids, quiet delivery, past-tense
  copy — is expressible through Expo's push API and through bare APNs/FCM alike
  ([#25](https://github.com/Raketa02/Raketa/issues/25)).
