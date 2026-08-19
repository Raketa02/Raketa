# The fit badge and the engine under it — seven terms against ten, and a clamp that is not there

Research output for `Raketa02/Raketa#6`. **Facts and citations only.** Where the specification
set and the shipped code disagree this file quotes both and states the delta. It does **not**
decide whether to bend the badge to the engine or the engine to the badge — that is the next
ticket, and the two answers are genuinely different products.

## Method, and what "verified" means here

The specification set was read on the branch that carries it. The engine was **executed**, not
read about: `MatchFitEngineV1().score(...)` was called ~215 000 times from the repo's own test
snapshot builders (`backend/tests/unit/matchmaking_snapshots.py`) under the project venv. Every
claim tagged **[EXEC]** below is the output of the shipped engine on constructed inputs — no
reimplementation, no inference from a docstring.

Six executions back this document:

| Run | What it did | Scale |
|---|---|---|
| **E1** Suite | ran the three matchfit test files as-is | 757 passed, 0 failed |
| **E2** Adversarial sweep | seeded random walk over every input the ten terms read, pushed to both extremes | 60 000 scores |
| **E3** Realistic sweep | same walk, restricted to inputs a real snapshot could carry, stratified by how many others are seated | 80 000 scores |
| **E4** Constructed corners | hand-built worst case and best case with all ten terms scoring | 2 scores |
| **E5** Unrated viewer | the case `UI` §B9 says omits the badge | 1 score |
| **E6** Determinism | the same inputs twice, and reason-object identity against `terms` | 2 scores |

**Source shorthand.** `1` = `1-now_screen_production_spec.md` · `UI` =
`rakieta-now-section-ui-spec.md` · `DOM` = `now-section-domain-spec.md` · `SPEC` =
`rakieta-now-section-specification.md` · `4` = `4-match_recommendation_engine_architecture.md`
(**design input, not an authority** — `README.md` L51–57) · `R5` =
`5-now_screen_architecture_review.md` · `ADR-27` =
`docs/adr/0027-fit-and-certainty-are-separate-ranking-is-policy.md` · `ADR-26` =
`docs/adr/0026-matchmaking-engines-snapshot-input-contract.md`.

**Two words that are not the same word.** `DOM` §A.0 and `R5` use **coverage** for Match Fit's
second number, and `ADR-27`'s *title* says "certainty" while its Decision says "coverage"
(`ADR-27:55`, `:74`). In the code, `coverage: int` (`app/engines/fit.py:473`) and
`Certainty` (`app/engines/forecast.py:55`) are unrelated: the first is the share of table weight
that ran, the second is the pairing forecast's grade of its own margin. This document uses
**coverage** for the first and **certainty** for the second, always.

---

## 1. The delta — what the card needs, what the engine gives

One row per input the `.fit` badge and its card consume. Left column cites the specification set;
middle column cites `backend/`; right column states the gap and nothing more.

