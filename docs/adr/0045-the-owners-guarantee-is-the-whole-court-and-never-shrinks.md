# ADR-0045 — The owner's guarantee is the whole court, and a share is provisional coverage

- **Status:** Accepted
- **Date:** 2026-08-20
- **Supersedes:** the `guarantee` money model in [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md)
- **Dissolves:** the bounded invariant in [ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md)

## Context

[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) modelled a split-payment private
court as a **shrinking** exposure: `guarantee = court price − Σ(funded seats)`, held against the
owner's account, decreasing złoty for złoty as each share arrives. Every subsequent decision has
been spent patching the consequences of that one sentence.

[ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md) had to bound it — a marketplace
payer is refunded when the sold format goes unmet, so the guarantee jumps back to the whole court
price and *"only ever decreases"* survives only *"while the match is alive"*. That bound is the
tell. A number that shrinks as money arrives and then leaps back to its starting value is not a
model of anything; it is a running total dressed as a liability.

The arithmetic makes the defect concrete. Ania books a 120 zł padel court, split four ways, and
pays her own 30 zł. She opens two seats; two strangers pay 30 zł each. Under the shrinking model
her exposure now reads 30 zł. The fourth seat never sells, so the strangers are refunded 60 zł
and her true exposure was 90 zł all along. Whatever instrument was standing behind the 30 zł —
an authorisation, a saved card, a promise — is short by 60 zł at exactly the moment we have
already paid the strangers out and can no longer decline.

Three further problems fall out of the same root:

- **The card cannot tell the truth.** [Issue #17](https://github.com/Raketa02/Raketa/issues/17)
  already required Ania's card to print *the whole court price*, because two of four seats sold
  reads as 60 zł while the worst case is 120 zł. Under a shrinking guarantee the number we
  display and the number we stand behind are different numbers, and the gap is only discovered
  on the Saturday it matters.
- **A stranger's withdrawal re-exposes the owner.** If a share reduces the guarantee, taking that
  share back must raise it. That is the re-inflation the model has been trying to forbid.
- **Refunds have to be clawed back from the club.** Shares are paid through to the club as they
  arrive. If the owner's exposure has fallen accordingly, then a refund has to come out of money
  the club is already holding.

## Decision

**We will treat a split-payment owner's guarantee as the whole court price, from booking until
the reservation is reconciled, and never as a shrinking remainder.**

- **A share that arrives is *provisional coverage*, not a reduction.** It is paid straight
  through to the club exactly as before. What it does **not** do is release any part of the
  owner's liability while a refund of that share is still possible.
- **An invited player's share releases the owner permanently, the moment it is paid.** Those
  payers are never refunded ([ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md)), so
  nothing can bring the liability back. The two kinds of payer already differ on refundability;
  this is the same line drawn on the guarantee.
- **A marketplace share never releases the owner before reconciliation**, because until then the
  game may fail to fill and the money goes back.
- **The club is only ever paid, and never debited.** Every refund and every shortfall is Raketa's
  own cash flow, recovered from the owner at reconciliation
  ([ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md)). A player's
  change of mind can never reach into a club's account.

**`guarantee` stops being a computed remainder and becomes a constant** — the court price — for
the whole life of a split reservation that has not filled. What varies is not the owner's
liability but how much of it has already been covered by somebody else's money.

## Considered options

- **Keep the shrinking guarantee and hold a residual.** Capture the unfunded part early and fence
  the marketplace-funded part separately until the refund risk passes. Correct, and it was the
  first proposal — but it needs two instruments, two release rules and a second charge path, to
  express something a constant expresses for free.
- **Keep the shrinking guarantee and re-charge on the jump.** Cheapest to build and it puts a
  collection risk precisely where we have just paid strangers out. Rejected: the one moment the
  model must not be able to fail is the moment it is most exposed.

## Consequences

**Easier**

- **The number the card prints is the number we stand behind**, from booking to reconciliation,
  with no divergence to reconcile and no moment where it moves.
- **A marketplace player may withdraw freely before the lock at no cost to the owner** — their
  payment never reduced the owner's liability, so returning it cannot raise it. The withdrawal
  right in [ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md) is
  affordable only because of this ADR.
- **The re-inflation question disappears rather than being answered.** Nothing shrinks, so
  nothing can be re-inflated, and the *"a funded seat never becomes unfunded"* invariant stops
  being load-bearing for the owner's exposure entirely. ADR-0044's bound on it becomes a
  statement about refunds, not about liability.
- **The club is structurally insulated.** "Paid, never debited" is one sentence and it is true of
  every path.

**Harder**

- **The owner's headline liability never falls as the court fills**, which reads as unfair to
  someone watching three friends pay. The mitigation is entirely in the interface: the
  Paid/Pending view shows coverage moving even while the guarantee does not.
- **Raketa carries the float.** Refunding a withdrawing marketplace player out of our own money
  and recovering it later is a real working-capital cost that the shrinking model pushed onto the
  club.
- **`guarantee` as a derived field is gone**, and any reader expecting it to change as seats fund
  is now wrong. It is a constant with a lifetime, not a running total.
