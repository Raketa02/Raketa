# ADR-0127 — A signal expires or it is refused; it never quietly decays

- **Status:** Accepted
- **Date:** 2026-08-27

## Context

[§9.5.1](../specs/matchmaking/matchmaking-engine.md) of the design document proposes two
mechanisms for the deck's interest signal, and both work the same way. The interest lift
*"decays linearly over the last 7 before it drops off entirely."* The cap is
*"`OUTSTANDING_INTEREST_CAP = 20` per sport, **soft**: past it the oldest decays faster."*

Two different problems, one move: **soften an edge by quietly moving a number the player was
never shown.** Each collides with something already accepted, and neither collision is one the
existing guardrails would have caught.

**The lift.** [`the-engine.md`](../specs/matchmaking/the-engine.md) §8 carries *They said Let's
play to you* at **`+14`** — a fixed bound in a closed roster, the largest printable signal in
the table, and the only guaranteed inclusion left
([ADR-0099](0099-relaxation-offers-the-searchers-own-asks.md) as amended: an interest lift may
**admit** below `QUALITY_FLOOR` where nothing the engine computes may). A decay turns `+14`
into `0 … +14`. The card then prints **the same sentence** at day 2 and at day 20 while the row
sits in a different place, and *Why 78?* — the one screen whose whole promise is that it shows
its working — carries a contributor that moved for a reason nowhere on the screen.

And the fact the decay would price **is already on the card.** Interest evidence crosses as
`{"kind": "interest_received", "days_ago": 2}`. Age is shown. A decaying lift charges for it a
second time, invisibly, which is the shape
[ADR-0126](0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md) and
[ADR-0115](0115-a-tag-about-the-person-may-be-shown-never-scored.md) each refused in their own
term.

**The cap.** [`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §7 already has
it *checked* at write time. A soft cap does not refuse anything — it reaches **backwards** and
shortens the life of yeses the player already sent, under a rule they were never told, because
they sent a twenty-first. The product that refuses to tell somebody *no* by silence would be
doing exactly that, to the person who did nothing wrong.

**Why the guardrails do not fire.** [ADR-0123](0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)
budgets the **silent** stack per player at `MOVE_NOTICE`. A decaying lift is *printable*, so it
sits outside that budget and the roster test stays green while the guarantee thins — the same
failure mode ADR-0126 found one stage later. The rule that catches this one has to be stated,
because no test on the map was going to.

## Decision

**We will give both edges a hard, visible shape. A signal expires, or it is refused. It never
quietly decays.**

### 1. `INTEREST_TTL = 21 days`, and the lift does not taper

The lift is a flat **`+14`** for the entire life of the yes, and then absent. No decay curve, no
final-week taper. §9.5.1's linear decay is **refused**.

21 days is chosen against the failure that matters at this pool size, which is not staleness. A
yes is silent and fires only when the *other* person runs a search; at launch density, a player
may not search for a fortnight, and a yes that expired before they looked was never a signal at
all — it was a silent loss to both. 21 days is also long enough that the re-deal after expiry
(*already asked* is a deck exclusion, so the person returns to the deck) reads as a fresh chance
rather than a loop.

### 2. Age is carried, never priced

`days_ago` continues to cross as evidence on every interest-lifted candidate. The client may say
*"said yes 18 days ago"*, and the ranking contribution is the same `+14` that a two-day-old yes
earns. One fact, one charge, on the visible side of the line.

### 3. `OUTSTANDING_INTEREST_CAP = 20` per sport, hard

`POST /api/v1/interest` **refuses** at the cap with a closed reason code. Nothing decays faster;
no already-sent yes has its life shortened by a later one. §9.5.1's *soft* is **refused**.

**Outstanding** means sent, unexpired, and **not yet mutual** — a mutual has been answered and
is no longer in flight.

### 4. The cap is shown before it bites

`GET /api/v1/interest` carries the **per-sport** outstanding count and the cap in force. A cap
the player cannot see is a refusal they cannot predict.

### 5. An expiry is dated at birth, never announced at death

Every outgoing interest row carries `expires_at` from the moment it is created. On expiry the
row is simply gone; there is no *expired* state and no archive. The product never has to say
*no* because it said *until when* at the start — and a list of yeses that were not returned is
the inverted shape of what
[ADR-0109](0109-a-read-back-names-what-it-withholds.md) refused.

### 6. All three numbers are configuration; three shapes around them are contract

Under [ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md), a number is
configuration and a shape is contract. `INTEREST_TTL`, `OUTSTANDING_INTEREST_CAP` and
`PASS_SUPPRESS` are **ruleset rows**. What is contract is `expires_at` on an outgoing row, the
`outstanding` / `cap` pair and the refusal code, and — for `PASS_SUPPRESS` — nothing at all.

**The client never hardcodes any of the three and never computes an expiry.** It reads a moment
the backend sent and renders a number the backend sent. A phone in somebody's hand can be months
behind the backend, which is the whole reason ADR-0106 drew the line where it did.

### 7. The rule, for the next edge that wants softening

**An engine that cannot print the reason a number moved may not move it.** An expiry is
explicable — *the yes was 21 days old*. A refusal is explicable — *you have 20 out*. A decay is
not: it is a number sliding for a reason no card carries and no code names.

## Consequences

- **The lift is a cliff, and the cliff is the price.** A candidate admitted **below**
  `QUALITY_FLOOR` on a 20-day-old yes, with the reason printed, is not there the next morning.
  In a thin pool that is a visibly emptier list, and the soft version would have faded them out
  instead. We take the cliff because a fade is unexplainable and a cliff is at least **dated** —
  `expires_at` was on the row from the first day.
- **Hitting the cap is a hard stop with no way to buy room.** Waiting, or a mutual. There is
  deliberately no *release my oldest* gesture: that is the soft cap with the player's hand on
  it, and reinstating it needs an argument that the **player** choosing which yes dies is
  different from the **engine** choosing — which it may well be, and which nobody has made.
- **Reversal is an API change, not a ruleset release.** `+14` is a fixed entry in the wire's
  closed vocabulary; making it a range crosses ADR-0106's line. That is the intended cost.
- **The falsifiers.** `INTEREST_TTL` is falsified by acceptance rate of interest-lifted
  candidates by **age of the yes**, which needs `matches` — and, on day one and without it, by
  **yeses that expired having never lifted anybody**: if most yeses expire unfired, 21 days is
  answering the wrong question and the pool is too quiet. The cap is falsified by refusals at
  the cap **and the distribution of outstanding counts**, because a raw refusal count cannot
  distinguish *20 is too low* from *somebody is saying yes to everybody*, which is the behaviour
  it exists to catch. Both demand rows in
  [`search-telemetry.md`](../specs/matchmaking/search-telemetry.md).
- **`INTEREST_TTL` is five-numbers-shaped**
  ([`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md)); the cap is not. Moving
  the TTL changes what is admitted below the floor and **nothing on any screen would say so**.
  Moving the cap changes a refusal the player sees the instant it happens. That difference is
  §5 and §4 of this record doing their work.
