# ADR-0030 — A departure is an audience, not a state

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

A player who leaves a match after paying for a seat occupies the single most money-bearing
position in the Now model, and the specification set has no state for them. The architecture
review names it as finding **B3** — *"There is no state for the player who left, and it is the
money-bearing one"* — and proposes adding five keys to fix it.

Executing the v37 resolver showed the diagnosis is close but wrong in a way that changes the
fix. `m.left` is written in three places and read in exactly **one**: the Now strip's own
predicate, `filter(m => mySeat(m) && !m.left && …)`. The leaver is not in a wrong state; they
are *deleted from the screen* at the moment their money is undecided. Reach the card by URL
anyway and it addresses them as a stranger — *"Your share **would be** 38,00 zł"*, the
conditional tense, offered to somebody who has already paid, with the refund described in the
third person. Meanwhile the state document promises the opposite: *"neither removes the card
immediately, because the explanation is the point."*

The outcome is genuinely undetermined when they leave. Four positions are reachable — 100 % if
a full-price replacement pays, 50 % if a rescue player takes the seat, 0 % if the match plays
short, and forfeiture if the checkpoint cancels at a rebooking club — and the player was shown
all four before leaving. The one surface that could track which one landed renders none of them.

Two further defects compound it. `vacated` is a **scalar**, so a second departure overwrites the
first and erases that leaver's refund position entirely — with four seats, a four-hour rescue
window and a group that often knows each other, a second departure is a normal Saturday rather
than an edge case. And three separate states each claim to be *"the only outcome in the model
where a player loses money."*

The alternatives considered:

**Add the five keys B3 proposes** — `leftReversed`, `leftSearching`, `leftRefunded100`,
`leftRefunded50`, `leftForfeited` — taking the model from 35 contexts to 40. This encodes a fact
about the *departure* as a fact about the *match*: `leftRefunded100` and `leftRefunded50`
describe a match that is `confirmed` in both cases, differing only in what happened to somebody
who is no longer in it. Two cards for one match then have to be kept in step by hand, which is
exactly how they drift.

**Leave the card filtered and explain the refund elsewhere** — a notification, or the Inbox.
This is the cheapest option and it is the one where the player never learns whether they were
refunded, because the only surface that tracks the seat is the one they were removed from.

**Render by audience.** The match resolves to its one state; the card is rendered for the
viewer's relationship to it. The model already does this twice — the non-member rewrite, and
`confirmResult`, which the state document itself calls *"player-relative in a way no other state
is."* The mechanism is not being invented.

A separate force applies to private courts, and it pulls the other way from the open-match
rules. On an open match the commitment deadline marks the moment a court stops being *held* and
becomes *bought*: before it, reversal is free because releasing a hold costs nothing. A private
court is **bought at booking**, so that moment has already passed before the first share is
paid. Applying the open-match deadline there refunds a share out of money the club is keeping,
and the difference lands on the owner — who is then underwriting everyone else's free
cancellation. Nobody books a second private court after that happens once.

## Decision

**We will model a departure as a record, and the leaver as an audience on the match's own
state.** The context count stays at **35**. A departure carries the seat, the player, the time,
**the amount they paid**, and its outcome; the leaver's card is the match's card rendered for
somebody who used to hold a seat.

**We will replace the `vacated` scalar with `vacancies[]`.** Two departures produce two
vacancies, each settling on its own clock, and the recovery group's facet becomes honest —
*"2 of 4 · two seats stay funded"* rather than silently reporting one vacancy while two exist.
The cascade runs one process per vacancy. When a filler arrives, **FIFO by `vacatedAt`** decides
whose departure it settles.

**We will keep the leaver's card until the outcome settles, then for the same 24 hours a played
match gets.** The predicate becomes *I hold a seat, **or I held one and its outcome is not yet
settled***. An outcome **settles** when no further *seat* event can change it — at the checkpoint
for a rebooking club, at the join cutoff for a standard one, never at match end. Settlement is
**monotonic upward**: a club-side failure that refunds everybody may improve a settled 50 % to a
full refund; nothing may reduce a settled outcome.

**We will record the amount paid on the departure rather than re-deriving it.** After commitment
the seat stays paid and the amount is still recoverable; before commitment the seat is cleared
*and* unpaid, so there is nothing left to derive from and the card can name no amount at all.

