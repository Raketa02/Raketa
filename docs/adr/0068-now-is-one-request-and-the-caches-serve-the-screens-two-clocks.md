# ADR-0068 — Now is one request, and the caches serve the screen's two clocks

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0050](0050-now-below-the-strip-is-shelves.md) replaced Now's two fixed sections with five
shelves and recorded the cost honestly: *"fifty cards is a much larger surface than six, and
everything about it — retrieval cost, scoring cost, the payload, the scroll performance — is
roughly an order of magnitude bigger than what `4` Part 6 budgeted for."* That paragraph was
written as a debt, not a design, and this is where it is paid.

Three facts reshape the question before any number is chosen.

**It is 53, not 50 — and only 23 of them are scored.** The caps are 10 · 3 · 10 · 20 · 10.
Shelves 1–3 are match cards that run retrieval → eligibility → scoring; shelves 4 and 5 are
**people and clubs**, two index queries with no scorer anywhere near them
([ADR-0051](0051-now-is-ordered-not-drawn.md) *§The shelves that are not matches*). So the
funnel grew **6 → 23**, and the payload grew **6 → 53**. Those are two different budgets that
fail in two different places — one on the server's p99, one on a phone's parse and scroll —
and holding one number over both hides which is breaking.

**The player feed cache was sized against a client that no longer exists.**
`4-match_recommendation_engine_architecture.md` §6.1 specifies a **TTL 60 s** cache keyed
`playerId : sportFilter : surface`, and §6.3 projects *"~2,000 feed requests/min"* — both
computed under ADR-0038's 30-second polling. [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md)
abolished the timer: a player asks on **arrival, pull-to-refresh, an action, and a countdown
reaching zero**. A 60-second cache only pays when one player asks twice inside a minute, and
the one ask that would most often hit it is the one ADR-0054 gave an explicit promise to —
pull-to-refresh, which *"says what you are reading is real and I am checking."*

**The two non-match shelves run on a different clock and a different key.** *New on Raketa* is
30 days of new players; *New clubs* is 60 days of new clubs. Their **membership** is
`city : sport` and shared by everybody, where the three match shelves are resolved per viewer.
That asymmetry is what raises the contract question — one request, or two — because a shape
chosen for the cache would be visible in the wire.

The alternatives considered for the contract:

- **Two requests.** Lets the bottom half be cached across the whole city and served without a
  viewer. It pays for that with a screen that arrives in two beats — a second loading state on
  a cold open where [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md) gives exactly
  one shimmer, and a bottom half that appears under a thumb already scrolling, which
  [ADR-0032](0032-order-is-a-property-of-the-composed-screen.md) exists to prevent.
- **One request, one cache tier.** Simple, and it re-serves per viewer a half of the screen
  that is identical for everyone in the city.
- **One request, two cache tiers inside it.**

## Decision

**We will serve Now as one request whose two halves are cached differently, and the phone will
never learn there were two clocks.**

### The contract

