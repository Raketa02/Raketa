# ADR-0131 — A deal remembers for a day, so that a spent deal deals again

- **Status:** Accepted — **bounded 2026-09-16 by [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)** §4: a radar reading is not a deal and
  never enters the memory.
- **Date:** 2026-08-28

## Context

[`the-engine.md`](../specs/matchmaking/the-engine.md) §10.3 settles the deck's shape, and
one of its sentences turned out to be missing a number:

> **A spent deal deals again** — a new search, a new `search_id`, the same exclusions plus
> everybody **already dealt**. Exhausting a *deal* is not exhausting the *pool*, and the
> two were one sentence until this was asked: the honest empty state belongs to a fresh
> deal that came back with nothing, never to a player who has seen ten of forty.

*Already dealt* has no window on it anywhere in the spec set, and the deck does not work
without one in either direction.

**With no memory at all the sentence is false.** A deal's order is deterministic — three
bands over a `rank_key` that moves on nothing about the other cards
([ADR-0126](0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)) — and
nothing about those ten people has changed between one tap and the next. So a second deal
returns the same ten in the same order, and *a spent deal deals again* means *a spent deal
deals the same thing again*, which is the failure the sentence was written to prevent.

**With an unbounded memory the other half is false.** A player who dealt through their
whole city once would never be dealt to again, and the deck's honest empty state — which
[`the-play-screens.md`](../specs/matchmaking/the-play-screens.md) §7 makes *the exhausted
pool*, not the exhausted player — would arrive permanently and wrongly. It would also be a
third way a non-empty pool becomes an empty deck, and the telemetry
([`search-telemetry.md`](../specs/matchmaking/search-telemetry.md) §2) enumerates exactly
two: `n_excluded_by_suppression` and the pool description. A third that nothing counts is
the shape of failure ADR-0128 §5 calls *five-numbers-shaped*.

**The three deck numbers are set and this is not a fourth of them.**
[#194](https://github.com/Raketa02/Raketa/issues/194) settled `PASS_SUPPRESS = 30 d`,
`INTEREST_TTL = 21 d` and `OUTSTANDING_INTEREST_CAP = 20`, and
[`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §10 records all three
as **configuration**, with the contract shapes around them. Those three price *what a
signal is worth*. This one says *how long one surface's short-term memory is*, which is a
fact about the shape of the surface rather than a price anybody is arguing over — the same
distinction that puts `EXPOSURE_RETENTION_WEEKS` in the domain and the roll's cadence in
the settings, and `NEWCOMER_WINDOW` in the domain while the ruleset prices what being new
is worth.

**The engine document already says the number out loud**, in the sentence that names the
deck's natural exhaustion ([`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md)
§9.5.1):

> The deck's natural exhaustion (*"You have seen everybody compatible **today**"*) already
> does part of this work.

## Decision

**We will set `DEALT_MEMORY = 1 day`, in the matchmaking domain, as a rolling window.**

A deal excludes everybody the same player was dealt in the same sport within the last day,
read from the durable `search` record — `surface = DECK`, `band = RETURNED` — and from
nothing else.

> **Bounded 2026-09-16 by [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §4.** A radar *reading* is a
> recorded search with `surface = RADAR` and every drawn row `RETURNED`, and it is **not** a
> deal: `surface = DECK` above is the whole of the memory's source. A look never counts as
> dealt; only an answer given on the radar reaches the deck.

### 1. Domain, not ruleset and not configuration

It lives in `matchmaking/domain/deck.py` beside the ordering it serves, on
`EXPOSURE_RETENTION_WEEKS`'s rule: **how long a fact survives decides what can be asked of
it.** An environment that could shorten it would be an environment selecting behaviour a
domain test can observe, which [ADR-0028](0028-four-environment-model-and-typed-configuration.md)
forbids. It is not a ruleset row because a ruleset prices *who a player should meet*, and
this decides nothing about anybody's worth.

### 2. Rolling, not a calendar day

*Today* is the engine document's word and a calendar day is not what it means: a UTC
midnight lands in the middle of the evening the deck is for, and a player dealing at
23:50 would be re-dealt the same cards ten minutes later. The window is
`now − DEALT_MEMORY`, which is the same shape `NEWCOMER_WINDOW` and the interest expiry
are written in.

### 3. Read from the record, never from a cache

The deals are already durable rows written before their response returned
([ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md)). A Redis mirror
would be a fourth ledger whose loss would silently re-deal a card — the same split that
keeps the pass record durable while its suppression is not, arriving at the same answer:
**the gate is the cache; the evidence is the row**, and here the evidence is already
written, so there is nothing to cache.

### 4. It has a falsifier, and it is the deepest position reached per deal

`DECK_DEAL_MAX`'s own falsifier already collects it. If the median deal is exhausted and
the next deal is empty, the memory is too long for the pool it runs over; if p90 stops
before position four, nobody is reaching the end of a deal and the number is doing nothing
either way. Owner `RobertConstantin02`, and any change lands as an ADR naming who moved
it, on [`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md)'s rule.

## Consequences

- **A second tap deals the next people**, which is what the sentence promised, and a
  player who taps through everybody gets an honest empty deal rather than a loop.
- **It resets by tomorrow**, so nobody is permanently exhausted by having browsed once. A
  person neither passed on nor asked comes back the next day, which is the deck's own
  version of what `INTEREST_TTL` expiry does for *already asked*.
- **A thin pool can produce an empty deal a player caused**, and that is the cost. It is
  distinguishable in the record — `players_in_range` against `n_returned` on a row whose
  `n_excluded_by_suppression` is zero — and it is not distinguishable *on the screen*,
  which is the same limitation the deck's empty state already has and does not worsen.
- **It is one more thing that turns a non-empty pool into an empty deck**, joining
  `PASS_SUPPRESS`. Unlike that one, it lapses in a day and the player caused it in the
  session they are still in, so the honest response to *why is my deck empty* is the same
  one the surface already gives: come back tomorrow.
