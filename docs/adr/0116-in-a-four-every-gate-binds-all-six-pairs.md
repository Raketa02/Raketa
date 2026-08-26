# ADR-0116 — In a four, every gate binds all six pairs

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

Every pairwise gate this map has settled is computed against **the searcher**, because every
one of them was decided while looking at a shortlist, where the searcher is one half of every
pair on the screen.

- [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) — the candidate
  index holds no block data at all; the searcher's live block set travels in the
  `SearchContext` as `exclude_player_ids` and the backend re-verifies the returned rows.
- [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) — the ninth gate
  *"binds every seat"*, applied at candidate generation (§9.2) *"before §9.9 enumerates
  combinations — so the group objective is drawn from an already-eligible pool and never sees
  the constraint."*
- [ADR-0103](0103-where-the-curve-saturates-the-gate-begins.md) — the tenth gate excludes a
  candidate at `Δμ ≥ LEVEL_TOL_mode`, against the searcher's μ.

**A four contains six pairs. The searcher is in three of them.**

Resolving [#180](https://github.com/Raketa02/Raketa/issues/180) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
found that the other three are gated against nobody. I search; the engine seats me with `a`,
`b` and `c`; all three passed every gate **against me**; nothing ever compared `a` to `b`.

Two of the resulting line-ups are not merely incoherent:

- **`a` blocked `b` last month.** ADR-0095 gives a block a *symmetric effect* and says it
  *"reaches every surface that shows one player to another"*. A line-up shows `a` to `b`, and
  the engine has just put them on a court together for ninety minutes.
- **`a` declared `WOMEN_ONLY`; `b` and `c` are men.** ADR-0096 chose **mutuality** precisely so
  that a one-directional filter would not *"leave a woman open to every man who searched
  `ANY`"*. Under a searcher-only gate she is open to every man a third party seats beside her.

In both cases the *rule* already covers the case and only the *mechanism* is searcher-shaped.
ADR-0096's own sentence — *"a player shares a court with all four for ninety minutes; binding
only the partner seat would be incoherent"* — is the argument for this ADR, applied one step
further than it was applied.

**A pairwise gate over candidates cannot be spent at candidate generation.** Eligibility for a
*seat* is a property of a **combination**, not of a candidate, so no filter over the index can
express it. §9.9 already has the precedent: *"any seat below `QUALITY_FLOOR` disqualifies the
whole combination."*

The level gate is the one that required an argument rather than a mechanism. In a four,
`w_bal` **can** see a wide gap that the pairwise level terms cannot — `balance_norm` reads
*team* strengths, so 3.0 + 4.0 against 3.5 + 3.5 balances almost perfectly (3.45 against 3.50)
while putting a 3.0 on court with a 4.0 in a friendly, which is the pairing ADR-0103's closing
paragraph refuses by name.

## Decision

**We will evaluate every absolute pairwise gate over all six pairs of a four, inside
enumeration, and admit only combinations in which all six pass.**

Three gates bind pairwise:

| Gate | Source | In a four |
| --- | --- | --- |
| Block | [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) | No block edge, either direction, between any two of the four |
| Gender preference | [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) | Mutually satisfied between every pair, not only with the searcher |
| Level | [ADR-0103](0103-where-the-curve-saturates-the-gate-begins.md) | `Δμ < LEVEL_TOL_mode` for every pair |

**Newness tightens the pairs it is in, not the search.**
[ADR-0113](0113-newness-changes-the-gate-never-the-weights.md) gates a newcomer pairing at
`LEVEL_TOL_COMP` in both modes, *"binding the pairing and not the search"*. Every pair
containing a newcomer therefore takes `LEVEL_TOL_COMP`, whoever ran the search. Gating only the
newcomer's own pairs with the searcher would recreate exactly the hole ADR-0113 was written to
close — the bad first game arriving through somebody else's list.

**The mechanism is one `K × K` bitmask.** Admissibility is precomputed once per line-up — 276
pair triples at `K = 24` — and a combination is admissible iff its three candidate-pairs are
set. Three lookups against 6 072 evaluations; the added work is `O(K²)` against a cubic
enumeration and cannot overtake it.

**It fails closed, without exception.** ADR-0095's paired invariant is inherited unchanged: *a
term that cannot be evaluated stands down; a gate that cannot be evaluated excludes.* Gender
and μ are already in the candidate index
([ADR-0111](0111-the-index-holds-only-what-a-player-changes-about-themselves.md)). Blocks are
not — ADR-0095 keeps them out of the index deliberately — so the line-up route makes **one bulk
block query over the `K` candidate ids**, and if it cannot be resolved the line-up refuses
rather than returning a four.

**Nothing changes for a shortlist, a deck, or singles.** There are no cross pairs in a two, so
the searcher-only reading is already the six-pair reading.

## Consequences

**A four can be impossible where candidates are plentiful.** Five eligible candidates no longer
guarantee an admissible combination. The honest answer is a **partial line-up** — the shape
[`the-two-contracts.md`](../specs/matchmaking/the-two-contracts.md) §5 already fixed — and it
needs a reason the client can say out loud, so `NO_ADMISSIBLE_COMBINATION` joins
`NO_CANDIDATE_ABOVE_FLOOR` and `POOL_EXHAUSTED` in the `unfilled_reason` vocabulary. Without
that code the gate is indistinguishable from a thin pool, on the screen and in the telemetry.

**It is harsher than a shortlist gate, and it compounds.** Every pairwise exclusion removes a
whole family of combinations. Combined with ADR-0113, a newcomer's for-fun four narrows three
of its six pairs from 0.90 to 0.55, and at launch density
([#161](https://github.com/Raketa02/Raketa/issues/161): 63% of searches already return fewer
than five candidates) **a newcomer's first doubles game may frequently be unreachable**. That is
the trade ADR-0099 and [#175](https://github.com/Raketa02/Raketa/issues/175) have both already
taken deliberately — *a bad match is worse than no match*, and a first game is the one this
product can least afford to get wrong.

**ADR-0096 is amended in one sentence and strengthened in its argument.** Its claim that the
gate *"is applied at candidate generation … so the group objective never sees the constraint"*
is now true only of the searcher's own three pairs; the group objective sees the other three as
an admissibility mask and still never scores on them. **A protected characteristic may gate; it
may never score** is untouched, and the fenced type at `app/engines/matchfit/` is untouched —
the mask is built in the module where the I/O is, before the pure scorer is called, exactly
where [ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5 puts
gating.

**ADR-0095's re-verify gains a second reader.** The backend already re-verifies the searcher's
blocks against returned rows; it now re-verifies the candidate-to-candidate edges of a returned
line-up too, on the same seam, for the same reason
([ADR-0109](0109-a-read-back-names-what-it-withholds.md)).

**One class of gate is deliberately left out: anything from a context that does not exist.**
[ADR-0098](0098-matcher-demands-as-executable-contracts.md)'s pending-pair set — *do these two
already have an open challenge* — is a `matches` fact that fails soft, and it stays soft and
searcher-only. A gate that fails closed on an absent provider would empty every line-up.

**It is falsifiable, and cheaply:** the count of combinations refused by the pairwise gate, per
line-up, recorded from the first search
([ADR-0104](0104-the-search-record-is-the-answer-and-never-expires.md)). If it is
indistinguishable from zero the gate is decorative; if it dominates the enumeration the pool is
too thin for doubles and that is a density finding, not a gate finding.
