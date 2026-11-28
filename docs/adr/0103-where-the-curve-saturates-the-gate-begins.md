# ADR-0103 — Where the curve saturates, the gate begins: a level gate at each mode's own tolerance

- **Status:** Accepted
- **Date:** 2026-08-26

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** The searches, the level-fit term, the quality floor and the judged pairings are gone (#579, #580), so the case-3 arithmetic, the never-relaxed list, the pool description's reason codes and #169's per-search counts below describe nothing that runs. The gate stands as the **level window**: two people may share a court only while `|Δμ|` is below their kind of game's own tolerance — 0.55 competitive, 0.90 for fun — with no constant of its own (`matchmaking/domain/level_window.py`). It is asked of every pair the proposer, the fill and a rescue would seat, and it bounds a post's level range.

## Context

[ADR-0098](0098-matcher-demands-as-executable-contracts.md) gave the matcher the invariant
every later context inherits: **a gate may be honestly empty; a term may never be honestly
neutral**, the test being whether a zero would be *measured* or *invented*. It governs what a
term may say when it knows nothing.

Resolving [#168](https://github.com/Rakieta02/Rakieta/issues/168) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Rakieta02/Rakieta/issues/155)
found the *other* half of the same idea missing, and found it by arithmetic rather than by
argument.

`the-five-numbers.md` defines `QUALITY_FLOOR` by six
judged pairings rather than by an integer, and states the constraint the weights must satisfy:

```
Fit(case 3)  <  QUALITY_FLOOR  ≤  min( Fit(1), Fit(2), Fit(4), Fit(5), Fit(6) )
```

with the note that **if no weight vector satisfies it, that is the useful failure.** It failed.

**Case 3** is *"two levels above, forecast lopsided, everything else fine"*, and its verdict is
**not shown** — the evening §9.7 exists to prevent. Under the design document's for-fun weights
it scores **60.4**, against **52.6** for case 2, whose verdict is **shown**. Competitive is
fine unaided (39.5); for-fun is not, and not marginally.

The cause is structural rather than a bad number. In for-fun, a zero on level *and* balance
together costs 18.7 points of 100, while a zero on availability alone costs 17.6 — and case 3
keeps its tags while case 2 loses its slots. **Any candidate two levels away who is socially
well matched outranks a same-level candidate who is socially blank, at every weight vector that
keeps social vibe the largest for-fun term** — which is item 1 of #168 and the clearest
statement in the product of what *for fun* means.

Three ways out were weighed. **Reweighting for-fun** closes the deficit only by moving roughly
nine points into level fit, which either makes level the largest for-fun term (deleting the
inversion) or drops availability to ~9 (contradicting case 2's own existence). **Re-judging
case 3 as shown in for-fun** removes the only *not shown* case, leaving the floor with no lower
bound in that mode and making one floor for both modes unsustainable — which
`the-five-numbers.md` refuses by name.

The third is the diagnosis, and it is mechanical:

| Δμ | Level fit | Predicted balance |
|---|---|---|
| below ~0.34 | discriminating | discriminating |
| ~0.34 → `LEVEL_TOL_mode` | discriminating | **pinned at `BALANCE_PCT_MIN`** |
| beyond `LEVEL_TOL_mode` | **pinned at 0** | pinned at `BALANCE_PCT_MIN` |

`pct = clamp(100 − Δμ·145 − σ_pair·32, 35, 96)` reaches its floor at **Δμ ≈ 0.34** for a
typical σ_pair of 0.495; [#164](https://github.com/Rakieta02/Rakieta/issues/164) promoted that
clamp from cosmetics to the term's zero, and this is where it bites. Level fit reaches zero at
`LEVEL_TOL_COMP = 0.55` and at `LEVEL_TOL_FUN = 0.90`.

So past `LEVEL_TOL` **both level-sensitive terms are blind**, and the engine cannot tell a 0.9
gap from a 2.5 gap. It is not that a large gap scores badly — it scores *identically* to a
moderate one, while the risk keeps growing. A quality floor is a bar over a score, and **a bar
cannot discriminate what the score cannot see.**

## Decision

**We will exclude a candidate whose level gap reaches the searching mode's own tolerance,
before anything is scored.**

```
gate:  Δμ  ≥  LEVEL_TOL_mode          ( 0.55 competitive · 0.90 for fun )
```

It is the tenth gate. **It introduces no constant** — it reuses the tolerance each mode's curve
already names, which is the whole argument: the gate sits exactly where the term stops having
an opinion.

And it states the invariant the case failure exposed, as the mirror of ADR-0098's:

> **A term may never be honestly neutral; and a term must never be blind over the range it is
> asked to score. Where the curve saturates, the gate begins.**

Three consequences follow immediately and are part of the decision:

- **It joins the never-relaxed list** in ADR-0099,
  beside the nine gates, the reliability floor and the quality floor.
- **It does not resurrect §9.8's struck rung 4.** ADR-0099 removed level relaxation because a
  rung may only relax what the searcher themselves asked for, and **nobody asks for a level
  range** — the searcher asks for a sport, a radius and some times. That is unchanged: this is a
  gate the player never set and never widens.
- **Both level curves become strictly informative over the admitted range.** Neither mode's level
  term can now return a saturated zero, because everyone who could is gone before scoring.

## Consequences

**The six judged pairings need a new lower bound, and get a better one.** Case 3 is now excluded
by the gate rather than by the floor, so it no longer constrains `QUALITY_FLOOR` from below. It
is replaced by **case 3′** — *just inside the level gate, forecast at its floor, no shared slot,
at the edge of the radius, no tag relationship either way* — the honest "nothing works" pairing,
which is a sharper lower bound than case 3 ever was because it is the worst thing the engine is
still willing to look at.

**The empty state gets a better sentence.** A thin pool now distinguishes *nobody at your level*
from *nobody good enough*, as separate reason codes on
ADR-0099's pool description. The client
writes both; the engine names which.

**In competitive it changes almost nothing, and that is accepted.** Candidates beyond Δμ 0.55
were scoring around 39 and `QUALITY_FLOOR` already hid them. The gate is close to redundant
there. Uniformity is the reason to keep it anyway: one rule, stated once, that makes the
exclusion *nameable* instead of emergent from a weighted sum.

**In for-fun it is a real exclusion, and it is the point.** A player at 3.0 will not be shown a
4.0 in a friendly. The document's own words are the justification — *the floor is nobody spends
the evening watching* — and that sentence was, until now, expressed nowhere: `FUN_FREE_BAND`
expresses the top of the curve and `LEVEL_TOL_FUN` expressed the bottom, but neither refused
anybody.

**A gate is harsher than a weight in a thin market, and this one has no relief valve.** At
launch density ([#161](https://github.com/Rakieta02/Rakieta/issues/161): 63% of searches already
return fewer than five candidates) it will occasionally be the reason a screen is empty. That is
the same trade ADR-0099 already took
deliberately — **a bad match is worse than no match** — and the empty-result rate remains a
guardrail metric and never sufficient grounds to move it.

**It is falsifiable, and the falsifier is specific:** acceptance and return rate of games at
Δμ between 0.75 and the gate — the widest gaps still admitted. If those convert as well as
games at Δμ 0.2, the tolerance is too tight and the gate moves with it, because the gate *is*
the tolerance. If they convert far worse, the tolerance is too loose and both move the other
way. **The gate and the curve can never drift apart, because there is only one number.**

The measurement needs the outcome half of the telemetry chain, which needs `matches`, which is
out of scope — so this ships as an argued judgement with its falsifier attached, like the other
five numbers. Search-side, [#169](https://github.com/Rakieta02/Rakieta/issues/169) must record
**how many candidates the level gate excluded, and the smallest Δμ among them**, per search;
neither can be reconstructed afterwards.