| # | What the UI card needs | What the engine gives | The gap |
|---|---|---|---|
| 1 | **7 weighted terms** summing to 100: skill overlap 30, predicted balance 20, group reliability 15, time and travel 15, match type 8, price vs ceiling 7, preferences and side 5 (`1` §5.2 L930–940; restated `UI` §B9 L676) | **10 weighted terms** summing to 100: skill overlap 24, predicted balance 14, time fit 12, **match viability 12**, group reliability 11, travel 8, ladder qualification 6, price 6, match type 4, familiarity 3 (`matchfit/v1/constants.py:84-93`; `WEIGHT_TOTAL = 100` at `:72`, enforced `:349-353`) | Three of the seven are **split or renamed** (time and travel → `time_fit` 12 + `travel` 8), two are **new** (`match_viability` 12, `ladder_qualification` 6), one is **new from a modifier** (`familiarity` 3), one **does not exist** (preferences and side 5). No shipped term corresponds to *preferences and side*; `PlayerProfile.appetite` and `.commitment_horizon` exist on the input and are read by no v1 term |
| 2 | **3 modifiers** after the weighted sum, before the clamp: `+8` promotion badge, `+5` played none of them, `−8` three or more, all regulars (`1` §5.2 L963–973) | **None.** *"The prototype's `+8` / `+5` / `−8` modifiers, applied after the weighted sum … are abolished; ladder qualification and familiarity become terms with weights"* (`ADR-27:58-61`). Nothing is added outside the weighting (`matchfit/core.py:189-204`) | The two positive modifiers became terms at weights 6 and 3; **the `−8` "the same four again" penalty has no successor at all**. `FamiliarityFact` (`fit.py:335-342`) records *whether you have played them*, and the term scores it as a positive — no shipped term penalises over-familiarity |
| 3 | **Clamp to 20–99**, applied after the modifiers, after rounding (`1` §5.2 L975: *"No match ever scores 100 … None scores below 20"*; `DOM` §D.9 D3 L990 `// ROUND, THEN CLAMP`; `DOM` §D.9 D6 L1029 *"99 is attainable; 100 is not"*) | **No clamp.** *"A clamp here provably could not bind, and a guard that cannot fire is one nobody should watch"* (`matchfit/v1/engine.py:47-53`). What is asserted instead is `0 <= fit <= 100` on the value object (`fit.py:490-493`) | **The engine's range is 0–100, not 20–99, and it uses both ends.** [EXEC E2] over 60 000 draws: min **8**, max **100**, **175 scores below 20**. [EXEC E3] over 80 000 realistic draws: **7 scores above 99**. [EXEC E4] a constructed worst case scores **15 at 100% coverage**. The badge's `✦ {score}` content contract (`UI` §B9 L673, *"integer, clamped `20…99`"*) is violated at both ends by the engine that feeds it |
| 4 | **3 reason *sentences***, `reasons: readonly [string, string, string]`, top 3 by contribution (`4` §3.3 L351; `DOM` §D.9 D3 L991–992; wire type `1` §8.1 L1261 `reasons: string[]`) | **3 `ScoredTerm` objects**, `reasons: tuple[ScoredTerm, ...]` (`fit.py:475`), `ranked_by_contribution(scored)[:3]` (`engine.py:191`, `constants.py:329`). Each carries `code: TermCode`, `kind`, `weight`, `value: Ratio`, `fact: TermFact` (`fit.py:383-387`) | **The count matches; the type does not.** An enum member is not a string. The engine emits *"numbers and machine codes, never words … no display text, no formatted Level, no formatted price and no formatted time"* (`fit.py:45-50`), proved by an AST gate: the whole output vocabulary holds exactly **two** `str` fields, both version tags (`tests/unit/test_matchfit_invariants.py:1805` `test_the_score_carries_no_display_text`). The sentence templates exist only in the v37 prototype (`prototype-v37/…` L1160–1190) and **nowhere in `frontend_player/`** |
| 5 | **1 warning string**, `warn: string \| null`, the lowest-contribution term when its **raw** value `< 0.55` (`4` §3.3 L352; `DOM` §C.2 L360; boundary `DOM` §J.3 L2022 *"warn raw 0.55 → no warning"*) | `warning: ScoredTerm \| None` (`fit.py:476`), the lowest contributor when its raw value `< CONSTANTS.warning_threshold` (`engine.py:192`), and **`warning_threshold = ratio(40, 100)`** (`constants.py:314`) | Same asymmetry (ranked by contribution, gated on raw value), same nullability — but **the threshold moved from 0,55 to 0,40 and no source document records the move**. Not flagged by `R5`. A term at raw 0,50 warns under the spec and is silent under the engine |
| 6 | **`target: Level`** on the score — the level the skill term measured against (`4` §3.3 L353; `1` §5.2 L946 *"the open seat's ideal level, or the band midpoint, or your own level"*) | **No `target` field on `MatchFitScore`** (`fit.py:472-478`). The seat target lives on the *other* engine's output: `PairingAnalysis.seat_target` and `.target_band` (`forecast.py:299-332`) | The field did not vanish, it **moved to another engine's output**. A card that prints the target must read the `PairingAnalysis` the score was computed from, not the score |
| 7 | **Coverage: nothing.** Every ranking rule and the badge read one number. `FEED_ORDER` sorts on `fit.score` (`DOM` §D.3 L603–611); `.fit.hi` fires at exactly 90 with nothing else consulted (`1` §3.9 L466, §10.1 L1395; `UI` §B9 L672) | **`coverage: int`**, a whole percent, computed at `engine.py:189` as weight-that-ran over all table weight (`core.py:207-221`), carried never blended (`fit.py:441-444`; `test_matchfit_invariants.py:369` `test_coverage_is_never_blended_into_the_score`) | **A second number the card contract has no field for.** Confirmed unread: grep of `backend/app/` finds readers only inside `app/engines/fit.py`; no module, no route, no schema; `coverage` appears in neither `openapi.player.json` nor `openapi.club.json`. Its intended consumer is a ranking policy (`ADR-27:81-85`) **that does not exist in the repository** |
| 8 | **Badge omitted when `score === null`** — the player has no rating in that sport (`UI` §B9 L674; `DOM` §D.1 L526 `[GAP-D1]`) | **`fit: int`. Never `None`.** An unrated viewer excludes the skill-overlap term and scores the other nine | [EXEC E5] an unrated viewer in a full, cheap, nearby, well-timed match scores **fit 91 at coverage 62** — `int`, not `null`. The badge has no null to key on, and at 91 it would render **coral**. This is a delta no source document records |
| 9 | **Badge geometry**: inline-flex, height 23 px, padding `0 9px`, gap 4, radius 7, type 11/700 Archivo, `--night` `#0A3441` at rest, `--coral` `#E8482B` at `.hi`, content `✦ {score}` (`UI` §B9 L663–682; canonical CSS `1` §3.9 L454–456) | not the engine's business (`fit.py:45-50`) | **No gap.** The geometry survives the engine change untouched. Only the *content contract* and the `.hi` *trigger* break |
| 10 | **`.hi` coral at `score >= 90`** — *"the only place on this screen where a threshold changes a colour … a 90 is rare and means drop what you are doing"* (`1` §3.9 L466) | the engine has no opinion; nothing gates on coverage anywhere in `backend/` | The trigger is computable from what ships. Whether it *should* be is `R5` E2 and §4 below. [EXEC E3] a 90+ is **not** rare against the shipped engine: **3 436 of 80 000 draws (4,3 %)** reach 90 |
| 11 | **Server-built copy**: *"Every string on this screen comes from the server. The client does not build a sentence"* (`1` §8.2 L1269–1273) | the engine cannot supply one — see row 4 | Settled against `1` §8.2 twice over: by `DOM` §A.0's tie-breaker row (*who owns copy → normative = Review*) and by the type system. This is `R5` A5, and it is **confirmed by the AST gate**, not merely argued |
| 12 | **A ranker**: `FEED_ORDER = [desc(fit.score), asc(match.start), asc(club.dist), asc(match.id)]`, lanes, floors, caps, diversity (`DOM` §D.3 L603–611; `4` §3.3 L367–372, §3.4 L397–420) | **Does not exist.** `matchmaking.py` is the snapshot input vocabulary and contains no `sorted`, no `key=`, no filter (`matchmaking.py:1`). `ADR-27:81-85` puts ranking in the calling module's application layer; no such module is written | The whole selection layer is unbuilt. The only sort in the layer is *within* one score (reasons, `core.py:240`) and *within* one pairing (three doubles splits, `pairing/v1/engine.py:426`) |
| 13 | **Fit reaches the client at all** — `GET /now` returns `bestFit: MatchCardView[]` with `fit: {score, reasons, warn}` (`1` §8.1 L1218–1227, L1261) | **Nothing is wired.** No router, schema, dependency or composition-root entry references `matchfit`, `pairing` or `forecast`. `openapi.player.json` has no fit, recommendation, matches or "now" path; `openapi.club.json` declares no paths at all | The engine ships as a pure computation with a large test suite and **zero production callers**. Every wire-shape decision in the delta above is still free |

