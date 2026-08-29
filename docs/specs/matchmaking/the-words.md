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
`my_sigma` and `their_sigma` are never printed; they are the range's input
([#235](https://github.com/Raketa02/Raketa/issues/235)).

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

**A declined prompt is asked again**, today, and that is
[#237](https://github.com/Raketa02/Raketa/issues/237)'s to fix — not a copy softener here.

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
| **Pre-send** (`SH.propose`) | `{name} gets {window} to answer. Nobody is contacted until you send it.` |
| **Post-send**, per seat | rendered from `answer_by` through §B16's duration formatter — `{name} · {duration} left` |
| **Mutual yes** | `You both said yes — this one's already on.` **No deadline clause.** |

**`{window}` is a contract obligation, not a constant.** A pre-send sentence naming a
duration must name the number the backend will actually derive, or it stops naming one. Booked
onto [#241](https://github.com/Raketa02/Raketa/issues/241) and
[#232](https://github.com/Raketa02/Raketa/issues/232): either the send response's window
length crosses on the `challenges` contract, or `SH.propose` says *"a day"* nowhere and
states only the irreversibility clause.

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
- **The level row's range** — [#235](https://github.com/Raketa02/Raketa/issues/235).
- **What the send refuses, and in whose words** —
  [#241](https://github.com/Raketa02/Raketa/issues/241).
- **Anything on an out-of-scope surface** — the record sheets, *Show them again*, the
  seat-impact line, at-stake, Player Score's strands, languages. A code with no surface gets
  no words, and the map's Out of scope is the list.