**We will never offer a leaver the result-entry or confirm-result affordance.** Scoring is a fact
about who was on court. This is the same rule that fixes finding B2, where a standby player is
asked to score a match they did not play.

**We will treat private courts as a different money model, not a variation on this one:**

- **No commitment deadline.** A share is final the moment it is paid, refunded only when
  somebody takes the seat.
- **Two outcomes, not four** — 100 % if anyone takes the seat, 0 % if nobody does. No 50 % tier:
  the discount exists to save a court that would otherwise be lost, and nothing is at risk here.
  No forfeiture: no checkpoint can cancel a private court.
- **The owner cannot leave.** Leaving is vacating a seat while the match survives; an owner
  vacating orphans the guarantee that *is* the match's court. This is the one departure the model
  refuses. Cancelling the whole booking is a different act, governed by club terms.
- **`guarantee = court price − Σ(funded seats)`**, derived and never tracked, held against the
  owner's account rather than paid to the club. Because a funded seat never becomes unfunded, the
  guarantee only ever **decreases** — no departure can re-expose the owner.
- **Solo and split fork at booking.** A solo booking is a traditional court booking, paid in
  full; adding friends afterwards is a roster act with no money attached.
- **Opening a seat to the marketplace requires unanimous consent** from the currently-paid
  players, the same bar the cascade's consent stages use. **Inviting a named person requires
  none**, and any participant may do it.

**We will restate the money-loss claim** as *the only outcome where a player **who stayed** loses
money*, which is what makes the checkpoint exceptional and what was presumably meant.

**We will give destructive commands a command log keyed `(command, idempotency key)`** with a
24-hour expiry, rather than keeping an idempotency key on an emptied seat or answering a replay
from the departure record.

## Consequences

**The context count does not move**, so the resolution ladder, the tag mapping and the
conformance suite are untouched. The cost lands instead on the card renderer, which now takes
the viewer's relationship to the match as an input — a change every client pays for, including
in the states where the answer is "render it exactly as before".

**Two findings collapse into one fix.** B2 and B3 are the same defect — the result flow offered
to people who did not play — and the audience model closes both. B7 and B8 are resolved here too.

**A departure is a first-class record, which the model did not previously have.** That is a new
persisted concept with its own identity and lifecycle, and it must exist before the Matches
aggregate is written, not bolted on afterwards. It is also the thing that makes two simultaneous
leaves expressible at all.

**A leaver's card can now outlive the match.** In the cancelled case the card is showing an
answer about money for a match that no longer exists. This is correct — the money question
outlives the match — but it means "the match is gone" can no longer be assumed to mean "the card
is gone", and any cleanup that walks matches will strand departures unless it walks those too.

**Monotonic settlement means an outcome is not final when it is displayed as final.** A card can
say "refunded 50 %" and later say "refunded in full" because the club lost the court. Clients
must not cache a settled outcome as immutable, and the copy must not promise finality it does not
have.

**Private courts now diverge from open matches in the money model**, which is a second set of
rules to hold in one's head and a second set of paths to test. The compensation is that the
private rules are strictly simpler — two outcomes, no deadline, no cascade, no checkpoint — and
that the alternative was a model in which booking a private court exposed the owner to other
people's cancellations.

**Refusing the owner's departure is a refusal the system must actively make.** Today nothing
refuses it, so this is new behaviour rather than a documented default, and the failure mode if it
is missed is an orphaned guarantee on a court nobody is responsible for.

**Unanimous consent to open a seat puts three people between a leaver and their money.** That is
a real cost, chosen deliberately: the others bought a game with people they selected, and that is
the thing being changed. The leaver's card deliberately does **not** show the pending consent
request, because it would become pressure aimed at their friends that they cannot act on.

**The command log needs an expiry rule and a home.** A 24-hour window is chosen because the
failure it guards is HTTP-retry-scale rather than outbox-scale, but it is a new table, a new
write on every destructive command, and a new thing to prune.

**Two questions are left open on purpose**: what a marketplace share pays for on a solo-booked
court that is already fully funded, and when the owner's hold is captured or released for seats
nobody ever pays. Both are tracked as wayfinder tickets and neither disturbs anything decided
here.
