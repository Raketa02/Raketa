# Spec delta — the private court's money, and what opening it costs

**Governs over** `3.1-enrolled_match_states_and_transitions.md` ADJACENT (the four private
states), and over the `privateOpen` and `privateReserved` rows in
`rakieta-now-section-specification.md` §7 and `rakieta-now-section-ui-spec.md` §B6. Everything
else in those documents stands unchanged.

**The decisions:** [ADR-0042](../../../adr/0042-a-share-returns-to-the-seats-last-funder.md),
[ADR-0043](../../../adr/0043-opening-a-court-is-the-private-paths-commitment.md),
[ADR-0044](../../../adr/0044-a-marketplace-seat-is-a-promise-of-a-game.md).
**The reasoning:** [`Raketa02/Raketa#17`](https://github.com/Raketa02/Raketa/issues/17).

The source documents are **not edited**. 486 `[SRC: line N]` citations and 27 bare-filename
cross-references resolve against their bytes.

---

## 1. The governing sentence covered one case of three

`3.1` ADJACENT states: *"Every public share that is paid reduces the owner's guarantee, złoty for
złoty."* True, and true of only one kind of empty seat.

| The empty seat | Its **funder** | What an arriving share does |
|---|---|---|
| Nobody ever took it | nobody — the owner's uncaptured hold | releases that much of the hold ← *the sentence as written* |
| Someone paid and left | the departed player | settles their departure at 100 % |
| The owner bought the court outright | the owner | reimburses the owner |

**What governs:** a paid share returns to the seat's **last funder**. `guarantee` is a derived
view of row one, not the money model.

Consequences that are not in either source document:

- The price of a marketplace seat is **always** `divide_among_players(courtPrice, soldFormat)`.
  An owner never names it.
- The owner is reimbursed **immediately** on the share being paid, never held to match end.
- **An owner's own seat is not sellable.** They may hand the playing spot to a named person —
  the mechanism `3.1` §3.2 already gives every participant — and remain the owner and remain
  liable. An injured owner's court still reads *n* of *n* with no vacancy the marketplace can
  find.

## 2. `privateOpen` currently prints a false statement — but the state set does not change

**The defect.** The private branch tests `openSeats > 0` **before** `payModel === 'split'`
(`now-section-domain-spec.md` §7 rung 7), so a court bought outright and then opened resolves to
`privateOpen`, whose copy reads *"every public share that is paid reduces what you guarantee, zł
for zł."* That owner guarantees nothing — they paid the court price at booking, as
`privateReserved`'s own copy says.

**What governs:** no new situation, and the count stays at **33**
([ADR-0040](../../../adr/0040-one-ladder-resolves-a-situation.md)). Under
[ADR-0041](../../../adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)
the client writes the sentence from `{situation, facts}`, and the two owners differ only in the
**facts**: one is owed nothing and stands to recover, the other still carries an unfunded
remainder. Two sentences, one situation, no second rung.

**The facts the card needs** — carried, not derived on the phone:

| Fact | Why it cannot be computed client-side |
|---|---|
| what the owner still carries | the sum of unfunded seats, which the phone does not hold |
| what the owner stands to recover | the sum of seats they funded that are open |
| **the whole court price** | the true worst case if nothing further sells — §4 |
| whether the court has been opened, and whether anyone has paid into it | the two lock moments, §3 |

## 3. Opening a court is the private path's commitment — an act, not a clock

`3.1` ADJACENT says *"commitment runs purely on the clock because there is no group to
complete"*, and
[ADR-0030](../../../adr/0030-a-departure-is-an-audience-not-a-state.md) concluded the private
path has no commitment deadline at all. It has no *deadline*; it has an **act**.

**Two doors, two moments:**

| | Shuts at | Reopens |
|---|---|---|
| The court can be closed again | **the moment it is opened** | never |
| The owner's club cancellation right | **the first stranger's payment** | never |

They are separate because *"can never be closed"* protects the people who joined, and with
nobody joined it protects nobody. Collapsing them would leave an owner paying in full for a
court that was offered and refused.

**A friend joining commits nobody; a stranger commits the owner permanently.** Until a
marketplace payment lands, the club's own cancellation window applies unchanged and every payer
is refunded to their original method.

**Preconditions and prohibitions:**

- Before a court may be opened, **every seat is either paid or empty** — a held seat is paid for
  or vacated first.
- After opening: no un-opening, no withdrawing a remaining vacancy, no removing a joiner, no
  selling the owner's own seat.
- **The court stays private permanently**, including when every original participant has gone.
  The half-price rescue fill never applies — on a bought court a 15 zł fill against a 30 zł
  refund is 15 zł short with nobody to cover it — and the open path's commitment deadline has
  nothing to grip.
- **The platform never discounts a seat on the owner's behalf**, and never boosts an opened seat
  in the recommendation pool. It is ranked by fit like everything else.
- **A converted court accepts any level.** Raketa has no admission gate; the **target band**
  scores fit and never gates. The owner gets no veto over applicants — that would hand back most
  of the control this section removes.
- Booking with split payment and opening every seat immediately is **allowed**. The liability is
  the deterrent.

## 4. An unfillable court refunds the marketplace, and only the marketplace

`privateReserved`'s copy — *"you can play with fewer players — the court is yours either way"* —
is true of a court bought for your own people. It is **not** true of a marketplace seat.

**What governs:** when the sport's **sold format** cannot be met **at the checkpoint**, everyone
who bought in from the marketplace is refunded in full and the owner carries the court.

- The trigger is an **unmet format** — fewer than 4 for padel, fewer than 2 for tennis and
  squash — not *"incomplete"*, which means something else on the open path and would drag that
  path's consequences with it.
- It resolves **before** the match, not after. Three people do not turn up to a padel court and
  then get refunded.
- **Players who paid before the court was opened are not refunded.** They bought a court with
  the owner; the stranger bought a game from us.

The arithmetic closes: the owner's worst case is the whole court price — exactly what they owed
before they opened it. **Opening a court can never leave an owner worse off than not opening
it.**

**This bounds an invariant.** *"A funded seat never becomes unfunded, so a guarantee only ever
decreases"* keeps its job with its scope named: only while the match is alive. The checkpoint
that finds the court unfillable settles it in one move to the full court price. Nobody departed;
the match failed.

## 5. What is deliberately not decided here

- **The strings.** Client-owned
  ([ADR-0041](../../../adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)).
  This delta fixes which facts reach the phone, never the Polish.
- **The third booking option** — *book this court and sell the seats* — named as the honest home
  for split-and-open-immediately, and not built.
- **A level toggle on open-match creation** — whether a creator may let out-of-range players
  request to join. It is a match-creation feature and it changes what a Now card's button says
  (*join* versus *ask to join*), which is already a known gap. Not decided here; a converted
  private court never has one.
- **The ledger** that records the owner's reimbursement and the window between it and a club
  cancellation.
