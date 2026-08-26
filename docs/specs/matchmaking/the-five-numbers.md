# The five numbers that decide whether the product says nothing at all

Settles [#167](https://github.com/Raketa02/Raketa/issues/167) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

Most of the matcher's constants are a starting vector in a config file. These five are
**product decisions wearing a config file's clothes**, because each one decides whether a
player is shown somebody or shown an apology. They are set here, with an argument, a
falsifying measurement, and a named owner — never a provenance.

**Owner of all five: `RobertConstantin02`.** With one developer the name confers no authority;
that is not its job. It is so that the next person to hold one of these inherits a named
handover rather than a config file with no history. Any change to any of the five **lands as
an ADR that names who moved it** ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)),
and for the quality floor the ADR must additionally name **which of the six judged cases below
it now decides differently**.

**None of the five is measurable before the outcome half of the telemetry chain exists**,
which needs `matches`, which is out of scope. They are decided by argued judgement, shipped
with their falsifier attached, and revisited when the evidence exists. The falsifiers are
therefore also **demands on the search-side telemetry** (§6) — a search-time fact that is not
recorded from the first search cannot be reconstructed later, and a number whose falsifier can
never be run is a starting position that has quietly become permanent.

---

## 1. The quality floor — set by six judged cases, not by an integer

`QUALITY_FLOOR` is the Fit below which a candidate is not shown at all. It cannot be
calibrated against a distribution: there are no players, and the weights are not fixed. It is
therefore **defined by the cases it must satisfy**, and its integer is read off those cases
once the weights land.

Each case is *a searcher, and one candidate*. The verdict is whether that candidate appears.

| # | The candidate | Verdict | What it constrains |
|---:|---|---|---|
| 1 | Same level, free the same three evenings, five minutes away — nothing in common socially, no history either way | **Shown** | If this is not shown, nothing is |
| 2 | Ideal level, even forecast, lives close — but the two grids share **no** slot at all | **Shown** | Availability overlap is evidence a game can be *arranged*, not a proposed time; the times rung exists for exactly this |
| 3 | Two levels above, forecast lopsided, everything else fine | **Not shown** | The evening §9.7 exists to prevent |
| 4 | Everything exceptional, but the searcher is in competitive and the candidate has declared friendly-only | **Shown, low, reason printed** | Intent is a weight and not a gate ([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)) |
| 5 | Average on everything. Nothing bad, nothing good — the median stranger | **Shown** | This is where the bar sits |
| 6 | A strong match well inside the searcher's radius — but the searcher is outside **theirs** | **Shown, docked, card says so** | A candidate's own radius is a Liveness dock and never a gate ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)) |

As a constraint on any candidate weight vector:

```
Fit(case 3)  <  QUALITY_FLOOR  ≤  min( Fit(1), Fit(2), Fit(4), Fit(5), Fit(6) )
```

**If no weight vector satisfies it, that is the useful failure** — either the weights are wrong
or one of the six is misjudged, and the argument happens against a named case rather than
against an integer somebody dislikes. This is the constraint handed to
[The ranking weights](https://github.com/Raketa02/Raketa/issues/168), which fixes the integer.

The document's starting position of **52** is not adopted and not rejected here; it is simply
not yet an answer to anything. It survives only if it satisfies the six.

> **Resolved in [`ranking-weights.md`](ranking-weights.md) §10, and the failure this section
> anticipated is the one that happened.** No weight vector satisfies the six in for-fun, and the
> diagnosis was that neither instrument could do the job — the floor is now backed by a level
> gate ([ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)). **Case 3 is
> excluded by that gate rather than by the floor**, so it no longer bounds the floor from below
> and is replaced by **case 3′**, the worst pairing still admitted to scoring. **52 is refuted by
> case 5** — the median stranger scores 46.0 in competitive, so 52 hides the case whose stated
> job is to sit at the bar. The floor is **44**, and all six now carry explicit term-value
> readings so they can be re-run by machine.

- **Falsified by:** return rate of games arising from candidates just above the floor versus
  just below it. Requires the outcome half.
- **Never relaxed, and the empty-result rate is never on its own sufficient grounds to move
  it** ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)).
- **One floor, both modes, every sport.** Each extra dimension is another place the bar can be
  lowered quietly for whichever pool is thin — *"tennis is sparse, so tennis's bar is lower"*
  is the Wikimedia move with a per-sport label on it. A mode that genuinely needs its own bar
  earns one later, with evidence, as an ADR.

### The evidence rule that sits beside it

