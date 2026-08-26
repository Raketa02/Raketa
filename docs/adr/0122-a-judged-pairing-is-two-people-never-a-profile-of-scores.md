# ADR-0122 — A judged pairing is two people, never a profile of scores

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

`QUALITY_FLOOR` is the only constant in the engine that refuses to be an integer.
[`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md) §1 defines it by **six judged
pairings** and the constraint

```
Fit(case 3)  <  QUALITY_FLOOR  ≤  min( Fit(1), Fit(2), Fit(4), Fit(5), Fit(6) )
```

and [`ranking-weights.md`](../specs/matchmaking/ranking-weights.md) §10 read it off as **44**,
recording seven totals — `78.4 / 61.5`, `72.9 / 52.6`, `20.4 / 24.2`, `73.8`, `46.0 / 47.9`,
*high* — and claiming that each case *"now carries an explicit term-value reading"*, that the
floor is *"re-derivable by machine"*, and that the six are *"§20.1's first scenario fixtures"*.

**None of the three was true.** The document held only the totals. The working that produced
them was never written down, so §11's rule — *turning a term on is a ruleset release that
re-runs the six cases and may move the floor* — had nothing to re-run.

[ADR-0120](0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md) was the first decision to need
the fixture and the first to find it missing. It changed the availability formula and had to
re-check the floor; with no recorded reading for the struck `proximity` factor it could establish
only a **range**, `44.7 ≤ case 5 competitive ≤ 46.5`, and the floor survived on a worst-case
margin of seven tenths of a point that nobody could tighten.

Resolving [#186](https://github.com/Raketa02/Raketa/issues/186) reconstructed the readings rather
than restating them. **The recorded totals do not reproduce**, and not by rounding: an exhaustive
search of the reading space for case 1 finds nothing within a point of both `78.4` and `61.5`,
and the closest candidate requires scoring the same *"socially blank"* fact as `0.00` on playing
style and `0.20` on social vibe. Case 5 is worse — eighty distinct reading-sets land within a
third of a point of `46.0 / 47.9`, and none of them reads like *"average on everything"*.

Two of the discrepancies are explained rather than merely observed:

- **Case 4 still carries a deleted modifier.** Its readings give `80.2`; less the `intent_opposed`
  −6 that [`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md) §6 **deleted** and
  §7 records as deleted, `74.2` — against a recorded `73.8`. The §10 table predates its own §7.
- **§10's sensitivity line reads the wrong cell.** It states that case 5 read as misaligned puts
  it at `38.0`. `46.0 − 38.0 = 8.0 = 16.092 × 0.50`, which is intent `0.35` — the **for-fun**
  row's competitive-candidate cell. Competitive misaligned is `0.00`, which puts it at `32.3`.

Reconstructing exposed something the prose had been hiding, and it is the reason this is an ADR
rather than a spec edit: **two of the six cases are not describable as one pairing at all.**

- **Case 3′** — *just inside the level gate* — names a mode-relative constant.
  [ADR-0103](0103-where-the-curve-saturates-the-gate-begins.md) gates at `Δμ ≥ LEVEL_TOL_mode`,
  0.55 competitive and 0.90 for fun. At Δμ 0.54 the candidate is a hair inside competitive's gate
  and reads **0.554** on for-fun's curve, nowhere near a gate; at Δμ 0.89 competitive has already
  excluded them and there is no number to record. One Δμ cannot serve both modes.
- **Case 5** — *average on everything* — over-specifies. Level fit and predicted balance **read
  the same input**. Level `0.50` needs Δμ 0.275 competitive; balance `0.50` needs Δμ **0.132**.
  No pairing is average on both, so the median stranger as written is not two people but a
  wish-list of term values.

## Decision

**We will hold the six judged pairings as a fixture of inputs describing two people, and never as
a profile of term values.**

The fixture is [`judged-pairings.json`](../specs/matchmaking/judged-pairings.json), argued in
[`the-judged-pairings.md`](../specs/matchmaking/the-judged-pairings.md). Five rules follow, and
each of them decided a case.

1. **The fixture holds inputs; values are generated.** A case states μ, σ, shared and total grid
   cells, distance, both radii, tag ids, declared intent, gender and preference, block and hold
   state, and profile commit date. Every term value and every Fit is **derived**. This is
   [ADR-0120](0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md)'s lesson made structural: a
   formula change re-derives the whole fixture for free, which is exactly what it could not do.

2. **A case whose prose over-specifies is re-judged, never value-pinned.** Where two terms share
   an input, the **free** variable is pinned and the dependent one falls out. Case 5 pins **level
   at 0.50** — Δμ 0.275 — and predicted balance reads **0.160**. Balance cannot be the pinned
   term: on day one σ is a constant 0.34 for every player, so balance is a pure function of Δμ
   carrying no independent input, and pinning it would let a derived quantity drive the fixture.

3. **A case whose defining property is mode-relative is two pairings.** Case 3′ becomes
   **3′-comp** at Δμ 0.54 and **3′-fun** at Δμ 0.89. Case 5 is **not** split, and the distinction
   is not arbitrary: 3′ names a per-mode constant, while the median stranger is one pair of people
   whom a competitive and a for-fun searcher both meet. The modes reading one Δμ differently *is*
   the product — 0.275 sits inside `FUN_FREE_BAND` and reads 0.96, which is that band's entire
   argument.

