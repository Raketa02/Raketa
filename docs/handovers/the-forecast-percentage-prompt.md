# Paste this into a fresh session

Everything below the line is the prompt. It assumes a session started at the repo
root with no prior context. The diagnosis it references is
[`the-forecast-percentage.md`](the-forecast-percentage.md) beside this file.

---

Grill me on a decision I have to make about this repo's forecast engine. Read
`docs/handovers/the-forecast-percentage.md` first — it is the diagnosis, and it is
evidenced, so do not spend the session re-deriving it. Verify it if you want, but
briefly.

**Already fixed, so do not propose it:** the units defect is shipped.
`combine_group_sigma` returns `√(2·Σσᵢ²/n)` — the two-player basis, which at n = 2 *is*
`combine_sigma` exactly — so a four is no longer charged √2× a pair for the same doubt. A
level four of unsettled players moved 46 % → 62 %. Candidate A below is **done**.

**The established facts, which are not what I want grilled:**

`backend/app/engines/matchfit/v1/terms.py::forecast_pct` computes
`pct = clamp(100 − gap·145 − σ·32, 35, 96)`. One function, two callers, two
populations: the pairwise term passes a **two**-player combined σ; the group
forecast (`engines/matchfit/v1/group.py::_predicted`) passes
`combine_group_sigma` = `√(Σσᵢ²)` over **four**. The group's `gap` was correctly
re-based to side strengths when it was written; the σ was not, and
`sigma_coefficient=32.0` is pinned by the ruleset, `ranking-weights.md`,
`the-engine.md` and ADR-0103 to *"a typical σ_pair of 0.495"* — the n=2 figure.
So a four pays √2× what an identical pair pays for the identical per-player
doubt. On seeded data a perfectly level four reads 46%, which the client calls
*Lopsided*. Above σ_group 2.03 the clamp pins `pct` to its floor for every gap.

**What I actually need decided — this is the session:**

`pct` is currently two claims in one number: how far apart the sides are, and how
sure we are of either. `matchmaking-engine.md` §9.3.2 says that is deliberate —
*"level fit compares two anchors; balance asks how confident those anchors are"* —
but it was written about a pair, and `sigma_group` **also** crosses the wire
beside `pct`, so the same doubt is arguably priced twice and no document notices.

Three candidates, each with a real cost:

- ~~**A — re-base the group σ to the pair's scale.**~~ **Shipped.** It fixed the
  units without asking whether `√(Σσ²)` is the right aggregate for a group's
  uncertainty at all — which is now question 2.
- **B — take σ out of `pct` entirely.** Kills the double channel and makes `pct`
  mean what the card's word table claims. But it contradicts §9.3.2 head-on, and
  `the-words.md` §16 puts `confidence` in exactly one place in the product — so
  the doubt would then be expressed nowhere a player can see.
- **C — split the two claims into two served numbers.** One number, one claim.
  But ADR-0136 draws a hard line about what may cross beside a forecast, and
  whether a confidence is "a second score" is exactly the line it draws.

**How to run it.** Use the `grilling` skill. Attack my reasoning, not the code.
Specifically:

1. Make me say what `pct` is *for* — one sentence, no hedging — before I pick a
   candidate. If I can't, that is the finding.
2. Push on question 2 in the handover: is a doubles outcome's uncertainty really
   four independent error sources in quadrature, or is it closer to the
   worse-known **side**, or the worst single player? I have not thought about this
   properly and I will try to skate past it.
3. A is shipped, so the live question is whether it was **enough**. A level four
   of players nobody has a settled rating for still reads 62 % — *One side
   favoured* — with a gap of exactly zero. Make me say whether that is the product
   telling the truth or the product being unhelpful, and do not accept *it is what
   the spec says* as the answer.
4. Force a falsifier. `BalanceRules`' own docstring calls these *"the most
   directly falsifiable numbers in the engine"*. Whatever I pick, I have to say
   what data would prove it wrong and when we would look.
5. Ask whether `pct_min = 35` should exist for a group at all. A floor an entire
   population sits on is a constant, not a clamp.

**Constraints, so we do not design something unshippable:**

- ADR-0093 — a coefficient change is a **new dated ruleset**, never an edit to
  `r2026_08_26_a`.
- ADR-0119 — `make gen-ruleset-diff` regenerates a committed artifact that CI
  diffs, and it covers groups (34 `LINEUP` + 34 `FILL_SEATS`, 13 with recorded
  objectives). Expect it to move, and the printed report is the argument the PR
  makes.
- `make gen-judged-pairings` does **not** move for a group-only fix — the six
  judged pairings are pairwise. Which is its own finding: ADR-0122's fixture
  structurally cannot catch this class of defect, and if we care, the session
  should say what would.
- The shipped client assumes the current distribution: `balancePresentation.ts`
  word breaks at 85/70/55, and `BalanceBar`'s `BALANCE_SCALE` amplifies ×34
  around a centre of 50. If `pct`'s distribution moves, those need re-checking.

Do not write code. I want the decision and its argument. End with what would go
in the ADR.
