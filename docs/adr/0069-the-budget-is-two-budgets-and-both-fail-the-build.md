# ADR-0069 — The budget is two budgets, and both fail the build

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

`4-match_recommendation_engine_architecture.md` §6.2 budgets a Now request at **~62 ms cold,
~12 ms warm, < 2 ms from the feed cache**, and states the gate: *"budgets fail the build when
exceeded, measured at p99 with 500 live city matches."* Every row of that table was sized
against a **four-card render**, **two retrieval lanes**, and a client that polled.

[ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md) leaves none
of those three standing: there are **five lanes**, **29 cards**, and **no feed cache**, so the
warm row is now the floor rather than a fallback. The table needs replacing, and the question
of *what fails the build* needs re-asking, because the surface has two failure modes and §6.2
only ever gated one of them.

**The second budget has never existed.** Payload has no gate anywhere in the specification set,
and [What a card carries](https://github.com/Raketa02/Raketa/issues/42) is about to walk 33
situations field by field. Without a ceiling handed to it, it will decide the card's contents
with no idea what 29 of them weigh — and every field will be individually defensible, which is
precisely how a payload budget is lost.

**Degrade was written for two lanes.** §5.5 gives a per-lane kill switch and
`degradeMode: 'off' | 'recency'` — *if the scorer throws or exceeds its budget, the lane serves
soonest-first with no badge, because a feed with no ranking is better than no feed*. Three of
the five shelves are now scored, one of those has no floor at all, and two are not matches and
cannot degrade to recency in any meaningful sense.

## Decision

**We will hold Now to two budgets — a latency budget and a payload budget — and both will fail
the build.**

### The latency budget

`4` §6.2's table is replaced. There is no feed-cache row, because there is no feed cache.

| Stage | Cold | Warm |
|---|---|---|
| Retrieval, 5 lanes | 17 ms | 12 ms |
| Eligibility, ~200 candidates | 0.7 ms | 0.7 ms |
| **Context build**, ~130 matches | **65 ms** | **0 ms** |
| Scoring, ~130 candidates | 2.6 ms | 2.6 ms |
| Assembly + composition, 5 shelves | 1 ms | 1 ms |
| Render + serialise, 29 cards | 6 ms | 6 ms |
| **Total** | **~92 ms** | **~22 ms** |

**One gate, on total server time: p99 ≤ 150 ms, measured at 500 live city matches on a 29-card
screen with a warm context cache. The cold-cache ceiling is 250 ms.**

- **The gate is the total, because that is what a player feels.** The per-stage rows stay as
  **diagnosis, not as gates**: a stage that doubles while the total stays inside 150 ms is a
  thing to look at, not a build to fail. Gating each row independently would fail builds for
  reallocations nobody can perceive.
- **The measurement condition is stated in full and it is not §6.2's.** Five hundred live city
  matches is inherited; the 29-card screen and the warm context cache are new, and naming the
  cache state is the load-bearing half — a p99 measured against a cold cache is measuring the
  cache, not the funnel.
- **The cold ceiling exists because ADR-0068 moved that cost onto the player.** With the feed
  cache deleted there is nothing between a cold context and the screen, so the cold number is no
  longer a private detail of the server.

### The payload budget

**150 KB uncompressed for the whole composed envelope**, measured on the fullest realistic
screen, and it **fails the build**.

- **At 29 cards that is ~5 KB a card** — generous for `{situation, facts}` plus a fit sub-object
  carrying a clamped score and three reasons, and tight enough that shipping all seven scoring
  terms per card fails rather than quietly landing.
- **It fails the build rather than advising**, for the reason the ceiling exists at all: a
  ceiling that only advises is one that [#42](https://github.com/Raketa02/Raketa/issues/42) can
  reason past a field at a time. The test composes the fullest realistic screen and asserts the
  byte count; it is about fifteen lines and it is the only thing that makes the number real.
- **`FitScore`'s full return value is a server-side type, not a wire type.** `4` §3.3 returns
  seven terms with weight, value, contribution and sentence, plus modifiers — 
  [ADR-0037](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md) already reduced what the
  card shows, and this budget is what keeps the reduction from being re-litigated.

### Degrade, per shelf

`degradeMode` narrows to the shelves that have a scorer. The per-shelf kill switch is kept.

| Shelf | Scored | On scorer failure |
|---|---|---|
| *Best fit for you* | yes | **Soonest-first, no badge**, title falls back to **Same level** |
| *Full, but worth waiting for* | yes | **Dropped entirely** |
| *Recently viewed* | yes | Renders, **no badge** |
| *New on Raketa* | no | Unaffected |
| *New clubs* | no | Unaffected |

- **Best fit never goes silent**, which is ADR-0050's rule and not a new one — the *Same level*
  fallback already exists for a thin week, and reusing it for a failed scorer means the degraded
  screen is a screen players have already seen rather than a mode built for an incident.
- **The waitlist shelf is dropped**, because an **80 floor with no scorer is not a claim we can
  make**. Asking somebody to wait is ADR-0050's bigger ask; asking them to wait for something we
  cannot currently grade is worse than not asking.
- ***Recently viewed* survives without a badge**, because it makes no claim beyond *you looked at
  this* — the reason ADR-0051 gave it no floor is the same reason it needs no score to be honest.

## Consequences

**Easier**

- The two ways this screen fails are now separately visible, so *"Now got slow"* and *"Now got
  fat"* are different red builds rather than one vague one.
- [#42](https://github.com/Raketa02/Raketa/issues/42) inherits a hard constraint rather than an
  open field, and can decide 33 situations against a number instead of against taste.
- A scorer outage degrades to a screen that already exists in the product, so the degraded path
  is exercised by ordinary thin-week testing rather than only by an incident.

**Harder**

- **A single total gate hides reallocation.** A stage can regress badly and stay green while
  another improves, and nothing will report it until the total tips. The per-stage rows are the
  mitigation and they are only as good as somebody reading them.
- **150 KB is a judgement, not a measurement.** No device testing stands behind it; it was chosen
  as a per-card allowance that a reasonable card fits and an unreasonable one does not. The first
  real device profile may argue it either way.
- **The build now fails on a byte count**, which will at some point block a legitimate field for
  a reason that feels bureaucratic. That is the cost of the gate being real, and the response is
  to argue the ceiling in an ADR rather than to raise it in a config file.
- **The numbers are modelled, not measured.** No composed Now exists to profile — the funnel
  layer is unwritten (ADR-0051) — so the table is an extrapolation from `4` §6.2's measured
  per-candidate costs. The first implementation is also the first measurement, and it may find
  the shape wrong rather than the numbers.

**Neutral**

- Nothing here changes an engine, a floor, a shelf or a claim. This is a gate over work that
  ADR-0068 and ADR-0050 already specified.
