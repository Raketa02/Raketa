# Handover — the forecast percentage is charging a four twice for the same doubt

**Status:** **candidate A shipped 2026-09-02** — the units defect is fixed and the arithmetic
below is history. What is still open is the question underneath it, and the prompt to grill it
with is [`the-forecast-percentage-prompt.md`](the-forecast-percentage-prompt.md).

> **What changed.** `combine_group_sigma` now returns `√(2·Σσᵢ²/n)` — the two-player basis the
> coefficient was always calibrated against, which at n = 2 *is* `combine_sigma` exactly, so
> every pairwise reading is byte-identical. A level four of unsettled players moved 46 % → 62 %.
> The ruleset diff moved 13 group objectives by a uniform +3.552363 and flipped no seating;
> the judged pairings and the walkthroughs did not move at all.
>
> **What did not change.** `pct` still discounts for doubt, so a level four of players nobody
> has a settled rating for still does not read *very even*. Whether it should is §B/§C below,
> and it is a product decision rather than a defect.
**Scope:** `pct` on `ForecastSchema` — the number the builder's card prints and the number
`balance_norm` feeds into the group objective `G`. Nothing else.

---

## The one-paragraph version

`pct` answers *how even will this game be*, and it is deliberately **two** claims in one
number: how far apart the two sides are, and how sure we are of either. That was designed
for a **pair**. The group forecast reuses the same formula and the same coefficient on a
spread combined over **four** people, which is √2 times larger by construction — so a four
is charged 1.41× what an identical pair is charged for the identical per-player doubt. On
the seeded cohort that puts a perfectly level four at **46%**, which the client's own word
table calls *Lopsided*, with a printed gap of `0,00` directly above it.

---

## The mechanism, exactly

`backend/app/engines/matchfit/v1/terms.py`:

```python
def forecast_pct(gap: float, sigma: float, rules: BalanceRules) -> float:
    return clamp(100.0 - gap * rules.mu_coefficient - sigma * rules.sigma_coefficient, ...)
```

Released values (`backend/app/modules/matchmaking/infrastructure/rulesets/r2026_08_26_a.py`):

| | |
| --- | --- |
| `mu_coefficient` | 145.0 |
| `sigma_coefficient` | 32.0 |
| `pct_min` / `pct_max` | 35 / 96 |

**One function, two populations.**

- Pairwise (`predicted_balance`): `gap` = `|Δμ|` between two players, `sigma` = the **pair's**
  combined σ (`_combined` in `matchmaking/domain/fence.py` → `combine_sigma(a, b)`).
- Group (`_predicted` in `engines/matchfit/v1/group.py`): `gap` = the distance between two
  **side strengths**, `sigma` = `combine_group_sigma` = `reduce(combine_sigma, sigmas)` over
  **four** players = `√(Σσᵢ²)`.

The `gap` was correctly re-based when the group forecast was written — a four's gap is
between side strengths, not between people. **The σ was not**, and the coefficient was never
re-derived. `forecast_pct`'s own docstring is where the merge is defended:

> *One forecast, two sets of people. A pairing's gap is between two players and a four's is
> between two side strengths, but the claim being made — how even will this be — is the same
> claim and reads the same three numbers.*

The claim is the same. The third number is not on the same scale.

### What it costs

`√(Σσᵢ²)` grows with `√n`, so at any per-player σ the four pays exactly `√2` × the pair:

| per-player σ | pair σ (n=2) | costs | four σ (n=4) | costs |
| --- | --- | --- | --- | --- |
| 0.35 | 0.495 | −15.8 | 0.700 | −22.4 |
| 0.60 | 0.849 | −27.2 | 1.200 | −38.4 |
| 0.85 | 1.202 | −38.5 | 1.700 | −54.4 |

The calibration comment in the ruleset, and `ranking-weights.md`, and `the-engine.md`, and
ADR-0103 all pin the intended operating point to **"a typical σ_pair of 0.495"** — the n=2
row. Nothing anywhere states an operating point for n=4.

Two consequences worth naming separately:

1. **The floor swallows the signal.** At σ_group ≥ 2.03 the clamp pins `pct` to 35 for
   *every* gap, so the forecast stops responding to the thing it is about. Four players at
   σ 1.02 each — ordinary for new accounts — is already there.
2. **It moves for a reason the player cannot act on.** Adding a fourth person lowers the
   forecast. Nothing they can do to the line-up fixes it.

### Reproduce it

```bash
cd backend && make up && make seed
# then, signed in as the-populated-player, POST /api/v1/lineups {"sport":"PADEL","mode":"FOR_FUN"}
```
Observed: all three arrangements read `pct 46`, `sigma_group 1.692`,
`split {your_side: 3.15, their_side: 3.15, gap: 0.0}`.

---

## What the specs actually say

**The σ term is intentional — for a pair.** `matchmaking-engine.md` §9.3.2:

