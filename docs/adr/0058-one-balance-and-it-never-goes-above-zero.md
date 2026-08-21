# ADR-0058 — A player has one balance, and in v1 it never goes above zero

- **Status:** Accepted
- **Date:** 2026-08-21
- **Completes:** [ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md), which created a debt without saying what holds it

## Context

[ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md) decided that a failed
collection *"becomes a debt to Raketa"* and that a debt *"blocks only what creates new
liability"* — no booking a court, no starting a split reservation, but paying for a seat in
somebody else's match stays open. It never said what a debt **is**: a balance, a record, a
collection of unpaid obligations.

`now-section-domain-spec.md` §H.5 assumes the opposite sign as well — a **wallet**. It appears
as *"wallet money is immediate"*, as the thing *"no automatic rule may ever put money in"*, and
as the thing that *"never merges with the club card"*. The spec's own risk register is blunt
about what it costs: *"the wallet is stored value, which is e-money in several jurisdictions
above a threshold; caps, expiry and refundability need a legal answer per market"* — and marks
it as **blocking release in affected markets**.

So the ledger is being asked to hold a signed per-player position whose negative half is
required by an accepted ADR and whose positive half is a regulated financial product nobody has
asked a lawyer about.

## Decision

**A player has exactly one balance — the ledger's own derived per-player position — and in v1 it
may only be zero or negative.**

- **A debt is that balance, not a separate record.** So *"why do I owe 30 zł"* is answered by the
  same movements that answer *"what was I charged"*, from the same stream
  ([ADR-0055](0055-the-ledger-is-event-sourced-one-stream-per-player.md)), with the causes that
  say why ([ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md)).
- **No wallet, no stored value, no platform credit.** This keeps Raketa clear of e-money
  regulation entirely, and it satisfies §H.5's *"no automatic rule may ever put money in the
  wallet"* by leaving nothing to put it in. The one thing it has to absorb is the checkpoint
  credit on `cancelledCheckpoint` — a **club-initiated** act (`I-12`) — which becomes a **club
  card** entry. The club card and a balance never merge, which is the invariant §H.5 already
  stated for a wallet, now true by construction.
- **No line items, no ageing, no allocation.** A payment against a debt is one movement with
  cause `debtCleared`, and the number moves. FIFO allocation, per-obligation ageing and partial
  settlement are the machinery **debt write-off and escalation** would need — a question
  ADR-0047 deliberately stops short of and this map rules out of scope. Building its substrate
  here is how out-of-scope work arrives through the back door. Provenance is not given up: a
  debt reads back to the seat that caused it through `collectionFailed`, which names its
  reservation.
- **Now shows a debt, in one line, and it is the only money the ledger ever puts on Now.** A
  player who owes cannot create a match or book a court, and Now renders the create tab — so
  without the line they meet the block as a refusal. It rides as a **fact on the composed
  screen**, never as a situation
  ([ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)): it is
  not a match and has no rung on the ladder. The sentence is written client-side like every
  other. **This is a line the `GET /now` wire contract must carry**, and it is recorded here so
  it is not decided twice.

## Considered options

- **A wallet in v1, with the debt as its negative half.** One symmetric concept, and it makes
  refunds instant. Rejected on the spec's own risk entry: stored value is a regulated product,
  it needs a per-market legal answer, and it would gate release on a question that has nothing to
  do with playing padel.
- **Debt as its own aggregate, with line items.** What a collections system needs, and the shape
  the ledger would eventually feed. Rejected as scope: it is the substrate for escalation and
  write-off, and those are out of scope by name.
- **No balance at all; a debt is a flag plus an amount on the player.** Cheapest, and it is a
  number with no explanation behind it — the exact failure ADR-0034 pointed at the ledger to
  avoid.

## Consequences

**Easier**

- **One number, one sign, one query.** A balance below zero blocks; a balance at zero does not.
- **E-money regulation is not on the release path**, and the decision is recorded rather than
  discovered by whoever asks a lawyer first.
- **A debt explains itself** from the movements that created it, with no second store to keep in
  step.

**Harder**

- **There is nowhere to put goodwill.** Raketa cannot issue credit to a player it has
  inconvenienced — only a club can, through its card. The first support incident that wants to
  say *sorry, have 20 zł* has no mechanism, and reversing this is a regulated-product decision,
  not a feature.
- **A partial payment against a debt has no defined meaning beyond moving the number**, so a
  player who owes for two reservations cannot be told which one they have just cleared. That is
  fine while debts are rare and small, and it is the first thing collections would have to add.
- **Now gains a money line**, on a screen whose stated invariant is that it never charges
  anything (`I-13`). The invariant survives — the line is informational and navigational — but it
  is the first money the ledger has ever put on the home screen, and it will attract more.