The floor is a fixed bar over a score whose ingredients vary **per comparison**: §10
renormalises for that candidate, so a candidate missing a term they would have scored badly on
is *lifted* by its absence. Ranking survives this — absence is not evidence of badness. A
**cut** does not: at the bar, giving nothing becomes a small advantage over giving something
mediocre.

**The bar stays absolute, and a separate rule carries the honesty:** below a minimum of
evidence *about that specific person*, they are not shown — **a gate, not a score adjustment**,
in keeping with [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)'s *a gate
may be honestly empty; a term may never be honestly neutral*.

- Expressed as a **fraction of the terms live for the platform**, never a count, so it keeps
  meaning the same thing when a term turns on and the denominator changes. **At least half.**
- It counts **gaps specific to that person**, never platform-wide absence. On day one nobody
  has a reliability record; that must not gate the market.
- **Today it excludes nobody**, and that is the point. With the availability grid required
  ([ADR-0102](../../adr/0102-silence-is-never-scored.md)) every new profile produces evidence on
  every day-one term. It is standing insurance, in place before it is needed, so that the day a
  new term arrives *we know nothing about this person* cannot quietly become a passing score.

---

## 2. `MIN_SHORTLIST` — 5

**What it now does.** It no longer triggers anything. [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)
removed automatic widening: the engine never widens on its own, it carries the offers with
their real counts and the player takes one. `MIN_SHORTLIST` is what decides **whether the
offers are computed at all**.