---

## 2. Side 1 — the model the specifications specify

`DOM` §A.0's tie-breaker table rules that the **prototype's** seven-term model is normative in
that document, *"with every supersession flagged `[SUPERSEDED-A1]`"* (`DOM` L20). The flag appears
five times: `DOM` L20, L334 (§C.2 heading), L957 (§D.9 heading), L1367 (§D.14 D5), L2164 (§K.4
risk 7). So the specification set knows it is describing a superseded model and says so inline.

### 2.1 The seven terms (`1` §5.2 L930–953)

| Factor | Weight | Formula as written |
|---|---:|---|
| Skill overlap | **30** | `max(0, 1 − \|myLevel − target\| / 0.55)` |
| Predicted balance | **20** | `forecast.pct / 100` · default **0.70** when no forecast is possible |
| Group reliability | **15** | `(0.5 × min(scores) + 0.5 × mean(scores)) / 100` · default **0.80** when nobody else is in |
| Time and travel | **15** | `max(0, 1 − max(0, distanceMin − 20) / 18)` |
| Match type | **8** | `1.0` counted · `0.72` friendly |
| Price vs your ceiling | **7** | `clamp(0, 1, 1 − (payable − 30) / 30)` |
| Preferences and side | **5** | `0.9` — a **hard-coded stub** (`DOM` §C.2 L360; §K.1 L2110) |

`1` L940: *"**Weights sum to exactly 100.** A match scoring 1.0 on everything scores 100 before
modifiers."*

### 2.2 The three modifiers (`1` §5.2 L963–973)

`+8` promotion badge → reason *"qualifies for your ladder"* · `+5` you have played none of them →
*"opponents you have not played"* · `−8` three or more others, all regulars → *"the same four
again"*. L965: *"Applied after the weighted sum, before the clamp. **Mutually exclusive by
construction.**"*

Internal contradiction, unresolved in the set: `DOM` §D.9 D4.5 L1003 reads the prototype as
*"`+8` is **independent**; `+5` and `−8` are **mutually exclusive** (`else if`)"*.

### 2.3 The clamp (`1` §5.2 L975, verbatim)

> **Final score is clamped to 20–99.** No match ever scores 100, because certainty is never
> warranted. None scores below 20, because a score of 3 is not more useful than a score of 20 —
> both mean *no*.

Order pinned only in `DOM` §D.9 D3 L990 and D5 L1014: **round first, then clamp**.

### 2.4 Reasons, warning, target — and a negative finding

**Part 5 contains neither the reason sentences nor the warning string.** A grep of `1` for
`warn`/`reason` returns only the modifier table's *"Reason shown"* column header (L967), the wire
type (L1261) and unrelated prose. The mechanism is specified **outside doc 1**:

- `4` §3.3 L351–352 — `reasons: readonly [string, string, string]; // top 3 BY CONTRIBUTION` and
  `warn: string | null; // lowest contribution IF its RAW value < 0.55`.
- `DOM` §D.9 D3 L991–993 and §C.2 L360–361 — the same rule, with the asymmetry spelt out:
  reasons rank on `weight × value`, the warning fires on the **raw** value.

The sentence templates themselves exist only in the prototype (`prototype-v37/…` L1160–1190),
one per term, and the warning is not its own string — it re-uses the losing term's sentence
(prototype L1189).

**"The target"** in Part 5 is the *level* the skill term scores against, not a target score or a
target band for the badge: `target = the open seat's ideal level, or the band midpoint, or your
own level` (`1` §5.2 L946). It is a field on the score in `4` §3.3 L353 (`target: Level`).
`DOM` §D.9 D4.2 L998–1000 notes the third branch — *"else my own level (which makes overlap = 1.0
and is the optimistic default doc 5 A1 objects to)"*.

### 2.5 The badge (`UI` §B9 L663–682)