> *Not the same term as level fit, and the difference is the point. **Level fit compares two
> anchors; balance asks how confident those anchors are.** Two players 0,03 apart with wide
> bands may play a lopsided game.*

**The group forecast is specified once**, `matchmaking-engine.md` ~line 1323, and it simply
reuses the constant:

```
forecast(four): σ_group = √(Σ σᵢ²)
                pct     = clamp(100 − gap·145 − σ_group·32, 35, 96)
```

**No document anywhere acknowledges the scale difference.** `the-group-objective.md`
contains zero occurrences of "σ" or "sigma".

**Every fixture in the repo uses a pair-scale σ_group** — `0.41` in `builder.test.tsx` and
`forecastMappers.test.ts`, `0.4` in the domain tests. No test has ever seen the number a
real four produces, which is why this survived to production data.

---

## The three candidate answers, and what is wrong with each

Nothing below is a recommendation. Each is a starting position to attack.

### A — Re-base the group σ to the pair's scale — **SHIPPED**

Present σ_group on the two-player basis, so n=2 is unchanged and n=4 lands where the
coefficient was calibrated.

- *For:* the narrowest possible reading — it is a **bug fix**, not a recalibration. One
  coefficient goes back to meaning one thing. Every pairwise number stays byte-identical.
- *Against:* is `√(Σσ²)` even the right aggregate for a **group**? A four's outcome
  uncertainty is not obviously the quadrature sum of four independent player σs. This fixes
  the units without answering that — **and it still does not**, so the question survives A
  and is question 2 below.

### B — Take σ out of `pct` entirely

`pct` becomes purely a function of the gap. Confidence crosses as `sigma_group`, which it
already does.

- *For:* kills the double channel. Today `pct` prices σ **and** `sigma_group` is served
  beside it, so a client that used both would count the same doubt twice — and no document
  notices this. It also makes `pct` mean exactly what the card's word table claims.
- *Against:* directly contradicts §9.3.2's *"two players 0,03 apart with wide bands may play
  a lopsided game"*, which is a real effect. And `the-words.md` §16 puts `confidence` in
  exactly one place in the product, so `sigma_group` currently has no surface — removing σ
  from `pct` would leave the doubt unexpressed anywhere the player can see.

### C — Split the two claims

`pct` is the gap alone; a separate served field carries the confidence, and the client draws
the caveat rather than the engine discounting the figure.

- *For:* one number, one claim, which is the rule ADR-0136 was written to hold.
- *Against:* ADR-0136 draws a hard line about what may cross beside a forecast — evidence for
  a figure already served, yes; a second score, no. Is a confidence a second score? And
  §16's *one place* rule was argued for.

---

## Constraints any answer has to satisfy

- **ADR-0093 / `terms.py` header:** *"No constants live here… changing one must be a dated
  release rather than a code change."* A corrected coefficient is a **new dated ruleset**,
  not an edit to `r2026_08_26_a`.
- **ADR-0119 — the ruleset gate.** `make gen-ruleset-diff` regenerates a committed artifact
  and CI diffs it; the report it prints is the argument the PR has to make. The corpus
  **does** cover groups (34 `LINEUP` + 34 `FILL_SEATS` answers, 13 with a recorded
  `objective` and `arrangement`), so a σ rescale moves `G` and can flip seatings where
  balance was the deciding margin. Expect a real diff and be ready to defend it.
- **`make gen-judged-pairings` will NOT move.** The six judged pairings are pairwise only —
  `judged-pairings.md`: *"One searcher, six candidates"* — and carry `sigma_pair`. Worth
  saying out loud: **ADR-0122's fixture structurally cannot catch this class of defect**, and
  that is its own finding. If the answer is B or C, the pairwise numbers move too and this
  gate fires.
- **ADR-0103** pins the level gate to the pairwise saturation point (*"reaches its floor at
  Δμ ≈ 0.34 for a typical σ_pair of 0.495"*). Changing the **group** side leaves that alone;
  changing the pairwise side reopens the gate.
- **The client is already shipped against this.** `balancePresentation.ts`'s word breaks are
  85 / 70 / 55 and `BALANCE_SCALE` amplifies the gap ×34 around a centre of 50. If `pct`'s
  distribution moves, check the words still land — *Very even* at the top of the new range,
  *Lopsided* reachable at all.

---

## Questions for the grilling

1. Is `pct` **one** claim or two? If two, why is it one number — and if one, which one?
2. What is a *group's* uncertainty? `√(Σσ²)` treats four players as four independent error
   sources adding up. Is a doubles outcome's uncertainty actually that, or closer to the
   worse-known **side**'s, or to the max?
3. `sigma_group` crosses and nothing draws it. Is it evidence, or is it dead weight on the
   hottest payload in the product?
4. What would falsify whichever answer is chosen? `BalanceRules`' own docstring calls these
   *"the most directly falsifiable numbers in the engine"* — so what is the check, against
   what data, and when?
5. Should `pct_min = 35` exist at all for a group? A floor that a whole population sits on is
   not a clamp, it is a constant.
