# ADR-0046 — One reconciliation, two hours after the reservation ends

- **Status:** Accepted
- **Date:** 2026-08-20
- **Supersedes:** the checkpoint trigger in [ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md)
- **Narrows:** [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) — a private court has no checkpoint at all, not merely one that cannot cancel it

## Context

[ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md) put the private path's money event
at the **checkpoint**, T−2h: an unmet sold format refunds every marketplace payer and the owner
carries the court. It argued the case explicitly — *"it resolves before the match, not after.
Three people do not turn up to a padel court and then get refunded."*

Working the owner's side of that rule broke it. Two hours before play the seat **can still sell**,
and a Saturday-morning sale is exactly the sale that saves the game. Refunding at T−2h gives up
on a match that may yet fill; refunding at the join cutoff gives up on it thirty minutes later.
Either way we crystallise an answer we do not have.

Worse, crystallising the owner's charge early makes a single seat touch her card three times. If
we charge her 30 zł at the club's deadline for an empty seat, and Zofia buys it on Saturday
morning, the seat's last funder is the owner and she must be reimbursed
([ADR-0042](0042-a-share-returns-to-the-seats-last-funder.md)). If a *different* seat is then
still empty and the game fails, Zofia is refunded and the owner is charged again. Every movement
is individually correct and the sequence is indefensible at a support desk.

There is also a payment channel the model had not accounted for: **a player can pay their share
at the club counter**, and the club marks it paid. That reconciliation is not instantaneous, so
any moment we pick before the club has reported is a moment where we may charge an owner for a
share that was already settled in cash.

The governing constraint is stated plainly: *if the rules are not clear enough, players leave the
platform.* A money model whose correctness depends on a sequence of compensating movements is not
a model a player — or a support agent — can hold in their head.

## Decision

**We will settle a split-payment reservation exactly once, two hours after the reservation ends,
and at no earlier moment.**

- **Nothing crystallises before then.** No pre-match cutoff kills a converted match, no charge
  lands on the owner at the club's cancellation deadline, and the seat keeps selling until match
  time. A converted court that reaches only 3/4 is **not cancelled** — the reservation is bought
  and it remains active; the players present may use it.
- **The two hours are a reconciliation window with a stated job**, not a generic dispute buffer.
  During it a share may still be paid online, and a share paid **at the club** may still be
  marked paid by the club. Only at its close do we determine what remains unpaid.
- **At its close, two movements and no others.** Every **marketplace** joiner is refunded in full
  if the sold format was never met; the owner is charged everything still outstanding. If the
  match filled, all shares are already collected and nothing happens at all.
- **Paying at the club is available to invited players only.** A marketplace seat is bought from
  Raketa, online, always. A refundable seat's money must sit somewhere we control — otherwise we
  owe a refund on money we never held, recoverable only from a club we have promised never to
  debit ([ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)).
- **A share reported after reconciliation reimburses the owner.** No new machinery: the seat's
  last funder was the owner, and a paid share returns to the seat's last funder
  ([ADR-0042](0042-a-share-returns-to-the-seats-last-funder.md)).
- **The lock survives unchanged.** Once a converted court is **full** and past the club's
  cancellation deadline, nobody may leave and no refunds are issued — a stranger joining a
  converted private court is buying a court that **definitely exists**, which an open match
  cannot sell, and that is what makes the commitment fair. Before the lock, a marketplace joiner
  may withdraw and be refunded, which costs the owner nothing under ADR-0045.

## Considered options

- **Keep the T−2h checkpoint and close the sale there.** No churn, and it discards every
  Saturday-morning sale — the sales most likely to rescue the match.
- **Keep the T−2h checkpoint and let the owner's charge churn.** Every movement correct, three
  card movements on one seat, and a support conversation nobody can win.
- **Refund at the join cutoff, collect from the owner later.** Tells the marketplace player
  before they travel, and splits one settlement into two moments — reintroducing the complexity
  this decision exists to remove.

## Consequences

**Easier**

- **One moment, one rule, one sentence**: *whatever the court did not collect, the owner pays,
  two hours after your slot; if the game never filled, everyone who bought a seat gets their
  money back at the same moment.*
- **The last-minute sale is preserved** — the match can fill right up to the start.
- **The owner's card is touched once.** No reimburse-then-recharge sequence exists to explain.
- **The club's cash channel is legitimised** rather than being a hole in the model.

**Harder**

- **A marketplace player who never got a game waits.** A 14:00 slot ending at 15:30 refunds at
  17:30 — around three and a half hours after they expected to play, and they may travel to a
  court for a game that does not happen. Accepted because until match time the seat genuinely can
  still sell, so there is no earlier moment at which we honestly *know*. What can and should
  arrive earlier is **information**, which moves no money.
- **A new deadline for the timekeeper** — `reservationEnd + 2 h` — alongside `d.commit`,
  `d.check`, `d.rescue` and rung 9's `vacatedAt + 24 h`.
- **The club becomes a participant in settlement**, not merely a payee. A club that never marks
  a cash share paid causes an owner to be charged for money the club is holding.
- **ADR-0044's reasoning is reversed on its own example.** Three people *do* now turn up to a
  padel court and get refunded afterwards. Its substance — a marketplace seat is a promise of a
  game, and pre-opening payers are never refunded — is untouched; only its moment moves.
