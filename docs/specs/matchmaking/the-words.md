# The words

Nothing the matcher sends is prose. What crosses is `Term`, eight typed evidence variants,
`DegradedReason`, `ConcernSchema.term`, `LivenessReason`, `WireInclusionReason`,
`ModifierCode`, `UnfilledReason`, `GroupReason`, `Prompt`, `ForecastAssumption`,
`SortOption`, `Window`, `Rung`, `RelaxationAsk`, `DayPart`, `SocialTag` and the five
challenge standings — and **the app writes the words for all of them**
([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md),
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).

This file is that deck. It is the artifact the Play build tickets cite by section, and the
artifact a later copy edit is made against — so that §F1's voice can be checked against
itself in one place rather than a dozen.

Decided by
[Every sentence the client writes from a code](https://github.com/Raketa02/Raketa/issues/234).

---

## 1. Where the copy lives

**This client already answered this, four times, and the answer is written down.**
`authErrorMessage.ts`: *"Localization goes **code → message**, never message → message.
The backend's `message` is a diagnostic written for a log; rendering it directly ships
English into every locale and lets a copy edit on the server change what an app already
installed says. So the copy lives here, chosen by the stable code."*
`socialTagPresentation.ts`: *"The ids are the platform's and the labels are this app's…
The three tables are exhaustive by type."*

So: feature-local `*Presentation.ts` modules inside the Play feature, one per **vocabulary
owner** rather than per screen — three cards and the whyfit sheet read the same tables.

**Two shapes, and the split is whether the sentence quotes a value.**

| Shape | For | Why |
| --- | --- | --- |
| `Readonly<Record<Code, string>>` | every code with no payload | Keyed by the generated union, so a missing key is a **compile error** — ADR-0106's *"a compiler says so"* |
| one function per variant, dispatched on `kind` | the eight evidence variants | A reason line is a sentence **over** its evidence (`delta`+`direction`, `shared_count`+`next_slot`, three tag-pair sets); a flat table cannot hold it. ADR-0106's own *"a renderer per variant"* |

**Three tables Play must not re-type.** `SocialTagId`, `DayPart` and `Weekday` already ship
in `player_profile`. Play is their **third** caller, which is `recoveryMessage.ts`'s own
stated trigger — *"Auth and onboarding each held a copy of this table, and the second one
recorded the rule: a third copy is the signal to move it"* — so they are **promoted to
`shared/`**, not copied and not re-worded.

## 2. Mode — three places, and nowhere else

The ticket assumed every code needs words *"in two modes"*. That was inherited from the
prototype, where the strings were generated prose. **On codes it is false**: §4's rule makes
a reason line state its evidence's facts, and the facts do not move between modes — only the
weight does, and no card prints a weight.

Mode reaches exactly three places:

1. **The concern sentences** (§7), where the harm genuinely differs by direction — a for-fun
   candidate to a competitive searcher forgoes 16.1 points, the reverse forgoes 10.0, and
   both clear the bar.
2. **`INTENT_ALIGNMENT`'s renderer** (§6), whose evidence literally carries `my_mode`.
3. **The whyfit sheet's header line**, *"tuned for a … game"* — **absent** where
   `SearchEnvelope.mode` is null, per
   [#233](https://github.com/Raketa02/Raketa/issues/233) §6.

**Everything else is one deck.** Where mode is needed, it is a small explicit override table
beside the default one, never a second full column: sixty codes × three columns invents a
distinction for fifty of them, and the day somebody edits one column and not the other the
two readings drift with nothing that goes red.

**The deck's null mode resolves to the default, never to for-fun.** Deriving
`NO_PREFERENCE → FOR_FUN` client-side is the engine's own resolution rule rewritten in
TypeScript — refused by name in #233 §6.

> **And the two sources must not be merged.** `IntentAlignmentEvidence.my_mode` carries the
> mode *the engine actually used*, on every candidate, **deck included** — while
> `SearchEnvelope.mode` is null there. So the intent renderer reads the evidence and the
> sheet header reads the envelope, and on the deck they correctly disagree: the row says
> what kind of evening was priced, the header names no mode. A build session "fixing" one to
> match the other breaks whichever it touches.

## 3. An unknown code

`tsconfig.json` sets **`noUncheckedIndexedAccess: true`**, so `TABLE[code]` is already
`string | undefined`. ADR-0106 §6's gap branch is **forced by the compiler**, not remembered.
What is left to decide is only what it says, and where a drop is legal instead.

**The rule, testable:** *a code renders a named gap wherever the screen states a count or a
total its row belongs to; everywhere else it is dropped.*

That is ADR-0106 §6's own argument — *"the player sees a Fit of 78 explained by
contributions that sum to 61"* — generalised by what it was protecting rather than by the
word *evidence*.

| Placement | Unknown code | Because |
| --- | --- | --- |
| whyfit term row | **gap**, keeping the row's weight, value and contribution | the column has to add up (#233 §7) |
| whyfit not-counted block | **gap** | it is the renormalisation basis |
| modifier row | **gap** | the block is headed by a derived total |
| an unfilled seat | **gap** | the seat is *stated* as unfilled; a blank is not an answer |
| a challenge standing | **gap** | the code **is** the whole line |
| a card reason line | **dropped** | ADR-0106 §6: *"the card shows three reasons out of eight and always did"* |
| liveness / inclusion tags | **dropped** | same |

**The gap's words, one string, everywhere:**

> **This app is too old to read this one — update Raketa.**

It names neither the code nor the vocabulary. A raw `SOCIAL_VIBE` is a wire token in a
player's face; *"an unknown evidence kind"* is a sentence about our schema. And one string
rather than five, because a per-placement wording is five sentences that must all stay true
of one condition.

> This is deliberately **not** the shape `evidencePresentation.ts` uses, and the difference
> is the rule above. There, an unreadable direction *"draws no mark at all, rather than a
> default one"* — because the mark is decoration over a row whose content came from the
> server, and *"the row still shows what the category said."* Here the code often **is** the
> content.

## 4. What a reason line may say

`the-play-screens.md` §1 forbids the obvious register by name: *"a client thresholding a
term value would be that judgement in TypeScript, differently in every client."*

> **A reason line states its evidence's own facts and never grades them.**

No *well*, no *strongly*, no *good*. The grading vocabulary belongs to `concerns[]`, which
is the engine's judgement and arrives ranked.

This is also why a reason line cannot simply name its term. §5's filter has already removed
every term whose value the card draws — so a survivor that said *"Your weeks overlap"* would
sit on a card with no overlap row and carry no fact at all. The filter and the register are
one decision, not two.

**Counted phrases route through one pluralisation helper.** §J4's gap — *every counted phrase
must route through proper plural handling before any further market* — is the map's fog, not
this file's; what this file owes is that no string here hardcodes an `s`.

## 5. The de-duplication filter, per surface

§B10 filters generated prose by prefix and by the word *"level"*. On codes it becomes a set —
and **the spec's single filter is wrong on two of three cards**, because §10's narrowed rule
is *a reason line never restates a value the card **already renders***, and the three cards
render different things.

| Surface | Draws | So it drops |
| --- | --- | --- |
| `CandidateCard` (competitive) | head-to-head row, balance bar, (later) Player Score block | `LEVEL_FIT`, `PREDICTED_BALANCE`, and `RELIABILITY` only once the score block prints |
| `CandidateCardSocial` (for fun) | Level row, You overlap row, meta line's km | `LEVEL_FIT`, `AVAILABILITY_OVERLAP`, `DISTANCE` |
| `DeckCard` | Level row, Predicted balance row, You overlap row, meta line's km | `LEVEL_FIT`, `PREDICTED_BALANCE`, `AVAILABILITY_OVERLAP`, `DISTANCE` |
| `SH.whyfit` | everything, on purpose | **nothing** — #233 §7: a summary block would break §10 *"on the one screen whose job is showing values"* |

**The filter is declared beside each card as the set of terms that surface draws**, so the
rule is checked against the component rather than remembered.

**Two rules on top of it:**

- **`INTENT_ALIGNMENT` is never filtered.** After the drops it *is* `said[0]` on the
  competitive card — third-largest term in both modes, and a dedicated row would delete the
  sentence it duplicates ([#230](https://github.com/Raketa02/Raketa/issues/230) §1).
- **A concerned term is removed from the reason list** (§7). One term saying *"✓ X"* and
  *"! X"* on one card is §10's rule broken at its own root; the reason slot goes to the next
  survivor, and the sheet still shows the term with its concern marked in place.

**And the order inverts.** §B10 takes the top three, *then* filters — which is what makes the
card's "three reasons" sometimes one, and is the direct cause of its `[GAP: no fallback
string]`. **Filter first, then take three.**

### When nothing survives

On the **competitive** card it cannot happen: `DISTANCE` never stands down and the card draws
no distance row, so a survivor always exists. On the **deck** card the line rests on exactly
three terms — `INTENT_ALIGNMENT`, `PLAYING_STYLE`, `SOCIAL_VIBE`, since `RELIABILITY` stands
down for everybody day one — and all three are optional.

> **The fallback is the top `LivenessReason`, not the fourth-ranked term.**

The row's question is *why this person*, and when no term survives the filter the liveness
code answers exactly that: `NEWCOMER_LIFT`, `INTEREST_RECEIVED`, `RECENT_ACTIVITY`. Falling
back to a filtered term breaks §10 on purpose to fill a slot. Nothing new crosses the wire —
#233 §7 already routes liveness reasons to the sheet's *What else moved you here*, and this
renders the top one a level up.

**With no liveness reason either, the row is hidden — not blank.** §G5's *"renders a blank
line next to the fit pill"* is the bug being fixed; an absent row is not an empty one.

## 6. The eight terms

### 6.1 Labels — the whyfit row heads

| `Term` | Label |
| --- | --- |
| `LEVEL_FIT` | Level fit |
| `PREDICTED_BALANCE` | Predicted balance |
| `INTENT_ALIGNMENT` | The kind of evening |
| `RELIABILITY` | Their record |
| `AVAILABILITY_OVERLAP` | When you both play |
| `PLAYING_STYLE` | On court |
| `SOCIAL_VIBE` | Around the game |
| `DISTANCE` | How far |

Eight, not seven, and `FAMILIARITY` is **not among them** — it is a modifier (§9), which is
finding B's *"Fresh faces"* corrected.

### 6.2 Reason lines — one renderer per evidence variant

Levels use §B16's format throughout: two decimals, decimal comma, U+2212 minus, em dash for
an absent one.

**`LevelFitEvidence` `{my_mu, their_mu, delta, direction}`** — filtered off all three cards,
so it appears only in the sheet.

| `direction` | |
| --- | --- |
| `ABOVE` | `{delta} above you` |
| `BELOW` | `{delta} below you` |
| `LEVEL` | `Level with you` |

**`PredictedBalanceEvidence` `{pct, my_sigma, their_sigma, confidence}`**

> `Forecast {pct}% even · {confidence}% sure`

The second figure is the platform's own caveat stated in the same breath as the claim — §F1
rule 4's *fact · mechanism* — and this is the **only place `confidence` is drawn at all**:
`SH.player`'s `"{conf}% sure"` went out of scope with the sheet, and #218 recorded that it
was a different number anyway (the *pairing's* confidence printed as a fact about a person).
`my_sigma` and `their_sigma` are never printed. The candidate's σ reaches a screen exactly
once, as the **likely range on the card** — §6.4 — and never as a number of its own.

**`IntentAlignmentEvidence` `{my_mode, their_intent, aligned}`** — read `my_mode` off the
evidence, never off the envelope (§2).

| `my_mode` | `their_intent` | |
| --- | --- | --- |
| `COMPETITIVE` | `COMPETITIVE` | `They're here to compete too` |
| `FOR_FUN` | `FOR_FUN` | `They're here for a fun game too` |
| either | `NO_PREFERENCE` | `They'll play either kind of evening` |
| `COMPETITIVE` | `FOR_FUN` | *not a reason — see §7* |
| `FOR_FUN` | `COMPETITIVE` | *not a reason — see §7* |

**`ReliabilityEvidence` `{score, strands[], floor_breached}`** — written, and **unreachable
day one** (`NoPlayerScoresExist`, map Decision 3). It is written anyway because the
vocabulary is closed and a code with no words is how a term arrives blank the day its
provider lands.

> `Player Score {score}`

`floor_breached` is not drawn here — it is `RELIABILITY_FLOOR_BREACH`'s (§9), and printing it
twice would make one dock look like two.

**`AvailabilityOverlapEvidence` `{shared_count, next_slot}`**

| | |
| --- | --- |
| `shared_count > 0`, `next_slot` present | `{shared_count} slots you both ticked · next {slot}` |
| `shared_count > 0`, `next_slot` null | `{shared_count} slots you both ticked` |
| `shared_count == 0` | `No shared slots — one of you would have to bend` |

`{slot}` is §B16's slot name (*"Tue evening"*), built from the **promoted** `DayPart` and
weekday tables (§1) rather than a third list.

**`PlayingStyleEvidence` / `SocialVibeEvidence` `{matched[], complementary[], clashing[]}`** —
one renderer each, differing only in their heading noun, because the two terms carry
different weights and invert between modes and *"a client renders them under different
headings."* Tag ids resolve through the **promoted** `socialTagLabel`.

Precedence: `matched` → `complementary` → `clashing`.

| Fired | On court | Around the game |
| --- | --- | --- |
| `matched` | `Both of you: {labels}` | `Both of you: {labels}` |
| `complementary` | `{a} meets {b}` | `{a} meets {b}` |
| `clashing` only | *not a reason — see §7* | *not a reason — see §7* |
| all three empty | `Different on court, not incompatible` | `Different around the game, not incompatible` |

The last row is the term's **measured zero** and its words are the code's own: *"a pair with
nothing firing is different, not incompatible — the term's zero is a real clash, never an
absence of relationship."* It is **not** the same state as the term standing down (§8).

**`DistanceEvidence` `{km, area_code, outside_their_radius}`**

| `outside_their_radius` | |
| --- | --- |
| `false` | `{km} km away` |
| `true` | `{km} km away — outside the ring they set` |

The second is a fact the searcher is owed rather than a penalty applied behind their back:
*"somebody who set a small radius is not refusing to be found, and the searcher is shown the
fact rather than having the person removed."*

### 6.3 `area_code` is not a word, and no card may print one

**`area_code` is a coordinate string** — `A+050612+0019938` — and `areas.py` refuses to make
it a name, in writing:

> *"the human-readable area a player card prints has no producer in this repository yet, and
> deriving one there would be inventing a naming scheme nobody has calibrated. **That refusal
> stands.**"*

So §B11's meta line `"{area} · {km} · active {x}"` has **two** slots with nothing behind
them, not one: `active {x}` was already refused in writing (#218), and `{area}` is refused
here. #218 marked `area_code` present — it is present, and it is not a word.

The module licenses exactly one client sentence from it, and that one is honest:

> *"A card saying **they are in your area** is a comparison the client makes between two
> codes, which is exactly the shape [ADR-0021](../../adr/0021-client-derived-state.md)
> licenses a client to compute."*

So the meta line becomes **`{km} km`**, with **`In your area · {km} km`** when the two codes
are equal. Nothing else. The day a gazetteer exists, `area_code_of` is the one function that
changes and this line gains a name without any other consumer moving.

### 6.4 The level row — three facts, and the word the prototype spent on the wrong one

§B11 and §B12 draw the row as `"{level} · band {low}–{high}"`, where `{low}–{high}` is
`2,55–2,87`. **That is not a band.** The four bands are New 1,0–1,5 · Developing 1,6–2,6 ·
Established 2,7–3,8 · Advanced 3,9–5,0; `2,55–2,87` is the **likely range**, μ ± σ. The
prototype spent the domain's word on a different concept, and a reader who has seen the band
names anywhere else in the app reads the pair as the band's own edges — which is exactly what
`Band`'s docstring forbids: *"a card can never name a band that disagrees with the number
beside it."*

So the range carries a word of its own, and the band keeps its name:

> `{level} · {band} · likely {low}–{high}`   — e.g. `2,71 · Established · likely 2,55–2,87`

*Fact · mechanism*, §F1 rule 4's shape, the same one `Forecast {pct}% even · {confidence}% sure`
takes: the level and its plain-language meaning, then the caveat. Levels use §B16's format on
all three numbers — two decimals, decimal comma.

**All three come off `player_card`.** `level` and `band` already ship; `range` is the one
contract change the card audit found, and the card carries it because
[ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md)'s rule admits it
— *a card says only what its subject published, and every field on it is a fact about that
person alone*, which is the same rule that keeps `distance_km` off the card. **The band's
numeric edges are not on the card**: the only thing that would draw them is the band bar, and
the band bar is drawn from the player record sheet, which is out of scope.

**The client computes nothing here** — not the range from `their_sigma`, and not the band's
edges from a table of four. Either would be a domain rule encoded in TypeScript, the objection
that promoted `distance_km` out of the distance evidence in the first place.

## 7. Concerns

`concerns[]` is keyed by the same eight `Term` values, ranked by points forgone
(`weight × (1 − value)` against `concern_points = 5`), and emitted by the engine. **Its own
table**, not the reason line in amber: a concern is the opposite claim about the same term,
so one sentence cannot serve both — and #233 §7 marks concerns **in place** on the sheet,
which makes reason and concern co-resident on one row rather than alternatives.

The card draws one; the sheet marks all of them. *"The cap is the client's."*

| `term` | Concern |
| --- | --- |
| `LEVEL_FIT` | `A wide level gap — the game may be one-sided` |
| `PREDICTED_BALANCE` | `Forecast to be uneven` |
| `INTENT_ALIGNMENT` (competitive searcher) | `They're here for a fun game, and you're not` |
| `INTENT_ALIGNMENT` (for-fun searcher) | `They're here to compete, and you're not` |
| `RELIABILITY` | `Their record is thin on turning up` |
| `AVAILABILITY_OVERLAP` | `Almost none of your week is theirs` |
| `PLAYING_STYLE` | `{a} against {b} on court` |
| `SOCIAL_VIBE` | `{a} against {b} around the game` |
| `DISTANCE` | `A long way out` |

`INTENT_ALIGNMENT` is the one term whose concern is genuinely two sentences: #230 priced both
directions and **both fire**, so a single wording would state one player's mismatch as the
other's.

The two tag terms take their clashing pair, which is why §6.2 routes `clashing`-only here:
a clash is a graded claim, and the engine is the only thing entitled to make it.

## 8. A term that stood down

Three codes, minted by #233 §8, and the sentence is `(term, reason)` — *"`INTENT_ALIGNMENT +
NOTHING_FROM_THEM` and `SOCIAL_VIBE + NOTHING_FROM_THEM` are two different sentences from one
code."*

`NOT_YET_ON_THIS_PLATFORM` is stated **once, in the footer**, never per card — #233 §8's two
tiers, so reliability's line does not print identically on twenty cards and read as twenty
separate shortfalls.

> **Footer:** `Some of what the engine weighs isn't on this platform yet, so it isn't counted
> for anybody.`

The six degradable terms, per side:

| `Term` | `NOTHING_FROM_YOU` | `NOTHING_FROM_THEM` |
| --- | --- | --- |
| `INTENT_ALIGNMENT` | `You haven't said what kind of evening you're after` | `They haven't said what kind of evening they're after` |
| `RELIABILITY` | — | `Nothing on their record yet` |
| `AVAILABILITY_OVERLAP` | `Your week is blank` | `Their week is blank` |
| `PLAYING_STYLE` | `You haven't picked any on-court tags` | `They haven't picked any on-court tags` |
| `SOCIAL_VIBE` | `You haven't picked any tags about the evening` | `They haven't picked any tags about the evening` |
| `LEVEL_FIT`, `DISTANCE` | *never stand down* | |

**`NOTHING_FROM_YOU` wins a tie** (#233 §8) — it is the only one the reader can act on.

**`RELIABILITY + NOTHING_FROM_THEM` deliberately says nothing about *when*.** The code
swallows three causes — no record, the last observation past the horizon, no strand clearing
`min_observations` — so that the day reliability goes live the sheet still cannot date
anybody. ADR-0106 §5's recency refusal is held by the vocabulary's shape rather than by a
reviewer noticing, and the wording must not reintroduce it: *"nothing on their record yet"*
and never *"not recently"*.

**`NOTHING_FROM_YOU` never appears on a card**, only in the sheet's not-counted block — a
list of twenty cards each telling you your own week is blank is one fact printed twenty
times, and the prompt (§12) is where that belongs.

## 9. Modifiers

Four codes, all of which print — *"a modifier that could move a score without owing a
sentence would be Liveness wearing stage 4's clothes."* The block is headed by the derived
`applied` (#233 §4), and **day one it is empty for nearly everybody**.

| `ModifierCode` | |
| --- | --- |
| `CALIBRATION_VALUE` | `Playing them would sharpen your rating` |
| `FAMILIARITY` | `You've played them before` |
| `WELCOMING_RECORD` | `Good with players who are new` |
| `RELIABILITY_FLOOR_BREACH` | `Their record sits under the bar` |

**Block heading:** `Then the engine adjusted it` · **sub-total label:** `The eight terms` ·
**the derived figure:** `{applied} from adjustments`.

`record_rows.py` forbids summing the list, so the block's figure is `fit − Σcontributions`
and never a re-addition of the rows. The words above must not tempt anyone into one: no row
prints a running total.

## 10. Why this person is on the list

**`WireInclusionReason`** — a union of one, and it **admits**:

> `INTEREST_LIFT` → `They already said yes to you`

**`LivenessReason`** — ten codes. `INTEREST_RECEIVED` and `INTEREST_LIFT` fire for the same
person and are two facts with **one tag** (#231, Open #14): the tag is bound to the admitting
code, and the sentence replaces it.

| `LivenessReason` | |
| --- | --- |
| `INTEREST_RECEIVED` | `Wants to play you` |
| `PREVIOUS_ACCEPT` | `Said yes to you before` |
| `ANSWER_RATE_AND_SPEED` | `Answers quickly` |
| `RECENT_ACTIVITY` | `Around this week` |
| `OVERLAP_PROXIMITY` | `Free around when you are` |
| `RECIPROCAL_ASYMMETRY` | `You're well inside their range` |
| `NEWCOMER_LIFT` | `New here` |
| `CHALLENGE_LOAD_SOME` | `A few challenges waiting on them` |
| `CHALLENGE_LOAD_BUSY` | `Plenty of challenges waiting on them` |
| `CHALLENGE_LOAD_FULL` | `A full inbox — they may be slow to answer` |

**The two silent signals have no words and must never get any** — *"a silent move carries
points and no code, so there is no name on the value to print."* A client inventing a
sentence for one would be publishing what the enum was shaped to withhold.

**`RECENT_ACTIVITY` is the one to watch.** It is a *reason code*, which is the sanctioned
crossing; *"active today"* on a meta line is the refused one (ADR-0106 §5). The wording is
deliberately un-datable — *around this week*, never a timestamp, a day or a green dot.

**Sheet zone heading** (#233 §7, zone 4): `What else moved you here`.

## 11. An empty seat, and why this four

**`UnfilledReason`** — four codes, per seat, and #223 made them the court's own statement of
its shortfall rather than AC-69's *"Only found N"*. Each routes its remedy to the pool, where
the ladder is.

| `UnfilledReason` | |
| --- | --- |
| `NO_CANDIDATE_ABOVE_FLOOR` | `Nobody in range was a good enough fit for this seat` |
| `NO_ADMISSIBLE_COMBINATION` | `Plenty of people, but no four of you work together` |
| `POOL_EXHAUSTED` | `Nobody left in range — everybody who fits is already seated` |
| `NO_SHARED_SLOTS` | `Seated, but the four of you share no slot — you'd all have to bend` |

**`NO_SHARED_SLOTS` must not read as a refusal.** It is *"a dock, never a refusal: the
availability term zeroes and the screen says you would all have to bend, and nobody is
removed from the court for it."* The sentence above states the state and names nobody as the
cause, which is §F1 rule 5 with no rule to name.

**`GroupReason`** — five codes, *"one closed code, never a number"*. `G` is recorded and
never returned, so these sentences are the whole of the group objective's explanation, and
none of them may quote a figure.

| `GroupReason` | |
| --- | --- |
| `EVENEST_ARRANGEMENT` | `The evenest way to split these four` |
| `STRONGEST_WEAKEST_SEAT` | `Nobody here is out of their depth` |
| `BEST_AVERAGE_FIT` | `The best all-round fit across the four seats` |
| `MOST_SHARED_SLOTS` | `The four of you share the most slots` |
| `GROUP_RAPPORT` | `These four read each other well` |

`GROUP_RAPPORT` covers two group terms (`CROSS` and `CROSS_MIN`) and gets **one** sentence —
the code is the vocabulary, and splitting it in copy would publish a distinction the enum
deliberately does not carry.

**And the court seat's sheet explains the pairing's Fit, never the `G` that seated them**
(#233 §9). No sentence here appears inside `SH.whyfit`.

## 12. The four prompts

*"Codes, never sentences… **Keep 15 km?** is one phrasing of `KEEP_THIS_RADIUS` in one
language, and a backend that shipped it would own the copy for every client that ever
exists."* Each rides on a search response
([#226](https://github.com/Raketa02/Raketa/issues/226)), so *"it never blocks"* is true by
construction.

| `Prompt` | Title | Body |
| --- | --- | --- |
| `KEEP_THESE_TIMES` | `Keep these times?` | `{n} slots now · {was} on your profile. Green rings are new, faded ones you dropped.` |
| `KEEP_THIS_RADIUS` | `Keep {radius_km} km?` | `You've widened to this three searches running. Make it your usual, or keep it to this one.` |
| `UPDATE_PLAY_INTENT` | `Your searches say something else` | `Your last five {sport} searches were {mode}. Your profile still says otherwise — want to change it?` |
| `REFRESH_YOUR_TIMES` | `Is this week still right?` | `The matcher reads this grid every time it looks for anybody — for you and for the people it puts in front of you. A grid that is three months old quietly ruins every match it touches, so it is worth keeping honest.` |

`REFRESH_YOUR_TIMES` keeps §F2 #9 **verbatim** — it is one of the ten strings that define the
voice, and this is the prompt it was written for.

Every prompt closes with §F2's *"Either way the search runs now."* The value each quotes is
`RaisedPrompt`'s own payload — *"the value already in play, never a value the engine
picked."*

**A declined prompt suppresses itself for thirty days**, and three of the four say so
([#237](https://github.com/Raketa02/Raketa/issues/237)). A decline writes no value, so it is the
one answer nothing else would record; the sentence exists because a thirty-day silence nobody is
told about is a hidden mechanism, which is
[ADR-0128](../../adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)'s own instinct
(*"the fix is a sentence on the deck about what a pass does"*).

| `Prompt` | After §F2's closer |
| --- | --- |
| `KEEP_THESE_TIMES` | — |
| `KEEP_THIS_RADIUS` | `Not now means not for a month.` |
| `UPDATE_PLAY_INTENT` | `Not now means not for a month.` |
| `REFRESH_YOUR_TIMES` | `Not now means not for a month.` |

§F1 rule 4's fact·mechanism shape with **no agent**, which is what keeps rule 6 — no *we*, no
*Rakieta*, no passive. It rides §1's code → message mechanism as a `Record` over the `Prompt`
union, so `KEEP_THESE_TIMES`'s blank is a **typed absence** rather than a string somebody
forgot: it is the one prompt with no suppression at all, because a grid legitimately differs per
search where a radius, a declaration and a described week do not
([`the-play-screens.md`](the-play-screens.md) §2,
[#164](https://github.com/Raketa02/Raketa/issues/164)). The shared closer is unchanged on all
four, and `REFRESH_YOUR_TIMES` keeps §F2 #9 verbatim.

## 13. A challenge's standing — five codes, ten sentences

#221: *"**Challenge sent** and **Challenge for you** are one standing read from two sides, not
two states."* So the code is one and the sentence is two, keyed by `(standing, side)`, with
side derived from whether the reader holds the organiser seat.

| Standing | To the organiser | To an invitee |
| --- | --- | --- |
| `AWAITING_ANSWERS` | `Waiting on {n} answers` | `They're waiting on you` |
| `ON` | `Everybody's in` | `You're in — everybody's in` |
| `LINE_UP_INCOMPLETE` | `{n} in, {m} still to answer — the chat is already open` | `You're in. {m} still to answer, and the chat is already open` |
| `DECLINED` | `{name} said no — that seat is open again` | `You said no` |
| `LAPSED` | `{name}'s day ran out — that seat is open again` | `Your day ran out` |

**`LINE_UP_INCOMPLETE` carries #221's constraint in its words.** *"The chat opens on the first
acceptance and grows with each one"*, which makes it **not a waiting room** — and its obvious
phrasing (*"waiting for the rest"*) is the one that would be false.

**`LAPSED` is not a decline** and the words hold that apart: a day ran out, nobody said no.
The `answers challenges` strand needs the denominator, so a lapse that reads as a refusal in
copy is a fact quietly restated as a different one.

**Five, not twenty.** The twenty card states are *"a presentation vocabulary spanning money,
booking and results this context does not own"*, and an unknown standing takes §3's gap
rather than a shorter list.

## 14. Deadlines — "24 h" is not a string

#221 gives **each invited seat its own `answer_by`**, and
`ChallengeOpenedFromMutualInterest` carries *"no deadline"* — a distinct event *"because a
nullable `answer_by` is how a later reader invents a deadline that never existed."*

So the constant is wrong three ways at once, and the fix is three different sentences:

| Moment | |
| --- | --- |
| **Pre-send** (`SH.propose`) | `Nobody is contacted until you send it.` — **no duration**, per §21 |
| **Post-send**, per seat | rendered from `answer_by` through §B16's duration formatter — `{name} · {duration} left` |
| **Mutual yes** | `You both said yes — this one's already on.` **No deadline clause.** |

**~~`{window}` is a contract obligation, not a constant.~~** A pre-send sentence naming a
duration must name the number the backend will actually derive, or it stops naming one — and
[#241](https://github.com/Raketa02/Raketa/issues/241) took the second branch: **`SH.propose`
names no duration at all.** The send response cannot feed a *pre*-send sheet, no `challenges`
route is called before the first send, and the deadline the sentence was reaching for is per
seat and arrives immediately after the act. §21 carries the reasoning; the pre-send row below
loses its `{window}` clause and keeps only the irreversibility.

**`SH.propose`'s closing *"Nothing opens until they accept"* is false for doubles.** #230
already rewrote the pre-send line for the seat count; this is the same sentence in its second
location, and it becomes:

> **Singles:** `Nothing opens until they accept.`
> **Doubles:** `{sport} is doubles — you need {n} more. The first person to say yes is in, and you can start talking then.`

## 15. Names

`Nickname` is **2–64 characters**, `users` holds no name at all, and ADR-0107 is explicit:
*"every sentence naming somebody uses the whole handle or names nobody — the prototype's
`split(' ')[0]` has nothing behind it here, and inventing a first name is the product
addressing a person by a name they never gave it."*

> **One `playerName()`: the handle, whole, and `You` for yourself.** Used by §B10's
> head-to-head row, §B16's side-name formatter, §B17's `SH.propose`, and **all eight of
> §F3's toasts that name somebody.**

**A seat label may truncate visually; a sentence may not, and a spoken name never does.**
ADR-0107's rule is against *inventing* a familiar form — a visual truncation invents nothing,
and the accessible name carries the whole handle, which is where the rule actually bites.

**§B16's side-name formatter is redrawn, not kept.** *"You + Marek"* is a layout that assumed
short words; at 64 characters the 46px seat is the binding constraint (§G5 already lists the
overflow at *first-name* length) and it decides the formatter rather than the other way
round. The unknown player stays a question mark.

## 16. The searching states

§B14 draws *"Level fit, predicted balance, reliability, when your weeks overlap, distance,
vibe, fresh faces — the same seven terms"* and *"level, band width, reliability, overlap"*.

**That is #233 §5's defect in a second place**, and stale identically: it includes **fresh
faces**, which is a *modifier*; omits **`INTENT_ALIGNMENT`**, third-largest in both modes; and
**"band width" is not a term at all**. #233 §5's ruling reaches here unchanged — *"any
replacement summary is a weight claim in prose with no gate behind it."*

> **Drop the inventory. Keep the count.**

| Instance | |
| --- | --- |
| Pool ranking | `Ranking everybody you could play…` + `{players_in_range} in range for {sport}` |
| Engine fill | `Looking for the evenest four…` + `{players_in_range} in range` |

The count is `PoolDescription.players_in_range`, and it comes from the **response** — #223
moved it off the prototype's 650 ms timer, which printed a number before the answer existed.

**The whyfit header** loses its inventory the same way (#233 §5): the count is the derived
number of live rows, and the mode clause is absent where `mode` is null.

> `{n} weighted terms{, tuned for a competitive game | , tuned for a fun game}. Weights persuade; you decide.`

*"Weights persuade; you decide"* survives — §F1 rule 7, and #233 booked it here by name.

## 17. Windows, rungs and sorts

**`Window`** — *"a code, never a sentence: **tonight** is the client's word"*. §B16's title
case is kept; these are window names, which §F1 rule 1 exempts.

| | |
| --- | --- |
| `TODAY` | Tonight |
| `TOMORROW` | Tomorrow |
| `WEEKEND` | This weekend |
| `THIS_WEEK` | This week |
| `ANY` | Whenever suits |

`ANY` is *"the only rung that claims nothing"* — an empty grid reads `ANY`, so *Whenever
suits* must not read as an enthusiastic answer to a question nobody answered.

**`RelaxationAsk` × `Rung`** — the ladder ships on the pool alone (#223), and every *widen*
sentence is gated by `radius_clamp`, since each is addressed to a player who may already be
at 50 km.

| | |
| --- | --- |
| `TIMES` | `Look outside your week` |
| `RADIUS`, rung `B` / `C` | `Look out to {radius_km} km` |

`Rung` letters are never printed — *"they are letters rather than numbers"* precisely so
nobody lines them up against a struck rung, and printing either spelling publishes an
engine-internal ordering.

**`SortOption`** — the row draws `sorts_available` and vanishes when empty (#231).

| | |
| --- | --- |
| `BEST_FIT` | Best fit |
| `CLOSEST` | Closest |
| `MOST_RELIABLE` | Most reliable |
| `EVENEST` | *out of scope — #231* |

`MOST_RELIABLE` is in the vocabulary and never offered today; `EVENEST` reads
`would_be_forecast`, which nothing has ever written. Both keep words so that the table is
exhaustive by type; neither is reachable.

**`ForecastAssumption`** — one value, and ADR-0108 makes the figure and its caveat one thing.

> `EMPTY_SEAT_MATCHES_ITS_PARTNER` → §F2 #6, **verbatim**: *"Runs on what is seated so far,
> reading each half-empty side as if the missing player matched the one already there. It
> settles as you add."*

## 18. Cited, not written

| Vocabulary | Where its words already are |
| --- | --- |
| `SocialTag` (19) | `socialTagPresentation.ts` — label, name and emoji, **promoted to `shared/`** (§1) |
| `DayPart` (3), weekday (7) | `availabilityPresentation.ts`, **promoted to `shared/`** (§1) |
| Levels, distances, percentages, money, clock times | §B16 and §F1 rule 8 — one shape each, already fixed |
| Balance word and tone | §B9 |
| Error codes | `authErrorMessage.ts` and `shared/errors/recoveryMessage.ts` |

## 19. What this file does not decide

- **Pluralisation and Polish-market copy.** §J4's gap; the map's fog. What is owed here is
  that no string hardcodes an `s`.
- **Telemetry wording.** §J7's eleven observations; the map's fog.
- ~~**What the send refuses, and in whose words**~~ — settled by
  [#241](https://github.com/Raketa02/Raketa/issues/241) in §21.
- **Anything on an out-of-scope surface** — the record sheets, *Show them again*, the
  seat-impact line, at-stake, Player Score's strands, languages. A code with no surface gets
  no words, and the map's Out of scope is the list.
- **A clash word for the two tag-term concerns, and `KEEP_THESE_TIMES`'s colour-named body**
  — both surfaced by §20 and named there rather than invented.

---

## 20. What each control announces

Decided by
[What each Play control announces](https://github.com/Raketa02/Raketa/issues/236).

`design-system.md` [Part 13](../../../frontend_player/docs/design-system.md#part-13--accessibility)
is the **requirement** — names on everything tappable, `accessibilityState` on selected
chips, modal semantics on the sheet, an announcement on every toast, and *"never colour as
the only signal."* §E6 is the **inventory**, and it opens by recording what the prototype
has: *"seven `aria-label`s in the whole file, two of them in this feature. No `role`, no
`aria-live`, no `alt`, no `aria-selected`, no `aria-pressed`."*

Neither is the **sentences**, and Part 13's rule is that *"a control's label is its content
**and** its state."* An accessible name is copy — it is localisable, it quotes numbers that
need §B16's formats, and it composes codes whose sentences are already in this file. So it
lives here, through §1's mechanism and no other: **code → message, never message → message.**
A label is never a template inlined in a component.

**§E6 is a starting inventory, not a specification.** Five of its rows are rewritten below
rather than adopted, and each rewrite says why.

### 20.1 The rule that decides an element

Part 13's two worked examples disagree on their face and the rule has to reconcile them: the
question navigator is *"one element, one label — never one per segment"*, where the
availability grid is twenty-one elements with the column heads hidden.

> **One accessibility element per action. Everything with no action of its own merges into
> the nearest action above it.**

Actions are what a listener navigates *by*. The navigator has none, so it is one element; a
grid cell is an answer, so there are twenty-one. This is the same rule stated once instead of
twice, and it is the rule §G3's component boundaries are drawn against —
[`the-play-components.md`](the-play-components.md) decides the **React component tree**, this
file decides the **accessibility tree**, and they are independent: a card may be one element
built from six components, or six elements built from one.

**The cap is on what precedes an action, not on the label.** A merged label leads with the
identifying facts and continues with the argument; a listener who has heard enough interrupts
and acts. Roughly twenty words before the first action is the bound, and a merged label that
cannot state its subject inside it is evidence the seam is wrong.

### 20.2 The role vocabulary — React Native, not ARIA

§E6 asks for `tablist`, `radiogroup`, `switch`, `progressbar`, `image`, `dialog` and
`status`. React Native's `accessibilityRole` has near-namesakes for most, and its
`accessibilityState` offers only `{disabled, selected, checked, busy, expanded}` — **no
`pressed`**, which §E6 asks for three times.

> **Prefer the role that carries the state; where no role carries it, the label carries it;
> never style alone.**

That is [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid)'s own
argument — *"`checkbox` rather than `button` because the state is the point and the role is
what carries it: 21 buttons announce 21 identical actions, where 21 checkboxes announce 21
answers"* — and [6.10](../../../frontend_player/docs/design-system.md#610-the-radius-slider)'s,
and [7.9](../../../frontend_player/docs/design-system.md#79-the-question-navigator)'s refusal
of `progressbar` for a control with no max.

Where §E6 says *pressed* — a seat selected for a swap — it becomes `selected`, the state
React Native actually ships.

### 20.3 The candidate card

The card body's action is *Why 78?* — [#231](https://github.com/Raketa02/Raketa/issues/231)
repointed the long-press there when K-7 ruled the record sheets out. So the card is **two
elements**: the body, and its primary button. The fit pill is not a third; it merges.

**The card is spoken in a different order than it is drawn.** Identifying facts lead, the
argument follows. This is the one recorded divergence from visual order in the feature, and
it exists because §10 is titled *Why this person is on the list* — dropping the reason lines
to satisfy a word count would delete what the card is for.

| | |
| --- | --- |
| **Card body** | `button`. `{name}. Fit {n} out of 100. {level} · {band} · likely {low}–{high}. {In your area · }{km} km. {reason}. {reason}. {reason}. {reason}. {concern}.` |
| **Primary button** | `button`. `Add {name} to the court` · `Challenge {name}` — the visible label is *Add* / *Let's play*, which announces identically on twenty cards. Naming the subject is [6.9](../../../frontend_player/docs/design-system.md#69-the-photo-tile-and-picker)'s remove control, whose label *"names which photo it removes"*. |

`{name}` is §15's `playerName()` — **the handle, whole.** A seat label may truncate; a spoken
name never does.

**`Fit {n} out of 100`, not §E6's *"Match score 78 out of 99"*.** Fit is `CONTEXT.md`'s term
— *"how good the game would be, printed on the card as one number out of a hundred"* — and
*Match Fit* is the engine's name, which a card must not borrow. **§E6 rewritten, first of
five.**

**The ✦ is hidden**, per §E6, and it is hidden by the merge rather than by a separate rule.

**A concern needs no marker, seven times out of nine.** §7's sentences carry their own
polarity — *A wide level gap — the game may be one-sided*, *Their record is thin on turning
up*, *A long way out*. The two tag terms do not: `{a} against {b} on court` and `{a} against
{b} around the game` read as neutral description, and a listener cannot hear the amber. §20.12
books the gap rather than inventing the word here.

### 20.4 The court — side and role, never an index

§E6 proposes *"Seat 3, Marek Z., level 2,92. Tap to replace."* **An index is not a place.** A
listener has no picture of the court, and H-25 makes the number mean different things in
different sports — squash puts both players on the same half, so seat 3 is not where seat 3
was. **§E6 rewritten, second, third and fourth of five** — the seat, the clear badge and the
empty seat all lose their numbers.

| | |
| --- | --- |
| **Court** | A summary element preceding the seats: `{Sport}, {n} of {m} seats filled.` Four seats announced against nothing is four seats a listener cannot place. |
| **Seat, them** | `button`. `{side}, {name}, level {level}` |
| **Seat, you** | `button`. `{side}, you` |
| **Seat, your partner** | `button`. `{side}, {name}, level {level}` |
| **Seat, empty** | `button`. `{side}, empty{. UnfilledReason}` — §11's sentence when the engine has one, nothing when the seat was never filled |
| **Seat, selected for a swap** | the above, plus `accessibilityState={{ selected: true }}` |
| **Clear badge** | `button`. `Remove {name} from {side}` |
| **Swap toggle** | `switch`. `Swap players`, `checked` |
| **Balance bar** | `image`. §B9's balance word and its figure — the word is the point, since the bar is a colour |

`{side}` is *your side* / *their side*, and in doubles the partner seat says *your side, your
partner*. The **holding ring** — the 430 ms press feedback — announces nothing: it exists to
confirm a finger is down, on a channel this listener is not using.

**The 9,5pt seat label does not earn `allowFontScaling={false}`.** Part 13 permits the escape
only *"inside the level bar's drawn geometry"*, and §15 already ruled the court's case the
other way: *"a seat label may truncate visually; a sentence may not, and a spoken name never
does."* The visible label scales and truncates, the spoken one is whole, and nothing is
invented. **This also settles [#240](https://github.com/Raketa02/Raketa/issues/240)'s
truncation question**, which is recorded there rather than held by both.

### 20.5 The deck

The deck card is §20.3's card with two buttons instead of one.

| | |
| --- | --- |
| **Not today** | `button`. `Not today, {name}` |
| **Let's play** | `button`. `Let's play, {name}` — the 🎾 hidden, per §E6: *"otherwise it announces as 'tennis ball let's play'"* |

**When a card leaves, two things happen and both are deliberate.** §E3's first finding is that
focus is destroyed on every render and nothing restores it, so today a listener is dropped at
the root with no idea what happened. The toast announces the act; an explicit
`setAccessibilityFocus` moves focus to the incoming card's body. #228 §12 made both actions
optimistic, so the next card is already there to receive it.

**If the swipe of UI Open decision #9 ships, it is never the only path.** VoiceOver and
TalkBack consume the drag before the card sees it, so a swipe-only deck is one a listener
cannot answer. §E2 records the two buttons as what exists today; they stay.

### 20.6 The sheets — three, not five

`SH.player` and `SH.playersocial` are out of scope (K-7), so the five are **three**, plus the
prompt sheet carrying §12's four prompts.

Part 13 already locks `accessibilityViewIsModal`, hidden siblings, and focus returned to the
trigger on close. The one thing it leaves open is where focus lands on the way *in*:

> **The title, not the first action — one rule for all of them.**

`SH.whyfit` is an explanation with no action worth jumping to; `SH.saveav` and the prompts are
questions whose answer should be heard before it is offered; and `SH.propose`'s first action
is **send**, the only irreversible act in the tab. Landing focus on it by default would make
the worst outcome the cheapest to trigger. §E6's contrary precedent — the splash's *"focus
moved to 'Open the chat'"* — is on a surface the map ruled out with chat.

**`SH.whyfit`'s accessible name is not its visible title.** The title draws `Why ✦ {score}`,
and the ✦ must not be spoken, so the sheet is labelled `Why fit {n}`. It is the one place in
the feature where the two differ, and it differs because a glyph is doing work in the visible
one.

### 20.7 The availability grid, and the diff variant

The editor is [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid),
reused unchanged and **not restated** — `checkbox`, `checked`, `"Monday morning"`, column
heads hidden. §E6's *"'EVE' should be announced as 'evening'"* is already done there.

**`SH.saveav`'s diff grid is a different control with a third fact.** Newly-on draws a volt
ring, newly-off drops to 45% opacity — and the sheet's own body text says *"Green rings are
new, faded ones you dropped"*, which is Part 13's prohibition in the one place the copy
**names the colour as the mechanism**.

| | |
| --- | --- |
| **Diff cell** | Not interactive — a `span` already. `{Day} {part}` · `{Day} {part}, newly added` · `{Day} {part}, dropped` |

`KEEP_THESE_TIMES`'s body is a **copy edit, booked in §20.12** — it instructs sighted players
in a vocabulary no listener can use.

### 20.8 Why-fit — the meter is decoration

The row draws a label, a mono `×{weight} → {weight × value}`, **then** a meter, then the
reason. The number is already text two words earlier.

> **The meter is hidden and the row's words carry it.**

This is [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid)'s
argument again — *"the column heads are therefore decoration to assistive technology and are
hidden from it; without that, every cell is announced twice."* A bar visualising a printed
number is that same double announcement. **§E6 rewritten, fifth of five**: its *"expose it as
a progress indicator with its current, minimum and maximum values"* would publish a precision
the row already states in a shape the row already chose. `SH.player`'s three meters are the
only others in the prototype and K-7 ruled them out, so **`progressbar` appears nowhere in
this contract.**

Rows announce `{term label}. {figure}. {reason}` — §6.1's heads, §6.2's renderers, §7's
concerns marked in place per #233 §7. The header is §16's sentence.

### 20.9 The three live regions

All polite. There are three, and no fourth:

| | |
| --- | --- |
| **The toast layer** | Part 13's requirement, with §20.10's amendment |
| **The searching status** | §16's two sentences, with `players_in_range` from the response |
| **The provisional forecast figure** | The only figure in the tab that changes while focus is elsewhere |

The third is the one nobody had claimed. Moving a player across the net changes the forecast
while focus stays on the seat that moved — so the figure announces, carrying §17's
`EMPTY_SEAT_MATCHES_ITS_PARTNER` caveat rather than a bare number, which is ADR-0108's rule
that the figure and its caveat are one thing.

**The pool header's percentage gains its word.** §E5: the 24pt figure is *"tinted with no word
alongside it, leaving colour as the only cue"* — where the forecast card pairs the tone with
§B9's balance word every time. Part 13 forbids it outright, so the header draws the word too.
A visual change, decided on an accessibility rule, and recorded here because nothing else
claimed it.

[#239](https://github.com/Raketa02/Raketa/issues/239)'s failure sentences go **into** the
toast region. It writes the words; this section says which regions exist.

### 20.10 Politeness, and the one announcement that interrupts

`AccessibilityInfo.announceForAccessibility` **interrupts** on both platforms. Nineteen toasts
fire from this feature, and one landing mid-card cuts a listener off in the middle of the
reason lines they were listening to. Part 13's requirement was written against onboarding,
which has one toast at a time.

> **`announceForAccessibilityWithOptions` with `queue`.** The requirement survives with its
> mechanism named more precisely — a Part 16 amendment, booked in §20.12, not an exception.

**One announcement interrupts, and earns it.** [#227](https://github.com/Raketa02/Raketa/issues/227)
made the send discard the Play stack to `[Now]`, which is a placeholder — so the toast is the
**entire** confirmation that the one irreversible act in the feature succeeded. It fires
**after the destination has mounted**, so the platform's own screen-change notification does
not clobber it, and it does not queue behind anything, because there is nothing left on screen
to tell the listener the challenge went.

### 20.11 Two collapse conditions, and one screen rule

`the-play-screens.md` §3 licenses the fill animation — *"presentation over a completed answer,
and the client may take its time."* That permission is granted to **craft aimed at sight**. A
listener gets none of the craft and all of the latency, in front of an answer already in
memory.

> **`isScreenReaderEnabled` collapses the fill animation and the deck's stagger to their end
> state, and zeroes #228 §9's minimum-display latch.**

It is a *second* condition on the same path as reduced motion, not a second path — a player
may have VoiceOver on and reduced motion off, which is the common case. #239 owns the
reduced-motion collapse; the two share one helper. The searching region then announces the
**result** once and never a stage, which is §3's *"no fake stages"* reaching a second surface.

**Every screen title takes `accessibilityRole="header"`**, and nothing announces a screen
change beyond what the platform already fires. §C records the page header as *not* a shell
region — *"the title scrolls away"* — so the header role is what makes it reachable again,
both readers navigating by heading.

### 20.12 What this section does not write, and what gates it

**Two gaps, named rather than invented:**

- **A clash word for the two tag-term concerns.** §7's `PLAYING_STYLE` and `SOCIAL_VIBE`
  concerns render `{a} against {b}` and read as neutral description. §7 says why they are
  different — *"a clash is a graded claim, and the engine is the only thing entitled to make
  it"* — and the word belongs beside those sentences, not in a label.
- **`KEEP_THESE_TIMES`'s body.** *"Green rings are new, faded ones you dropped"* names a
  colour as the mechanism. §12 owns the rewrite.

**One obligation on the design system**, to land with
[#219](https://github.com/Raketa02/Raketa/issues/219)'s outstanding rows so the amendment log
stays in order: **Part 13 — every toast announces, queued rather than interrupting; the send
confirmation is the single exception.**

**Two gates**, booked onto [#232](https://github.com/Raketa02/Raketa/issues/232). An
unenforced rule drifts silently, and §E6's *"seven `aria-label`s in the whole file"* is what
that looks like:

- **Label coverage is a compile error, not a test.** §1's `Record` keyed by the generated
  union already gives it: a code with no renderer does not build.
- **A lint rule over `features/play/`** — every `Pressable` carries an `accessibilityLabel`
  or an explicit hide. This is the one that catches the historical failure, because the
  historical failure was an omission and a type cannot see one.

### 20.13 Cited, not written

| | Where it already is |
| --- | --- |
| The tab bar's five tabs | [#227](https://github.com/Raketa02/Raketa/issues/227) — `tab`, label, `selected` on all five; the ⚡ hidden; §E7 dissolved |
| The availability grid, in edit mode | [6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid) |
| Touch targets — §E4's fourteen under 44pt | [#219](https://github.com/Raketa02/Raketa/issues/219), which found the system stricter |
| Contrast, Dynamic Type, tabular figures, reduced motion | [Part 13](../../../frontend_player/docs/design-system.md#part-13--accessibility) |
| Focus order | §E3 — DOM order matches visual order on every Play screen |
| Numbers, levels, distances, durations | §B16, through §18 |
| Pluralisation | §19 — no string hardcodes an `s`, accessible names included |

## 21. A refused send — two codes, and the naming done elsewhere

[#241](https://github.com/Raketa02/Raketa/issues/241). The send re-verifies five facts and
refuses **whole** ([`the-play-screens.md`](the-play-screens.md) §5.1). Neither refusal carries
a payload, so neither sentence has a name in it until the client has re-read the source that
holds one.

| Code | The sentence | Then |
| --- | --- | --- |
| `line_up_no_longer_sendable` | `Something's changed — one of these players can't be invited now.` | Read the origin search back; the withheld rows mark their seats. |
| the open-challenge refusal (#221) | `You've already got a game waiting with {name}.` | `{name}` comes from the player's **own** challenges, not from the refusal. |
| neither seat marked after the re-read | `Something's changed, and one of these players can't be invited right now.` | The dead end §5.1 names, stated rather than left silent. |

**The first sentence says *changed*, not *unavailable*.** The fact is that the line-up went out
of date; a person's standing is not the organiser's to be told, and §4's register — a line
states facts and never grades them — is what keeps *can't be invited now* from becoming a
verdict on somebody. Four causes reach it wearing one sentence, exactly as ADR-0130 has them
reach the withheld row.

**The second is the only one with a name in it**, because #222 puts that gate on the
*embarrassment* side rather than the safety side, and an open game of yours is already on your
own list. It is still not read off the refusal — §5.1's rule that a refusal names nobody is
about the wire, not about what the screen may end up saying.

**Plural-safe.** A doubles send can lose two seats to one press and both codes can fire for one
press, so neither sentence may be built from a singular assumption — the first says *one of
these players* because the count is not on the wire either, and counting them would be the
payload this refusal refuses to carry.

**And §14's `{window}` obligation is discharged by deletion.** `SH.propose` names no duration:
there is no `challenges` route the client calls before its first send, `GET /sports` carries
the right argument and the wrong home — a per-seat answer window is not a property of squash —
and the same screen states the real deadline, per person, from a real timestamp, the moment
after the act. What the pre-send sheet owes is the irreversibility, which is the fact the
player cannot recover from.
