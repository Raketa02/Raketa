# ADR-0105 — Determinism is a set-iteration problem in Python, and pinning the hash seed hides it

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

[`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §13
promises that *"same request + same snapshot + same ruleset ⇒ byte-identical response,"* as a
property test rather than an aspiration, and gives four rules to get there. It was written for a
Go service, and [ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) put the
matcher in Python. Two rules survive verbatim. Two do not, and the mismatch is not cosmetic —
**one of them names a hazard Python does not have, and by naming it hides the one Python does.**

**"No ambient time in the core" is already enforced and needs nothing.** `.importlinter`'s
`engines-are-pure` contract forbids `datetime` to `app.engines`, and `matchfit` inherits it by
ADR-0093. What the rule still owes is a sentence about the *other* half: `app/modules/matchmaking/`
is not fenced, so the search's `at` must arrive from the `Clock` port at the composition root, as
[ADR-0024](0024-instant-as-aware-datetime-minute-coordinates.md) and `app/infrastructure/clock.py`
already require of everything else — *"everything above this line takes `now` as an input."*

**"No map-iteration order dependence" does not transfer.** Go randomises map iteration; Python
dicts have been insertion-ordered since 3.7. Transcribed as written, the rule tells a reader to
guard the one collection in Python that is already safe.

The hazard Python actually has is **set iteration**, and it is narrower and nastier than the Go
rule it replaces. Since PEP 456, `str` and `bytes` hashing is seeded per interpreter, so the
iteration order of a set of **strings** differs between processes and is perfectly stable within
one. Measured on this repo's interpreter, over the same eight ids:

```
seed 1   str: a5 e9 fa 94 b6 c7 0b d8      uuid: a5 c7 e9 0b 94 b6 d8 fa
seed 2   str: fa b6 c7 e9 d8 a5 94 0b      uuid: a5 c7 e9 0b 94 b6 d8 fa
seed 3   str: 94 b6 a5 fa e9 0b d8 c7      uuid: a5 c7 e9 0b 94 b6 d8 fa
```

`uuid.UUID` hashes its integer value, so a set of `UUID` objects is stable. **A set of the same
ids as strings is not** — and an id becomes a string every time it crosses a boundary: a JSON
payload, a text column, a dict key rebuilt from a request. The type that makes the bug appear is
not the type the developer chose; it is the type it arrived as.

Nothing in this repository sets `PYTHONHASHSEED`. So the failure shape available today is the
worst one there is: **every test passes, and two gunicorn workers disagree** about the order of a
shortlist — which is exactly *"it showed me somebody different when I went back,"* the support
ticket §13 says has no possible answer.

## Decision

**We will forbid ordered traversal of a set, and refuse to pin the hash seed.**

### 1. A set is never the source of an order

No `set` or `frozenset` may be the source of an ordered traversal — directly, or transitively
through a comprehension, a `dict` built from one, or a sort whose input came from one. Membership
tests are what a set is for and are untouched. Where a collection must be both deduplicated and
traversed, it is sorted on the way out, on the total order in §3.

The rule is stated on the collection rather than on the element type on purpose: **auditing every
element type at every call site is not a thing anyone will keep doing**, and the element type is
precisely what changes silently when an id crosses a boundary.

### 2. The enforcement is two processes with different seeds — not a lint

The property test runs the same search in **two subprocesses started with deliberately different
`PYTHONHASHSEED` values** and asserts the responses are byte-identical. A lint cannot see through
a comprehension over a set-returning call; an in-process property test cannot see the defect at
all, because within one interpreter the order is stable and correct.

### 3. The tie-break is one named total order

`(rank_key desc, fit desc, player_id asc)`, with `player_id` compared as its **canonical lowercase
string form**, named once as a constant and never re-spelled at each sort site. For canonical
lowercase UUIDs the string order and the integer order agree, so the choice is free; naming *which*
is not, because a re-spelling that reaches for the other one is invisible in review.

One consequence worth writing down rather than rediscovering: if this order is ever produced by
SQL, it is `ORDER BY` on the `uuid` column, never on a text cast — a text collation is entitled to
treat the dashes as variable-weight punctuation and hand back a different order than Python did.

### 4. `PYTHONHASHSEED` is never pinned in application configuration

Not in the Dockerfile, not in the Compose files, not in the deployment manifests, not in
`pytest.ini`. Pinning it makes the defect invisible instead of absent, and makes production
correctness depend on an environment variable that nobody will remember is load-bearing — which
is the failure [ADR-0028](0028-four-environment-model-and-typed-configuration.md) exists to
refuse: **the environment may select configuration defaults; it may never select behaviour a
domain test could observe.** A shortlist's order is behaviour a domain test observes.

The one place a seed is set deliberately is the test in §2, which sets two of them and compares.

## Consequences

- **The rule is wider than the matcher.** It binds `app/engines/` as a whole and anything that
  orders ids anywhere. That breadth is the reason this is its own record rather than a paragraph
  in [ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md) about telemetry
  storage, where nobody sorting a set of player ids in a future engine would ever find it.
- **A class of bug that survives every single-process test is caught in CI**, for the price of two
  subprocesses in one test.
- **A deduplicate-then-order path costs a sort** it did not cost before. At §17's sizes — a few
  hundred candidates — this is not measurable.
- **`set` keeps its real job.** Blocks, suppression, the searcher's pairwise set: all membership,
  all untouched.
- **Byte-identical replay is now a property test, and not yet a production guarantee.**
  Reproducing a *past* search additionally needs the index as it stood, which is
  `snapshot_version` and belongs to
  [The matcher's picture of the city](https://github.com/Raketa02/Raketa/issues/173). This record
  makes the scoring half deterministic; the index half is that ticket's.
- **§13 keeps all four of its promises and changes two of its four rules.** The conflict table in
  [`docs/specs/matchmaking/README.md`](../specs/matchmaking/README.md) carries the row.
