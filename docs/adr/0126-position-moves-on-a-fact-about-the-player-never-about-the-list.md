# ADR-0126 — Position moves on a fact about the player, never on a fact about the list

- **Status:** Accepted
- **Date:** 2026-08-27

## Context

[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §9.6 places a greedy
maximal-marginal-relevance pass over the top of every ranked list, and §9.11 raises its constant
for the deck:

```
pick = argmax over remaining of ( rank_key(c) − λ · max_similarity(c, already_picked) )
λ = 8, over the top 12 only          λ = 14 in the deck

similarity(a,b) = 0.35·level_bucket_match + 0.25·distance_ring_match
                + 0.20·intent_match       + 0.20·tag_jaccard
```

Its motivation is real and stated in one good sentence: *the top five should not be five copies
of the same profile*, and variety is also how a player discovers that the interesting match was
the fourth one.

**No ticket on the map [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
ever read §9.6.** Fifteen tickets settled stages 1–6 and 8 down to the last constant; this one
was adopted by silence, and found only while assembling the spec set
([#172](https://github.com/Raketa02/Raketa/issues/172)). One line of it was adopted on the way
past — *diversification may reorder, never promote a candidate below the floor* — because it
follows from decisions already made.

**The refusal it collides with is not the one the ticket named.** The third refusal is about a
number the engine cannot explain, and diversity produces no number: `fit` is untouched, *Why 78?*
still adds up, and a card reordered by this stage prints exactly what it printed before. What
moves is **position** — and the promise about position is §9.5's, which
[ADR-0123](0123-silence-is-budgeted-per-player-at-the-notice-threshold.md) turned from a policy
into arithmetic two tickets ago:

> A silent movement never exceeds the movement that owes an explanation:
> `|Σ silent| ≤ MOVE_NOTICE` — per player, not per signal.

**Stage 7 is a third silent mover, and ADR-0123's roster test cannot see it.** That test pins the
silent set to exactly `{previous_decline, exposure_adjustment}` and asserts their reachable net.
It is a test about **stage 6**. A λ=8 spread runs one stage later, in the same units, and moves a
player further than the 6 points that owe an explanation — while the roster test stays green.
That is the failure the record was written to close, reappearing one stage downstream of where it
was closed: a guarantee that is **enforced where it was located and false where it is read**.

**There is no reason it could print.** ADR-0106's evidence vocabulary is closed and every code in
it is a statement about the candidate; [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)
assembles a card per candidate. *You are fourth because the three above you resemble each other*
is a fact about the **other rows**, and there is no candidate it is true of. A reason code for it
would have to editorialise about other people on somebody's card — which §9.5.2 already refused
for a milder case, keeping reciprocal asymmetry out of the card and in *Why 78?*.

**Three of its four similarity components are undefined.** `level_bucket`, `distance_ring` and
`tag_jaccard` appear in no spec file on this map. μ is continuous and distance is kilometres, so
adopting §9.6 means inventing two binning schemes and a set-similarity over tags first: bucket
widths and ring boundaries are constants too, and the bill is nearer eight than four — none of
which owns a falsifier.

**And one of them is the construction [ADR-0115](0115-a-tag-about-the-person-may-be-shown-never-scored.md)
struck.** `tag_jaccard` reads raw tag ids, so two people who both ticked `OPEN_TO_MEET_SOMEONE`
count as similar and one of them is pushed down the list. ADR-0115 was written about a term with
a weight and diversity only orders, so it does not automatically bite — but the effect here is
that a tag **about the person** decides who a player actually sees, which is further than the
rule was ever asked to reach, in the direction of demoting somebody rather than lifting them.

**It does nothing where this product is.** [#161](https://github.com/Raketa02/Raketa/issues/161)
measured that **63% of searches return under five candidates** at launch density. A spread over
the top 12 of a list of three is a no-op wearing a constant. Its first real effect arrives at a
density the map has no measurement of — the same density its own §24 falsifier needs, *challenge
rate on positions 2–5 with and without*, which requires an experiment the runtime ruleset store
was deliberately deferred for. A constant whose falsifier cannot be run is a starting position
that has quietly become permanent
([`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md)).

Two lesser facts, recorded so the reversal is argued rather than rediscovered: outside the
line-up's **cross pairs** it is the only computation in the engine between two people neither of
whom is the searcher, and unlike them it is never printed; and it is the only `O(k²)` pass over
the shortlist.

## Decision

**We will strike stage 7, in both places, and rule that a candidate's position moves on a fact
about that player and never on a fact about the shape of the list.**

1. **The pipeline is eight stages.** `DIVERSIFY` is gone; terminal becomes stage 7 and explain
   stage 8. The adopted floor constraint goes with it — it constrained a stage that no longer
   exists, and a rule with nothing to bind is how a table gets a row nobody can falsify.

2. **§9.11's raised λ is struck with it.** It is the same mechanism at a larger constant, and the
   deck's variety is its own three-band ordering policy — people who already said yes, then high
   liveness, then the rest — plus `PASS_SUPPRESS`. The deck was the stronger case, because a card
   at a time makes order the whole experience; it is not strong enough to buy an unexplainable
   move, and it was never the case §9.6 argued.

3. **The rule, stated for the next spread that wants in:** *position moves on a fact about the
   player, never on a fact about the list.* A future diversity pass ships only if it can name a
   **printable** reason, or if it enters the silent stack and shares
   [ADR-0123](0123-silence-is-budgeted-per-player-at-the-notice-threshold.md)'s **one** budget at
   `MOVE_NOTICE` — one budget over all silent movement, never one per stage, for the reason that
   record already gives: two budgets drift apart in an edit and break the guarantee silently.

4. **The roster test grows to say so.** §17.3's `Diversity never promotes a below-floor candidate`
   is vacuous once the stage is gone and is replaced by a property that can fail: **the silent
   roster is the whole of silent movement** — position is a function of `fit`, the printable
   liveness signals and the clamped silent net, and of nothing else. A later stage that moves a
   row without a reason then arrives as a red test rather than as a green one somewhere else.

5. **`ranking-weights.md` §13 gains a paragraph, not a row.** The row §24 had and §13 lost is now
   deliberately absent, in the shape [`the-availability-term.md`](../specs/matchmaking/the-availability-term.md)
   §4 already uses: a table titled *every constant* is exactly where a missing row goes unnoticed,
   so an absence that is an answer says it out loud.

## Consequences

- **A build agent can no longer implement §9.6 from the document.** `the-engine.md` §9 becomes the
  struck stage rather than the open one, and the README's conflict table carries the verdict where
  a reader meets the section.

- **At a mature density the top of a list may genuinely be five similar profiles, and this record
  chooses that.** It is the honest cost and it is named here so the reversal is one argued ADR
  rather than a rediscovery: it returns when there is a pool dense enough for a top five to be
  samey **and** `search_candidate` rows to prove it, held meanwhile as fog on the map — *the list
  reads like a leaderboard*.

- **What still spreads a list is unchanged, and worth not confusing with this.** The **exposure
  adjustment** at ±6 is silent, budgeted and **candidate-side**: it is fairness about who gets
  shown across many searches, not variety inside one. `PASS_SUPPRESS` and the deck's exclusions do
  the deck's version of the same. Neither is a diversity pass, and neither becomes one by standing
  where one used to be.

- **The engine loses its only candidate-to-candidate computation outside doubles**, so every
  pairwise function in it now reads the searcher and somebody — which is what
  [ADR-0120](0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md) and
  [ADR-0117](0117-a-group-term-reads-only-what-fit-did-not.md) each assume, and neither had a
  reason to state.

- **`tag_jaccard` is the second construction ADR-0115 has now struck**, and both were reached by
  the same route: a formula written about ids rather than about rows. The matrix is the only place
  a tag may express a relationship — a spreading function is not a second one.

- **Two of the ticket's four questions were the stage's neighbours and outlive it.** The deal's
  size and `SHORTLIST_MAX` were unnamed for the same reason the stage was unexamined, and they are
  set as ordinary constants with falsifiers in `ranking-weights.md` §13; they need no record of
  their own, and would have had one only by association.
