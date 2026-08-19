# Spec delta — the fit badge and the model under it

**Governs over** `1-now_screen_production_spec.md` §5.2 and §3.9, and over
`rakieta-now-section-ui-spec.md` §B9's content contract and `.hi` trigger. Everything else in
those two documents stands unchanged and remains final.

**Authority for this file:** [ADR-0036](../../../adr/0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)
— a UI document is final on the screen, never on the arithmetic. **The decisions:**
[ADR-0037](../../../adr/0037-the-fit-badge-shouts-once-and-only-about-a-seat.md).
**The evidence:** [`../research/fit-model.md`](../research/fit-model.md), and
[`Raketa02/Raketa#10`](https://github.com/Raketa02/Raketa/issues/10) for the reasoning.

The source documents are **not edited**. 486 `[SRC: line N]` citations and 27 bare-filename
cross-references resolve against their bytes.

---

## 1. The model — §5.2 is superseded in full

| §5.2 as written | What governs |
|---|---|
| **7 weighted terms** summing to 100 (skill overlap 30 · predicted balance 20 · group reliability 15 · time and travel 15 · match type 8 · price vs ceiling 7 · preferences and side 5) | **10 terms** summing to 100 (skill overlap 24 · predicted balance 14 · time fit 12 · match viability 12 · group reliability 11 · travel 8 · ladder qualification 6 · price 6 · match type 4 · familiarity 3), per `backend/app/engines/matchfit/v1/constants.py` |
| **3 modifiers** after the weighted sum: `+8` promotion, `+5` played none of them, `−8` three or more all regulars | **None.** Every signal is a term ([ADR-0027](../../../adr/0027-fit-and-certainty-are-separate-ranking-is-policy.md)). `+8` became `ladder_qualification` (6); `+5` became `familiarity` (3); the `−8` is re-homed — see §4 |
| **Clamp to 20–99** applied to the score, after rounding | The **model** is unclamped, range 0–100. The **display** clamps to 20–99. See §2 |
| *"Preferences and side"*, weight 5, hard-coded to `0,9` | **Not a term.** Recorded as a known hole — see §4 |
| One number | **Two numbers**: fit, and coverage — the share of the weight that actually ran |

**Why the direction is this way and not the other.** §5.2's model has a measured defect: an
empty match scores **90,5** where a well-formed one scores **84**, so the score is monotonically
decreasing in information. The shipped model removes it — over 80 000 realistic scores an empty
court averages **63,0** against a full one's **76,4**, and fit and coverage correlate at
**r = +0,445**.

## 2. The badge — `UI` §B9 and §3.9

| As written | What governs |
|---|---|
| Content `✦ {score}` — integer, **clamped `20…99`** | **Unchanged as a display rule.** The engine's true 0–100 value ranks the list; the pill never prints below 20 or above 99. §5.2's two reasons — *"a score of 3 is not more useful than a score of 20"*, and never 100 because certainty is never warranted — are presentation reasons, and this is the rule the rating context already holds for Confidence |
| `.hi` coral at **`score >= 90`** | Coral when **all three** hold: fit ≥ 90 · coverage ≥ 80 % · **a seat is open**. And **at most one card per screen** is emphatic |
| `emphatic ⇔ score >= 90` in `FitBadgeProps` | **`emphatic` is a server-sent flag**, not a client-computed comparison. Emphasis depends on the other cards, so it is a property of the composed screen ([ADR-0032](../../../adr/0032-order-is-a-property-of-the-composed-screen.md)) |
| Omitted when `matchFit().score === null` | Omitted when **the viewer has no rating in that sport**. Behaviour kept; the key corrected, because the engine never returns a null score — an unrated viewer scores 91 at 62 % coverage in a good match |
| §3.9 *"a 90 is rare"* | **False as measured** — 4,3 % of realistic scores reach 90, and a list selects for the maximum. The three gates and the per-screen cap are what restore rarity |
| Geometry, type, tones, *"two bands only"* | **Unchanged and final.** Nothing here touches them |

`1` §2.2's coral rule needs **no amendment**: an emphatic badge points at a seat the player can
take.

## 3. The card's other fields

| As written | What governs |
|---|---|
| `reasons: string[]` — three sentences built by the server (`1` §8.2: *"Every string on this screen comes from the server"*) | **The client writes the words.** The server sends, per reason, the **term code and its typed fact payload** — not the weight, not the value, not the contribution. Proved necessary by an AST gate: the engine's whole output vocabulary holds two `str` fields, both version tags. This is doc 5 **A5**, already ruled for by `now-section-domain-spec.md` §A.0 |
| `warn: string \| null`, fired when the lowest contributor's **raw** value `< 0,55` | Threshold is **0,40** (`constants.py:314`), chosen and not inherited. The asymmetry is unchanged — ranked by contribution, gated on raw value — and 0,55 fires on *"acceptable but not great"*, which the specification's own principle argues against: *"warning about that would teach players to ignore warnings"* |
| `target: Level` on the score | Printed **only when precise** — the seat target, which exists only when exactly one seat is open. A target *band* is nearly always the viewer's own band restated, and is not printed. The field left `MatchFitScore` and lives on `PairingAnalysis`, so the response carries the balance forecast beside the fit score |
| Coverage | **Never a number the player sees.** It ranks, it gates emphasis, and it may become words in a reason line |
| Which side a skill mismatch fell on | **Carried.** *"You would be the strongest here"* and *"you would be stretched"* are different sentences, and the engine already records which |

## 4. Where the dropped product arguments went

- **`−8` "the same four again"** → a **variety rule in the ranking layer**, capping how many
  cards on one screen share the viewer's regular group. It is a property of a list, not of a
  match: a match with your usual group is not a worse match, it is a worse fifth suggestion.
  ADR-0027 already puts diversity caps in the ranker.
  A **second, independent** mechanism was identified and is **out of scope here**: a repeat
  opponent is weaker evidence, so it should narrow the rating's σ less — an **information
  weight**, which the rating context already reserves a slot for, feeding **calibration
  priority**, which *"changes who they are matched with, never where they sit."* It must not dock
  rating points; that would make the number wrong on purpose. Rating-context work, not Now's.
- **"Preferences and side"** (weight 5) → **a named hole, not built.** `PlayerProfile.appetite`
  and `.commitment_horizon` are on the input contract and read by no term. The declarations stay
  (deleting the questions would cost data we would have to start collecting again); the term
  returns only when it has something real to measure, and reopening the weight table is its own
  decision with its own evidence.

## 5. Part 6 — the finding it did not know

Part 6's *"full, but worth waiting for"* lane stands exactly as written: every full future match
in the sport, **Match Fit ≥ 80**, sorted descending, **one card on Now**. The engine scores such
a match today with no contract change, falling back from the seat target to the target band.

**What no document records:** a full match **outranks the joinable version of itself** — the same
four players score **91** with one seat open and **94** with none, because being full is the
strongest available evidence the match will be played and viability is the one term that can
never be excluded. So the two lanes **cannot be merged into one ordered list**: it would be
topped by matches nobody can join. The hard boundary between Part 5's list and Part 6's single
card is load-bearing.

Charted as [`Raketa02/Raketa#20`](https://github.com/Raketa02/Raketa/issues/20).

## 6. What did not change

`backend/app/engines/` — **not one line.** Every decision above lands in the response shape, the
ranking layer or the client, and the warning threshold ratified the code's existing `0,40`.

Doc 5's **A3** (travel and price used as exclusions) and **A4** (determinism forbids exploration)
are **refuted against the code** and need no delta: travel and price are weight-8 and weight-6
terms that never exclude at any distance or price, and the engine's determinism and the ranker's
permitted randomness are held by two different layers, one of which is unwritten. Both findings
are about `4-match_recommendation_engine_architecture.md`, which is not an authority.