- **`GET /now` returns the whole screen** — all five shelves in one envelope, composed by the
  server. The shape of that envelope is [#41](https://github.com/Raketa02/Raketa/issues/41)'s to
  draw; what is fixed here is that there is **one** of them.
- **The repeat guard does not reach across the boundary.** ADR-0050's rule — *"a shelf is dropped
  entirely when it would be nothing but repeats of a shelf above it"* — is entirely within the
  three match shelves, because a person and a club can never repeat a match. This is recorded
  because it is the argument a later session would reach for when reopening the split, and it
  does not hold.

### The caches

`4` §6.1's two-row table is replaced:

| Cache | Key | Invalidated by | Lifetime |
|---|---|---|---|
| **Match scoring context** | `matchId : recordVersion` | The version key itself — never stale | until evicted |
| **New-arrivals set** | `city : sport : kind` | **TTL only** | **15 min** |

- **The match scoring context is untouched.** It is the cache that pays — `seatTarget` is a
  401-candidate grid over three pairings, it depends only on the seated levels and the sport,
  and sharing it across every player who scores that match is `4` §3.3's 25× win. Shelves
  change none of that.
- **The player feed cache is deleted.** It was the answer to a load shape ADR-0054 removed, its
  explicit-invalidation list (join, create, waitlist) is already redundant with ADR-0054's
  *an action returns an update, one card, never a recompose*, and it is the only place on this
  screen that could serve a stale answer to a direct question. **Every ask now pays the funnel**,
  which is what the budget in [ADR-0069](0069-the-budget-is-two-budgets-and-both-fail-the-build.md)
  is sized for.
  - **Tap-time verification is unaffected.** `4` §5.2 draws its two alternatives from *"the
    cached feed the player is already holding"* — that is the client's composed screen, not the
    server cache, so the graceful failure survives the deletion intact.
- **The new-arrivals cache holds the set, and the order is computed per viewer.** *New on
  Raketa* is ordered by **closeness to the viewer's own Level** (ADR-0051), so the row cannot be
  cached even though its membership can. Twenty rows through a comparator is free, and paying it
  keeps the shelf honest for every player instead of near-honest for most.
- **A 15-minute TTL with nothing to invalidate it.** The shelves' own clocks are 30 and 60
  **days**; a quarter-hour of lag is invisible against that, and a cache with no invalidation
  path is the one shape that cannot go wrong.

### The depths, and the order of *New clubs*

- **The caps become 6 · 3 · 6 · 8 · 6 — 29 cards.** ADR-0050 fixed the shelf **count** at five
  and left the depth undefended; this defends it downward. At 320pt a shelf card is nearly full
  width with a ~5pt peek ([#11](https://github.com/Raketa02/Raketa/issues/11)), so card 10 is
  nine swipes away, and **every shelf already ends in a tail card into Find** — the overflow has
  somewhere to go, which is exactly what makes a deep cap buy cards nobody reaches. *New on
  Raketa* falls furthest, from 20 to 8, because it is also the shelf whose cards are **inert in
  v1** (ADR-0051): twenty untappable faces was the largest block of payload on the screen.
  - **The claims are unchanged.** Nothing about which shelves exist, what each says, the 70 and
    80 floors, or the fixed order moves. Only depth.
  - **A swiped tail card is the measurement that argues a cap back up.** Unlike ADR-0051's 70
    floor — which hides matches and can never report how many — a cap that is too tight leaves a
    trace in the one place a player goes when the shelf ran out.
- ***New clubs* is ordered newest first, with distance breaking ties.** The shelf's title is its
  claim, and ordering by distance would make a shelf that says *this is new* answer *this is
  near* instead. [ADR-0064](0064-a-radius-orders-now-and-bounds-only-a-search.md)'s rule is that
  a radius must not **exclude** on Now; newest-first excludes nothing, so the two do not collide.
  This also gives both non-match shelves the same shape: **a shared set with a per-viewer
  tiebreak.**

## Consequences

**Easier**

- One request, one shimmer, one composed order. ADR-0032's *order is a property of the composed
  screen* survives contact with a screen that has two clocks in it, and nothing arrives under a
  thumb.
- The half of Now that is identical for everyone in a city is computed once per city per sport
  rather than once per player, and the cache that does it needs no invalidation machinery.
- Deleting the feed cache removes a staleness path rather than mitigating one. There is now no
  configuration under which a pull-to-refresh returns something the server already knew was old.
- 29 cards instead of 53 is roughly half the payload, and the cut lands hardest on the cards that
  cannot be tapped.

**Harder**

- **Every ask now pays the full funnel.** The feed cache's floor of *< 2 ms* is gone, and the
  realistic floor is the warm funnel. This is affordable only because the context cache carries
  the expensive stage, so **a cold context cache is now felt by the player rather than absorbed**
  — the case ADR-0069's cold ceiling exists to bound.
- **The depths are a second product judgement with no measurement behind them**, exactly like
  ADR-0051's 70 floor. Six may be too few for a player in a dense city on a Saturday, and the
  tail card is the only signal that will say so.
- **Two cache tiers in one response is a shape that invites a third.** The next shelf that runs
  on its own clock will arrive arguing for its own key, and the rule that keeps this from
  becoming a cache per shelf is that a tier must be justified by a **shared** key, not merely by
  a different clock.
- **The new-arrivals cache grows with cities × sports**, where `4` §6.3's whole argument was that
  per-request cost does not grow with the platform. That still holds — this cache is small,
  bounded and city-scoped — but §6.3's entry-count table is now short by a row.

**Neutral**

- No engine changes. Caps, order, cache policy and composition are all ranking-layer policy,
  which [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md) already placed
  outside the engines and ADR-0051 confirmed.
- Redis and Celery are already backend dependencies, so both caches have a home and neither
  needs new infrastructure.
