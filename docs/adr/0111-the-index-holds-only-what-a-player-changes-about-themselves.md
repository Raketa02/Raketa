# ADR-0111 — The index holds only what a player changes about themselves

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

The design document gives the index's staleness budget two different values under one name,
and the map has been reading them as one number.

§17's SLO table says index staleness p50 **2 s**, p99 **15 s**. §18's degradation table says
serve normally under **15 minutes**, flag between 15 minutes and 24 hours, and **refuse** past
24 hours. [The scale posture](https://github.com/Raketa02/Raketa/issues/165) declined to pick
between them and handed the reconciliation here.

They were never in conflict — they are a service level and a failure mode — but §18's stated
*reason* for the refusal is now false, and that turned out to be the more interesting half.

§18 refuses past 24 hours because *"a day-old index can put a held or blocked player in front
of somebody."* That was true when the document was written. It is not true now:

- [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) confirmed and
  corrected §7.5 — **the candidate index holds no block data at all**; the searcher's live
  block set travels in the `SearchContext` and the backend re-verifies the returned rows.
- [ADR-0098](0098-matcher-demands-as-executable-contracts.md) did the same for history and the
  open-challenge set, and put the held account behind `AccountHoldQuery`.
- [ADR-0109](0109-a-read-back-names-what-it-withholds.md) extended the re-verify to a stored
  search read back later.

So every fact §7.5 called *must never be stale* is now, by three separate decisions, **not in
the index**. What is left in it — μ, σ, tags, the availability grid, play intent, area,
radius, gender and gender preference — is the same list under a description: **things a player
changes about themselves.** The two gates that do read the index
([ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s ninth,
[ADR-0103](0103-where-the-curve-saturates-the-gate-begins.md)'s tenth) read facts that move on
the order of months.

The description is not a summary. It is a constraint, and the ticket found the first thing it
excludes. §9.5 scores *Recent activity* at −5 … +4, *"Active now* vs *3 days ago"*, and
[The ranking weights](https://github.com/Raketa02/Raketa/issues/168) kept those bounds — but
**nothing in `backend/app` records when a player was last active.** Not a column, not an event.
An event-sourced store has no *the player opened the app* event, and writing one would be a
firehose in the same table the projection tails
([ADR-0110](0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md)).

The nearest available signal is `auth.refresh_token_issued` / `auth.refresh_token_rotated` —
real, durable, already-published contracts — against `REFRESH_TOKEN_EXPIRE_SECONDS = 86400`.

### Ruled out

- **A new `player_profile` activity event.** One append per app open, into the table the
  projection reads in order. The signal is worth −5 … +4 and the cost is the write path.
- **A plain `last_active_at` column touched on each authenticated request.** The obvious
  answer, and it puts one field outside the event store — therefore outside §7.4's rebuild
  guarantee and outside ADR-0110's watermark, so a rebuild would silently disagree with the
  tail on exactly one column. It breaks rebuild-equals-tail for a Liveness dock.
- **Standing the activity input down as `NoEvidence` until something owns activity.**
  Defensible, and it discards a signal the store already contains for the sake of a precision
  nothing downstream asks for.
- **`index_stale: true` on the wire**, as §18 specifies. §18 itself says the player sees
  nothing at that rung and recommends against the banner, so the field would ship with no
  consumer — and [What each Play screen needs from the contract](https://github.com/Raketa02/Raketa/issues/171)
  already refused a client-visible field with nothing behind it, drawing *Most reliable* **not
  at all** rather than drawing it inert.

## Decision

**We will state as an invariant that the candidate index holds only facts a player changes
about themselves, and that every fact which must be live is never in it. §17 and §18 are two
budgets, and §18's ladder is a quality ladder.**

- **The invariant, in one line:** *a fact that must be true at the moment it is read does not
  belong in the index.* It is the read-side counterpart of ADR-0098's *a gate may be honestly
  empty; a term may never be honestly neutral*, and it is what a future column is tested
  against — not "is this expensive to project" but "would being two seconds wrong about this
  hurt somebody".

- **§17's 2 s / 15 s is a target on the refresh loop.** It is what the tail interval and the
  snapshot interval are tuned to, and missing it raises an alert. It is not a behaviour change
  and no player-visible thing depends on it.

- **§18's 15 min / 24 h is a degradation ladder, and its reason is replaced.** The refusal
  past 24 hours stands, on quality grounds: a day-old index means stale μ, stale grids and
  stale intent, and a shortlist built from those is a confident bad list — §18's own worst
  outcome. It is **not** a safety stop, because there is no longer any safety-critical fact in
  the index for it to protect. Anyone who later moves a live-truth fact into the index for
  performance has to come back and re-argue this ADR, which is the point of writing the reason
  down rather than the number.

- **Staleness is internal.** It goes on ADR-0104's search record and into the structured logs,
  never onto ADR-0106's envelope. The wire gets it the day a product decision gives it a
  consumer, and that is an API release under ADR-0106 — correctly so.

- **`last_active_at` is projected from `auth.refresh_token_issued|rotated`, and the term's
  meaning changes to match.** The token lifetime is 24 hours, so the signal resolves **days,
  not hours**: `last_active_at` means *last session refresh*. §9.5's row is re-read as *this
  week* … *dormant* rather than *Active now* vs *3 days ago* — the −5 … +4 bounds are
  unchanged, because that is the discrimination they were actually buying, but the *Active now*
  end of the row is unreachable and the spec says so instead of claiming a precision the signal
  cannot carry. [ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md)
  §5 had already refused to print *"active 2 hours ago"* to a player under any name, so nothing
  downstream loses anything.

- **This makes `matchmaking` a reader of `auth`'s stream**, for a fact it does not own.
  Accepted, and narrow: it is one derived timestamp, read from a published contract, never
  written back, and it buys the only activity signal the platform contains. It is not a licence
  for the projection to read any context's stream for anything it likes — the test is the
  invariant above.

- **The demanded-but-nonexistent contexts get no columns.** §7.2 puts `player_score`, six
  strands and `opponent_variety` in the row; ADR-0098 made them ports with a contract suite and
  `NoPlayerScoresExist` as a registered implementation. **The port is the contract; the index is
  one implementation of it, and today's implementation is the null object** — so the columns are
  not in the table, and no projection subscribes to a stream that does not exist. A column that
  is `null` for every row for a year is an invitation to read it as a measured zero, which
  ADR-0098's invariant forbids in as many words. What this ADR hands forward is the shape of the
  eventual adapter: [The scale posture](https://github.com/Raketa02/Raketa/issues/165) priced a
  per-row port at **+0.58 ms**, so when `player_score` ships it lands as **denormalised columns
  fed by the same tail reader**, never as a port call inside the walk.

## Consequences

**Easier**

- §18's ladder stops being a safety mechanism nobody could point at, and the refusal survives
  on a reason that is still true.
- A future column has a test to fail rather than a review to pass, which is the same move
  §7.2's forbidden-PII schema test already made for privacy.
- The index never has to be re-verified for correctness, only for quality — the backend's
  live re-verify (ADR-0095, ADR-0098, ADR-0109) is the whole of the safety story and stays in
  one place.

**Harder**

- **Liveness's activity dock is coarser than §9.5 claims**, and the document's own example
  (*Active now*) is not reachable. The bounds stay, so the term keeps its weight while
  discriminating less than the table implies — a real loss, recorded rather than hidden.
- **`REFRESH_TOKEN_EXPIRE_SECONDS` is now load-bearing for a matchmaking term.** A change to
  the token lifetime silently changes the resolution of a ranking input, and there is nothing
  in `auth` that would know to say so.
- **The index cannot answer *is this person available right now*** — by construction, forever.
  Any future feature that needs live presence needs a mechanism that is not this one.
- **`player_score` arrives as a schema change rather than as a configuration change.** The
  contract suite already forces the shape; this ADR means it also forces a migration and a
  projection when the provider lands.
