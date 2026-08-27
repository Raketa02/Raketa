# The six judged pairings, term by term

Settles [#186](https://github.com/Raketa02/Raketa/issues/186) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
The rules are [ADR-0122](../../adr/0122-a-judged-pairing-is-two-people-never-a-profile-of-scores.md);
the fixture itself is [`judged-pairings.json`](judged-pairings.json) and **every table below is
generated from it**. Nothing here is hand-typed, and a hand edit is a merge conflict waiting to
happen.

[`the-five-numbers.md`](the-five-numbers.md) §1 defines `QUALITY_FLOOR` by six judged cases
rather than by an integer. [`ranking-weights.md`](ranking-weights.md) §10 read the integer off
them as **44** and claimed each case *"now carries an explicit term-value reading"*. It did not.
This is that reading, made for the first time.

---

## 1. The searcher

One searcher, six candidates — [§20.1](matchmaking-engine.md)'s walkthrough shape. Declared once;
every case varies only the candidate.

| | |
|---|---|
| Level μ | **2.80** — §20.1's own walkthrough players average there, and it is [#185](https://github.com/Raketa02/Raketa/issues/185)'s corpus centre |
| σ | **0.34** — every rating today is an *Initial Estimate* |
| Search radius | **10 km** |
| Availability grid | **4 cells of 21** ([ADR-0102](../../adr/0102-silence-is-never-scored.md)) |
| Social tags | `PLAYS_TO_WIN`, `WARMS_UP_PROPERLY`, `HERE_TO_IMPROVE`, `HERE_TO_MEET_PLAYERS`, `STAYS_FOR_A_DRINK`, `BOOKS_THE_NEXT_ONE` |
| Gender · preference | `PREFER_NOT_TO_SAY` · `ANY` |
| Clock | **2026-09-02, a Wednesday** — [#185](https://github.com/Raketa02/Raketa/issues/185)'s reason: on a Saturday `TODAY` and `WEEKEND` collapse |

**The grid is four cells, and `the-five-numbers.md`'s case 1 says *three evenings*.** The count
moved, and the reason is stated rather than buried: the median stranger's judged **half** overlap
is not expressible over an odd denominator, and case 1's job is *full* overlap rather than a
particular integer. Four is the smallest grid that carries both.

## 2. The population, and which "day one" this is

`ranking-weights.md` §11 reads the floor off *the day-one live set*. That phrase has silently
meant two different populations, and this fixture separates them:

- **The day-one term set — adopted.** Seven terms live, reliability stood down, the basis
  renormalised ×100/87 competitive and ×100/91 for fun.
- **The day-one market — rejected.** Every player commits **2026-01-05**, so nobody is a
  newcomer.

The reason is [ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md): a pairing
containing a newcomer takes `LEVEL_TOL_COMP` in **both** modes, and at launch every player is
inside the fourteen days. Under a launch population `LEVEL_TOL_FUN` is exercised by no case at
all — and a constant no fixture exercises is a constant a release can move for free.

**Its price, printed rather than discovered: case 3′-fun is unreachable in the first fortnight.**
It needs two established players, which is day fifteen at the earliest. It bounds the floor from
below at 24.5 against case 3′-comp's 19.5, so nothing turns on it; a launch-population reading
would put case 3′ at one Δμ of 0.54 and 19.5 / 31.1, and the floor would hold there too.

**The gates are pinned neutral and never bind**: both players `PREFER_NOT_TO_SAY` / `ANY`, no
blocks either direction, no holds. These six cases test the **scorer**.

## 3. The readings

| Case | Mode | Δμ | level | balance | intent | avail | style | dist | vibe | **Fit** | Verdict |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 1 | comp | 0.000 | 1.000 | 0.813 | 0.850 | 1.000 | 0.200 | 1.000 | 0.200 | **82.0** | Shown |
| 1 | fun | 0.000 | 1.000 | 0.813 | 0.850 | 1.000 | 0.200 | 1.000 | 0.200 | **67.5** | Shown |
| 2 | comp | 0.000 | 1.000 | 0.813 | 0.850 | 0.000 | 0.200 | 1.000 | 0.200 | **69.3** | Shown |
| 2 | fun | 0.000 | 1.000 | 0.813 | 0.850 | 0.000 | 0.200 | 1.000 | 0.200 | **49.9** | Shown |
| 3'-comp | comp | 0.540 | 0.018 | 0.000 | 0.850 | 0.000 | 0.200 | 0.333 | 0.200 | **19.5** | **Not shown** |
| 3'-fun | fun | 0.890 | 0.015 | 0.000 | 0.850 | 0.000 | 0.200 | 0.333 | 0.200 | **24.5** | **Not shown** |
| 4 | comp | 0.000 | 1.000 | 0.813 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | **80.3** | Shown |
| 5 | comp | 0.275 | 0.500 | 0.160 | 0.850 | 0.500 | 0.200 | 0.500 | 0.200 | **44.5** | Shown |
| 5 | fun | 0.275 | 0.962 | 0.160 | 0.850 | 0.500 | 0.200 | 0.500 | 0.200 | **47.8** | Shown |
| 6 | comp | 0.000 | 1.000 | 0.813 | 0.850 | 1.000 | 0.200 | 1.000 | 0.200 | **82.0** | Shown, docked |
| 6 | fun | 0.000 | 1.000 | 0.813 | 0.850 | 1.000 | 0.200 | 1.000 | 0.200 | **67.5** | Shown, docked |

```
24.5  <  QUALITY_FLOOR  ≤  44.5
```

**`QUALITY_FLOOR = 44` holds, and 52 stays refuted** — case 5 reads 44.5 competitive and 47.8
for fun, so the case whose stated job is *this is where the bar sits* is hidden by 52 in **both**
modes rather than one. The integer does not move, so
[`the-five-numbers.md`](the-five-numbers.md)'s change rule is not triggered and no case now
decides differently.

**But the margin is half a point, and §10's two-point allowance is spent.** That allowance existed
for *"the roundings in the readings"*; the readings are now exact arithmetic over pinned inputs
and there is nothing left to round. 44 is a ceiling-tight number. The next term activation that
moves case 5 for-fun downward moves the floor with it.

## 4. The three cases that are not what they looked like

### Case 3′ is two pairings

*Just inside the level gate* names a mode-relative constant:
[ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md) gates at
`Δμ ≥ LEVEL_TOL_mode`. At Δμ 0.54 the candidate is a hair inside competitive's gate and reads
**0.554** on for-fun's curve — nowhere near a gate. At Δμ 0.89 competitive has already excluded
them and there is no number to record. One Δμ cannot serve both modes.

### Case 5 over-specified, and was re-judged rather than value-pinned

*Average on everything* is not reachable. **Level fit and predicted balance read the same input:**
level 0.50 needs Δμ 0.275 competitive, balance 0.50 needs Δμ **0.132**.

The fixture pins **level**, and balance falls out at **0.160**. Balance cannot be the pinned term:
on day one σ is a constant 0.34 for everybody, so balance is a pure function of Δμ carrying no
independent input, and pinning it would let a derived quantity drive the fixture.

**Case 5 is not split per mode**, and the distinction against case 3′ is not arbitrary. 3′ names a
per-mode constant; the median stranger is one pair of people whom a competitive and a for-fun
searcher both meet. The two modes reading one Δμ differently **is the product** — 0.275 sits
inside `FUN_FREE_BAND` and reads 0.962, which is that band's whole argument: *a friendly against
someone a quarter-point above you is no worse than one against your exact twin.* Forcing 0.50
there means Δμ 0.575, which is not a median stranger but a noticeably mismatched one.

### Case 4's verdict lost its mechanism

`the-five-numbers.md` says *"Shown, low, reason printed"*. **Low is unachievable.** A candidate
exceptional on everything who loses only the intent term scores **80.3** — the second-highest
number in the set. It read as low when the `intent_opposed` −6 modifier existed. §6 deleted that
modifier on the argument that opposition already costs strictly more than silence, which is a
claim about *relative* cost and does not make 80 low — and nobody checked what the deletion did
to the one case that exists to test intent.

**The fixture asserts what is checkable:** shown, above the floor, intent term exactly `0.00`,
reason printed. *Low* is a claim about rank within a population, and a fixture has no population —
the same distinction [#180](https://github.com/Raketa02/Raketa/issues/180) drew when it gave the
group objective ordered contrasts instead of judged verdicts.

## 5. Two cases are one-line assertions against case 1

Because the searcher is shared, two candidates differ from case 1's in exactly one input — which
proves what the prose only asserts.

| | Differs by | Assertion |
|---|---|---|
| **Case 2** | `shared_cells` 4 → 0 | Fit falls by exactly the availability weight — **12.64 competitive, 17.58 for fun**. Availability overlap is evidence a game can be *arranged*, and its absence costs its weight and not a point more |
| **Case 6** | candidate radius 10 → 1 km | `Fit(6) == Fit(1)` **identically**. The searcher sitting outside the candidate's ring is a Liveness dock and never enters Fit ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)) |

Case 6's identity is the only form in which a machine can assert that a named fact moved
**nothing** — which is the whole of its verdict.

## 6. What "socially blank" is worth, and the counterfactual that proves it

Case 1 is *nothing in common socially*. Both players hold tags in both columns' domains and **no
relationship fires**, so both tag terms read the measured zero of **0.20** — never a stand-down.

The alternative is not a matter of taste, and here is the number that settles it. Case 1 read with
both columns *stood down* and renormalised over five terms:

| | comp | fun |
|---|--:|--:|
| Case 1, tags declared, nothing fires | 82.0 | 67.5 |
| Case 1, **both columns stood down** | **92.9** | **94.4** |
| Case 4, *everything exceptional* | 80.3 | — |

**Declaring nothing beats declaring everything by twelve points.** That is the renormalisation
pathology [`the-five-numbers.md`](the-five-numbers.md) §1 built the evidence gate against, argued
there in prose and never before given a number. It is why *socially blank* is a measured zero.

The candidate's tags are `QUIET_AND_FOCUSED`, `GENEROUS_ON_LINE_CALLS`,
`SETTLES_UP_ON_THE_SPOT`, `HERE_TO_COMPETE` — checked against all thirty-seven rows of
[`tag-relationship-matrix.md`](tag-relationship-matrix.md): no match, no complement, no clash in
either mode, and at least one id in each column's domain so neither stands down.

## 7. What the reconstruction found in the recorded totals

**The seven totals in `ranking-weights.md` §10 do not reproduce, and not by rounding.** An
exhaustive search of the reading space for case 1 finds nothing within a point of both `78.4`
and `61.5`; the closest candidate scores the same *socially blank* fact as `0.00` on style and
`0.20` on vibe. Case 5 admits eighty distinct reading-sets within a third of a point of
`46.0 / 47.9`, and none reads like *average on everything*.

Two discrepancies are explained rather than merely observed:

| Recorded | Reconstructed | Explanation |
|---|---|---|
| Case 4 · **73.8** | **80.3** | 80.3 − 6.0 = 74.3. The §10 table still carries `intent_opposed` −6, which §6 **deleted** and §7 records as deleted — **the table predates its own §7** |
| §10's *"misaligned puts case 5 at 38.0"* | **32.3** | 46.0 − 38.0 = 8.0 = 16.092 × 0.50, i.e. intent `0.35` — the **for-fun** row's competitive-candidate cell. Competitive misaligned is `0.00` |

The §10 totals are **struck**. They are superseded rather than corrected, because fitting readings
to a remembered total is the failure a fixture exists to prevent.

## 8. What this owes, and what it does not

**It owes no code today.** *This map plans; it does not build* — the reader is
[#187](https://github.com/Raketa02/Raketa/issues/187): the §20.1 scenario harness, the
release-time floor re-derivation, and `make` targets on this repo's generate-commit-diff idiom
(`gen-api`, `check-ruleset-diff`, third instance).

**It is not [#183](https://github.com/Raketa02/Raketa/issues/183)'s machine**, and the two must
not be merged. [`the-replay-harness.md`](the-replay-harness.md) asks *how does this ruleset move
the population* and has no floor in it; this fixture asks *does this ruleset still show the six
things we said it must*, which is pass/fail against named verdicts.
[ADR-0121](../../adr/0121-a-fixture-stands-for-a-comparison-never-for-a-city.md) already bars the
six from the synthetic corpus as circular, so they are designed not to overlap. Same idiom, two
targets.

**It adds nothing to the map's missing-surface fog.** The fixture is read in a pull request, not
in production, and every falsifier it touches was already written.