4. **One searcher, six candidates**, in the shape [§20.1](../specs/matchmaking/matchmaking-engine.md)'s
   walkthroughs already take. Two cases become single-variable assertions against case 1: **case 2
   is case 1 with the grid emptied** (the deltas are exactly the availability weights, 12.6 and
   17.6), and **case 6 is case 1 with the candidate's radius shrunk** — `Fit(6) == Fit(1)`
   *identically*, which is the only form in which a machine can assert that a fact moved nothing.

5. **Every input is declared, and the gates are pinned neutral.** Both players
   `PREFER_NOT_TO_SAY` / `ANY`, no blocks either direction, no holds. A gate that binds inside the
   fixture would make a case unscoreable without anyone noticing; the six cases test the
   **scorer**, and [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s
   gate earns its own fixture when somebody wants one.

**And the two "day one"s are separated.** `ranking-weights.md` §11 reads the floor off *the
day-one live set*, which has silently meant two different populations: the day-one **term set**
(seven live, reliability stood down) and the day-one **market** (everybody a newcomer). The
fixture runs on the **day-one term set** and a **steady-state population**. The reason is
[ADR-0113](0113-newness-changes-the-gate-never-the-weights.md): a pairing containing a newcomer
takes `LEVEL_TOL_COMP` in *both* modes, and at launch every player is inside the fourteen days —
so under a launch population `LEVEL_TOL_FUN` is exercised by no case at all, and a constant no
fixture exercises is a constant a release can move for free. That is the defect
[#184](https://github.com/Raketa02/Raketa/issues/184) had to print as a cost when the corpus's
near-constant σ left the ×32 coefficient unexercised; here it is avoidable, so it is avoided.
**Case 3′-fun is therefore unreachable in the first fortnight, and the spec says so.**

### What it costs, and what the reconstruction found

`QUALITY_FLOOR = 44` **holds, and its bound moved**:

```
24.5  <  QUALITY_FLOOR  ≤  44.5
```

The binding case is still the median stranger. **52 stays refuted** — case 5 reads 44.5
competitive and 47.8 for fun, so the case whose stated job is to sit at the bar is hidden by 52
in both modes rather than one. The integer does not move, so
[`the-five-numbers.md`](../specs/matchmaking/the-five-numbers.md)'s change rule is not triggered
and no case now decides differently.

But **§10's two-point allowance for *"the roundings in the readings"* is spent, not inherited.**
It existed because the readings were prose; they are now exact arithmetic over pinned inputs and
there is nothing left to round. 44 is a ceiling-tight number against 44.5, and the next term
activation that moves case 5 for-fun downward moves the floor with it.

**Case 4's verdict lost its mechanism, and the fixture asserts less than the verdict says.**
*"Shown, low, reason printed"* is unachievable: a candidate exceptional on everything who loses
only the intent term scores **80.3**, the second-highest number in the set. It read as low when
`intent_opposed` −6 existed. `the-five-numbers.md` §6 deleted that modifier entirely on the
argument that opposition already costs strictly more than silence — which is a claim about
*relative* cost and does not make 80 low — and **nobody checked what the deletion did to the one
case that exists to test intent**. The fixture asserts what is checkable: shown, above the floor,
intent term exactly `0.00`, reason printed. *Low* is a claim about rank within a population, and
a fixture has no population, exactly as [#180](https://github.com/Raketa02/Raketa/issues/180)
found when it gave the group objective ordered contrasts instead of judged verdicts.

**The evidence rule is now arithmetic rather than argued.** Case 1 read with both tag columns
*stood down* and renormalised scores **92.9 / 94.4** — higher than case 4, *everything
exceptional*, at 80.3. Declaring nothing beats declaring everything by twelve points. That is the
renormalisation pathology `the-five-numbers.md` §1 built the evidence gate against, and it has
never before had a number on it. It is recorded in the spec as a computed counterfactual row, and
it is why *"socially blank"* reads **0.20 on both columns** — tags declared, no relationship
fired, a measured zero — and never as a stand-down.

## Consequences

**Easier**

- §11's rule becomes executable. Turning a term on re-runs the six cases by machine and prints
  the new bound, instead of re-opening a judgement nobody recorded.
- A formula change costs nothing. [ADR-0120](0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md)
  would have been arithmetic instead of a range.
- A weight release that quietly hides the median stranger fails a named case rather than
  passing unnoticed.

**Harder**

- Every case now carries roughly fifteen inputs instead of a sentence, and the sentence was
  readable. The spec keeps the prose beside the inputs for that reason.
- A tag-relationship-matrix edit can move a case's reading. That is correct — §11 says a term
  activation re-runs the cases — but it means [`tag-relationship-matrix.md`](../specs/matchmaking/tag-relationship-matrix.md)
  edits now have a fixture to satisfy, where before they had none.
- The searcher is shared, so a searcher-side change moves all six readings at once. Honest, and
  occasionally inconvenient.

**Risks**

- **44 sits half a point under its bound.** Recorded rather than mitigated: the margin is now
  known exactly, where before it was known to be somewhere under a point.
- **Case 5's inputs are a solution to a judged value, not an observed pair.** The judgement is
  *the median stranger is average*, and the inputs realise it. A market whose real median differs
  makes the case wrong in a way the fixture cannot detect — which is what its falsifier, return
  rate just above versus just below the floor, exists to catch.

**Follow-ups**

- The reader is not built here — *this map plans; it does not build*. Filed as
  [#187](https://github.com/Raketa02/Raketa/issues/187): the §20.1 scenario harness, the
  release-time floor re-derivation, and `make` targets on this repo's generate-commit-diff idiom.
- `ranking-weights.md` §10's seven totals are **struck** and replaced by a pointer to the fixture.