Computing them means genuinely re-running generation and scoring per rung — the counts must be
real, because a count on a screen that was estimated breaks the third refusal. That is roughly
3 ms per rung ([#161](https://github.com/Raketa02/Raketa/issues/161)), cheap but not free, and
on most searches it is a lever nobody needs.

**The value: 5, not the document's 3.** Three results is already a thin screen; the offers cost
about 6 ms; and the number's real question is *how short is short enough that the player would
want another option*. At launch density this means offers are computed on roughly two thirds of
searches rather than one half ([#161](https://github.com/Raketa02/Raketa/issues/161): with 20
players scattered over a metro, 49% of searches return fewer than three candidates and 63%
fewer than five).

- **Falsified by:** rung take-up rate by shortlist length. If nobody holding four or five
  results ever takes an offer, 5 is too high.
- **The density hypothesis it now owes** rises with it: players per sport per district needed
  to clear **five** with no rung taken. It cannot be borrowed — nobody publishes a measured
  density threshold for a local matching product.

---

## 3. The widening ceiling — twice, clamped to the profile's own maximum

The ladder is **times → radius ×1.5 → radius ×2.0**
([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)). There is no third
radius rung.

- **Why it stops at double.** [#161](https://github.com/Raketa02/Raketa/issues/161) measured
  that at launch density, tripling the radius still leaves 15% of searches under five
  candidates. Widening does not rescue a thin market; past double it mostly spends the player's
  travel budget on failing. Recruiting a city club by club is worth more at that size than
  every term in §9.3 combined.

- **The cap already exists and is not this ticket's to invent.** The search radius is a Player
  profile field — `backend/app/modules/player_profile/domain/search_radius.py`, **1–50 km,
  whole kilometres, default 10**, set at profile commit and edited afterwards through
  `SearchRadiusChanged`. The glossary already gives it both halves of its job: *a filter when
  the player searches, and a weight when the engine proposes*.

  **Every rung clamps to `SEARCH_RADIUS_BOUNDS.maximum_km`.** A relaxation may never offer a
  radius the player could not have set for themselves — that is the same principle as *a rung
  may only relax what the searcher themselves asked for*, applied to the range the product
  allows them to ask within.

  Two consequences, both intended:
  - A searcher already at 50 km gets **no radius rung at all** — only the times rung. The
    honest empty state arrives sooner for them, correctly: there is nothing left to offer.
  - A searcher at 40 km has both multipliers clamp to 50, so **one radius rung is offered, not
    two**. A rung that would duplicate another rung's radius is not offered twice.

- **There is no per-search radius input.** The searcher's ask *is* their profile radius. A
  player who wants 40 km sets 40 km — that is their ask, not a relaxation.

- **Taking a wider search repeatedly offers to become the default.** *"Keep 15 km?"*, inline,
  bounded by the profile's own slider, and **never a silent write**. This is the third instance
  of one pattern — the intent drift prompt ([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md))
  and *"Keep these times?"* are the other two — and consistency is the argument. The engine
  notices drift and asks; it never acts on it.

- **Falsified by:** acceptance rate per rung. A rung whose matches never convert should be
  removed, not tuned.

---

## 4. The reliability bar — 70, on the number the player can see

**Which number.** The **published Player Score** — the one on the player's own profile — and
not the matcher's private per-mode blend of the six strands. The two are different numbers: the
screen blends at 35/20/15/12/10/8, §9.3.4 weighs per mode at 25/32, 24/4 and so on.

[ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) already rules that the
matcher reads what the player is shown and never re-derives it. A penalty justified by a figure
that exists nowhere a human can look is unexplainable, and a player who works their visible
score back up must be able to see the penalty lift.

**This is the one deliberate place the matcher reads the blend instead of the strands**,
recorded as an exception so it does not later read as an oversight.

**The value: 70.** Roughly *you have missed something like a fifth of what you committed to*.

**The demand this raises on `player_score`.** Does a published score exist after one game, and
does it mean anything that early? The contract, in the shape the other demands take
([ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)): **the score is not
published until there is enough behind it to be fair, and until it is published the bar does
not fire.** A bar that can brand somebody on one observation is worse than no bar.

- **Falsified by:** ghost and no-show rate of games arising from candidates just above the bar
  versus just below it.
- **Never relaxed, at any rung.**

## 5. The reliability penalty — `MODIFIER_BUDGET + 1`, which is 11 today

Derived, not picked. The property that has to hold is the document's own sentence: **a stack of
small positives must never lift somebody over a recent no-show.** The modifier stack is clamped
to ±10, so the smallest penalty that keeps the promise is **11** — and defining it as
`MODIFIER_BUDGET + 1` means it moves by itself if the budget ever does. The document's 12 has
no separate argument behind it.

**And the promise is smaller than the sentence sounds, which is stated rather than fixed.** The
penalty guarantees the *modifier stack* cannot erase a no-show. It does nothing against the
main score: a candidate who is otherwise a superb match still lands well clear of the floor
after taking it, and appears — low, with the reason printed.

That is the right outcome, and it is why the bar is a dock rather than an exclusion:

- Excluding outright would be the platform refusing to show a genuinely good match over one
  missed game. *The weights persuade, the player decides* — and where a player wants somebody
  gone entirely, the block exists ([ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)).
- The sentence in §9.3.4 overstates what the number delivers. **The number is not changed to
  match the sentence; the sentence is corrected.**

---

## 6. What was deleted: the opposite-intent penalty

`intent_opposed` (−6) is **removed**. §6.4 scores a directly opposite declaration **0.00**
*and* levies a further flat modifier — the same single fact moving the score in two places,
which §6.5 and §9.3.6 forbid everywhere else in the same document.

The zero is the whole answer, and the gap that matters is already the right shape:

- A candidate who has **not declared** has the term dropped and renormalised away — they are
  scored as though intent did not exist.
- A candidate who has declared **the opposite** loses the term's entire weight.

So declaring against the searcher already costs strictly more than saying nothing, without a
second charge. The extra modifier existed to *bury* the candidate, which is a gate wearing a
modifier's clothes, and [ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)
settled that intent is a weight and not a gate.

The six cells of the alignment table are unchanged and were settled in
[ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md).

---

## 7. What the search-side telemetry must record, from the first search

Handed to [The search-side telemetry](https://github.com/Raketa02/Raketa/issues/169) as a
demand, in the shape [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) used
for the contexts that do not exist. **Every fact here is search-time and cannot be
reconstructed afterwards.** Without them, all five falsifiers above are unrunnable even on the
day outcomes arrive.

| For | Record, per search | Why it cannot wait |
|---|---|---|
| **Quality floor** | How many candidates were scored, how many cleared the floor, and **the Fit of the best candidate that did not** | *The best match you refused to show* is the entire falsifier, and it exists only at scoring time |
| **Quality floor** | Which terms produced evidence per scored candidate | The renormalisation basis. Without it a Fit is uninterpretable a year later |
| **Evidence rule** | Whether a candidate was withheld for insufficient evidence, and which terms were missing | Distinguishes *nobody was good enough* from *nobody was known enough* |
| **`MIN_SHORTLIST`** | Shortlist length, and whether the rung offers were computed | Take-up by length is the falsifier |
| **Widening ceiling** | Which rungs were offered, each one's real count, which was taken, and the radius clamp if it bit | Acceptance rate per rung; and the clamp tells you how many searchers are already at the ceiling |
| **Reliability bar** | Whether the penalty fired for each scored candidate, and whether it was what put them below the floor | Separates *docked* from *docked out* |

Nothing here is a display string, and nothing here crosses the wire outward — this is the
engine's own record ([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md)).
