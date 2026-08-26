# ADR-0109 — A read-back names what it withholds, and a silent yes stays silent

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

Two surfaces on the Play screens turned out to show a person the product has since agreed not
to show, or to show a fact the product promised to keep quiet. Both are small, both are
one-line fixes, and both are the kind of thing that is only ever found by reading two accepted
records against each other.

**The read-back.**
[ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) makes every search a
durable, unexpiring row and `GET /searches/{id}` a primary-key lookup;
[`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §1 asserts *a round trip
through the record reproduces the response*. That is what makes *Why 78?* open instantly a
week later.

[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) says the block
reaches **every surface that shows one player to another**, and
[ADR-0108](0108-a-forecast-is-a-route-not-a-search.md) just applied that to a route with no
record at all. A stored search read back an hour, or a month, later is the same surface with a
longer memory: it will happily render a card for somebody who blocked the searcher in between.
The immutable record and the live gate cannot both win.

**The silent yes.** §9.5.1 of
[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) defines *Let's play* as
**a silent, one-directional, sport-scoped yes**: *"Nobody is notified. Nothing is scored. It
becomes visible only when one of you goes looking for a game."* The prototype's deck says the
same thing in the player's own words — *saying yes is cheap, silent and reversible.*

The deck's empty state nevertheless wants to say *"requests you sent are waiting (3)"*, and
[`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §7 defines only
`POST /interest` — nothing reads it back. The obvious read route would return the player's
outgoing and incoming interest. **Incoming-and-not-yet-mutual is exactly what §9.5.1 forbids
surfacing**: a route listing who has said yes to you turns a silent signal into an inbox, and
the promise made to the person who said it stops being true.

## Decision

### 1. The read-back re-verifies, and a withheld row is stated rather than vanished

`GET /searches/{id}` re-reads the fail-closed gates — blocks and holds — against live state
and withholds any row that now fails. The stored record is **not** rewritten: it is immutable,
and that is ADR-0104 untouched.

**The response says a row was withheld, and why, in the coarse gate spelling already in use.**
It does not silently return nineteen rows where twenty were recorded.
[ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §6 spent a whole
section on this failure mode for an unknown evidence kind — *a breakdown that quietly stops
adding up is the same class of lie as a recomputed score, and worse for being invisible* — and
a shortlist that quietly loses a row is the same lie one level up.

`the-two-contracts.md` §1's round-trip assertion narrows accordingly: **the round trip
reproduces the recorded answer, plus live gate state**, and the test asserts both halves.
Written down because a test drafted naively against the whole payload will fail on a
re-verified row and on a re-minted photo URL ([ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)),
and the temptation will be to loosen the test rather than to read this.

### 2. A read route for interest exists, and returns only what its author consented to publish

`GET /api/v1/interest` returns:

- **the player's own outgoing interest**, all of it — their own act, theirs to see;
- **mutuals** — both sides said yes, so both consented.

**Incoming-and-not-mutual never crosses, on any route, in any shape** — not as a list, not as
a count, not as a badge. A one-sided yes reaches its recipient exactly one way: as an
**interest lift** on a card, in a search *they* chose to run, with its reason printed. That is
the mechanism §9.5.1 designed, it is already in the contract as `inclusion_reason:
INTEREST_LIFT`, and it is enough.

This joins §21's existing refusal — *passes and declines are never surfaced to the other
party, in any response, ever* — and takes the same enforcement: a schema test over every
response type, not a test per route.

## Consequences

**A stored search stops being purely historical, and says so.** It is now *what we computed,
minus who we may no longer show you* — which is a slightly more complicated thing to explain
than a snapshot, and the right one. The alternative was a screen that renders a card for
somebody who blocked you, which is the exact failure ADR-0095 was written to prevent, arriving
through the one route nobody thought of as a surface.

**`GET /searches/{id}` is no longer free.** It was a primary-key lookup; it is now a lookup
plus a block-set read, and it fails closed — a search that cannot re-verify is a `503`, not a
degraded render. On the *Why 78?* path this is the difference between a sheet that opens
instantly and one that opens after a small query, and the block set is the cheapest read in
the system. If it ever stops being cheap, the answer is caching the block set, never skipping
the check.

**The empty deck gets a smaller sentence than the prototype's, and a true one.** *"Requests
you sent are waiting (3)"* is the player's own outgoing count and survives intact. What is
gone is any version of *"2 people are waiting for you"* — which no screen may say until those
people are met in a search.

**Somebody will ask for the inbox.** It is an obviously valuable screen and it converts: a
list of people who already want to play you is the strongest thing this product could show
anybody. It is refused because the signal only exists at all on the promise that it is silent,
and a yes given under that promise cannot be re-read as consent to appear in a stranger's
inbox. If it ever ships, it ships as a **differently-consented** signal collected afresh, and
never by re-interpreting the yeses already banked.

**Two more refusals that are only enforceable by a schema test,** joining §21's. The pattern
is now established enough to be a rule rather than three separate assertions: **a fact the
product promised not to surface is asserted absent from every response shape, once, centrally**
— because a per-route test passes forever and then a new route is added.
