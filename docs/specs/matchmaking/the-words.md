# The words

Nothing the matcher sends is prose. What crosses is `Term`, eight typed evidence variants,
`DegradedReason`, `ConcernSchema.term`, `LivenessReason`, `WireInclusionReason`,
`ModifierCode`, `UnfilledReason`, `GroupReason`, `Prompt`, `ForecastAssumption`,
`SortOption`, `Window`, `Rung`, `RelaxationAsk`, `DayPart`, `SocialTag` and the five
challenge standings — and **the app writes the words for all of them**
([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md),
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).

This file is that deck. It is the artifact the build tickets cite by section, and the
artifact a later copy edit is made against — so that §F1's voice can be checked against
itself in one place rather than a dozen.

Decided by
[Every sentence the client writes from a code](https://github.com/Raketa02/Raketa/issues/234).

> **It is the whole app's deck, and it lives here for historical reasons rather than scope ones.**
> §13 and §14 have been `challenges`' since the day this file was written, and
> [#339](https://github.com/Raketa02/Raketa/issues/339) added §22–§24 for the Chats tab, the
> challenge screen, the conversation, its plan card, Now and the game screen. It stays in
> `matchmaking/` because a dozen documents and as many docstrings cite it by relative path, and a
> move would break every one of them with no path left to repair it. Its **screens** are
> [`the-play-screens.md`](the-play-screens.md) and
> [`the-loop-screens.md`](../the-loop/the-loop-screens.md); its **seams** are
> [`the-play-components.md`](the-play-components.md) and
> [`the-loop-components.md`](../the-loop/the-loop-components.md).

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

**The owner is the vocabulary, not the feature, and §22 is where that starts to bite.** Four
features hold copy now: `challengePresentation.ts` keeps §13, §14 and §21; `conversationPresentation.ts`
takes §23's system lines; `planPresentation.ts` takes §22.2 and §22.4; and the tab's own lines sit
with the shell. Nothing about the rule changes — a module per vocabulary owner is what it always
said, and one feature was simply all there was.

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
| `CandidateCard` (competitive) | the photo panel's Level, one head-to-head band — both levels, the bar and the forecast — the Social tag row's **matched** tags, and the record block's **Player Score** | **every reason line, and the concern** — it argues nothing at all since 2026-09-09 (§5a). The set below is what it renders a value for, and therefore what it **states as a clause**: `LEVEL_FIT`, `PREDICTED_BALANCE`, `RELIABILITY` |
| `CandidateCardSocial` (for fun) | Level row, You overlap row, meta line's km — **no tag row** | `LEVEL_FIT`, `AVAILABILITY_OVERLAP`, `DISTANCE` |
| `DeckCard` | Level row, Predicted balance row, You overlap row, meta line's km — **no tag row** | `LEVEL_FIT`, `PREDICTED_BALANCE`, `AVAILABILITY_OVERLAP`, `DISTANCE` |
| `SH.whyfit` | everything, on purpose | **nothing** — #233 §7: a summary block would break §10 *"on the one screen whose job is showing values"* |

**The filter is declared beside each card as the set of terms that surface draws**, so the
rule is checked against the component rather than remembered.

### 5a. The competitive card stopped arguing, so its filter has nothing to filter

**On 2026-09-09 `CandidateCard` lost its reason lines and its concern line.** Everything it
**measures** is untouched — the photo panel, the fit pill, the head-to-head band with both
levels and the forecast over its bar, the record blocks, the stake boxes, the tag row. What
went is the prose beneath the pill: *4 km away*, *They're here to compete too*, *3 slots you
both ticked · next Tue evening*, and the amber concern under them.

The reason is §10's own, read against a list rather than against a card: twenty rows each
carrying three sentences is a screen a player scrolls past. The case for one person is
`SH.whyfit`'s, and every row has carried a control named after that sheet since #309 — *Why
78?*, which is a button and not a gesture. **The argument moved; it was not deleted.**

**The set is unchanged**, and that is deliberate. `COMPETITIVE_CARD_DRAWS` is still
`['LEVEL_FIT', 'PREDICTED_BALANCE', 'RELIABILITY']`, because *Draws* is a claim about which
values the surface renders and the surface renders all three. What the set no longer does on
this card is filter sentences; what it still does is decide **clauses** — §20.1 makes a card
state every value whose own drawing announces nothing, and that rule is untouched.

**The lines are not composed rather than composed and dropped.** A filtered list still has
survivors and survivors reach the spoken name; a card that argues nothing must speak no
argument, because §20.3's licence is that the card is *spoken in a different order than it is
drawn* and never in different **content**. `candidateFacts` takes `argues: false` for that,
and the two registers stay one card.

The other two surfaces are untouched: the social and deck cards have no sheet behind them, so
their sentences are the only place their terms could be said, and `SH.whyfit` still filters
nothing at all.

**The competitive card's set survived its own redraw unchanged**
([#309](https://github.com/Raketa02/Raketa/issues/309)). A two-`Side` row, a bare bar and a
*Predicted balance* row collapsed into **one band**, and the drawn set is still
`['LEVEL_FIT', 'PREDICTED_BALANCE']` — because the band replaced the three **elements** that
drew those two terms and not the two **facts**. That is the row above read the way it is meant
to be read: *Draws* is a claim about which values a surface renders, never about how many boxes
it renders them in.

**`RELIABILITY` joined that set the day the Player Score block printed, which is
[#312](https://github.com/Raketa02/Raketa/issues/312).** The row above said *"only once the score
block prints"* and the block prints now, so the sentence `Player Score {score}` stops appearing
as a reason line on this card and goes on appearing on the other two, which draw no block.

The set is **unconditional** where the block is not, and the two read different fields: the block
prints `player_card.player_score` — the **published** figure — where the filtered sentence is
written over `ReliabilityEvidence.score`, the engine's. ADR-0140 §6 makes those two reads
deliberate, and §1 above says why the card must not borrow the engine's: *"taking the card's
figure off the engine's record would make what a player is shown a consequence of whatever the
reliability term happens to carry"*. Both reads hit the same port in the same request, so a term
that fired without a published score is not a state the contract produces; the day it were, the
card would state the fact nought times, and the answer would be the second read rather than a
fallback that prints the engine's number under the block's name.

**And the Level is now printed twice on that card** — hugely on the photo panel, and again on
the right of the band. §10's rule is not broken by it and the distinction is worth keeping: the
panel prints what the player **published** (`player_card.level`, drawn whatever fired) and the
band prints one side of a **comparison** (`level_fit.theirMu`, computed against the other). §10
forbids a *reason line* restating a value the card renders, which is a rule about the two
registers — a fact **stated** and a fact **argued** — rather than a rule about pixels. The fact
is said once, in `levelRow`, and `LEVEL_FIT`'s sentence is filtered off exactly as before.

**The two tag terms are the one entry in that table that is drawn in half**
([#311](https://github.com/Raketa02/Raketa/issues/311)), and the drop is conditional because the
term is. `tagTermReason`'s precedence is *matched, then complementary, then the measured zero*, so
a term with anything in `matched` writes `Both of you: {tags}` — the very ids the row has just
drawn as tinted chips. That is §10 at its own root, and the chips are the richer form, so the
sentence goes. A term with **nothing** matched writes its complementary pair or its measured zero,
neither of which the row draws, and both survive — which is what the ticket protects when it says
complementary and clashing *"already reach this card as reason sentences"*.

So the terms are **not** in the card's declared drawn set: that set is *terms the card renders a
value for*, and adding these two would take all four registers away to stop one of them repeating.
The condition lives beside the set instead, in `candidateFacts`, and it is stated over **the tags
the row actually drew** rather than over the term's own `matched` list — the row is capped at six,
so a match beyond the cap is a chip nobody drew, and a filter keyed on the term would delete the
only sentence saying it and leave the fact stated nought times. A card that draws no row filters
nothing, which is how the social and deck cards keep their `Both of you` line.

**The other two cards draw no tag row, and the reason is about those cards.** A tag row wants the
card's full width; both of them are **media-top**, so their content column *is* the card and their
rows are already the three in the table above. The competitive card earns the row because it is
the surface where *who somebody is* is the question — a game for fun asks whether two people are
free at the same time — and it can afford the trade the row costs, which is the `Both of you`
sentence. Adding a row to either of the others would spend that sentence on chips they have no
width for.

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
no distance row, so a survivor always exists. **The redraw does not touch that claim** — it
rests on the drawn set and on the card having no distance row, and #309 changed neither: the
panel states a Level and a Sport, and a Sport is not a `Term`.

**Nor does the record block, and the surviving set is genuinely one smaller now.** #312 put
`RELIABILITY` in the drawn set, so five terms survive the filter where six did — and the claim
still holds for its own two reasons, neither of which the block reaches: `DISTANCE` never stands
down, and this card has nowhere to render a distance. That is **confirmed in
`candidateCards.test.tsx` rather than by reading**, on a candidate whose only firing terms are the
drawn set plus `DISTANCE` and who carries no liveness reason to fall back to. On the **deck** card the line rests on exactly
four terms — `INTENT_ALIGNMENT`, `RELIABILITY`, `PLAYING_STYLE`, `SOCIAL_VIBE` — and **all four
are optional**, which is the property the claim rests on rather than the count. `RELIABILITY`
was in this sentence as a term that stood down *for everybody*, and it no longer does: it has a
provider ([ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md))
and it fires for anybody the platform has watched. What that changes is one word — a fourth term
can now survive the filter, so *nothing survives* is rarer on this card and is not impossible,
because a candidate with no record still stands it down as **their own** gap.

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

**`ReliabilityEvidence` `{score, strands[], floor_breached}`** — written **unreachable** and
**reached since**. It was `NoPlayerScoresExist` on day one (map Decision 3) and it is written
anyway *because* the vocabulary is closed, so that a code with no words is not how a term
arrives blank the day its provider lands. That day came
([ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)),
and the sentence below was already here to draw — **which is the whole of what writing it early
bought**. It stands down **per person** now rather than platform-wide: absent from a card is
a fact about that candidate, and the platform's own gap is the one thing that is stated once in
the sheet's footer.

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
> codes, which is exactly the shape [ADR-0021](../../adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
> licenses a client to compute."*

So the meta line becomes **`{km} km`**, with **`In your area · {km} km`** when the two codes
are equal. Nothing else. The day a gazetteer exists, `area_code_of` is the one function that
changes and this line gains a name without any other consumer moving.

**Both codes have to reach the card, and for a while only one did.** `area_code` crossed on
the player card and on the distance evidence, and both of those are the *candidate's* — so
the one sentence this section licenses could not fire for anybody
([#279](https://github.com/Raketa02/Raketa/issues/279)). The searcher's own is
`SearchEnvelope.my_area_code`, on the envelope beside the week the search ran on and recorded
with it: a read-back never recomputes, and the profile's area is what it is *now*, so a card
drawn from the profile would say *in your area* about an area the player has since left. A
search recorded before it was kept omits the field, and the clause is dropped rather than
answered — an empty code compares unequal to every real one and would quietly say *never*.

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
person and are two facts with **one tag**: the tag is bound to the admitting code.

**Which of the two forms that tag takes is per card, and #231's open decision #14 is reversed
on the competitive one** ([#309](https://github.com/Raketa02/Raketa/issues/309)). #14 replaced
the two-word tag with `INTEREST_LIFT`'s sentence — *a full sentence does not go where a
two-word tag went* — which was the right reading of the sentence it had been handed and the
wrong conclusion, because the two-word form was never gone: it is the twin's, and *two facts
with one tag* is exactly what licenses taking it. So the competitive card draws **`Wants to
play you` as a volt tag beside the handle**, bound to `INTEREST_LIFT` and worded by
`INTEREST_RECEIVED`; **the social card draws the same two-word tag, and the deck card draws
nothing** ([ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §4, §8 — the liker is unmarked on the deck, and the sentence under the name is
retired on both list cards in favour of the tag). A second tag joins it on the list cards,
**`You said yes`** — client-side, from the reader's own outgoing list, no code and no nudge.
Neither is a new field, and the twin's own sentence can still only reach a card as the reason
fallback — which the competitive card never takes (§5).

**The tag has a coral sibling, and the volt one replaces it**
([#310](https://github.com/Raketa02/Raketa/issues/310)). *Best match* is the client's own two
words for *the highest ✦ on this screen* — no code, because it is a fact about a **list** rather
than about a person, and which row wears it is
[`the-play-screens.md`](the-play-screens.md) §4.1's rule. It is *Best match* and not *Best fit*:
the sort chip beside it reads *Best fit*, and one screen saying the same two words for an
ordering and for a row would have a reader hunting for the connection. Where both would fall on
one card, the volt one wins, *because it's the stronger fact* — so a card that draws the coral
tag is one no admitting code fired on.

**The volt tag also carries a border, and the order of the two is the rule.** The lifted card
takes a green outline in `voltStroke`, bound to *the tag being drawn* rather than to
`inclusion_reason`: the tag is the word, the border is its second copy, and colour is never the
cue. That is `design-system.md` 5.1's **marked** card state, and it is the client's drawing —
nothing about it crosses the wire.

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

**Nothing draws any of the five, as of 2026-09-09.** Three of them had a row of their own
under the forecast card's names and two were deliberate silences; the row is gone. Read
underneath two side strengths, a signed gap, an evenness percentage and a face per seated
player, a sentence naming what the engine went looking for is a caption on an answer the
reader has already been given four views of — the same objection the two silences were for,
arriving for the other three. The **code** is unchanged, still served and still parsed; the
table above is what a client would write if it drew them again, and it stays for that.

## 12. The four prompts

*"Codes, never sentences… **Keep 15 km?** is one phrasing of `KEEP_THIS_RADIUS` in one
language, and a backend that shipped it would own the copy for every client that ever
exists."* Each rides on a search response
([#226](https://github.com/Raketa02/Raketa/issues/226)), so *"it never blocks"* is true by
construction.

| `Prompt` | Title | Body |
| --- | --- | --- |
| `KEEP_THESE_TIMES`, on a week with cells | `Keep these times?` | `{n} slots now · {was} on your profile. A plus is new, a dash is one you dropped.` |
| `KEEP_THESE_TIMES`, on a cleared week | `Keep these times?` | `Nothing ticked · {was} on your profile. The matcher skips a blank week rather than scoring it nought.` |
| `KEEP_THIS_RADIUS` | `Keep {radius_km} km?` | `You've widened to this three searches running. Make it your usual, or keep it to this one.` |
| `UPDATE_PLAY_INTENT` | `Your searches say something else` | `Your last five {sport} searches were {mode}. Your profile still says otherwise — want to change it?` |
| `REFRESH_YOUR_TIMES` | `Is this week still right?` | `The matcher reads this grid every time it looks for anybody — for you and for the people it puts in front of you. A grid that is three months old quietly ruins every match it touches, so it is worth keeping honest.` |

`REFRESH_YOUR_TIMES` keeps §F2 #9 **verbatim** — it is one of the ten strings that define the
voice, and this is the prompt it was written for.

**`KEEP_THESE_TIMES` has two bodies and one arm**
([#277](https://github.com/Raketa02/Raketa/issues/277)). The marks it names are
[6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid)'s diff
variant's — a **plus** for newly-on, a **dash** for newly-off — and never the colour they are
drawn in. The sentence they replace — *"Green rings are new, faded ones you dropped"* — named
the **colour as the mechanism**, which was Part 13's prohibition on the day it was written;
and once the diff variant replaced the volt ring and the 45% opacity with shapes, it was also
describing marks that are **not on the screen**, on every week rather than only a cleared
one.

The second body is the **cleared week**, made a legal value on the wire by
[#247](https://github.com/Raketa02/Raketa/issues/247). It has no *new* half — the whole grid
is the dropped one — and *"0 slots now"* would assert a **measured zero**, which is the one
reading [ADR-0102](../../adr/0102-silence-is-never-scored.md) refuses: a blank grid is
*absent*, never *never*. So it states what actually happens, with **the matcher as its
subject** — §F1 rule 6's shape, and `REFRESH_YOUR_TIMES`'s own. It is the only prompt body
that states a scoring rule, and it earns it, because the count it replaces was already
stating one and stating it wrongly.

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

### The two answers, and the third way of giving one of them

| `Prompt` | Yes | Not now | The sheet's close control |
| --- | --- | --- | --- |
| `KEEP_THESE_TIMES` | `Save it to my profile` | `Just for this search` | `Close without saving these times` |
| `KEEP_THIS_RADIUS` | `Make it my usual` | `Keep it to this one` | `Close without changing your radius` |
| `UPDATE_PLAY_INTENT` | `Update it` | `Just for this search` | `Close without changing your profile` |
| `REFRESH_YOUR_TIMES` | `Let me fix it now` | `Not now` | `Close without changing your week` |

Three of the four pairs were **already written down** and are reused rather than invented:
`SH.saveav` ships the first ([#237](https://github.com/Raketa02/Raketa/issues/237) §5), the
drift prompt's are `matchmaking-engine.md` §6.3's *Update it* and *Just for this search*, and
the radius pair is its own body's closing clause. Not one of them quotes a value, so they are
§1's **first** shape — a flat `Record` beside the switch that writes the sentences.

**A *yes* is a write through the route that owns the value**, and `REFRESH_YOUR_TIMES` is the
one that promises none, because it carries none. It is only ever the prompt on screen when the
week the search ran on **is** the profile's — an edited week raises `KEEP_THESE_TIMES`, which
sorts first — and re-sending an unchanged week lands the same state and records nothing. So its
*yes* hands the player back to the grid on the screen behind the sheet, and the label says so
rather than claiming a save that would not happen
([#275](https://github.com/Raketa02/Raketa/issues/275)).

**Dismissal is a decline**, so the close control is a third way of pressing *not now* and is
named for what closing leaves alone rather than for the act — never *Close*, which says nothing
out of visual context, and never the decline button's own words, which would offer a listener
the same choice twice. §20.6 puts focus on the title on the way in, which is what makes the
question heard before either answer is offered.

## 13. A challenge's standing — seven codes, and an ended row names who

#221: *"**Challenge sent** and **Challenge for you** are one standing read from two sides, not
two states."* So the code is one and the sentence is two, keyed by `(standing, side)`, with
side derived from whether the reader holds the organiser seat.

> **Amended twice by [Closing the loop](https://github.com/Raketa02/Raketa/issues/321), and the
> five sentences already built are untouched by both.** `LINE_UP_INCOMPLETE` now counts **open
> seats** ([ADR-0150](../../adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)),
> `WITHDRAWN` is a sixth code
> ([ADR-0142](../../adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)),
> and the invitee column gains a third reading for somebody who has left. Rewriting the rest was
> ruled out of scope by [#331](https://github.com/Raketa02/Raketa/issues/331) and none of it moves.

> **And once more by [#389](https://github.com/Raketa02/Raketa/issues/389), which found that third
> reading owed one row up too.** The invitee's `AWAITING_ANSWERS` sentence assumed the reader had
> not answered, and in doubles one has — §13.2. Every sentence above is untouched by that as well,
> and #331's ruling still binds anything §13.2 does not name.

> **And a seventh code, with the ended rows re-keyed, by
> [ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
> (2026-09-15).** A court that has been a game ends with its game and reads **`CALLED_OFF`**; every
> ending carries **`ended_by`**, the player whose act ended it; and an ended row's sentence is keyed
> by that player's own seat rather than by side — the second table. The four live rows and
> `WITHDRAWN`'s two sentences are untouched; `{name}` in the `DECLINED` and `LAPSED` rows now names
> `ended_by` rather than the first decline in court order.

| Standing | To the organiser | To an invitee |
| --- | --- | --- |
| `AWAITING_ANSWERS` | `Waiting on {n} answers` | `They're waiting on you` |
| `ON` | `Everybody's in` | `You're in — everybody's in` |
| `LINE_UP_INCOMPLETE` | `{n} in, {m} seats open — the chat is already open` | `You're in. {m} seats open, and the chat is already open` |
| `DECLINED` | `{name} said no — that seat is open again` — or `{name} left — nobody else is coming`, by `ended_by`'s seat (below) | `You said no` |
| `LAPSED` | `{name}'s day ran out — that seat is open again` | `Your day ran out` |
| **`WITHDRAWN`** | `You withdrew this` | `{name} withdrew this — that court is closed` |
| **`CALLED_OFF`** | keyed by `ended_by`'s seat and not by side — the table below | the same |

**The ended rows, keyed by the standing and by `ended_by`'s own seat**
([ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§7). One rule for every ending on the shelf: the sentence names the person whose act ended the
court, `{name}` is that person's whole name (§15), and **the face on the row is that person's**
(`the-loop-screens.md` §1.1).

| Standing · `ended_by`'s seat | The row |
| --- | --- |
| `CALLED_OFF` · `LEFT` | `{name} left` |
| `CALLED_OFF` · still seated, another player | `{name} called the game off` |
| `CALLED_OFF` · still seated, the reader | `You called the game off` |
| `DECLINED` · `LEFT` | `{name} left — nobody else is coming` |
| `DECLINED` · `DECLINED` | `{name} said no — that seat is open again` — as above, now naming `ended_by` |
| `LAPSED` | `{name}'s day ran out — that seat is open again` — as above, now naming `ended_by` |

**The sentence is always true of the person it names.** It is keyed by `ended_by`'s own seat, so
a seat that `LEFT` reads *left* and a seat that `DECLINED` reads *said no*, whichever the server's
bound picked between two; a lapsed seat is never named on a `DECLINED` court, because a no
outranks silence in the fold that picks the name. **`{name} left — nobody else is coming`** is the
row the 2026-09-14 fix dropped rather than draw as *? said no* — a court somebody joined and walked
out of, leaving the reader alone with nobody deciding — and it now keeps its day like every ending.
**A reader whose own act ended it still leaves the inbox at once** — their own *no*, their own
*left*, their own removal — and a stale route reads `You said no` / `You left` / `You withdrew this`
as before; **the presser's own row stays its day**, reading `You called the game off`.

**`CALLED_OFF` is the game's fourth end, seen from the court** — the departure that leaves one
player on a game, or *Call it off* — and it is the one word for that ending everywhere: the tag on
the row (`the-loop-screens.md` §1.2), the card, the button and its sheet (§22.9), the screen's
headings. ***Cancel* appears nowhere.**

**`LINE_UP_INCOMPLETE` carries #221's constraint in its words.** *"The chat opens on the first
acceptance and grows with each one"*, which makes it **not a waiting room** — and its obvious
phrasing (*"waiting for the rest"*) is the one that would be false.

**And it counts seats, because it can never count answers.** The row shipped reading
*"{n} in, {m} still to answer"* off an `awaiting` count, and `standing_of` returns
`AWAITING_ANSWERS` if **any** seat is awaiting — so at the rung that yields
`LINE_UP_INCOMPLETE` nothing is, `{m}` is structurally zero, and the built line reads *"2 in, 0
still to answer."* `StandingFacts` takes `open` instead. **A field that could only ever be zero
is what let the sentence be wrong**, and #221's constraint is untouched: the phrasing that would
be false is still *waiting for the rest*.

**`LAPSED` is not a decline** and the words hold that apart: a day ran out, nobody said no.
The `answers challenges` strand needs the denominator, so a lapse that reads as a refusal in
copy is a fact quietly restated as a different one.

**`WITHDRAWN` is neither**, and its word is the documentation's own. Not *cancel* or *call off*,
which is the game's and is `CALLED_OFF`'s (ADR-0172 §1 — *Call it off* on a court that has been a
game records that standing, and `WITHDRAWN` is *Remove the challenge*'s alone); not *stand down*,
which the root [`CONTEXT.md`](../../../CONTEXT.md) owns platform-wide for a term that cannot be
evaluated. **The invitee who never answered is told the same as the one who accepted** —
separating them would say who else was on the court.

### 13.1 The third reading — an invitee who has left a challenge that has not

**Two sentences, added by [#339](https://github.com/Raketa02/Raketa/issues/339), because the two
above assume the invitee is in and one reader is not.**

A padel four: the organiser invites three, one declines, two accept. No seat is awaiting, so the
standing is `LINE_UP_INCOMPLETE` — and the player who declined still holds a seat, so
`GET /challenges` still returns it. Keyed on `(standing, side)` alone they read *"You're in. {m}
seats open, and the chat is already open"*, which is false in both clauses.

> **The invitee sentence reads the reader's own seat, not only their side.**

| The reader's own seat | The sentence |
| --- | --- |
| `ACCEPTED` | `You're in. {m} seats open, and the chat is already open` |
| `DECLINED` | `You said no. They are still filling the court.` |
| `LAPSED` | `Your day ran out. They are still filling the court.` |
| `LEFT` | `You left. They are still filling the court.` — the third way out, since [ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md): they left the game this court had become. §13.2's row reads `You left. They are still waiting on answers.` |

**The row is not filtered away instead**, because `GET /challenges` is *every challenge you hold a
seat in* and a departed seat is still a seat — which is the reason the scenario above already gives.
A row that vanished would take the only available explanation with it.

**And not because the pair rule still binds them** ([#393](https://github.com/Raketa02/Raketa/issues/393)).
It does not: the pair **releases the moment a seat leaves**, so a departed invitee is reachable again
at once, in any sport, by anybody. What keeps them out of **this** challenge is `already_asked_at`
feeding `NobodyIsAskedTwice`, which is per aggregate and is not the pair rule.

**Neither sentence says how many are in**, and that is deliberate: they have left, so who is on
that court is no longer theirs to be told. `{m}` is the count of **open seats**, which is a fact
about the arrangement rather than about anybody in it.

### 13.2 The same reading, one row up — an invitee who has answered a challenge still awaiting others

**Three sentences, added by [#389](https://github.com/Raketa02/Raketa/issues/389), because the
invitee sentence above assumes the reader has not answered and in doubles one has.**

A padel four: the organiser invites three, **you accept**, two have not answered. `standing_of`
returns `AWAITING_ANSWERS` while **any** seat is awaiting — *"Awaiting outranks line-up incomplete
deliberately"* — so the standing is right, the side is right, and *"They're waiting on you"* is
about somebody who has already spoken. A reader who **declined** reaches it too: their seat is open
and therefore not live, while another invitee's awaiting seat holds the standing, and
`GET /challenges` returns every challenge you hold a seat in. **Singles cannot reach any of it** —
the only invitee accepting takes the challenge to `ON`.

**The lapsed reading waits on the sweep, and that is stated rather than hidden.** A seat past its
window *"reads as lapsed whether or not anything has swept it"* for the **standing**, but the wire
sends the seat's `answer` as it is stored — so between the deadline and the sweep the reader's own
answer is still absent, and they are drawn the unanswered sentence. §13.1 has the identical gap for
the identical reason, so the two are consistent; what closes it is the sweep, and neither section
re-derives a lapse on the client. **The client does not read the clock** — that is
[`challenge.ts`](../../../frontend_player/src/features/challenges/domain/challenge.ts)'s standing
refusal, and a sentence is not a good enough reason to break it.

> **The invitee sentence reads the reader's own seat, not only their side** — §13.1's rule, owed on
> the row above it.

| The reader's own seat | The sentence |
| --- | --- |
| *no answer yet* | `They're waiting on you` — unchanged, and the one case it was always true of |
| `ACCEPTED` | `You're in. Waiting on {n} answers, and the chat is already open` |
| `DECLINED` | `You said no. They are still waiting on answers.` |
| `LAPSED` | `Your day ran out. They are still waiting on answers.` |

**The first clause is the reader's own fact and the tail is the challenge's.** That is why
`You said no.` and `Your day ran out.` are §13's own words rather than new ones, and why only the
tail differs from §13.1's: what changed between the two standings is not what the reader did, it is
what is still happening without them. *They are still filling the court* would be false here —
nobody is filling anything while an answer is owed.

**`{n}` is the organiser's own sentence, embedded.** The accepted reader's line is §13's
`LINE_UP_INCOMPLETE` invitee shape with one clause swapped, and the clause is `Waiting on {n}
answers` verbatim — read from the same `awaiting` count the organiser's row prints, so **the two
sides cannot disagree about the number**.

**The chat clause is #221's refusal, not decoration.** The room opens on the first acceptance, so an
invitee who has accepted always has one — theirs opened it or an earlier one did. An accepted reader
told only that somebody is being waited on is exactly the waiting room #221 says this is not.

**Neither of the two who have left hears a count**, for §13.1's reason unchanged. A count of
outstanding answers is not a count of who is in, and it still tells somebody off the court what
shape it is in.

**The organiser has no split**, and that is not an omission: their seat is accepted from birth, so
`Waiting on {n} answers` covers every case they can reach. The asymmetry is the whole of why the
invitee needed a third reading and they did not.

**Seven, not twenty.** The twenty card states are *"a presentation vocabulary spanning money,
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
| **Your own seat**, on your own row | `{duration} left to answer` — added by [#339](https://github.com/Raketa02/Raketa/issues/339) |

**The fourth is new because the screen that needs it is.** `{name} · {duration} left` names
somebody else and is the **organiser's** sentence, listing each seat and its own clock; until this
map there was no surface that showed you *your* challenge, so nobody had written the sentence for
your own seat. Naming yourself on your own row would be the app telling you who you are. It is the
Chats row's line whenever the challenge is yours to answer and unanswered
([`the-loop-screens.md`](../the-loop/the-loop-screens.md) §1.2) — the badge's own predicate, reused,
so the badge, the sort and the line cannot disagree.

**All four are folded against the response's `read_at` and never against this phone's clock**, and
none of them gates a control: the buttons are drawn from the standing the platform sent
([#327](https://github.com/Raketa02/Raketa/issues/327)). **Draw the clock, never obey it.**

**The window moved from 24 hours to 48 and not one string changed**, which is the payoff of this
section's own title. [ADR-0151](../../adr/0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md)
supplied the reasoning the number never had — *a window must exceed the gap between app opens, not
equal it* — and because the number is spelled in exactly one file and no sentence quotes it, the
deck was not touched. The organiser's `Waiting on {n} answers` is unchanged for the same reason:
there was never a number in it.

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

A player has a **Name** — free text, **2–64 characters**, spaces allowed, never unique — and a
**Nickname**, a unique handle that is drawn as `@nickname` under the name on the You tab and on
the record screen and is **said nowhere**
([ADR-0171](../../adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
**The name is what every sentence says**, and ADR-0107 §4's rule reads on it: *every sentence
naming somebody uses the whole name or names nobody — the prototype's `split(' ')[0]` has nothing
behind it here, and inventing a first name is the product addressing a person by a name they
never gave it.* A name the player typed with a space in it is a name they gave; a first name cut
out of it by a sentence is not.

> **One `playerName()`: the name, whole, and `You` for yourself.** Used by §B10's
> head-to-head row, §B16's side-name formatter, §B17's `SH.propose`, and **all eight of
> §F3's toasts that name somebody.** No sentence, row, card, sheet, toast, seat label or spoken
> name carries the nickname.

**The result screens join that list, and they name a person only where a person acted**
([ADR-0141](../../adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)). A games seat
carries a name and nothing else about its occupant, so the row's eyebrow says *who you
played* — the fact that tells two padel games in a week apart, where a duration cannot — and two
sentences name somebody: *{name} put a score up* and *{name} agreed with your score*. **The two
columns of a score stay sides.** A score is a **side's** claim, capped one per side and
answerable by either of the two who played it, so a column headed with a name would charge a
doubles score to one of them and a listener reading a set cell by cell would hear the wrong
person's six.

**A seat label may truncate visually; a sentence may not, and a spoken name never does.**
ADR-0107's rule is against *inventing* a familiar form — a visual truncation invents nothing,
and the accessible name carries the whole name, which is where the rule actually bites. A list
truncates by dropping whole names (*Laia Quintana +2*), never by shortening one; where a box draws
the **stem** (ADR-0157) it is cut at the name's first break — a dot or a space — so *Diego
Fabregat* draws *Diego* there; what a box does past that, its own ellipsis, is that box's
business. **The two initials over a generated poster are the one derived form** —
[ADR-0167](../../adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md) §3's
exception, cut from the name at the same break (*Ania Kowalska* → `AK`), its fence unchanged.

> **Elsewhere in this file, *handle* is the word of the day the section was written**, and names
> what this section now calls the name — a `tomek.p` in an example is a seeded handle from before
> ADR-0171. Every rule those sections cite is this one, and none of them is changed by the word.

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

`MOST_RELIABLE` is reachable since [#306](https://github.com/Raketa02/Raketa/issues/306): it
reads the published Player Score the card now carries, and is offered on a search whose
candidates have one. `EVENEST` reads `would_be_forecast`, which nothing has ever written, so it
keeps a word and no ordering — the table stays exhaustive by type.

**`GameResult`** — the run of form on a card. The field crossed with
[#306](https://github.com/Raketa02/Raketa/issues/306) and nothing drew it;
[#312](https://github.com/Raketa02/Raketa/issues/312) drew it, and **neither code has a sentence
of its own — on purpose.**

| | |
| --- | --- |
| `WIN` | *no sentence: a square in `ink`, and one share of §20.3's count* |
| `LOSS` | *no sentence: a square in `muted`, and one share of the same count* |

**The row is drawn as five marks and spoken as one clause**, and both halves refuse the same
thing. On the drawing it is outcomes in order, oldest to newest, distinguished by a **lightness
step** and never by a word — a square carries no label, and both squares are drawn. To a listener the whole row is `{won} of the last
{n} won` (§20.3), because five clauses would read the row as a table and no clause at all would
leave Part 13's *never colour alone* failing in the register it was written for. **A per-code
sentence would be the thing both registers avoid**, so this table stays what it is: the codes
are exhaustive, and their words are the count they are counted into.

**Fewer than five is a real answer** and is never padded — three results are three squares, the
gap is the statement, and `{n}` is the run's **own** length rather than 5. **There is no date
beside any of them** — a moment here would be activity recency, which no card carries in any
shape (ADR-0106 §5).

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
- **A clash word for the two tag-term concerns** — surfaced by §20 and named there rather
  than invented.
- ~~**`KEEP_THESE_TIMES`'s colour-named body**~~ — settled by
  [#277](https://github.com/Raketa02/Raketa/issues/277) in §12.

**And four more, added with §22–§24 by [#339](https://github.com/Raketa02/Raketa/issues/339):**

- **How a hold ends.** §22.5 gives this app its first hold sentence and nothing else; there is no
  appeal surface in this build, and a sentence offering one would be a promise nobody made.
- **Anything a reply would say.** Replies are on the map's fog — a question about a *message's
  shape*, not about delivery, since ADR-0147 made every entry ride one sequence.
- **The unread mark inside a conversation.** Out of scope, and whatever it is called it is **not**
  `read_at` — that field is the fold instant and means the opposite.
- **Moderation and reporting.** §5.2 of the source names *a report opened*; nothing here opens one,
  so no code has a sentence.

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
repointed the long-press there when K-7 ruled the record sheets out. The competitive card is
**three elements**: the body, the *Why 78?* button, and the primary button. The other two cards
are **two**, because *Why 78?* is the body's press alone on them. The fit pill is never one of
them; it merges.

**The third element is #309's, and the body keeps its press rather than losing it.** The
designs draw *Why 78?* as a secondary button beside the primary action, which is the one control
on the card that used to be invisible. §20.1's rule is *one element per action*, and a body with
no action of its own would be an element that rule cannot account for — where a big target and a
small named one for the same act cost a listener one swipe. So the count changes and the rule
does not.

> **This section counts the elements the components declare, and on iOS the platform may hand a
> listener fewer.** A card body is a `Pressable`, `Pressable` is `accessible` by default, and an
> accessible view on iOS **groups its descendants** — so a button drawn *inside* the body is not
> separately focusable there however it is named. That is **older than #309**: the primary button
> has been drawn inside the card body on all three cards since they were built, and §20.3 has
> counted it as an element for as long as it has existed. #309 does not introduce it and does not
> fix it; what #309 changes is that the count is now three, so the discrepancy is worth stating
> rather than inheriting. Resolving it means deciding **where the body's press lives** — a body
> that keeps its action cannot contain the buttons, and a body that gives it up needs a press
> state [6.6](../../../frontend_player/docs/design-system.md#66-press-states) has not specified
> for a region inside a card. That is a design-system decision and a whole-feature change, so it
> is **booked here** the way §20.12 books its own gap, rather than settled in a card ticket.

**The card is spoken in a different order than it is drawn.** Identifying facts lead, the
argument follows. This is the one recorded divergence from visual order in the feature, and
it exists because §10 is titled *Why this person is on the list* — dropping the reason lines
to satisfy a word count would delete what the card is for.

**The competitive card has no argument to put last** (2026-09-09, §5a). Its reason and concern
sentences are gone from the drawing and therefore from this name: the divergence above is a
licence to reorder, never to say something the reader cannot see, so the card body's label
ends at the tags. Its `{n}` is a **whole number** for the same reason — the pill draws
`Math.round`, and a listener hearing *Fit 78,42131 out of 100* beside a reader seeing `✦ 78`
would be the two registers on two numbers. The social and deck cards keep every clause below.

| | |
| --- | --- |
| **Card body** | `button`. `{name}. Fit {n} out of 100. {level} · {band} · likely {low}–{high}. {mark}. {In your area · }{km} km. {record}. {stake}. {tags}. {reason}. {reason}. {reason}. {reason}. {concern}.` — the competitive card stops after `{tags}` |
| **_Why 78?_** | `button`. `Why {name} fits {n}` — the visible label is `Why {n}?`, and two cards on one screen can carry the same Fit, so this one names its subject for the reason the primary does. **Not** the sheet's own name (§20.6): that string is the answer's, and this is the question. |
| **Primary button** | `button`. `Add {name} to the court` · `Challenge {name}` — the visible label is *Add to the court* / *Challenge*, which announces identically on twenty cards. Naming the subject is [6.9](../../../frontend_player/docs/design-system.md#69-the-photo-tile-and-picker)'s remove control, whose label *"names which photo it removes"*. |

**The add's visible word is *Add to the court*, and choosing it was a copy decision.** #309's
designs offer three wordings of one action — *Add to the court*, *Add to the four*, *Add — this
is the match*. *Add to the four* is **wrong on a squash court**, where the drawing's own
coordinates give two seats; *Add — this is the match* is a **claim** the card is not making, and
the one sentence on the surface with no evidence under it. The destination is true at every seat
count and in both modes, so the visible word and the spoken name now differ by the name alone —
which is the whole of what naming the subject was for. The bare `Add` stood while the button
stood alone at the foot of the card, and stopped when *Why 78?* joined it: a bare verb beside a
second control is the one place the missing object is felt.

**`{record}` is the three record blocks, and `{stake}` is the two stake boxes**
([#312](https://github.com/Raketa02/Raketa/issues/312)). Both are the competitive card's alone,
and both sit with the identifying facts for the reason `{tags}` does: what the platform has
watched somebody do, and what a game against them would move, are the same register as their
Level, where *why this person* is the reasons'. They are drawn in that order and spoken in it —
§20.3's one divergence from visual order is about the **argument**, and none of these five
clauses is one.

| Block | Says |
| --- | --- |
| Player Score | `Player Score {n} out of 100` — the scale stated, because this is the **second** out-of-a-hundred figure on the card and the first is Fit |
| Last 5 | `{won} of the last {n} won` — **one clause, and `{n}` is the run's own length** |
| Counted | `{n} counted games` — through `counted()`, so no sentence hardcodes an `s` (§4, §19) |
| Win, counted | `Win, counted {±d}` |
| Lose, counted | `Lose, counted {±d}` |

**A hidden block says nothing**, which is nought to three record clauses and **two or none** for
the stake: the pair is symmetrical and the contract sends both or neither, where the three record
fields are three independent absences.

**The run of form is counted rather than read out**, and this is the one place a listener gets
something a reader does not. *Last 5* is five squares distinguished by **fill**, so five clauses
would read the row as a table — *won, won, lost, won, won* — and no clause at all would leave the
listener with nothing, which is Part 13's *never colour alone* failing in the register it was
written for. And the denominator is the **real** one: a run of three says *of the last 3*, because
fewer than five is a real answer and the gap is the honest statement — *of the last 5* over three
squares would pad in words exactly what the drawing refuses to pad in squares.

**The at-stake pair is absent in two ways that are not this file's**, and neither reaches the
label: the field is omitted in for fun, where a counted result is *meaningless* rather than
unavailable, and it is **refused on a doubles seat**, where *a win against one named person isn't
a thing that exists until the other three seats are known*. The second is a rule keyed off the
sport's seat count, and it is taken before the label is composed.

**`{tags}` is the Social tag row, and it is nought, one or two clauses**
([#311](https://github.com/Raketa02/Raketa/issues/311)). It sits after the identifying facts and
before the argument because that is where the row sits *in meaning* rather than where it sits on
the card: what somebody published about themselves is the same register as their level, and *why
this person* is the reasons'. Four rows produce four shapes:

| Row | Says |
| --- | --- |
| Compared, something matched | `Tags you share: {a}, {b}` · `Their other tags: {c}` — either clause omitted when empty |
| Compared, nothing matched | `No tags in common` |
| Not compared | `Their tags: {a}, {b}` |
| Nothing to draw | — |

**The shared ones are grouped rather than marked one by one.** The chip carries `· you too` on
its own words, because on the drawing the tint would otherwise be colour as the only cue; the
spoken name gathers them under one clause instead, because a listener hearing *you too* six times
is being read a table. And the clause takes `socialTagName` and never `socialTagLabel`: prose does
not carry glyphs (§6.2), so what is drawn as `🏆 Plays to win · you too` is heard as *Plays to
win* inside *Tags you share*.

**This is the answer to the objection that kept tags off a card at all, not an exception to it.**
`CandidateCardSocial` refused them because drawing them *"would put content on the card that the
label cannot announce"* — the half of [Part 13](../../../frontend_player/docs/design-system.md#part-13--accessibility)
a hidden decoration is allowed and a fact is not. The content **can** be announced, so it is, and
the rule that ships with the row is **do not draw a tag the label does not speak**. The social and
deck cards still draw none, for a reason about those cards rather than about tags: see §5.

**`{mark}` is the photo panel's ON COURT mark, and it is one clause or none**
([#313](https://github.com/Raketa02/Raketa/issues/313)). It sits straight after the level row
because the two are the **panel's** pair — it prints a Level hugely and the mark above it, and a
listener meets that object before the argument over it.

| Verdict | Says |
| --- | --- |
| Checked and passed | `Photo checked: on court` |
| Checked and flagged | — |
| Never checked | — |
| No photograph — the generated poster | — |

**The last three are one answer and that is the point.** A card must not tell one player that
another player's photograph was doubted: that is a moderation outcome about a third party, and
[ADR-0138](../../adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)
publishes **only the positive**. The absence is where every other answer meets, and the spoken
register is where a difference would be easiest to leak — so there is no *not checked* sentence
and no *we could not see a court*, which is the uploader's copy and belongs to the person who
chose the photograph.

**It leads with the noun, and the drawing does not.** Two words over somebody's picture are
plainly about the picture; a clause in a run of sentences is not, and *on court* arriving
between a Level and a forecast is one comma away from **activity recency** — the thing
`player_card` refuses at every granularity, *"not a timestamp, not active today, not a green
dot"*. So what is drawn is `ON COURT` and what is said is `Photo checked: on court`.

**There is no number in either register, and there never will be.** ADR-0133's clause survives
ADR-0138 untouched: the confidence never crosses on any route, so there is nothing to print and
nothing to derive one from — *we are 38% sure this is a court* is a figure a player can do
nothing with.

**Two things the competitive card draws and does not say.** The photo panel prints a **Level**,
which reaches the name already as the first figure of `{level}` — printed twice and said once
(§10). It also prints the **Sport**, which does not reach the name at all: it is the *search's*
sport, identical on every row, and the screen's own eyebrow has said it once already. Twenty
rows each opening with *Tennis* is the noise this fixed order exists to prevent. The mark is
what separates them: it is true of one player and not of the next, so it is a fact rather than a
constant and it takes a clause.

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
| **Balance bar** | `image`. §B9's balance word and its figure — the word is the point, since the bar is a colour |
| **Seated name, on the forecast card** | `button`. `{side}, {name}, why fit {n}` — the way in to `SH.whyfit` for somebody already seated |

`{side}` is *your side* / *their side*, and in doubles the partner seat says *your side, your
partner*.

**The swap toggle is gone, and its row with it** (2026-09-09). It was `switch`. `Swap players`,
`checked` — the one control in this contract that carried `checked` on a mode. A tap on a seat
meant *replace this player* with it off and *trade these two* with it on; the forecast card's
names row became a **face per seated player**, which took the first meaning off the court, so
the seat kept one and there was no mode left to announce. What a seat does is now said once,
above the court, as ordinary drawn text the screen owns — *not* a name on any element here,
because no element on this court has an action that word describes.

**Neither guard toast survived it.** *That seat is yours — turn on Swap players to change
sides* and *{name} already accepted — they keep their place* both refused a **replacement**,
and a tap replaces nobody now. §21's two sentences are unaffected: they are about a line-up
going out of date, not about a tap.

**The holding ring is struck rather than announced**
([#278](https://github.com/Raketa02/Raketa/issues/278)). The sentence that stood here gave the
430 ms press feedback no announcement *"on a channel this listener is not using"*, which was an
inventory of the prototype and not a decision: the ring came in beside the two record sheets
K-7 removed, and its gesture went with them. What replaces it is
[6.6](../../../frontend_player/docs/design-system.md#66-press-states)'s own rule — **one
channel per state** — applied where the seat already answers it. A seat dims to `.7` on
press-in, so a finger being down is confirmed; a ring would be the second channel on the state
that already has one, which is the argument the ⚡Play disc was refused a dim under. The court
earns no press-state row, 6.6's avatar *peek* row is left alone because it describes a
different interaction, and there is no `motion.hold` entry, because how long a finger is held
is not *how long a state is shown* and the two do not belong under one word.

### 20.4.1 A seat's hold, and the route that does not need one

A seated player's Fit had no explanation anywhere in the product. The pool is the one surface
that explains a person and it **removes** everybody already on the court, so the gap was total
rather than awkward — and ⚡ *Let the engine fill the seats* is what makes it matter, because
that court is four people the searcher never chose and never saw a card for.

> **The forecast card's names row is the route, and a hold on the seat is a shortcut to the
> same sheet.**

The names row already prints every seated handle in full, one per line, split by side — it is
why §5 lets a 46pt seat cut a name to four characters — and it is present whenever a seat is
filled on both sides, which a ⚡-built court always is. So the route is a list of names, which
is the most navigable thing a listener meets, and it costs no new element. **The side headings
hide** once the names are buttons: each one names its own side, exactly as the court's caption
and side labels hide because each seat names its own (7.12).

**A hold may never be the only way to reach anything.** There is no long-press gesture in the
accessibility API, so a hold is a *fallback* — it duplicates a route and never carries one. The
deck's is the app's only other, and this is the rule that keeps it honest rather than a
precedent that spreads.

**Only a seat holding another player whose row still exists is a way in.** No route serves a
searcher their own candidate row, so *why fit* about yourself is not a thing; an empty seat has
no Fit and is already explained twice, by §11's sentence beneath the seats and by its own
spoken name; and a withheld row carries one field and no card, so there is no breakdown left to
draw. A name is a button where there is something behind it and plain text where there is not —
never a button that opens an apology.

**The hold does nothing, and says nothing.** A tap on a seat is *select* then *trade*, so a
hold on one mid-trade is most likely a slow tap, and answering hesitation with a modal punishes
the one two-step interaction on the screen. No sentence is owed because nothing advertises the
gesture — the same reason the clear badge draws no refusal, *"the × a player cannot use is
never on screen to press."* The names row is unaffected. *(This paragraph said "while the swap
toggle is on" until 2026-09-09, when the toggle went and select-then-trade stopped being one
mode of two.)*

**The 9,5pt seat label does not earn `allowFontScaling={false}`.** Part 13 permits the escape
only *"inside the level bar's drawn geometry"*, and §15 already ruled the court's case the
other way: *"a seat label may truncate visually; a sentence may not, and a spoken name never
does."* The visible label scales and truncates, the spoken one is whole, and nothing is
invented. **This also settles [#240](https://github.com/Raketa02/Raketa/issues/240)'s
truncation question**, which is recorded there rather than held by both.

### 20.5 The deck

> **Rewritten 2026-09-14 by [ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) §3.** The deck card is its own card now — the mock's, full
> bleed, dark wash, three round buttons and a drag — and this section's *two buttons* and *§E2
> records the two buttons as what exists today* are superseded by name. Its other half stands
> and is the rule the swipe ships under.

| | |
| --- | --- |
| **✕ Not today** | `button`. `Not today, {name}` |
| **i Details** | `button`. `{name}'s record` — opens the player record sheet; so does a long-press on the card |
| **🎾 Let's play** | `button`. `Let's play, {name}` — the 🎾 hidden, per §E6: *"otherwise it announces as 'tennis ball let's play'"* |
| **The stamps** | not elements: `LET'S PLAY` and `NOT TODAY` are drawn, never spoken; the spoken result of the answer is |

**When a card leaves, two things happen and both are deliberate.** §E3's first finding is that
focus is destroyed on every render and nothing restores it, so today a listener is dropped at
the root with no idea what happened. The toast announces the act; an explicit
`setAccessibilityFocus` moves focus to the incoming card's body. #228 §12 made both actions
optimistic, so the next card is already there to receive it.

**The swipe shipped, and it is never the only path.** VoiceOver and TalkBack consume the drag
before the card sees it, so a swipe-only deck is one a listener cannot answer. The three
buttons are the accessible path and are never removed; the test that pinned *no gesture
dependency* now pins *the buttons remain*.

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

**One editor cell can carry a suffix, and it is a fact rather than a state.** A times rung
adds one slot to the searcher's own grid for one search, and *Find a game* marks that cell
with a plus ([#283](https://github.com/Raketa02/Raketa/issues/283)). A plus is not readable,
so the suffix is the whole of what a listener gets — and it is **after** the cell's ordinary
name, never instead of it, because the square is still Thursday evening and `checked` still
says what the *week* holds rather than what the search did.

| | |
| --- | --- |
| **Editor cell, marked** | Still a `checkbox`, still unchecked. `{Day} {part}, added for this search` |

The suffix is the diff grid's *", newly added"* said the other way round, because it is a
different claim: that one is the player's own week against their profile, this one is a cell
the **engine** added to one search. The sentence under the grid explains the mark and
**names no cell** — `takenRungLine`'s own rule, since the control that offered the widening
says *look outside your week* rather than naming a Saturday morning.

**`SH.saveav`'s diff grid is a different control with a third fact.** Newly-on draws a
**plus** in `volt` on `ink` and newly-off a **dash** in `muted` — shapes from the tick's own
family, which is
[6.8](../../../frontend_player/docs/design-system.md#68-the-availability-grid)'s diff variant
replacing the volt ring and the 45% opacity the prototype drew. Colour is a second signal on
every one of them and the mechanism of none.

| | |
| --- | --- |
| **Diff cell** | Not interactive — a `span` already. `{Day} {part}` · `{Day} {part}, newly added` · `{Day} {part}, dropped` |

§12's body names those same two marks, so the sentence a reader is given and the suffixes a
listener is given describe one drawing rather than two
([#277](https://github.com/Raketa02/Raketa/issues/277)).

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

**One gap, named rather than invented:**

- **A clash word for the two tag-term concerns.** §7's `PLAYING_STYLE` and `SOCIAL_VIBE`
  concerns render `{a} against {b}` and read as neutral description. §7 says why they are
  different — *"a clash is a graded claim, and the engine is the only thing entitled to make
  it"* — and the word belongs beside those sentences, not in a label.

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

**The lint rule's scope widens with §24**, and it is the one gate here that is scoped by folder
rather than by type: `features/challenges/`, `features/conversations/` and `features/plans/` join
`features/play/`. A rule that watched one feature while three more drew controls would be the
guardrail that silently stops matching, which this repo already holds is worse than none.

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
| the open-challenge refusal, **with no name to be had** | `Two people on this court already have a game between them.` | The row this table was missing — see below. |

**The named sentence assumed a name is always found, and it is not.** The pair rule binds
**every** pair on the court, so the open challenge in the way can be between two *invitees* — a
game that is theirs, on a list the organiser has no right to read. And the name arrives a round
trip after the refusal does, so there is a moment where the refusal is true and the list has not
answered. Both reach the fourth sentence, and they are **deliberately not told apart**: the
player can act on neither, and explaining *why* there is no name would publish who is missing
from whose list. The named sentence **replaces** it when the list names somebody — a general
statement becoming a specific one, which is the same shape the row above already has, where
`line_up_no_longer_sendable` stands while the read-back is in flight and the seats gain their
marks when it lands. Added by [#274](https://github.com/Raketa02/Raketa/issues/274).

**The court's own mark is the same sentence, per seat.** A refused send is not the only way a
seated player goes out of date: reading the origin search back marks the seats its withheld rows
identify, and that mark is a **set difference** the client derives — a withheld row carries no
id, so there is nothing else to derive it from. The seat is **marked, never emptied**, the
marked player **stays in the forecast**, and the line states the fact and never the cause:

> `Something's changed — they can't be invited now`

It is written once, in `features/play/components/courtPresentation.ts`, in the same register and
under the same ceiling as the row above it — four gates reach one sentence, and naming which
fired would tell a searcher that a particular person blocked them or changed a safety setting.
Settled by [#239](https://github.com/Raketa02/Raketa/issues/239) §8.

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

---

## 22. The loop's own sentences

Decided by [Write the screen specs](https://github.com/Raketa02/Raketa/issues/339) on the map
[Closing the loop](https://github.com/Raketa02/Raketa/issues/321). The surfaces are
[`the-loop-screens.md`](../the-loop/the-loop-screens.md); the sentences are here, because this file
is the app's one copy deck and §1's mechanism is the only one there is.

**Four features own copy now, not one.** §1 says *"feature-local `*Presentation.ts` modules inside
the Play feature, one per **vocabulary owner** rather than per screen"* — and the rule is the
**vocabulary owner**, not the feature. So `challengePresentation.ts` keeps §13, §14 and §21;
`conversationPresentation.ts` takes §23; `planPresentation.ts` takes §22.2 and §22.4; and the
tab's own three lines sit with the shell. **Nothing below is a template inlined in a component.**

**Most of this section is short and that is the point.** Every sentence the previous map already
wrote and tested is **cited rather than reproduced**, and the ones that had a home elsewhere stayed
there: [#331](https://github.com/Raketa02/Raketa/issues/331) ruled rewriting the challenge copy out
of scope, and a session that opens by rewriting §13 is rewriting solved work.

### 22.1 The Chats tab

**The panel states the limit that makes this a sports app**, and both of the design's promises are
dropped: *"when you count yourself into something tonight"* is Around, which this build does not
have, and *"inside a game or a plan"* is wrong in the other direction, because a conversation opens
on the **first acceptance**, before there is a game at all.

> **Chat exists only where you have agreed to play**
> A conversation opens the moment somebody accepts — theirs or yours. There is no way to message a
> stranger, and that line is what keeps this a sports app.

**The two section headings carry no count**: `CHALLENGES` and `CONVERSATIONS`. The badge is the
only number on the screen ([#326](https://github.com/Raketa02/Raketa/issues/326) §6), and the
section widened to hold a challenge you **sent**, which is what broke the design's
`CHALLENGES FOR YOU · 1`.

**Neither empty state may assert that nothing is happening** — Now's standing refusal, inherited,
because a send lands here now. Both are one line, present-tense, and point at the act:

| Section | Empty |
| --- | --- |
| `CHALLENGES` | `Challenges you send and challenges sent to you land here.` |
| `CONVERSATIONS` | `The moment somebody accepts, the two of you can talk here.` |

**`PLACEHOLDER_COPY.chats` dies with them**, and `shellCopy.test.ts`'s *never says nothing is
happening* **moves with the copy rather than being deleted**.

### 22.2 The plan

**The panel inverts.** ADR-0145 §6: it stops explaining an absence and names one, because a player
seeing *Zabłocie Sport · Saturday · 18:00* inside an app may reasonably assume the app did
something about it. It did not. Drawn on the game screen — since
[#414](https://github.com/Raketa02/Raketa/issues/414) **inside the plan card**, between the chips
and the lock — never in the conversation, where it would be permanent chrome above a composer.

> **Agreed between you — nothing is booked**
> Raketa does not hold courts. This is the note you are keeping between you: anybody here can
> change any of it, and everybody sees who changed what.

**The three slots are labelled by what they are**, in ADR-0144's order and never renumbered:

| Slot | Empty | Filled |
| --- | --- | --- |
| where | `Where` | the value, as typed |
| day | `Day` | the weekday |
| hour | `Hour` | the clock time |

**One refusal, and it is written copy rather than a disabled control**, because the day and the
hour are filled in either order and either one can be the second:

> `That moment has already passed — change the day or the hour.`

**It names both remedies** because the platform has no opinion about which is wrong, and it names
no value, because the sentence is true whichever pair produced it.

**There is a lock, and it is an act rather than a state**
([ADR-0155](../../adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
superseding ADR-0144's *There is no lock*). What it does is post **a system line into the room** —
§23's `{name} locked the plan` — and the backend sends `locked_at` and no adjective. **What the
card says about it is a counter and a control**
([#403](https://github.com/Raketa02/Raketa/issues/403)), and the count is derived from the three
fields and never sent:

| Element | Reads |
| --- | --- |
| The eyebrow | `The plan` — drawn uppercase, 3.3's section rule |
| The counter | `N of 3 set` · `Locked` once somebody has |
| The button | `Lock the plan` — **always**, and never with the reason appended |
| The button, busy | `Locking…` — its own word, because nothing is being saved |
| The count line, where the button will be | `N of M in — you can plan now, lock when everyone's here` — while the room has no game ([ADR-0164](../../adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md) §5, [#425](https://github.com/Raketa02/Raketa/issues/425)) |

**The reason is not on the label because it is on the counter.** The mock read *Lock it in · set
all three first*; the counter directly above already reads `1 of 3 set`, and a second sentence
would be the same count in a second spelling. **Once locked the button is gone**, not settled:
a second lock records nothing and answers `200`, so the counter's one word carries the whole
fact. The lock's own refusals have a sentence each by their code —
`Set all three before locking the plan.` for `the_plan_is_not_complete`, which the greyed button
makes unreachable and the card writes anyway; `Not everyone's here yet — lock the plan once they
are.` for `the_court_is_not_whole`, which the absent button makes unreachable from a room with no
game and which a game a seat has since been left open on can still meet, so it names what will
change rather than a control — and `plan_not_found` gets `This plan is not one you can change.`;
`plan_is_history` and `account_held` say what they already said for a slot.

**The count line is the note an absent control is owed.** While the room has no game the button
is not drawn — absent, never greyed, on #324's rule — and in its place one line, `2 of 4 in — you
can plan now, lock when everyone's here`: `N` the room's members, `M` the sport's seats, and both
halves of what the player needs — that they may plan now, and exactly what brings the button. It
becomes the button on the nudge that brings the game. `2 of 2 in` is a sentence this app never
draws: a singles room opens with its game.

**`locked by everybody` stays deleted.** It is a phrase the prototype's own data cannot support —
no assent is recorded per person, and a lock is one person saying *we are agreed*, not four. And
**there is no *unlock* to word**, because the lock is a thing that happened: any member may still
move a slot, the plan stays locked, and the move writes its own line.

**§5.3's guard (*a four cannot be locked by two*) has its sentences now** (ADR-0164 §5): there is
a plan before the line-up completes, so the state it refuses is reachable — and the card answers it
before the server has to, with the count line where the button would be. The refusal itself is a
code, `the_court_is_not_whole`, with the sentence above for the one court that can still meet it.

**And *"whoever books becomes the owner"* is deleted rather than rewritten.** Decision 3 said the
sentence would be rewritten; ADR-0144 found it has no moment left to be posted at. A sentence with
nothing to trigger it is not rewritten; it is gone.

**The game screen's eyebrow on the plan lead is the format and the kind** — and nothing else
([#414](https://github.com/Raketa02/Raketa/issues/414)):

| Format | Counted | Friendly |
| --- | --- | --- |
| two seats | `SINGLES · COUNTED` | `SINGLES · FRIENDLY` |
| four seats | `DOUBLES · COUNTED` | `DOUBLES · FRIENDLY` |

Stored as words (`Doubles · Counted`) and drawn uppercase by 3.3's rule, so a listener hears words
and not letters. **`COUNTED`, never `COMPETITIVE`** — that is a search's mode (§5.4 #8), and the
design's own forecast sentence says *a counted game*. A kind this build cannot read drops its
clause and the format stands. There is **no title under it**: the card names the people and the
plan names the day, so the handles and *arranged n ago* the other arms' eyebrow carries would be
the same facts twice. The words drawn on that screen are otherwise the decided ones — `The plan`,
`N of 3 set` · `Locked`, `Lock the plan`, the panel above, `Open the chat`, `We played`.

### 22.3 The withdraw — *Remove the challenge*

**The second irreversible act in this app that reaches other people, and it takes the shape the
first one already has** — `SH.propose`'s: a title naming the **moment** rather than the act, so the
act is named once by the control that carries it out, and a dismissal **named by what it does**.

**Since [ADR-0165](../../adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
§4 the withdraw is admitted exactly while nobody besides the organiser holds an accepted seat, and
its name is *Remove the challenge*** — met on the organiser's Chats row by the swipe §22.10's
conversation row answers with *Leave the game*, and on the challenge screen's arm where nobody has
joined (built by [#428](https://github.com/Raketa02/Raketa/issues/428)). One label on the revealed
control, on the screen's button and on the sheet's act, on `Send the challenge`'s precedent; the
visible label is the whole sentence, so it is the accessible name too.

| | |
| --- | --- |
| The revealed control, and the screen's button | `Remove the challenge` |
| Sheet title | `Before you remove it` |
| Body | `It disappears for the people you asked, too.` |
| The act | `Remove the challenge` |
| In flight | `Removing…`, on the sheet's act |
| Dismissal | `Keep it open` |

**One line, and it is the one ADR-0165 §6 asks for: it is gone for the invitees too** — the
consequence the organiser cannot see from their own list, and the one that reaches other people.
The word is *remove* because what the act does to a court nobody has joined is take a send back:
nothing anybody agreed to is lost, and the people asked simply stop being asked. It says nothing
about the pair rule releasing: that is a fact about what becomes possible afterwards, and a
confirmation is not the place to sell a consequence.

**A refusal is said on the sheet, in words**, on §22.10's line — a row has no fold for a re-read to
land on, so the sheet stays up and says why, and the lists are re-read once it is dismissed:

| Code | The sentence |
| --- | --- |
| `somebody_has_joined` | `Somebody's in now, so it's no longer yours to remove.` |
| `challenge_is_over` | `This one is already over.` — §22.10's own sentence, named once |
| anything else | `challengeErrorMessage`'s sentence; the route's other codes cannot reach a row drawn only to the organiser of a court nobody has joined |

**The row goes on the reply**: an own removal is the reader's own act in the sense an own *no* and
an own *left* are, so *You withdrew this* is never drawn on their row; to the people asked it is
§13's sixth sentence, kept its day as news.

**Retired with #428**: the withdraw's three body lines — *Everybody who accepted loses this court* /
*The conversation goes with it, and what people wrote is deleted* / *This cannot be undone* — its
title *Before you withdraw*, its act *Withdraw the challenge*, its control *Withdraw* with the
spoken name *Withdraw this challenge*, and *Withdrawing…*. They named a court people had joined,
which nobody ends for the others any more. ADR-0142's *destroyed, not delisted* still holds where a
room exists — the court the organiser is alone in again — and the second line moved with the
reading that needed it to §22.9, where the room is a game's.

**On a court that has been a game the same route is *Call it off*, and it is any player's**
([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), ADR-0165 §5): the game is
called off in the act, so the sheet names the game rather than the court. Its words are §22.9's,
settled with the ending's and the fill door's by [#419](https://github.com/Raketa02/Raketa/issues/419).

### 22.4 The quick chips

**A chip posts words and nothing else** (ADR-0144). One per unfilled slot, in slot order, plus
`On my way` when the agreed day is today.

| Condition | Chip |
| --- | --- |
| where unfilled | `Where shall we play?` |
| day unfilled | `Which day works?` |
| hour unfilled | `What time?` |
| the agreed day is today | `On my way` |

**Each chip asks the question its slot is about and names nothing.** The prototype's three are
hard-coded content — one weekday, one part of day and one fixture venue — and §5.1's part of day is
deleted; a chip naming Saturday is a chip that is wrong six days a week.

**The fallback is conditional, and that corrects [#329](https://github.com/Raketa02/Raketa/issues/329).**
That ticket collapsed the rule to *one chip per unfilled slot plus the unconditional fallback,
which never reaches the four-chip cap* — three unfilled slots plus an unconditional fallback is
**exactly** four, and *On my way* on a Monday for a Saturday game is nonsense besides. Conditional,
the maximum is three.

**The box under them says `Message about this game…` while it is empty**
([#402](https://github.com/Raketa02/Raketa/issues/402)). A hint and not a label: it goes the moment
somebody types, so the name a listener gets is `Message` (§24.4) and this is only what the empty
box says. *About this game* because the room is for the whole episode and nothing else
([`the-loop-screens.md`](../the-loop/the-loop-screens.md) §3).

### 22.5 Not live, held, and somebody is typing

**Three states the records made reachable and left as rules.** ADR-0147 §8 made *not live* honest —
*"a chat that is not live looks not-live"* — ADR-0148 §9 made *held* reachable inside a
conversation, and ADR-0156 built the typing indicator. Each gets one sentence; the first two sit in
a `Note` above the composer and the third sits in the stream (§24.6).

| State | The sentence |
| --- | --- |
| not live | `Not live — you can still send, and anything you missed arrives when it reconnects.` |
| held | `Your account is on hold. You can read here, but not write.` |
| typing, one | `{name} is typing…` |
| typing, more | `{name} and {name} are typing…` · `{n} people are typing…` |
| ended, they left | `{name} left — this chat has ended.` · `{name} and {name} left — this chat has ended.` |
| ended, alone | `Nobody else is coming — this chat has ended.` |
| ended, with a game | `This chat has ended.` |

**The ended sentences are the fourth state, and they stand where the composer stood** (added
2026-09-14, [#429](https://github.com/Raketa02/Raketa/issues/429); `the-loop-screens.md` §3.7). A
room without a game is over the instant its challenge is, so the *{name} left* line of §23 is
written into a room nobody can read; the screen that held the room says it instead, in §23's own
words, and **never** *that seat is open again* — the court is over. Who left is folded from the
members the room last read and ADR-0165 §3's ending rule, not read off a line: with others in the
room every other member left, alone the last seat deciding said no, and with a game the room says
only that it ended, because why is the game card's to say. A fact rather than a warning or a
refusal, so it is neither amber nor coral.

**The typing sentences name people and never a count of one**, because the client already holds the
handles the frame's `player_ids` point at and a name is what the room is about. Three or more
collapses to a count on §19's rule rather than growing a list — a room is four people at most and
the reader is never in the list, so the collapse is reached only in a doubles court where everybody
else is typing at once, and *3 people are typing…* is the honest end of that. **The whole handle,
never a first name** (ADR-0107), and the ellipsis is a character rather than three dots so a screen
reader does not read *dot dot dot*.

**It is never about you.** The server filters the reader out of their own room's frame, so there is
no *you are typing* sentence to write and no state in which one could be reached.

**Not live says two things because two things are true**, and only a sentence carries both: sends
are ordinary authenticated `POST`s and the channel is unidirectional by construction, so writing is
unaffected and only reading has stopped being live. A dot could not say that, and Part 13 refuses
colour as the only signal in any case.

**Held names the fact and promises nothing**, because there is no appeal surface in this build and
a sentence offering one would be a promise nobody made. It is ADR-0130's register: state the
class of problem, name nobody, grade nothing.

> **A finding, recorded rather than acted on: this app has never drawn a hold.** `account_held` is
> a backend refusal with no client sentence anywhere, and the two above are the first. Nothing says
> how a hold ends, because nothing in this build can end one.

**One note for every refused control on the screen**, not one per control. It is one fact about the
account, and saying it five times is the failure #326 §6 names about counts.

### 22.6 The card's slots, and the screen's checklist

**The four `AWAITING_ENTRY` rungs have no copy anywhere** and this is it. Since
[#413](https://github.com/Raketa02/Raketa/issues/413) the card says the plan as **three slot rows**
rather than as one sentence — [`the-loop-screens.md`](../the-loop/the-loop-screens.md) §4.2.

| Slot | Label | Settled | Not settled |
| --- | --- | --- | --- |
| where | `WHERE` | the place, without its court; spoken whole | `Not agreed yet` |
| day | `DAY` | `Sunday` `9 Aug` — the weekday whole and the date beside it; **`Today` `14 Sep` on the day of the game** ([ADR-0166](../../adr/0166-the-day-row-says-today-and-no-card-does.md)), judged against the games list's `read_at`, and only here — the chip in the room and the tag on the game screen keep the weekday. *Today* only: no *Tomorrow*, no *Yesterday* | `Not agreed yet` |
| hour | `TIME` | `19:00` | `Not agreed yet` |

**`TIME` is the card's word for the `hour` slot**, as the design draws it; the chip in the room
keeps `Hour`, because a chip names the value you are about to set and a card labels the value
that was. **`Not agreed yet` is drawn now, and capitalised as a sentence** — it was the chips'
spoken word only, and the spoken names read the same constant, so a chip still says exactly what
the card draws.

**The sport is a word, top right** — `PADEL`, and `PADEL · FRIENDLY` for the marked kind. Nothing
writes *singles* or *doubles*: the court says the format.

**One line survives under the slots**, so no card loses a fact it drew before the shell:

| Rung | Under the slots |
| --- | --- |
| **Planning** · **Game on** | nothing — the slots are the whole account |
| **Needs result** | `{duration} left` |
| everything that is not a rung | `gameStandingLine`'s sentence, cited |

**The gloss is retired.** `Still to agree: where` named only the next slot, which was what kept it
four words and handed the fuller account to the checklist below; the slots draw all three, and an
unfilled one under a dim bar says the same thing without prose.

**The checklist is three lines, capped, in one order**, on the game screen and never on the card:

| | Line |
| --- | --- |
| what is true now | `Everybody said yes.` |
| what is still to agree | `Still to agree: {list}.` · `Nothing is left to agree.` |
| what it moves | **cited, not written** — `worthLine`'s built and tested sentence |

**`{list}` is the unfilled slot names in slot order**, joined with commas and a final *and*:
`where and the hour`, `where, the day and the hour`. This is the one place the whole list is
printed as prose.

**The first line explains why the plan card is there at all** — a `LINE_UP_INCOMPLETE` challenge
has an open conversation and no plan — and it is the same three words for all four rungs, because
the rungs differ by the clock and not by the arrangement.

**The third line is the whole of what survives ADR-0143 §8's refusal**, and it is already shipped.

### 22.7 Now, and the two answers

**Now's empty state**, present-tense, saying what the tab **is** and pointing at the act:

> `Every game you arrange shows up here — what is agreed, what is today, and what still needs a
> score.`
> `⚡ Play finds you one.`

**`PLACEHOLDER_COPY.now` dies with it**, and the test moves rather than being deleted.

**The two answers on the challenge screen**, and neither names a state the act cannot produce:

| | |
| --- | --- |
| accept | `I'm in` |
| decline | `Not this time` |

**`I'm in` replaces the design's *Accept — game on*.** [#324](https://github.com/Raketa02/Raketa/issues/324)
and #329 redefined *Game on* as *the plan is complete and the day is ahead*; accepting arranges
nothing and draws ***Planning***, so the phrase is false the moment it is tapped. **`I'm in` is what
the standing says back** — *You're in — everybody's in*, *You're in. {m} seats open…* — so the
label and the confirmation are one sentence in two persons.

**`Not this time` is kept exactly as drawn**, on #221's own words.

**The three doors this map adds**, each carrying its act's verb and each navigating rather than
writing:

| Control | Where |
| --- | --- |
| `Open the chat` | the challenge screen, the game screen, and the Now card's bubble — **one act, one spelling**; on the card it is the spoken name of an icon-only door |
| `⚡ Fill the seats` | the challenge screen's `LINE_UP_INCOMPLETE` arm, and it is the builder's own label for the identical act |
| `Fill the seat` | the Now card's wide door on **Needs a player**, and the game screen's primary act on that arm — **the same act, singular** ([#419](https://github.com/Raketa02/Raketa/issues/419)): one per surface, because a challenge screen is about a court still being built with as many seats open as the send left, and this door is about a game that had every seat and lost one. Two seats may be open (#411 rule 3); the door still names the errand one seat at a time, as the tag does. The one door that runs something before it navigates — the fill mints a search — and it still reaches nobody. `theActsWords.ts`', because two features say it |
| `Finish the plan` · `Open` · `We played` · `Confirm the result` | the Now card's wide door, one per name — [`the-loop-screens.md`](../the-loop/the-loop-screens.md) §5.2. **`Finish the plan` is Planning's word for the same door Game on opens with `Open`** ([#413](https://github.com/Raketa02/Raketa/issues/413)): the destination is the same and the errand is not. *Finish* and not *Lock*, because the lock is an act with its own control on that screen (ADR-0155) |

**And one ending whose card has two buttons and no wide door**: **`Called off`** is the card's
word for `GameStanding.CALLED_OFF`
([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md)) — an ending like *Never
played*, and unlike it in one respect the card must not draw: nobody let a window close on it,
somebody ended it. **The card names nobody, and the screen behind it does** (amended 2026-09-15,
[ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§8; it read *It was called off — nobody is named* while `called_off_by` was on no wire): where a
live card has its wide door the card offers **`What happened?`**, opening the game screen, and
beside it a square button with the trash glyph, spoken **`Remove this card`**, that clears the
card from Now at once — §22.9 has the screen's headings and the trash's rule.

**Nothing offline gets a third sentence.** `does-not-resume` is the shared value, unchanged, and
the two values split on **resumption**; a third keyed to the act would break the only distinction
the function has. One amber note above a greyed pair, pre-emptive, exactly as `BuilderScreen`
already ships it.

### 22.8 Leaving a game, and the seat it leaves open

**The third irreversible act in this app that reaches other people, and it takes the withdraw's
shape** ([ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md), #411
rules 1, 5, 6 and 8, built by [#418](https://github.com/Raketa02/Raketa/issues/418)): a title
naming the **moment**, the act named once on the control that carries it out, a dismissal named by
what it does.

| | |
| --- | --- |
| The control | `Leave this game` — `secondary`, **last** on the game screen's plan lead, drawn only while the agreed moment is ahead |
| In flight | `Leaving…` |
| Sheet title | `Before you leave` |
| Body | `The others keep the game and can fill your seat.` |
| Body | `You can't be asked back into this one.` |
| Body | `This cannot be undone.` |
| The act | `Leave the game` |
| Dismissal | `Stay in` |

**The first body line is the one that earns the sheet**, and it is the opposite of the withdraw's:
a departure destroys **nothing** — the others keep the game, the plan and the room — so the line
says what survives, and the second says the one cost that is the leaver's alone: `already_asked_at`
keeps them out of this court's pool for as long as it stands. Nothing here says the pair rule
releases, on §22.3's own line.

**Except when the leaving would end the game** (amended 2026-09-15,
[ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§9): when, besides the reader's own, exactly one seat on the court is still accepted and no seat
is awaiting an answer — the reader's leaving leaves one person on a game — the first line is
false, because nobody keeps anything. The sheet then gains §22.10's ending line **above** its
three, in the same case and the same words:

| | |
| --- | --- |
| Body, first, when the reader's leaving would leave one person on the game | `Leaving now calls the game off — for {name} too. Your chat goes with it.` |

`{name}` is that one person, their whole name (§15). The three lines below it stay as they are;
the title, the act and the dismissal do not move.

**The visible control is the whole sentence**, so it is the accessible name too — unlike
`Withdraw`, there is no shorter form a reader would want. A refused leave draws no new copy: a
stale tap re-reads and says nothing, `challenge_not_found` leaves the screen, and `account_held` is
`challengeErrorMessage`'s sentence as for every write in that feature.

**The rung**: **`Needs a player`** is the card's word for a court somebody left, above *Needs
result* and *Game on*; the state word one line over is `needs a player`, so the room's
header reads `Padel · needs a player`. The wide door says **`Fill the seat`** (§22.7, §22.9).
**`We played` is withheld** while the seat is open, and no sentence replaces it: the empty seat on
the card is the whole of the explanation.

**The open seat**: on the players card the row reads **`Open seat`** where a handle would be — an
empty face, no level row, and **nothing to press**, because there is no record to open for nobody.
On the card's spoken name it is one clause after the sport, counted: `An open seat` · `2 open
seats` (§24.5).

**The line**: `{name} left — that seat is open again` — §23's third `SEAT_LEFT` value, coordinated
with #416.

### 22.9 Filling the seat, calling it off, and the fourth end

**The reopened court's whole account, on the game screen and the card**
([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md), #411 rules 3 and 4, built
by [#419](https://github.com/Raketa02/Raketa/issues/419)).

**The door** is **`Fill the seat`** — §22.7's row: the card's wide door and the screen's primary act
on *Needs a player*, one word for one press, drawn only while the agreed moment is ahead. It goes
busy under its own label while the search runs, as the challenge screen's ⚡ does, and lands in the
builder.

**The control** is **`Call it off`** — `secondary`, above *Leave this game*, drawn only while a seat
is open and for **any player on the court** — an accepted seat
([ADR-0165](../../adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
§5, [#428](https://github.com/Raketa02/Raketa/issues/428); it was the organiser's first, with a
fallback to whoever was left, for one record). Not gated by the moment — the withdraw is not — so
on a short court past its moment it is the one act left. **The visible control and the sheet's act
carry one label**, on `Send the challenge`'s precedent: the act is named once, and what is under the
sheet is hidden while it is up.

**The sheet** is the withdraw's (§22.3), reworded for a court that has been a game:

| | |
| --- | --- |
| The control | `Call it off` |
| In flight | `Calling it off…` |
| Sheet title | `Before you call it off` |
| Body | `Everybody loses this game.` |
| Body | `The conversation goes with it, and what people wrote is deleted.` |
| Body | `This cannot be undone.` |
| The act | `Call it off` |
| Dismissal | `Keep it` |

**These are the author's words from #419, and they replace the placeholder #417 wrote here while
it had no client to build** — `Everybody still in loses this game.` / `Call the game off` / `Keep it
open` — three of the four changed on purpose: the first line drops *still in* because the sheet is
read by somebody who is, the act is the control's own word so it is named once, and the dismissal
is `Keep it` rather than the withdraw's `Keep it open`, because a game is not open the way a court
is. The second body line was the withdraw's own, and since #428 retired the withdraw's deck it lives
here alone — ADR-0142's *destroyed, not delisted* holds on a game's room, and a confirmation that
did not say so would be hiding the only consequence nobody can undo. The first names what the act ends: not *this court*, which is the challenge's word, but *this
game*, because that is what the people still in it lose. Nothing here says the pair rule releases,
on §22.3's own line. A refused call-off draws no new copy: a stale tap re-reads and says nothing,
`challenge_not_found` leaves the screen, and `account_held` is `challengeErrorMessage`'s sentence.

**The ending's words** — the fourth end, drawn as *Never played* is, **and the screen says who**
(amended 2026-09-15,
[ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§8; until then the title was *It was called off* and *nobody is named*, because `called_off_by` was
on no wire):

| | |
| --- | --- |
| The tag | `Called off` |
| The state word | `called off` |
| The standing line | `Called off` |
| Under the card's slots | **nothing** — the card names nobody, and offers two things instead of a line |
| The card's two buttons | `What happened?` — the on-dark fill where a live card has its wide door, opening the game screen · a square button with the trash glyph, spoken `Remove this card`, that clears the card from Now at once, for good, on every device — no sheet, because it removes a card and not a fact: the row and the screen behind it keep the news for their day |

**The screen's ending block, keyed by how it ended** — a departure told from a press by whether
`called_off_by` still holds a seat on the game (the leaver's is vacated):

| | Heading | Body |
| --- | --- | --- |
| a departure, singles | `The game was called off for lack of players` | `{name} left, so the singles game is called off. Nobody is marked for it — not you, not them.` |
| a departure, doubles | `The game was called off for lack of players` | `{name} was the last to leave, so the doubles game is called off. Nobody is marked for it — not you, not any of them.` |
| the button | `{name} called the game off` — the reader's own: `You called the game off` | `Nobody is marked for it — not you, not any of the others.` |

The body still says what the ghost's says about the strands — the same fact about the same people:
neither an evening nor a game that never happened, so nothing anybody is measured on moves — and
what changed is that the heading is a sentence and the body names the person. `{name}` is
`called_off_by`'s whole name (§15). The card is shelved a day from `called_off_at`, for a card
nobody clears.

**One word: called off.** The tag, the control and its sheet, the headings and every sentence in
this section use it; ***cancel* appears nowhere** — not on a control, not in a sentence, not in a
code.

### 22.10 Leaving from the Chats list, and before the court is whole

**The same act met twice more** — revealed by a swipe on a chat row, and drawn on the challenge
screen's two live arms ([ADR-0165](../../adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
§1, §6, built by [#427](https://github.com/Raketa02/Raketa/issues/427)). The sheet is §22.8's — the
title, the act and the dismissal are the same words — and what differs is the one line it says
and what it does with a refusal.

| | |
| --- | --- |
| The revealed control, and the screen's button | `Leave the game` — §22.8's act, now the control's word too: one label on the control and on the sheet's act, on `Send the challenge`'s precedent |
| Sheet title | `Before you leave` |
| Body | `Your seat opens for someone else and you'll leave the chat.` |
| The act | `Leave the game` |
| In flight | `Leaving…`, on the sheet's act |
| Dismissal | `Stay in` |

**One line where §22.8's sheet has three**, and it is the author's sentence: the seat and the chat
in one breath, because nobody is in a chat separately from being on its court, and the line exists
so that leaving the chat is not a surprise about leaving the game. §22.8's three are reached from a
screen about a game the reader has been looking at and say what survives and what the leaver gives
up; this one is reached from a list, one swipe deep, and has to say what the act **is** first.

**The line changes when the leaving would end the court** (amended 2026-09-15,
[ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
§9) — the reader is the only other accepted seat and no seat is awaiting an answer, read off the row
the list already holds — because then the seat opens for nobody. Which of the two it is, the
challenge's `game_id` decides:

| The court | Body |
| --- | --- |
| a game — `game_id` set | `Leaving now calls the game off — for {name} too. Your chat goes with it.` |
| never a game — `game_id` null | `Leaving now closes this court for {name}. Your chat goes with it.` |
| otherwise | `Your seat opens for someone else and you'll leave the chat.` — the line above, unchanged |

`{name}` is the one person left, their whole name (§15). The title, the act, the in-flight word and
the dismissal do not move, and the same three lines are said on the challenge screen's *Leave the
game*, which is the same sheet. The rule is read off a list that may be a beat stale; the server's
answer is what happens, and a refusal is said below as before.

**A refusal is said on the sheet, in words.** On the game screen a refused leave re-reads and says
nothing, because the fold the re-read lands on is the sentence; a list row has no fold, so the
sheet stays up and says why, with the act still there to press again:

| Code | The sentence |
| --- | --- |
| `game_moment_has_passed` | `The time you agreed has passed, so there's nothing to leave now.` |
| `challenge_is_over` | `This one is already over.` |
| `game_is_history` | `This game has already happened, or never will.` |
| `challenge_not_found` | `You don't hold a seat on this court.` — one code for three cases, chosen so a departure's refusal never confirms you *were* on it; the sentence confirms nothing about before |
| anything else | `challengeErrorMessage`'s sentence, as for every write in that feature |

Each names the fact and never the mechanism. For the four, the lists are re-read **once the sheet is
dismissed** — the sheet is drawn inside the row it is about, and a re-read that landed *over*
while the sentence was being read would take the row and the words away together — so a court that
has genuinely ended goes when the server says it has, and not a moment before.

**The rows go on the reply.** The leaver's chat row is gone by membership and their challenge row
by the inbox rule that already drops an own *no* — an own *left* is the reader's own act in the
same sense — and both go the moment the reply lands, before any list is re-read.

**The swipe is never the only path** (§20.12): the same act is the row's accessibility action,
under the same word, and taking it opens the same sheet.

## 23. The system lines — the codes, and what publishes nothing

**A system line is a code and its values, never a Message with a `kind`**
([ADR-0146](../../adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)). ADR-0022
decides it rather than taste: one shape forces either a **stored rendered sentence**, which freezes
copy into history so rewriting a line cannot rewrite the backlog, or a text field real for one kind
and meaningless for the other. **Nobody typed *Tomek set the day*.**

**`values` never repeats what the read already resolves.** The line carries `actor_id` and the
client fills `{name}` from the **`people`** beside it — the faces the response resolved for
everybody it names — so a handle correction reaches the whole backlog for free. **Not from the
members alone** ([#408](https://github.com/Raketa02/Raketa/issues/408), ADR-0148 §4 as amended):
membership is the accepted seats and then the game's line-up, so the person a *seat left* line is
about has by definition just left it, and a client naming off the roster drew `? said no — that
seat is open again`. `members` is still the roster and still the gate; `people` is the roster and
every author and actor the page names, resolved in the same read, and a page carries its own.

| Code | Published by | The sentence |
| --- | --- | --- |
| a seat accepted | `challenges` · `SeatAccepted` | `{name} is in` |
| seats invited | `challenges` · `SeatsInvited` | `{name} asked {n} more` |
| a seat left | `challenges` · `SeatDeclined` \| `SeatLapsed` \| `SeatLeft` | `{name} said no — that seat is open again` · `{name}'s day ran out — that seat is open again` · `{name} left — that seat is open again` |
| the game was played | `games` · `GamePlayed` | `{name} said you played` |
| a place recorded | `plans` | `{name} set the place · {value}` |
| a day recorded | `plans` | `{name} set the day · {value}` |
| an hour recorded | `plans` | `{name} set the time · {value}` |
| the plan was locked | `plans` · `PlanLocked` | `{name} locked the plan` |

**Eight codes, and the leave code is one with the answer as a value** — #221's *"that seat is open
again"* is the same news each way, and the facts stay apart in the value rather than in a
second code. **A lapse is still not a decline**, which is §13's rule holding one layer down —
and since [ADR-0162](../../adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md) there
is a **third value, `LEFT`**: somebody leaving a game they had agreed to, which is neither a no nor
silence, and the one departure whose actor was a member until this very line. `people` names
them exactly as it names a decliner; nothing on the wire moved.

**The lock is the one plan code that carries no value at all**
([ADR-0155](../../adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)). The
three slots *are* the value and the room already holds a line for each of them, so a value here
would be the second place they are true and the first thing to disagree with the slot line above it
after a later move. `{name}` is filled from the response's `people` like every other line — the
event carries `locked_by` and no name.

**It is an act and not a fourth slot, and it is not the slot count under another name.** A complete
plan is one everybody *could* agree; this says somebody did. There is no *plan complete* line and
never will be — that is a conclusion the record already implies, which is the same test
[ADR-0142](../../adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md) §3
applies to `GamePlanned` — while *these people have agreed* is reachable from no arrangement of the
three slots, because nobody wrote it down. **There is no unlocked code**: the lock freezes nothing,
and a slot moved afterwards keeps it and writes its own line.

**Setting a slot and moving one are one code told twice**, separated by the fold rather than by a
second class. ADR-0144: *"unlike a lapse and a decline, which do the same thing to the line-up and
are different facts, these are the same fact told twice."*

**A place line renders the place without the court when it does not fit.** #335: when a system line
overflows a Chats row, **the fix is a shorter value, not a second line** — one rule for both row
kinds instead of two.

### 23.1 The events that publish nothing, and why

A builder reading the event list would write a line for each. **Each of these is refused, and
three different rules do it** (six when this section was written; the rows since added each say
which rule).

| Event | Why nothing |
| --- | --- |
| `ChallengeSent` | no conversation exists yet — nowhere to write |
| `ChallengeOpenedFromMutualInterest` | it **is** the opening; `seq` 1 is whatever happens next |
| `GamePlanned` | **the seats already imply it** |
| `challenges.withdrawn` | it **destroys** the room in the same act |
| `games.seat_vacated` · `games.line_up_reseated` | the challenge's own `SeatLeft` and the acceptance that completed the court draw the lines, and membership reads the game's line-up live — a room told twice would write a second line |
| `games.called_off` | it **destroys** the room, on the withdrawal's arm, and writes no line ([ADR-0163](../../adr/0163-called-off-is-the-fourth-end-of-a-game.md); since [#424](https://github.com/Raketa02/Raketa/issues/424) it reaches the room, because the departure's call-off arrives with no withdrawal beside it) |
| `challenges.called_off` | the court's own ending on a court that has been a game ([ADR-0172](../../adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md) §1, §6) — written beside `games.called_off` in one transaction, it **destroys** the room as `challenges.withdrawn` does; whichever of the two is delivered first finds the room and the other finds nothing, and on a court whose game had already ghosted it is the only one that arrives |
| `games.dismissed` | a reader clearing a *Called off* card from their Now (ADR-0172 §5) — the room is gone before the card can be dismissed, so it reaches the room **not at all** |
| `ResultProposed` · `Corrected` · `Countered` · `Accepted` | `games` has its own conversation for the argument |

**No system line announces a derived standing, and there is no *Game on* line** — the prototype
writes that phrase four different ways. `GamePlanned` is refused on ADR-0142 §3's own test:
**an event may announce a conclusion only when no arrangement of the seats could reach it**, and
everybody having accepted is exactly such an arrangement. What a player sees instead is the **plan
card appearing** and membership stopping — drawn, not announced.

**A refused line is not a refused telling, and here that is load-bearing.** `GamePlanned` still
reaches the room and draws nothing, which is the shape `ChallengeOpenedFromMutualInterest` and
`challenges.withdrawn` already have — and `Game.planned_at` **is** `GamePlanned.occurred_at`, which
is where the room's own end is derived from
([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
§2). Dropping the delivery because nothing renders would drop the anchor with it.

**The room opening is not a line either**, and the same rule gives all three membership codes one
shape: **an acceptance, an invitation and a departure each write a line only when there was already
a room to write it in.** The first acceptor is a founding member, visible in membership.

**The result argument is refused on scope rather than on implication, and on scope alone.** It is
`games`' and `games` has its own eight-arm conversation for it: one fact in one place, and
ADR-0146's rename argument holds at any lifetime — *"two things called conversation in one codebase
is how somebody eventually subscribes the wrong one."* **The reason used to have a second half**,
that a room dying a day after the agreed point would carry the first two turns of an eight-day
argument and then vanish mid-sentence; that lifetime no longer exists
([ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §6),
and the refusal did not move, because it never depended on it.

**`GamePlayed` is the exception and earns it**: it is not the argument, it is the **answer to the
question this room was opened to ask**. It also closes the last of
[#322](https://github.com/Raketa02/Raketa/issues/322)'s four events with no sentence at all —
ADR-0150 §9 closed `SeatLapsed`, and the other two are refused above with their reason.

## 24. What each new control announces

§20's rules, applied to the five new surfaces. **§20.1's rule decides the element and §20.2's
decides the role**, and both are used rather than restated — except once, where a stream is a shape
neither of §20.1's two worked examples covers.

### 24.1 §20.1 gains its complement: a stream is navigated by its entries

> **One accessibility element per action — and one per entry in an ordered stream.**

§20.1 was written against a card and a grid: *"one accessibility element per action; everything
with no action of its own merges into the nearest action above it."* A conversation's backlog has
**no actions in it at all**, so the rule as written merges an entire history into one element a
listener cannot move through — which is the failure 6.8's own argument names from the other side:
*"21 buttons announce 21 identical actions, where 21 checkboxes announce 21 answers."*

A stream is navigated **by entry**, the way a grid is navigated by cell. The complement is stated
narrowly so it does not reach the card: it applies to an **ordered stream whose entries are the
content**, and nothing else on this map is one.

### 24.2 The Chats tab

| Element | Role | Announces |
| --- | --- | --- |
| Section heading | `header` | `Challenges` · `Conversations` |
| A challenge row | `button` | the handles, the sport, then the row's one line — `Ewa M., squash, 21 h left to answer` |
| A conversation row | `button` | the handles, the sport, then the last entry — `Tomek W. and Ola K., padel, Tomek set the day · Saturday` |
| The urgency stripe | — | **hidden.** The duration is in the row's own label, and a bar restating it is the second spelling #335 refused |
| The tab badge | — | **cited** — on the column's own `accessibilityLabel` (#326 §9), because `Column` is `accessible` and a `<Text>` dropped inside is swallowed |

**A row is one element because it is one action** — the whole row is the door, and #324 put every
act on the surface behind it. **The handles are whole**, and the list truncates for the eye and
never for the ear: §20.4's *"the visible label truncates, the spoken one never does"*, applied one
surface over.

### 24.3 The challenge screen

| Element | Role | Announces |
| --- | --- | --- |
| The card block | — | **one element, no action** — the handle, the level row, the Fit and its top reasons, capped at roughly twenty words before the buttons below it |
| Accept | `button` | `I'm in` |
| Decline | `button` | `Not this time` |
| Either, offline | `button` + `disabled` | the label, and the amber note is a separate element read before them |
| ⚡ Fill the seats | `button` | `Fill the seats` — **the ⚡ is decorative and hidden**, which is the tab bar's own precedent |
| Open the chat | `button` | `Open the chat` |
| Withdraw | `button` | `Withdraw this challenge` — **the accessible name says what it withdraws**, which is 6.9's rule (*"names which photo it removes"*) applied |
| The withdraw sheet | — | **cited** — 9.1's modal semantics, `accessibilityViewIsModal`, hidden siblings, Android back. **Focus lands on the title, not the first action**, per §20.6: that action is the destructive one, and landing focus there would make the worst outcome the cheapest to trigger |

**The card is one element and not one per row**, on §20.1 unchanged: it carries no action of its
own and the buttons are beneath it. A merged label that cannot state its subject inside the cap is
evidence the seam is wrong — here it states the handle first, which is the fact the whole screen is
about.

### 24.4 The conversation

| Element | Role | Announces |
| --- | --- | --- |
| The header | `header` | **every handle whole**, then the sport, then the game's state — `tomek.p and ola.k, Padel, planning`; `tomek.p, Padel` where there is no game. **One element** for the title and the line under it |
| A message | — | **the author, always** — `Ola K.: on my way` · `You: 18:00 works` |
| A system line | — | the rendered sentence, which already names its actor |
| A day separator | `header` | the weekday |
| The plan's heading | `header` | **one element** for the eyebrow and the counter — `The plan, 1 of 3 set` · `The plan, Locked` — which is `YOUR GAMES · n`'s shape one screen over, with a comma where the drawing has the pill |
| A slot chip | `button` | `{Slot}, {value}` · `{Slot}, not set` — `Day, Saturday`, `Hour, not set` |
| A day option | `radio` + `selected` | the weekday |
| An hour option | `radio` + `selected` | the clock time |
| Where | `textbox` | `Where` |
| Lock the plan | `button` | `Lock the plan` — with `disabled` while a slot is empty, `busy` and `Locking…` while it goes out, and **not there** once the plan is locked |
| The composer | `textbox` | `Message` |
| Send | `button` | `Send` |
| A quick chip | `button` | its own text |
| Details | `button` | `Open the game` — **not *Details***, which names a screen rather than what is behind it |

**A bubble's accessible name always names the author, even where the bubble does not.** The visible
label is drawn only in a conversation of more than two, because side and colour disambiguate the
pair — and *side and colour* is precisely what Part 13's **never colour as the only signal**
refuses to let a listener depend on. **The whole handle**, never a first name (ADR-0107).

**The day and hour options are `radio` rather than `button`**, on §20.2's rule — *prefer the role
that carries the state* — and 6.8's argument: seven buttons announce seven identical actions where
seven radios announce seven answers, one of which is chosen. **The slot chip above them is a
`button`**, because opening the row is an action and the value is not a state it holds.

**`Open the game` rather than `Details`.** The visible label is the design's and stays; the
accessible name names the destination, because *Details* is a word about a screen and every other
door on this map is named by its act.

**The greyed lock's reason is the heading two elements before it, in the reading order as well as
on the screen** ([#403](https://github.com/Raketa02/Raketa/issues/403)). #324's rule is that a
note above a greyed control has already said why, and the counter is that note in both registers:
a listener swiping through the card meets `The plan, 1 of 3 set` and then the chips before
reaching `Lock the plan, dimmed`, so the reason arrives first without a hint restating it. The
button's name never changes for the state — the state is `accessibilityState`'s — and once the
plan is locked there is no button to name, because the counter's `Locked` is the whole fact.

**The header draws one thing and says another, and that is §20.4 applied to a title**
([#401](https://github.com/Raketa02/Raketa/issues/401)). The drawn title is each handle's **stem** —
`tomek, ola` — and the drawn line under it is `Padel · planning`; the element is named by the
handles **whole**, joined with §22.6's final *and*, then the sport, then the state, with commas
where the drawing has a `·`, because a middle dot is a mark a listener has no reading for. It is
the Chats row's own shape (§24.2) one screen on, so the tab and the room do not change dialect. The
title and the sub-line are **one element** on §20.1: the line qualifies what the title names and
has no action of its own. The state is the Now card's name in lower case — the four-rung ladder,
never a standing (ADR-0157) — and a room with no game stops at the sport.

### 24.5 Now, and the game screen

| Element | Role | Announces |
| --- | --- | --- |
| `YOUR GAMES · n` | `header` | the heading and its count |
| A game card's body | — | **one element, no role, no action** — the tag, the sport, then the three slots as sentences: `Planning. Padel. Where, Zabłocie Sport, court 3. Day, Not agreed yet. Time, Not agreed yet.` · `Game on. Padel. Where, Zabłocie Sport. Day, Today 14 Sep. Time, 18:00.` — and the line under the slots where the card keeps one. **On a court somebody left, the open seat is said after the sport** — `Needs a player. Padel. An open seat. Where, …` · `2 open seats.` — because the court is hidden from a listener and the tag names the errand, not the shape (#418) |
| The wide door | `button` | its own verb — `Finish the plan`, `Open`, `Fill the seat`, `We played`, `Confirm the result` |
| The bubble | `button` | `Open the chat` — **the same words as every other chat door** |
| The rail's dots | — | **one element, `Game {i} of {n}`, and no role** — 7.9's own shape (*"one element, one label — never one per segment"*), and not pressable, so it announces a position rather than offering an action |
| The plan, read-only | — | **one element** — `The plan. Where, Zabłocie Sport. Day, Saturday. Hour, 18:00.` |
| The checklist | — | **one element**, its three lines in order |

**A card is three elements, and the first has no action.** The body used to be a `button` whose
name ended in the door's verb, because the body tap and the named door went to one place; since
[#413](https://github.com/Raketa02/Raketa/issues/413) the body is not pressable, so it is one
element of facts in the shape the read-only plan tags take — *one fact in three parts with no
action* — and the two doors follow it as elements of their own. The verb is therefore **not** in
the body's name: a body ending in `Open` beside a button announcing `Open` is the double
announcement 6.8 refuses. The place is spoken whole and the day with its date.

**The three read-only plan tags are one element** because they are one fact in three parts with no
action: §20.1 unchanged, and the reason `Tag` was chosen over `Chip` for them in the first place.

### 24.6 The typing indicator, and why it is polite

**The first live region on this map that is not the matchmaking tab's**, so it is stated here rather
than as a fourth row in §20.9 — that table is a closed list about *that* feature, and this is a
different screen with a different reader.

| Element | Role | Announces |
| --- | --- | --- |
| The typing bubble | one element, `accessibilityLiveRegion="polite"` | §22.5's sentence, whole — `ewa.m is typing…` |
| The three dots inside it | — | **hidden.** They are the drawing of the same fact, and announcing both is §1.6's count problem in two spellings |

**The bubble is the element and the sentence is its name** ([#404](https://github.com/Raketa02/Raketa/issues/404)):
the design draws three pulsing dots and no words, so the sentence a pulsing dot cannot say is
what the element is named, rather than a line of text drawn beside it. **A person is named in a
pair too.** A pair has exactly one possible typist and the name adds nothing a listener does not
know — but *somebody is typing* would be a second sentence kept only to withhold a name, the drawn
bubble carries none at all so the spoken name is the only place the name goes (§20.4), and one
sentence shape across every room is worth more to a listener than a shorter one in half of them.

**Polite, and this is the one place that word is load-bearing rather than inherited.** A listener in
a conversation is being read *messages*, one entry at a time, and an assertive region interrupts —
so the loudest thing on the screen would be the least important fact on it, delivered on top of
somebody's actual words. §20.10's argument about a toast landing mid-card is the same argument with
more at stake: a toast interrupts a card, and this would interrupt a person.

**It announces on change and not on a heartbeat**, which the wire already guarantees: a `typing`
frame arrives when the answer changes, so re-rendering the same sentence — and re-announcing it
every three seconds for as long as somebody types — is a thing the client cannot accidentally do.

**And it announces nothing when it goes away.** An empty `player_ids` removes the region's content;
a listener is not told *Ewa M. stopped typing*, because nobody said that and the platform does not
know it. What it knows is that nothing has been heard for five seconds, which is not a sentence
anybody needs.

### 24.7 Cited, not written

| | Where it already is |
| --- | --- |
| The tab bar's five columns, and the badge on Chats | §20.13, and [#326](https://github.com/Raketa02/Raketa/issues/326) §9 |
| The bottom sheet's modal semantics and focus rule | 9.1, and §20.6 |
| Every toast — announced, queued, one interrupting exception | §20.10 |
| The four `AWAITING_ANSWER` arms, the score grid, and every control on them | `gameAccessibility.ts`, built and tested by [#314](https://github.com/Raketa02/Raketa/issues/314) |
| The builder, the court and the seat | §20.4 and §20.4.1 — reached from Chats at a second route, and unchanged by the journey |
| Durations, weekdays, clock times, counts | §B16, through §18 |
| Pluralisation | §19 — no string hardcodes an `s`, accessible names included |

### 24.8 The court's pairing on the game screen

Two blocks on the plan lead ([#415](https://github.com/Raketa02/Raketa/issues/415), §25), and
§20.1 decides the elements: nothing in the forecast block has an action, so it is four elements of
facts; every row of the players card has one, so every row is a `button`.

| Element | Role | Announces |
| --- | --- | --- |
| `BALANCE FORECAST` | `header` | the eyebrow |
| The split row | — | **one element** — both sides named whole over *and*, then the gap: `You and kasia.w 2,70, tomek.p and marek b 2,71, gap −0,01` |
| The balance bar | `image`, **hidden** | its own §20.4 name is kept on the element — the word and the figure — and the subtree is hidden, because the row above speaks all three of its numbers and the reading beside it speaks the word: a fourth reading of one fact is 6.8's double announcement |
| The reading | — | **one element** — §20.4's order, the word then the figure, then the sentence: `Very even, 90%. A counted game — a confirmed score moves everybody’s level.` |
| The stake tiles | — | **one element, two clauses or none** — `If you win +0,08, If you lose −0,08` |
| `PLAYERS` | `header` | the eyebrow |
| A player's row | `button` | **the record it opens**, by whose it is — `tomek.p’s record`, and `Your record` for your own; the level row is the button's **hint**, so a listener hears under the name what the sighted reader sees under the handle |
| An open seat's row | — | **one element, no role, no action** — `Open seat`, its own words: there is no record to open for nobody, and a row that could be pressed would promise one (#418, §22.8) |
| The footer | — | one plain sentence, §25's |

**The bar's labels are stems and the row's name is whole**, which is §20.4's rule — *the visible
label truncates, the spoken one never does* — applied to the one place a handle is cut on this
screen. **Tap, not hold**: a row is a `button` because #285's argument against the hold is an
argument about exactly this table — a hold has no row in it.

## 25. The court's pairing

Decided by [#410](https://github.com/Raketa02/Raketa/issues/410) and built by
[#415](https://github.com/Raketa02/Raketa/issues/415), on
[ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md)'s reversal of §5.5's
refusal. The surface is [`the-loop-screens.md`](../the-loop/the-loop-screens.md) §5.5; the
sentences are here, in `games/components/gamePresentation.ts`, because the pairing is the game's
and §1's owner is the vocabulary.

**Most of this section is cited.** The four balance words and their breaks are §B9's through
`balancePresentation.ts` (§18); the level row is §6.4's through Play's `levelRow`; the figures take
§B16's shapes through the one formatter. What is new is the block's own frame and the one row shape
the app did not have.

| Where | Sentence | Note |
| --- | --- | --- |
| The forecast block's eyebrow | `BALANCE FORECAST` | stored as words, drawn uppercase |
| Between the two strengths | `gap` | lower case — a unit rather than a heading, the builder's own word in the same place |
| Under the figure, counted | `A counted game — a confirmed score moves everybody’s level.` | `worthLine`'s fact in the forecast's register — *movement*, beside the number that says how even — and not that sentence again four cards apart |
| Under the figure, friendly | `A friendly — nothing moves.` | the negative, kept: true whether or not anything reads it |
| Under the figure, unreadable kind | *nothing* | §3's drop — the figure stands and the clause goes |
| The stake tiles | `If you win` · `If you lose` | *if*, because on a game the result has not happened; **not** the card's `Win, counted` / `Lose, counted`, which name a mode a game has already answered |
| The players card's eyebrow | `PLAYERS` | |
| A row's handle | `{handle}` · `{handle} (you)` · `?` | the whole handle (ADR-0107), `player_record`'s own `(you)` mark after yours, the unknown player's `?` for a seat `users` cannot answer for |
| A row's level | `{level} · {band} · likely {low} – {high} · {n}% sure` | §6.4's three clauses cited, and the confidence as a fourth in the challenge card's own words |
| A row with no pairing row | *the handle alone* | somebody unrated is not in `seats`; nothing says so |
| The footer | `Tap anyone for their record — level, form and how they behave. Counted by the system; nobody writes text about people here.` | **tap**, not the design's *press and hold* (#285); the second sentence is the record's own authorship promise, said where a reader is about to open one |
| A row's control | `{handle}’s record` · `Your record` | §24.8 |

**Absence has no sentence.** ADR-0161 §4: the forecast and the split are omitted together when the
pairing cannot be computed, and *there is deliberately no reason beside the absence* — the block is
absent entirely, the tiles with it, and nothing on the screen says *unrated*, *unavailable* or
anything else. The players card is drawn regardless, because its rows are the court's seats and the
Level under each is what the pairing adds.