| Property | Value |
|---|---|
| Shape | inline-flex, height **23 px**, padding `0 9px`, gap **4**, radius **7** |
| Type | **11/700** Archivo (`UI` §A2.2 L145) |
| Rest | `background: --night` (`#0A3441`, `UI` §A1.1 L39); `color: #fff` |
| `.hi` (score ≥ 90) | `background: --coral` (`#E8482B`, `UI` §A1.1 L44) |
| Content | `✦ {score}` (U+2726, `UI` §A5.2 L290) — integer, **clamped `20…99`** |
| Omitted when | `matchFit().score === null` — no rating in that sport |
| Props | `type FitBadgeProps = { score: number; emphatic?: boolean }; // emphatic ⇔ score >= 90` |

**Two bands only. There is no third.** Placement: the `.hair` footer's left group (`UI` §B8 L635).

### 2.6 The colour rule the 90+ treatment is accused of breaking

The rule is in `1` §2.2 (L182–195):

> **This is the rule the whole screen rests on.** A colour used for two things is a colour that
> means nothing. … | **Coral** `--coral` | *You. Your action. Your position.* | The primary
> button, the active tab, the active dot, your seat in the glyph, your level mark, **the
> `.fit.hi` badge at 90+** | … **Coral is never decorative.** If coral appears on this screen and
> the player is not being pointed at a thing they own or an action they can take, that is a bug.

The 90+ treatment is `1` §3.9 L466: *"**Coral at 90+** is the only place on this screen where a
threshold changes a colour, and it is justified: a 90 is rare and means drop what you are doing."*

So the rule and its counterexample are **in the same document, four hundred lines apart**, and
§2.2's own table lists `.fit.hi` as a coral use immediately before stating the rule that excludes
it. `UI` §B9 L678 flags it; `UI` §G2 L1179 and §Open-decisions #9 L1253 both propose *"change the
trigger, not the colour"*.

### 2.7 Doc 4 — design input, not authority

`4` reproduces the seven terms, three modifiers and 20–99 clamp **identically** to `1` §5.2
(`4` §3.3 L294–306). Its own README verdict: *"it describes the engine doc 4 designed, not the
one that shipped under `backend/app/engines/`"* (`README.md` L51–57); `R5` L50 rules **"Replace
§3.3"**. What it adds beyond `1`: the formal `FitScore` shape (L347–355), the four-key total
comparator `FEED_ORDER` (L367–372), lane configuration with `floor: 80` and
`MaxPerClubHour(2)` (L397–420), a `seatTarget` grid-search cost premise (L312–342, which `R5` D1
separately shows is wrong against the shipped closed-form `_seat_target`), and **travel as a
retrieval filter** (`AND club_id = ANY($clubs_within_travel)`, L244) and an eligibility rule
(`new WithinTravelCeiling(), // → 'too-far'`, L280). Those last two are the whole of `R5` A3.

---

## 3. Side 2 — the engine that shipped

