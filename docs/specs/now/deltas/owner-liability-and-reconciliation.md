# Spec delta — the owner's liability, and the one moment a private booking settles

Resolves [#18 — The owner's hold: when it is captured, and what happens to a seat nobody ever
pays](https://github.com/Raketa02/Raketa/issues/18).

Governed by [ADR-0045](../../../adr/0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md),
[ADR-0046](../../../adr/0046-one-reconciliation-two-hours-after-the-reservation-ends.md) and
[ADR-0047](../../../adr/0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md).

---

## 1. The hold does not exist

`3.1` ADJACENT and [ADR-0030](../../../adr/0030-a-departure-is-an-audience-not-a-state.md)
describe a guarantee *"held against the owner's account"*, decreasing as shares arrive. Both
halves are withdrawn.

**What governs:** Raketa holds no money before reconciliation. At booking the owner pays their
own share and their card is saved with **explicit consent** to charge unpaid shares later. There
is no pre-authorisation, so there is nothing to capture, renew, lapse or release — the entire
lifecycle the ticket asked about stops existing.

`3.1` ADJACENT's *"commitment runs purely on the clock because there is no group to complete"*
loses its money role entirely. It describes when a private court's reservation becomes
uncancellable, and nothing else.

## 2. The guarantee is the whole court and it does not move

**What governs:** `guarantee = courtPrice`, constant from booking to reconciliation. Not a
remainder, not derived from funded seats.

- An **invited** player's share releases it permanently, złoty for złoty, on payment.
- A **marketplace** share is **provisional coverage**: paid through to the club, releasing
  nothing, because it is refundable until the sold format is met.
- The club is **only ever paid, never debited**. A marketplace refund is Raketa's cash flow,
  recovered from the owner at reconciliation.

**This is what the card must print.** [#17](https://github.com/Raketa02/Raketa/issues/17)
already required the whole court price; under the shrinking model the printed number and the
guaranteed number diverged. They no longer can.

## 3. One reconciliation, at `reservationEnd + 2 h`

**A new timekeeper boundary**, alongside `d.commit`, `d.check`, `d.rescue` and rung 9's
`vacatedAt + 24 h`.

Nothing crystallises before it:

- **No pre-match cutoff kills a converted match.** The seat sells until match time.
- **A converted court at 3/4 is not cancelled.** The reservation is bought and stays active; the
  players present may use it.
- **The owner is not charged at the club's cancellation deadline.**

The two hours are a **reconciliation window** with a stated job: a share may still be paid
online, and a share paid **at the club counter** may still be marked paid by the club. At its
close, exactly two movements:

| Condition | What happens |
| --- | --- |
| Sold format was met | Every share is already collected. **Nothing happens.** |
| Sold format never met | Every **marketplace** joiner refunded in full; owner charged everything outstanding |

Pre-opening payers are never refunded — unchanged from
[ADR-0044](../../../adr/0044-a-marketplace-seat-is-a-promise-of-a-game.md).

**A share reported after reconciliation reimburses the owner.** No new rule: the seat's last
funder was the owner ([ADR-0042](../../../adr/0042-a-share-returns-to-the-seats-last-funder.md)).

### `3.1` §3.6 and §6.1 — the checkpoint does not apply to a private court

ADR-0030 said no checkpoint can *cancel* a private court. Stronger now: a private court, opened
or not, **has no checkpoint at all**. The `check` row branches only on the open path.

## 4. Paying at the club is for invited players only

A marketplace seat is bought from Raketa, online, always. A refundable seat's money must sit
somewhere Raketa controls — otherwise we owe a refund on money we never held, recoverable only
from a club we have promised never to debit.

## 5. The lock, unchanged and now explained

Once a converted court is **full** and past the club's cancellation deadline: nobody leaves, no
refunds. Before the lock a marketplace joiner may **withdraw and be refunded freely**, which
costs the owner nothing because their payment never reduced the guarantee.

The justification belongs in the copy: **a stranger joining a converted private court is buying a
court that definitely exists**, which an open match cannot sell. That is what makes the
commitment fair, and it is the strongest thing on this path.

## 6. What the owner sees — four messages, two of which change outcomes

| When | What | Job |
| --- | --- | --- |
| At booking | Split means you are the booking owner and liable for unpaid shares; consent taken here | Inform |
| Throughout | Standing **Paid / Pending** view per player inside the reservation | Inform |
| **At the club's cancellation deadline** | *N seats unpaid; after today you cannot cancel for free and you are liable for the whole court* | **Act** — cancel free, chase a friend, or open the seat |
| **Before the charge** | What is about to be taken and why | **Act** — and turns the amount from an ambush into an expectation |

Plus a **player** reminder one hour before the match starts to everyone who still owes.

The deadline message is the only one in the whole flow that arrives while the owner can still
change the outcome.

## 7. Roster relief for an unpaid invited seat

- An owner may **revoke an unpaid invite at any time**. A held seat is a name with no money;
  [ADR-0043](../../../adr/0043-opening-a-court-is-the-private-paths-commitment.md) already
  requires them cleared before opening.
- **An invite carries a lapse clock**, so a held seat cannot ride silently to the deadline. It is
  what makes the deadline message possible.
- There is **no cheaper money instrument than opening the court**, which stays irreversible.
  Anything reversible re-opens the door ADR-0043 shut.

## 8. A failed charge is a debt, not a crisis

The club is whole and the match already happened. The owner owes Raketa, and the debt blocks
**only acts that create new liability** — booking a court, starting a split. Paying for a seat in
someone else's match stays open: it is money up front, it carries no risk, and blocking it makes
the debt harder to clear.

**Booking horizon: two weeks, uniform** — solo, split and open-match creation alike.

## 9. What is deliberately not decided here

- **The strings.** Client-owned
  ([ADR-0041](../../../adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)).
- **Write-off and escalation** — how long a debt sits, whether it is pursued beyond blocking, and
  who decides. A collections question, and it must not be answered by whoever builds the block.
- **The club-side mechanism for marking a cash share paid** — a club console surface, out of this
  map's scope. What is fixed here is that the mark is authoritative and that the window waits
  for it.
- **The PSP.** Saving a card, taking consent and charging later are mechanisms; the decisions
  above are ours.
