# ADR-0099 — Relaxation offers the searcher's own asks, and never bends the engine's judgement

- **Status:** Accepted
- **Date:** 2026-08-26

> **Amended 2026-08-26 by [`the-newcomer-path.md`](../specs/matchmaking/the-newcomer-path.md)
> §5: the ruling below stands, and two of its three subjects stop being *guaranteed inclusions*
> at all.** Since only the interest lift admits anybody, `inclusion_reason` described one of its
> three values. `NEWCOMER_WINDOW` becomes a printable **liveness reason** and `ZERO_EXPOSURE`
> becomes telemetry that never crosses the wire; `inclusion_reason` narrows to `INTEREST_LIFT`
> and stays a union so the next reason that genuinely admits somebody has somewhere to go. The
> substance is unchanged — **exposure fairness is still not a reason to show somebody a bad
> evening** — and the newcomer window's one real power is elsewhere: it exempts from
> **minimum evidence**, which is not the quality floor.

## Context

[`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md)
§9.7 holds the design's hardest conviction: **below `QUALITY_FLOOR` a candidate is not shown at
all**, and the pool is described instead. §9.8 supplies the mechanism that is supposed to make
that survivable — a relaxation ladder of four rungs, applied one at a time in a fixed order,
re-running generation and scoring, and announcing what was relaxed. This record settles
[#166](https://github.com/Raketa02/Raketa/issues/166) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**Three of the four rungs do not do what the table says they do.** Candidate generation (§9.2)
is `shard ∧ sport ∧ bounding box ∧ gates`. Nothing else filters anybody:

| Rung | The document's claim | What §9.2 and §9.3 make it |
| --- | --- | --- |
| 1 Familiarity | *"drop the novelty preference; show people you have played"* | Familiarity is a **modifier**, `−4 … +5` (§9.4). Those players were never excluded. The rung recovers at most four points, and for a `HERE_FOR_A_REGULAR_GAME` searcher the sign is already flipped, so it is a no-op |
| 2 Distance | radius × 1.5, then × 2.0 | **The only rung that admits a candidate who was not already there.** The searcher's radius is a §9.1 gate |
| 3 Availability | *"score candidates with no overlap, clearly labelled"* | Availability overlap is a **term** (weight 11 / 16). Nobody is excluded by it. Standing it down converts a **measured zero** into `NoEvidence`, the remaining weights renormalise, and the score rises |
| 4 Level | `LEVEL_TOL` × 1.4 | Level fit is a **term** (weight 26 / 11). Widening the curve makes a measured mismatch score higher |

So rungs 3 and 4 do not widen the catchment. They **raise scores until candidates clear a fixed
floor** — which is arithmetically indistinguishable from lowering the floor, and is the exact
move [`docs/research/matching-market-cold-start.md`](../research/matching-market-cold-start.md)
found the one on-point experiment against: Wikimedia lowered its search confidence threshold
specifically to cut Zero Results Rate, over 13.45M events, and the full sample **reversed** the
early win at Cohen's *w* = 0.001; they reverted. Their productive reduction came from a
completion suggester that fixed *query understanding* without touching the relevance bar.

Rung 3 additionally contradicts an invariant this map has already settled and `CONTEXT.md`
already carries, from [ADR-0098](0098-matcher-demands-as-executable-contracts.md): **a gate may
be honestly empty; a term may never be honestly neutral** — the test being whether a zero would
be *measured* or *invented*. A non-overlapping grid is a measured zero.

**There is no honest availability rung of the obvious shape.** §9.3.5's grid is a *recurring
weekly pattern* of 21 slots, and `proximity` is derived from it. Two grids that do not overlap
do not overlap in week two either. "Look further ahead" is not a knob that exists.

**On the announcement itself, the evidence is thinner than the design assumes.** The research
found **no A/B test anywhere** isolating disclosed widen against silent widen against a plain
empty state. What it did find points somewhere adjacent: Dietvorst, Simmons & Massey (2018)
measured that giving people *even a slight ability to adjust* an algorithm's output
substantially raises willingness to use it **and improves outcomes** — the measured lever is
**control, not disclosure**. Against it, the trust-calibration literature warns that an
explanation acts as a generic competence signal, so *"we widened your search to 16 km"* may make
a player accept a **worse** match with more confidence. Playtomic's out-of-range player
**requests** a spot the incumbents accept; Indeed and Zillow do not auto-widen at all; Baymard
endorses auto-relaxing only where there is exactly one clear alternative, and then with notice.

Two further defects surfaced while working the ticket:

- **§9.2 already contradicts §9.7.** Its *guaranteed inclusions* — interest-lifted, newcomers in
  their exposure window, zero-exposure players — **bypass the fit cut**. People below the floor
  are already being shown, which the "not shown at all" paragraph flatly denies.
- **`pool_description` cannot be a string.** [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)
  is the kernel's rule — *"emits values and stable machine codes, never display text"* — and
  the map extends it to the matcher unchanged. What crosses is structured; the client writes
  the sentence.

**And the pool is no longer one pool.**
[ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) made gender preference
a mutual ninth gate, so *players in range* is a different number for different searchers, and
the gap between a pre-gate and a post-gate count would be readable — which blocks are required
to be invisible in both directions.

## Decision

**We will treat relaxation as an offer over the searcher's own asks, and never as a change to
what the engine believes makes a good game.**

### 1. The line

**A relaxation rung may only relax something the searcher themselves asked for. It may never
touch a measurement, a term, a weight, or the quality floor.**

If `LEVEL_TOL` is too tight, that is a ruleset change carrying evidence (§24) — not a per-search
response to scarcity. A constant that moves because the market is thin *is* a market-driven
quality bar, whatever it is called in the config file.

### 2. The ladder, rebuilt

Three rungs, in this order. **The order is the engine's recommendation, not a lock.**

| Rung | The ask relaxed | Mechanism |
| --- | --- | --- |
| **A** | **Your times** | The engine tests single-slot additions to the searcher's own grid and offers the ones that would help. Carried as §8.1's existing `availability_override` for that one search |
| **B** | **Your radius** × 1.5 | `radius_km_used` on the response |
| **C** | **Your radius** × 2.0 | as above |

Times before distance: a slot you were already free in costs nothing, while distance costs
travel on every game forever. §9.8's rungs 1, 3 and 4 are **struck**. Rung A also covers the
empty-grid searcher, whose availability term returns `NoEvidence` today.

**Where the ladder stops is a number, and it belongs to
[#167](https://github.com/Raketa02/Raketa/issues/167)**, not to this record.

### 3. Offered, not applied

**The engine never relaxes anything on its own.** The strict answer returns, carrying every
available rung with its **real** count of candidates who would clear the floor; the client leads
with the cheapest and the player takes it. A player who knows they will never be free on a
Saturday may take the radius rung directly.

We accept the consequence deliberately: the engine computes the rungs it offers, so it knows
candidates exist and is withholding them. **That is the offer, and it is honest.**

**An accepted widen is scoped to that one search and never rewrites the profile.** Afterwards
the app may offer to make it permanent, reusing
[ADR-0094](0094-play-intent-declared-per-sport-in-its-own-aggregate.md)'s settled pattern:
inline offer on the search screen, 30-day suppression on decline.

### 4. Never relaxed

Every gate in §9.1 — now **nine**, including ADR-0096's gender preference — the reliability
floor, intent alignment below its floor, and, added here because its absence was the whole
danger, **the quality floor itself**.

**The §9.2 / §9.7 contradiction resolves in §9.7's favour, with one carve-out.** An **interest
lift is a human's own yes and outranks the engine's opinion**, so an interest-lifted candidate
may sit below the floor **with its reason printed**. The newcomer-window and zero-exposure lifts
may **reorder** but never **admit** below the floor: exposure fairness is not a reason to show
somebody a bad evening. *(Both accordingly leave `inclusion_reason` — see the amendment above.)*

**A candidate's own radius stays a Liveness dock and never becomes a gate at a relaxed rung**
(§9.3.8's reasoning is undisturbed). A gate that switches on with scarcity is the same disease.
`outside_their_radius` is already in the distance Evidence and **prints on the card**, at the
point of decision; the offer's count does not net it out. §24's falsifier is the right
instrument — *acceptance rate per rung; a rung whose matches never convert should be removed,
not tuned.*

### 5. What the app says instead

Past the last rung the shortlist is **empty** and the pool is **described**, structured, per
ADR-0022: `{sport, radius_km_used, players_in_range, window, post_gate: true}` plus reason
codes. Rungs cross the same way: `{rung, ask: TIMES | RADIUS, radius_km, slot,
candidates_above_floor}`. The client writes every sentence.

**The count is always post-gate, and no pre-gate count is ever carried**, so there is no delta
to read off. It is the only number that is true for that searcher, and refusal 3 binds it: it is
a number on a screen, so it counts real rows in the index and never estimates.

**The empty state is a primary screen, not a grey line** — NN/g's eye-tracking found users
missing a lightweight no-results message entirely and fixating on what sat below it.

**Availability overlap is evidence that a game can be arranged; it is never a proposed time.**
The matcher matches players and stops. No court is booked and nobody can promise a slot before
one exists, so `next_slot: {day, part}` is a reason on a card — *"you both play Saturday
mornings"* — never a booking, and rung A's offer is about the searcher's **grid**, not about a
game at ten o'clock. Who plays when is agreed by the players themselves, on a surface out of
scope here.

### 6. Doubles, and the deck

**A partial line-up is the answer.** When four seats cannot be filled above the floor, ⚡ returns
the seats that clear it, leaves the rest empty and says which. **A seat is never filled below
the floor to complete a four** — the group is the objective (§9.9), so one bad seat is a bad
evening for all four. §8.4 already specs completing a half-built game.

**The ladder does not reach the deck.** The deck has no surface to hang an offer on and its own
exclusions exhaust it faster than any pool; it runs out and says so.

### 7. The metric, with teeth

**Empty-result rate is a guardrail metric** — Kohavi's and Spotify's vocabulary, used here
deliberately so the position stops reading as idiosyncratic. It is reported **only** paired with
the return rate.

**Any change to `QUALITY_FLOOR` lands as an ADR**, and **the empty-result rate is never
sufficient grounds for one on its own.** The precedent is the SRE error budget: the protection
is not that the number can never move, it is that moving it is an attributable act by a named
person rather than a drift by whoever is under pressure that quarter. **Who owns each number by
name is [#167](https://github.com/Raketa02/Raketa/issues/167)'s business**; this record fixes
only the rule.

## Consequences

**The engine can no longer make a thin pool look less thin.** That is the point, and it is also
the cost: in a new market the app will say *"no players within 8 km"* to real people who wanted
a game, and the only cures it may offer are their own two asks. We are choosing this **on
principle, and the record should say so** — the research found **no controlled comparison of an
honest empty state against a low-quality result, in any domain**. §9.7's central conviction is
unfalsified and unsupported in the published record. The best external support is not a study
but a pattern at maximum scale: Google and Microsoft ad-quality floors suppress low-quality ads
*even when there is no competition*, in a business with maximal incentive to fill the slot.

**Half of a published design section is struck**, and anyone reading §9.8 without this record
will implement a ladder that quietly lowers the bar. The conflict table in
[`docs/specs/matchmaking/README.md`](../specs/matchmaking/README.md) carries the correction;
the source document is never edited.

**Every rung now costs a tap.** Offered relaxation is slower than applied relaxation, and some
players will abandon at the offer who would have accepted a widened result handed to them.
Dietvorst is the argument that the trade is worth it; it is measured on adjacent tasks, not on
this one, and **acceptance rate per rung is the number that would prove us wrong**.

**Rung A can manufacture ghosts.** A player who adds a Saturday slot they are not truly free in
produces a game they cannot attend, and ghost rate is worse than a decline. It is the sharpest
reason the rung must be an offer: only the player can answer truthfully, and the engine must
never widen a grid on their behalf. Watch ghost rate against rung-A acceptances specifically.

**Relaxation is now the honest cure for one problem only, and cannot touch the other.** Rungs A
and B/C help a searcher whose *asks* are narrow. They do nothing at all for a market that is
genuinely empty, or for a searcher whose ninth-gate preference makes their pool a fraction of
the city's. For those, the empty state is the entire answer — which is why
[#167](https://github.com/Raketa02/Raketa/issues/167)'s numbers and the honesty of the pool
description carry more weight than the ladder does.

**A density hypothesis is now owed.** Players per sport per district needed to clear
`MIN_SHORTLIST` **without** any rung, with its falsifier. It cannot be borrowed — nobody
publishes a measured density threshold for a local matching product; Nextdoor's 10 verified
members over 21 days is a chosen policy. It has to be derived here and measured later, and it
belongs in §24's table.

**Standing search does not graduate.** It stays fog on the map, with its two claims now
separated: *waiting finds a better match* is contradicted by dynamic-matching theory given
signals this product does not have, while *waiting retains a player who would otherwise leave*
is untested, plausible, and a different metric. The refusals fix its boundary in advance:
**notifying a player that a candidate exists is admissible; acting toward the candidate is
not.**