`ADR-26` and `ADR-27` are both **Accepted, dated 2026-08-17**. The engine landed the same day
(`7998dce`, *"AFK: feat(matchfit): skill overlap and predicted balance — the table closes at
ten"*). The specification set was committed to this repository two days later (`e7d7ce4`).

### 3.1 The ten terms and their weights (`matchfit/v1/constants.py:84-93`)

```
TermCode.SKILL_OVERLAP: 24,        TermCode.TRAVEL: 8,
TermCode.PREDICTED_BALANCE: 14,    TermCode.LADDER_QUALIFICATION: 6,
TermCode.TIME_FIT: 12,             TermCode.PRICE: 6,
TermCode.MATCH_VIABILITY: 12,      TermCode.MATCH_TYPE: 4,
TermCode.GROUP_RELIABILITY: 11,    TermCode.FAMILIARITY: 3,
```

`WEIGHT_TOTAL = 100` (`constants.py:72`), enforced at `constants.py:349-353` and by
`test_matchfit_invariants.py:1522`. `TermCode` is the ten-member enum at `fit.py:109-118`.

Each term is a **constraint** or **evidence** (`TermKind`, `fit.py`), and the kind decides what
absence means (`ADR-27:62-70`): a constraint the player never declared scores **full marks** and
keeps its weight; absent evidence is **excluded**, the surviving weights are renormalised, and
coverage falls. The weighted average is `weighted_value` over `renormalise(scored)`
(`matchfit/core.py:171-204`), called at `engine.py:188`. **Nothing is added outside the
weighting.**

### 3.2 The output type (`app/engines/fit.py:472-478`), verbatim

```python
    fit: int
    coverage: int
    terms: tuple[Term, ...]
    reasons: tuple[ScoredTerm, ...]
    warning: ScoredTerm | None
    engine_version: str
    pairing_version: str
```

A frozen `@final` dataclass, built at `engine.py:187-198`. `Term = ScoredTerm | ExcludedTerm`
(`fit.py:433`). `ScoredTerm` carries `code / kind / weight / value: Ratio / fact: TermFact`
(`fit.py:383-387`) and a derived `contribution = weight * value` (`fit.py:397-401`);
`ExcludedTerm` carries only `code` and `weight` and **has no `value` field, deliberately**
(`fit.py:419-420`). `TermFact` is a closed union of ten frozen dataclasses (`fit.py:348-359`) —
`SkillOverlapFact`, `BalanceFact`, `TimeFact`, `ViabilityFact`, `PriceFact`, `TravelFact`,
`MatchTypeFact`, `LadderFact`, `ReliabilityFact`, `FamiliarityFact`.

Public entry point: `MatchFitEngineV1.score(*, snapshot, profile, analysis, now) -> MatchFitScore`
(`matchfit/v1/engine.py:145-152`), matching the `MatchFitEngine` Protocol at `fit.py:508-533`.
`ENGINE_VERSION = "matchfit-v1"` (`constants.py:57`); `pairing_version` is read off the analysis
rather than taken as an argument, *"so a score cannot name a pairing version other than the one
that produced the forecast it was scored against"* (`engine.py:194-197`).

### 3.3 The range — no clamp, and both ends are reached

The docstring is explicit (`matchfit/v1/engine.py:47-53`):

> **No clamp at the end.** The source design clamped the score to a display range because its
> modifiers pushed it outside 0–100; with every signal inside the weighting, the fit is a weighted
> average of values in 0..1 and cannot leave the range. A clamp here provably could not bind, and
> a guard that cannot fire is one nobody should watch.

What is asserted instead, `fit.py:490-493`:

```python
        invariant(0 <= self.fit <= 100, f"a fit outside 0..100: {self.fit}")
        invariant(
            0 <= self.coverage <= 100, f"a coverage outside 0..100: {self.coverage}"
        )
```

Rounding is half away from zero, applied exactly once, at `core.py:256-277`.

**[EXEC E2]** 60 000 seeded draws over every input the ten terms read: **fit min 8, max 100**,
92 distinct values, **175 scores below 20** (0,29 %). **[EXEC E3]** 80 000 realistic draws: fit
24–100, mean 72,7; **7 scores above 99**. **[EXEC E4]** a constructed floor case — every term
present, skill overlap 0, viability 0, reliability 0, travel 0, price 0 — scores **fit 15 at 100 %
coverage**. The engine's own property tests assert the 0–100 range and say why a clamp could not
bind (`test_matchfit_properties.py:255`, `:275` `test_the_score_never_leaves_the_range_so_a_clamp_could_not_bind`).

### 3.4 Coverage — computed, carried, read by nobody

`coverage=whole_percent(measured_share(terms))` (`engine.py:189`); `measured_share` is
weight-that-ran over total table weight (`core.py:207-221`). It is *"never blended"* into the fit
(`fit.py:441-444`), asserted by `test_matchfit_invariants.py:369`
`test_coverage_is_never_blended_into_the_score`.

**Consumers: none in production code.** `MatchFitScore` and `coverage` appear only under
`app/engines/` and `tests/`. There is no reader under `app/modules/` (which holds only `auth`,
`rating`, `users`) or `app/api/`; neither OpenAPI document contains the string. `ADR-27:81-85`
assigns the composition of fit with coverage to a ranking policy object; **that object is not
written**.

**[EXEC E3]** coverage in realistic snapshots takes the values 48 (nobody seated: skill overlap,
balance, reliability and familiarity all excluded), 62, 72, 83, 86 and 100. Two terms ship dark
by design — `GROUP_RELIABILITY` 11 and `FAMILIARITY` 3 (`ADR-27:76-80`) — so a live full match
tops out at 86 unless `PlayHistory` and `PlayerScore` are supplied.

### 3.5 Travel and price — terms, never exclusions

Both are **constraint** terms sharing one decay curve. Travel, weight 8 (`engine.py:481-499`),
docstring at `:484-487`:

> **Never an exclusion**, at any distance. *Nothing is ever excluded on distance*: a match an
> hour away reaches a player who declared twenty minutes as a low score they can overrule, not as
> an absence they cannot see.

Price, weight 6 (`engine.py:452-478`), reads `payable` (post-club-card) and never `seat_share`
(`engine.py:455-458`). The shared decay curve's floor is `NO_MARKS`, never exclusion
(`core.py:150-154`), pinned by `test_matchfit_invariants.py:832`
`test_price_and_travel_score_zero_rather_than_dropping_out` and by the sweep at
`test_matchfit_properties.py:244-245`, which asserts both reach `{"full", "part", "zero"}` and
never `"excluded"`.

The governing rule, `ADR-27:86-90`:

> **Candidate generation excludes on facts, never on preferences.** Sport, seats remaining, the
> join cutoff, live inventory and calendar conflicts are hard filters. Distance, price and level
> are never exclusions — the intent pool's rules are explicit that *nothing is ever excluded on
> distance* and that price is *a condition, not a rejection* — so they reach the player as a lower
> score, not as an absence.

The one thing that *is* a hard filter is match phase, and the snapshot **refuses** it rather than
scoring it low: `invariant(self.phase is MatchPhase.FORMING, ...)` at `matchmaking.py:737-741`.

### 3.6 Determinism and the tie-break

**There is no randomness anywhere in `backend/app/`.** No `import random`, `secrets` or `numpy`
in the whole package; every textual hit inside `app/engines/` is a docstring *asserting the
absence* (`engines/__init__.py:11`, `fit.py:55`, `fit.py:514`, `matchfit/v1/engine.py:139`,
`forecast.py:340`). It is **machine-enforced**: `backend/.importlinter:88-121`, contract
`engines-are-pure`, lists `random`, `uuid` and `secrets` as forbidden modules for `app.engines`.

The only ordering in the engine is **within one score**, `matchfit/core.py:240`:

```python
    return tuple(sorted(scored, key=lambda term: -term.contribution))
```

Tie-break: **stable sort over table order**, which is descending weight (`core.py:236-238`;
`_TABLE` at `engine.py:627-642`). The warning uses `min` rather than the sort's last element
*"because the two agree on the value and not on the tie … One rule for ties, in both directions"*
(`core.py:243-253`), pinned by `test_matchfit_invariants.py:706`.

**[EXEC E6]** the same inputs twice produce an equal score, and every reason is the *identical
object* already in `terms` — the identity the docstring promises (`fit.py:458-461`) and the suite
asserts with `is` (`test_matchfit_invariants.py:672-676`). Also asserted in-suite:
`test_the_same_inputs_produce_the_same_score` (`test_matchfit_invariants.py:765`) and
`test_only_the_viability_term_depends_on_the_instant_it_is_asked_at` (`:775`).

`now` must be rounded to the minute or the call is refused (`engine.py:176-179`) — `ADR-26:86-89`,
*"makes every score reproducible from its stored inputs, and makes a result cacheable for a minute
instead of never."*

### 3.7 Reasons — structured, and provably wordless

`reasons=ranked_by_contribution(scored)[: CONSTANTS.reasons_returned]` (`engine.py:191`) with
`reasons_returned: int = 3` (`constants.py:329`). They are `ScoredTerm` objects, **the very same
instances** already in `terms`.

`warning=weakest if weakest.value < CONSTANTS.warning_threshold else None` (`engine.py:192`) with
`warning_threshold: Ratio = ratio(40, 100)` (`constants.py:314`).

**[EXEC E4]** a real reason payload, printed from the engine:

```
TimeFact(weekday=<Weekday.TUESDAY: 2>, minute=1110, days=None, hours=None, kind='time_fit')
TravelFact(minutes=0, radius=None, kind='travel')
LadderFact(qualification=<LadderQualification.QUALIFIES: 'qualifies'>, kind='ladder_qualification')
```

No sentence, no locale, no currency symbol. The AST gate
`test_matchfit_invariants.py:1805 test_the_score_carries_no_display_text` proves the entire output
vocabulary holds exactly **two** `str` fields — `engine_version` and `pairing_version` — plus ten
`Literal[...]` `kind` discriminators, over 52 annotated fields. Grepping the repo for the term
codes outside `app/engines` finds only two test files and **nothing in `frontend_player/` or
`frontend_club/`**: the copy table the client needs does not exist on either side yet.

---

## 4. `R5`'s findings against the code — confirmed and refuted

`R5` is a review of the **documents**. Its author read the shipped engine for A1 and A3 (the
weights it quotes at L110–122 and L184 are the shipped ones) but the code decides four of the five
findings differently from how the review frames them.

### A1 — *"Match Fit as written is the model ADR-0027 was accepted to remove"* — **Confirmed, exactly**

Every element of A1's comparison table matches `constants.py:84-93` term for term and weight for
weight, including its observation that *"match viability at weight 12 … is nowhere in Part 5"*
(`R5` L124–126). The three claims A1 makes about the shipped engine are each true in code: every
signal is a term (`ADR-27:58-61`; nothing added outside `weighted_value`, `core.py:189-204`),
coverage is its own number (`fit.py:473`), and there is no clamp (`engine.py:47-53`). **[EXEC E2]**
adds the fact A1 asserts but does not measure: **the score really does leave 20–99, at both ends**
— 175 sub-20 scores and a maximum of 100 in 60 000 draws.

A1's proposed card contract, *"`{fit, coverage, terms, reasons: TermCode[], warning}`"*
(`R5` L133), is **half right**: `reasons` are not `TermCode[]` but `ScoredTerm[]` — code *plus*
kind, weight, value and a typed fact payload (`fit.py:383-387`). The distinction matters, because
the fact payload is the only thing a client can build a sentence from.

### A2 — *"Coverage exists and neither the ranking nor the badge reads it"* — **structurally confirmed; its stated consequence refuted**

**The structural claim is confirmed and then some.** Nothing reads coverage — not the ranking
(there is no ranking), not the badge, not a schema, not an endpoint (§3.4). `DOM` §D.14 D5 L1367
and `UI` §Open-decisions #9 L1253 both already carry the fix as a proposal.

**The consequence claim is refuted by execution.** `R5` L147–151 asserts:

> At launch, coverage is structurally low … So the highest fit scores will systematically belong
> to the matches the platform knows least about — and Now will paint a coral *drop what you are
> doing* badge on them. That is the failure ADR-0027 exists to prevent, arriving through the
> presentation layer instead of the arithmetic.

**[EXEC E3]**, 80 000 draws stratified by how many others are seated:

| Others seated | n | mean fit | mean coverage | share reaching 90 |
|---:|---:|---:|---:|---:|
| **0** (empty court) | 19 980 | **63,0** | 48,0 | **1,38 %** |
| 1 | 19 960 | 75,6 | 93,1 | 4,45 % |
| 2 | 20 277 | 75,9 | 93,0 | 5,28 % |
| 3 (full) | 19 783 | **76,4** | 93,1 | **6,07 %** |

**Pearson r(fit, coverage) = +0,445.** Fit and coverage move *together*, and the empty court — the
exact case `ADR-27` was written about, which scored **90,5** under the old model against **84** for
a canonical full match (`ADR-27:14-16`) — now scores **13 points lower** than a full one on
average and reaches 90 four times less often. The monotonic-decreasing-in-information pathology is
**fixed in the arithmetic**, which is what `ADR-27:71-73` claims for the reclassification of skill
overlap as evidence. `R5` A2 assumed the pathology survived into presentation; against the shipped
engine it did not survive at all.

**What does survive is narrower, and still real.** Among the 3 436 draws reaching fit ≥ 90,
**276 (8,0 %)** sit at 48 % coverage — an empty court with four of ten terms excluded. So the
badge would paint coral on a thin score roughly one time in twelve, not systematically. A2's fix
is still motivated; its stated magnitude is not.

### A3 — *"Travel and price are used as exclusions, which ADR-0027 forbids"* — **Confirmed against doc 4; refuted against the engine**

The exclusions A3 names are real and they are **entirely in doc 4** — `4` §3.1 L244
(`AND club_id = ANY($clubs_within_travel)`) and `4` §3.2 L280 (`new WithinTravelCeiling(), // →
'too-far'`). A3's own citation line is `Rec §3.1, §3.2` (`R5` L171), and doc 4 is **not an
authority** (`README.md` L51–57).

**The shipped engine does the opposite of what A3 warns against.** Travel is a weight-8 constraint
term whose docstring says *"**Never an exclusion**, at any distance"* (`engine.py:484-487`); price
is a weight-6 constraint term (`engine.py:452-478`); the shared decay floor is `NO_MARKS` and never
exclusion (`core.py:150-154`); and a test exists specifically to hold the line —
`test_matchfit_invariants.py:832 test_price_and_travel_score_zero_rather_than_dropping_out`.
`DOM` §D.3 L617–620 already applies A3 to the feed rule (*"**`WithinTravelCeiling` must NOT be
included**"*).

So A3 is a finding about a **document describing an engine that does not exist**, and the fix it
asks for is already the shipped behaviour. Nothing in `backend/` needs to change for A3.

### A4 — *"The determinism invariant forbids exploration, which the ranker is required to own"* — **Refuted as a conflict; the premise is not in the code**

A4 (`R5` L202–204) reads the conflict off `4` §5.3/§9.1's output invariant 9, *"the same request
twice, same world → byte-identical feed"*. That invariant is doc 4's, and doc 4 is not an
authority.

**In the code there is no conflict, because the two properties are held by two different layers
and one of them is not written.**

- The **engine** is deterministic by decree and by import-linter: `backend/.importlinter:88-121`
  forbids `random`, `uuid` and `secrets` to `app.engines`; `ADR-0015:84-88` states the three
  purity rules; `engines/__init__.py:8-12` restates them. **[EXEC E6]** two identical calls return
  an equal score.
- The **ranker** is explicitly permitted the randomness the engine is denied — `ADR-27:81-85`,
  *"It may read configuration, run experiments and draw randomness, because it is not an engine and
  makes no claim to reproducibility."* `fit.py:52-56` says the same from the engine's side.
- **That ranker does not exist.** There is no module, no sort, no lane, no seed anywhere in
  `backend/app/` outside the engines.

A4's *fix* — restate determinism as reproducibility from `(player, minute-bucket, exploration
seed)` — is already half-shipped for the engine half: `now` is refused unless rounded to the
minute (`engine.py:176-179`), for exactly the reason A4 quotes from `ADR-26`. What A4 describes as
a blocking contradiction is, against the code, **an unwritten layer with its contract already
settled**. `DOM` §J.5 L2073–2082 `[GAP-J1]` records the same restatement.

### A5 — *"Every string comes from the server is the opposite of what this repo decided"* — **Confirmed, at the type level**

`1` §8.2 L1269–1273 says the server sends every string. The engine **cannot** —
`fit.py:45-50`, and the AST gate `test_matchfit_invariants.py:1805` proves the whole output
vocabulary holds two `str` fields, both version tags. `DOM` §A.0's tie-breaker already rules for
the review on this row (*who owns copy → normative = Review*, `DOM` L21). A5 is the finding the
delta's row 4 turns on.

### E2 — *"The fit badge at 90+ breaks the document's own colour rule"* — **Confirmed as a documentary fact; the code neither helps nor hinders**

The rule (`1` §2.2 L184–195) and the counterexample (`1` §3.9 L466) are both in doc 1, and §2.2's
table lists `.fit.hi` among coral's uses in the same breath as the rule that excludes it. That is
a self-contradiction inside a document `README.md` L15–19 makes *"final on the UI … on every value
it states"* — so the tie-breaker cannot break this one; the document contradicts itself, not
another source.

The engine has no view. But **[EXEC E3]** does undercut §3.9's justification: *"a 90 is rare"*
is false against the shipped engine, where **4,3 %** of realistic draws reach 90 and the top of the
range is 100, not 99. E2's proposed fix (gate on fit **and** coverage) is computable from what
ships today — both numbers are on the same object — and would cut the coral population to the
782 draws at 100 % coverage plus the 2 378 at 80–89 %, i.e. it would remove the 276 thin ones.

---

## 5. Facts neither side settles

Three deltas surfaced here are recorded in **no** source document and in **no** review finding:

1. **The warning threshold moved.** `0.55` in `4` §3.3 L352, `DOM` §C.2 L360 and the boundary test
   `DOM` §J.3 L2022; `ratio(40, 100)` in `constants.py:314`. Nothing records the change or its
   reason. A term at raw 0,50 warns under the specification and is silent under the engine.
2. **The `−8` penalty has no successor.** `+8` became `ladder_qualification` (6) and `+5` became
   `familiarity` (3), but nothing penalises *"the same four again"*. `FamiliarityFact`
   (`fit.py:335-342`) records the fact and the term scores it in the positive direction only. The
   product argument for the penalty is stated at `1` §5.2 L973 — *"Playing with your entire usual
   group every week is the pattern that makes a marketplace stop being a marketplace"* — and no
   shipped mechanism carries it.
3. **The unrated viewer no longer disappears.** `UI` §B9 L674 omits the badge when
   `score === null`; `DOM` §D.1 L526 `[GAP-D1]` describes the whole feed emptying for an unrated
   player. **[EXEC E5]** the shipped engine returns `fit: int` and never `None`: an unrated viewer
   in a full, cheap, nearby, well-timed match scores **91 at 62 % coverage** — which under the
   current badge rule renders **coral**. The engine excludes only the skill-overlap term and
   scores the other nine.

---

## 6. What remains open

`DOM` §A.0 rules only that the prototype's seven-term model is normative *inside `DOM`*, with the
supersessions flagged. It settles nothing below. This file deliberately closes none of it.

1. **Whether the badge's range becomes 0–100 or the engine gains a display clamp.** Both are
   coherent; they are different products. [EXEC] says the engine uses 8–100 in anger, so the badge
   as specified is currently wrong at both ends whichever way this goes.
2. **What replaces `✦ {score}`'s single number**, given that a fit of 91 at 48 % coverage and a fit
   of 91 at 100 % coverage are different facts (`fit.py:441-444`) and the badge has one slot.
3. **Whether `.fit.hi` gates on coverage** (`R5` A2/E2, `UI` §Open-decisions #9, `DOM` §D.14 D5) —
   and if so, what the coverage floor is. Nothing anywhere proposes a number.
4. **Whether the coral rule survives at all**, or `.fit.hi` is dropped as `UI` §Open-decisions #9's
   fallback proposes. This is a `1` §2.2-versus-`1` §3.9 contradiction the tie-breaker cannot
   resolve, because both halves are in the document the README makes final on the UI.
5. **Where the reason copy table lives**, now that A5 is settled for the client. Neither
   `frontend_player/` nor `frontend_club/` contains a single term code today; ten codes × ten fact
   payloads × Polish is the actual size of the job.
6. **What the `−8` "the same four again" signal becomes** — a negative term, a ranker diversity
   cap (`ADR-27:82-83` puts diversity caps in the ranker), or nothing.
7. **Whether the warning threshold is 0,55 or 0,40**, and which was the deliberate choice.
8. **What an unrated viewer sees** — the badge, no badge, or a different badge — now that `null`
   is not on the table. `UI` §G5 L1220 proposes copy for the empty-feed case
   (*"Finish your rating and we can tell you which matches are even."*) but that case no longer
   arises the way `DOM` §D.1 describes.
9. **Whether "preferences and side" (weight 5) returns as a term.** `PlayerProfile.appetite` and
   `.commitment_horizon` are on the input contract (`matchmaking.py:317`, `:327`) and read by no
   v1 term; `1` §5.2's value was a hard-coded `0.9` stub anyway (`DOM` §K.1 L2110).
10. **Which target the card prints**, given that `target: Level` left `MatchFitScore` and lives on
    `PairingAnalysis.seat_target` / `.target_band` (`forecast.py:299-332`) — i.e. whether the wire
    carries the pairing analysis beside the score.
11. **What the wire shape is at all.** Nothing is exposed: no router, no schema, no OpenAPI path.
    `1` §8.1 L1218–1227's `GET /now` is unbuilt, so every field name in the delta above is still
    free — and `ADR-0006` means whichever shape is chosen regenerates both clients' types.

---

### Provenance

Documents read on 2026-08-19 at `docs/specs/now/`: `1-now_screen_production_spec.md`,
`now-section-domain-spec.md`, `rakieta-now-section-ui-spec.md`,
`4-match_recommendation_engine_architecture.md` (design input only, per
[the set's README](../README.md)), `5-now_screen_architecture_review.md`,
`rakieta-now-section-specification.md`.

ADRs read at `docs/adr/`: `0025-binding-pairing-for-counted-matches.md`,
`0026-matchmaking-engines-snapshot-input-contract.md`,
`0027-fit-and-certainty-are-separate-ranking-is-policy.md`, and
`0015-engines-as-a-pure-versioned-layer.md` where cited.

Code read and executed at `backend/app/engines/`: `fit.py`, `forecast.py`, `matchmaking.py`,
`matchfit/{core.py, v1/constants.py, v1/engine.py}`, `pairing/{core.py, v1/*}`, plus
`backend/.importlinter`. Tests read at `backend/tests/unit/`: `test_matchfit_properties.py`,
`test_matchfit_personas.py`, `test_matchfit_invariants.py`, `test_pairing_invariants.py`,
`matchmaking_snapshots.py`.

Executions ran under the project venv (`raketa-KpiMVNy_-py3.11`, Python 3.11.6) from
`backend/`, importing `app.engines.matchfit.v1.MatchFitEngineV1` and building inputs with
`tests/unit/matchmaking_snapshots.py`. Sweep seed **20260819**. E1 was
`pytest tests/unit/test_matchfit_{properties,personas,invariants}.py` — **757 passed**. No file
under `backend/` was modified.
