# ADR-0080 — A payable is a share, and the card that would reduce it ships supplying nothing

- **Status:** Accepted
- **Date:** 2026-08-21
- **Resolves:** `rakieta-now-section-specification.md` §K-6 and §H11, and §G3.8's `[CONFLICT]` against Invariant 1
- **Narrows:** [ADR-0078](0078-club-policy-is-eight-fields-and-two-of-them-ship-dark.md), which kept `cardOffset[sport]` in the money chain without asking what supplies it
- **Confirms:** [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md)'s spine — *how much*, singular
- **Answers:** the price-vocabulary half of [#48](https://github.com/Raketa02/Raketa/issues/48)

## Context

Four names reached this repo from v37 for what a player is asked to pay and what reduces it:
`payable`, `shareAfterDisc`, `slotDisc` and `cardOff`. The domain spec composes them into one
chain (§D.12), and two of the four turn out not to describe anything we are shipping.

### The card asks the club and never asks the player

`cardOff(club, sport, share)` reads `CLUBS[club].card[sport]` — `0`, an integer, or `'full'` — and
takes nothing else. There is no argument for *which player*. So the rule as written hands **every**
player at a club a discount at that club's sports, unconditionally and forever. In the seeded
catalogue that is not hypothetical: two clubs declare `'full'` for squash, so under this rule every
squash seat at those clubs costs **0,00 zł** for everybody, and the card renders a struck-through
price with a `card −all` chip for a player who has signed up to nothing.

The reason the argument is missing is that the prototype models the player's half **somewhere
else**. `CARD` is a **MultiSport** plan — *"MultiSport Plus"*, a daily entry allowance
(*"2 of 2 entries left today"*), a QR code reception scans, and per-sport worth (*"Padel: not
accepted · Tennis: −15,00 zł · Squash: full entry"*). It has its own screen, its own settlement
story and its own two limits (*"your plan sets how many entries you get, the club sets how many
card holders share one court"*). None of it is wired to `cardOff`, and **the screen it lives on was
deleted from Now by a UI authority**: `1-now_screen_production_spec.md` opens by removing the
MultiSport block from every layout, token list and interaction.

So we hold the club's half of a two-sided feature and none of the player's, and running the half we
hold gives seats away.

### A discount that moves a price somebody already paid

`payable` is overridden to recompute `shareAfterDisc(m) = (m.price − slotDisc(m)) ÷ m.n` **on every
read**, then subtract the card. §H11 records the consequence and §G3.8 records it as a conflict: a
club cutting a slot's court price on Saturday morning changes what an already-sold seat *displays*,
with no refund. Invariant 1 says the opposite in as many words — *"written the moment the match is
created and never re-priced"*.

The code's own comment defends the club's right, and the right is not in question: **a club may
discount a court and may never price a seat**, or four seats would eventually cost more than the
whole court. What was never decided is what a court discount does to a seat that is already sold,
and the shipped answer — change the number, refund nobody — shows the player a price they did not
pay, on their own match, in the position where the amount they owe goes.

## Decision

**What a player is asked to pay is the share. A price is fixed onto a match when the match is made.
And one money number crosses the wire.**

### A payable is a share, and the card ships dark

**`payable == share` for every player, every match, in v1.** Nothing supplies a card, so nothing
reduces a share.

- **No struck-through price, no `card −{amount}` / `card −all` chip, no card-only filter.** `AC-63`'s
  discount chip and `AC-64`'s two wordings never fire, and `S.cardOnly` has no predicate to filter
  on. They are not conditioned on a value that happens to be zero; there is no card.
- **`card_offset` and `payable_from` stay in the kernel**, and every v1 call passes `NoCard`. This
  is deliberately *not* the case [ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md)
  refused. A **wire field with no reader** strands a phone on the day somebody removes it; a
  **kernel rule with no supplier** is depended on by nothing and costs one branch. What deleting it
  would cost is real: it is the single implementation of the capped-offset rule that the two source
  documents got wrong in two different ways, and `card_offset`'s docstring says so.
- **MultiSport is not refused — it is unbuilt.** It is a genuinely valuable Polish feature and it
  needs the player's half: which plan, how many entries today, the scan at reception, the club
  settlement row. That is its own effort, and it must arrive with both halves or not at all.

### A price is fixed onto a match when the match is made

**§K-6 resolves as (a): a slot discount reaches matches created after it, and no others.**

- **`shareAfterDisc` does not exist.** A club's cut is inside the court price *before* the share is
  divided, so there is no second share and no read-time recomputation. §H11's *"`payable` cannot be
  cached"* inverts: a payable is fixed at creation because nothing can move it.
- **`slotDisc` is real and nowhere near Now.** It is read at the moment a court is priced, which is
  before a match exists. It never reaches a card and never crosses the wire. This is the same place
  ADR-0078 put it when it moved it out of the versioned policy row and onto the club record.
- **Two matches on one court the same afternoon may carry different seat prices.** That is the price
  of the invariant, and it is the correct direction: each is the price its own players actually
  handed over.

### The wire carries one money number

**Not `{share, cardOff, payable}`.** ADR-0070's spine already says *how much*, singular, as integer
grosze with a currency beside it; the triple appears only in `1-now_screen_production_spec.md`'s
TypeScript sketch and was never adopted by the contract. It is retired here rather than reconciled.

**The two names stay apart server-side**, because they are not the same kind of fact: a `SeatShare`
is a property of the **match**, a `Payable` is a property of a **player against** that match. In v1
they are always equal; sending both would put two identical numbers on a phone and invite a screen
to print them as a discount that does not exist.

**A UI authority is final on the screen, not on the wire** ([ADR-0036](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)),
and the document holding the triple is the same document that deleted the card the triple exists
to express.

## Considered options

- **Keep the card as a club-wide standing rate and rename it.** Honest about what the code does, and
  it means clubs are giving squash away. Rejected: nobody decided to do that, and a rename would
  make an accident permanent.
- **Build the player's half now.** The right feature and the wrong ticket — a plan, a daily
  allowance, a scan at a counter and a settlement file back to the club is larger than Now.
- **Apply a slot discount to every seat and refund the difference** (§K-6 option b). One price per
  court, made true with money. Rejected: it lets a club move funds out of Raketa's account with a
  switch, on a Saturday morning, for seats sold days earlier.
- **Forbid discounting a slot once any seat is sold** (§K-6 option d). No divergence possible, and it
  removes the lever at exactly the hour a club most needs it.
- **Ship all three money fields, equal and zero** — ready for the card, at the cost of two fields we
  can prove are noise. Rejected on ADR-0071's own finding, pointed the other way: neither client
  validates the wire at runtime, so **adding** the field the day the card exists strands nobody.

## Consequences

**Easier**

- **The number on a card is the number the player paid.** No divergence to explain, no moment where
  it moves, and no support conversation about a price that changed after purchase.
- **§G3.8's conflict and §H11's warning both dissolve** rather than being documented. A payable is
  computable once, at creation, and every later read agrees with it by construction.
- **The fit engine's price term reads one number** that cannot change under it, so a match's fit
  score no longer has to be versioned against a discount somebody might publish
  (`now-section-domain-spec.md` §D8's warning is discharged).
- **`[GAP-D7]`'s ambiguity shrinks**: with no card there is no zero-versus-missing offset to confuse.

**Harder**

- **Two matches on the same court can show different seat prices**, and the feed can show both at
  once. Nothing explains it to the player, and nothing here proposes to — the alternative is worse.
- **We ship without MultiSport in a market where it is close to universal.** Clubs that accept it
  see no acknowledgement of that in the product, and the first question a club sales conversation
  will ask is when it arrives.
- **Somebody must remember the kernel rule is asleep, not dead.** Two correct functions with no live
  input are exactly the shape a later reader deletes as unused.

**Neutral**

- `slotDisc` survives with no reader on this map at all. It belongs to the surface where a court is
  priced, which is out of scope here, and it is recorded so nobody wires it into a card.
- The struck-through-price layout is not built, so the day the card returns it is a layout change as
  well as a contract change.
