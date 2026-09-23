# The Play components

**Where the seams fall across the three cards and the two courts, what each one owns, and
which of them the design system is entitled to.**

Produced by
[Where the seams fall in the three cards and the interactive court](https://github.com/Raketa02/Raketa/issues/240)
on the map
[Play tab, end to end](https://github.com/Raketa02/Raketa/issues/217).

[`the-words.md`](the-words.md) §20.1 already drew the line this file sits on: *"[#240](https://github.com/Raketa02/Raketa/issues/240)
decides the **React component tree**, this file decides the **accessibility tree**, and they
are independent: a card may be one element built from six components, or six elements built
from one."* The two documents are siblings, which is why this one is here rather than in the
client app — the third document a build session reads, after
[`design-system.md`](../../../frontend_player/docs/design-system.md) and
[`architecture.md`](../../../frontend_player/docs/architecture.md), and subordinate to both.

> **This decides seams, not composition.** What each surface *draws* is UI spec §B and
> [`the-play-screens.md`](the-play-screens.md); what it *says* is
> [`the-words.md`](the-words.md); what it *looks like* is the design system. What is here is
> where one component stops and the next begins, and who owns each number.

---

## 0. Ten of §G3's items were already decided, and are not re-opened

| Item | Where it was settled |
| --- | --- |
| §G3 #6 — *the sheet must become a real dialog with focus management* | `BottomSheet` already ships as a real modal with `accessibilityViewIsModal`, hidden siblings and Android back ([9.1](../../../frontend_player/docs/design-system.md#91-bottom-sheet)). Built, not owed. |
| §G3's *pinned call-to-action is a shared mutable and must not stay global* | [10.1](../../../frontend_player/docs/design-system.md#101-screen-structure) already makes the CTA a **screen-structure slot** above the tab bar. Per screen. No context, no returned slot, no mutable. |
| §G3's *decide whether the production header sticks* | [#227](https://github.com/Raketa02/Raketa/issues/227), which pinned it inside the scroller **against** the UI spec's own Open #6. |
| The three stat blocks, their `--paper2` fill and their 1 / 1.3 / 1.1 weights | Decision 3 removes Player Score and Last-5, and the block **stays removed on this side**. All three now cross ([#306](https://github.com/Raketa02/Raketa/issues/306)) — the backend assembles them and the contract carries them, each omitted rather than nought — but no card here draws one, so [`the-words.md`](the-words.md)'s own rule — *a gap wherever the screen states a count or a total its row belongs to, a **drop** everywhere else* — still makes all three a drop. The block does not exist, so neither do its weights. Same for §B12's Player Score row on the deck. What did change is the **sort**: `MOST_RELIABLE` reads the published Player Score off the card and is offered, which is the one place this side reads the block at all. |
| The at-stake pair, the *unsettled* tag, the seat-impact line, the *Evenest* sort | Decision 3 and [#231](https://github.com/Raketa02/Raketa/issues/231). |
| That the seat label truncates | [`the-words.md`](the-words.md) §20.4 — the visible label truncates, the spoken one never does. §5 below decides *to what*. |
| The de-duplication filter's shape | [`the-words.md`](the-words.md) §5 — *declared beside each card as the set of terms that surface draws*. |
| The forecast card's four eyebrows, four reading lines and shared-tags panel | [`the-words.md`](the-words.md). Nothing structural was left. |
| Where the sentences live | [`the-words.md`](the-words.md) §1 — feature-local `*Presentation.ts`, one per **vocabulary owner** rather than per screen. |
| Card radius naming, the court scrim, `textOnMedia`, display-number weight, the 9,5pt floor | [#219](https://github.com/Raketa02/Raketa/issues/219). |

**And one correction owed to the map.** [#231](https://github.com/Raketa02/Raketa/issues/231)
ruled `would_be_forecast` out of scope naming two consumers — the per-card seat-impact line
and the *Evenest* sort. There is a **third**: §B11's *With them seated · {pct}% even* row on
the social card, which [#218](https://github.com/Raketa02/Raketa/issues/218) read off the same
never-written field. It goes with them, and the social card's four rows are three.

---

## 1. What earns a design-system section

`shared/ui/README.md` says the folder is *"generic and feature-agnostic: if something here
starts to know about courts, bookings or matches, it belongs in a feature instead"* — and
`CourtPoster` sits in it drawing a court, while `LevelBar` knows what a band is. The stated
rule and the shipped contents disagree, so the port needs a test that decides rather than a
sentence that is already violated twice.

> **The design system holds drawn objects and control vocabulary — the things where two
> independent implementations would drift *on a number*. A feature holds every composition
> that names a domain noun.**

That is the rule the folder already follows in practice.
[7.5](../../../frontend_player/docs/design-system.md#75-the-level-bar)'s geometry was moved
into `size.levelBar` tokens for exactly this reason, recorded in Part 16: *"Half a drawn
object in each was how a value gets changed in one place."* `CourtPoster` is there because
one player id must always produce one poster; `Tick` was extracted because *"a second copy of
a 12 × 12 path is exactly the drift this folder exists to prevent."*

Applied to §G3's eight:

| | Owner |
| --- | --- |
| The court's ground, chrome and seat coordinates | **design system** — §4 |
| The balance bar | **design system** — §6 |
| The fit pill | **design system** |
| The switch behind the swap toggle | **design system** — 6.12 is specified and, since 2026-09-09, unbuilt |
| The availability grid's diff variant | **design system**, as a variant on 6.8 — §2 |
| The toast's queue, live region and dismiss | **design system** — 9.2 is specified and unbuilt |
| The three candidate cards | `features/play/` — §3 |
| `CourtMini`, `CourtBuild` and the seat | `features/play/` — §4 |
| The forecast card, the pool header, the searching state | `features/play/` |
| `CandidatePhoto` | `features/play/` — §4, §9 |

---

## 2. The five arrivals, and the numbering rule

Each arrives through
[15.1](../../../frontend_player/docs/design-system.md#151-adding-a-component) with a
[Part 16](../../../frontend_player/docs/design-system.md#part-16--amendments-after-locking)
row, and `design-system.md` and `theme.ts` change **in the same commit** (15.3) — which is why
none of them is written by this ticket and all five are booked onto
[#232](https://github.com/Raketa02/Raketa/issues/232), beside
[#219](https://github.com/Raketa02/Raketa/issues/219)'s outstanding rows and
[`the-words.md`](the-words.md) §20.12's queued-announcement amendment, so the amendment log
stays in order.

> **A returning component does not reclaim its old number.** 6.8's own amendment row settled
> this: *"6.7 is not reused … and a section number in this document never moves"*
> ([Part 17](../../../frontend_player/docs/design-system.md#part-17--what-the-reset-removed)).
> The reset deleted **7.1 the fit badge** and **7.2 the balance bar** because the engines
> behind them were deleted; both engines now ship, and both components come back — as **new
> sections**, at new numbers. The gaps stay the record.

| New | What | Why it is not a feature component |
| --- | --- | --- |
| **6.12** | The **switch** | [`the-words.md`](the-words.md) §20.4 fixed the swap toggle's role as `switch` with `checked`, and §20.2's rule is *prefer the role that carries the state*. Nothing in Part 6 carries `checked` on a **mode**: 6.3 is a segmented control, 6.2 a filter pill, and 6.11 is explicitly *"a claim a player either makes or does not"*. The visible label and the four mode lines stay Play's; only the control is the system's. |
| **7.10** | The **fit pill** | One shape, one threshold, drawn on four surfaces. Part 17 warns that the deleted 7.1's *"90 threshold named a scale the deleted engine defined"* — so the arrival **restates the scale it is against**: Fit is out of **100** ([`the-words.md`](the-words.md) §20.3, against §E6's 99), and the `.hi` step at ≥ 90 is re-argued rather than inherited. §B15's *"every call site overrides it inline to 26 tall with 12pt text; the class defaults are used nowhere"* is resolved by the arrival taking the used values, not the unused ones. |
| **7.11** | The **balance bar** | §6. |
| **7.12** | The **court** | §4. |
| 6.8 | A **diff** variant | [`the-words.md`](the-words.md) §20.7 calls the diff grid *"a different control with a third fact … not interactive"* — which describes a second accessibility tree, not a second file. It is 6.8's seven-by-three geometry **exactly**, and a second copy of that grid is the drift `Tick` was extracted to prevent. One component, two modes, two accessibility trees. Its volt-ring / 45 %-opacity scheme is a colour-only [Part 13](../../../frontend_player/docs/design-system.md#part-13--accessibility) violation found by [#236](https://github.com/Raketa02/Raketa/issues/236) and is fixed by the arrival, not after it. |

9.2's **toast** needs no section — it is specified and unbuilt. What it needs is the queue,
the live region and the dismiss §G3 #7 asks for; §7 below places them.

---

## 3. The three cards — three components over one parts kit

[#218](https://github.com/Raketa02/Raketa/issues/218) established that the three cards are
three renderings of **one** `CandidateSchema`. That is an argument for one contract, and it
was read as an argument for one component. It is not.

> **Three components, over one parts kit. Not one component with a `surface` prop.**

A single card would carry `surface === …` at nine sites — the prototype's condition rewritten
in TypeScript, and the thing §G3 #1 is complaining about (*"around sixty lines of
interpolation each, with eight conditional blocks"*) arriving in a new spelling. The three
genuinely differ in shape: after Decision 3 the competitive card is **photo-left with a
head-to-head row**, and the social and deck cards are **media-top with fact rows**.
[`the-words.md`](the-words.md) §5 already names them as three with three different filters.

**[#309](https://github.com/Raketa02/Raketa/issues/309) widened that gap rather than closing
it.** The competitive card's photo became a **panel** with the Level printed on it, its head
row became an **identity row** with a tag where the fit pill was, and its three head-to-head
elements collapsed into **one band**. So it no longer shares a head with the other two:
`CardHead` stayed theirs, and `PhotoPanel`, `IdentityRow` and `HeadToHeadBand` are the
competitive card's. Configuring one head to draw either a pill or a tag on the name line, and
either a tag or nothing beneath it, takes **two flags to say which** — which is this section's
own `surface === …` arriving one component down. The kit is what the three still share, not
what they are made to share. (The slot beneath `CardHead`'s name line held *They already said
yes to you* as a sentence until [ADR-0169](../../adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
§8 put the two-word tag there instead — both interest tags on both list cards, and the head's
two-line shape unchanged.)

**And 2026-09-09 widened it once more: the competitive card argues nothing.** Its reason lines
and its concern line are gone, so `ReasonLine` is the other two cards' component now. Every
figure it draws is untouched — the panel, the pill, the band, the record blocks, the stake
boxes, the tag row — and what went is the prose beneath the pill, because the case for one
person is `SH.whyfit`'s and every row carries a button named after that sheet. The rule behind
it is [`the-words.md`](the-words.md) §5a, and `candidateFacts` says it in one input: `argues`,
which stops the lines being composed rather than filtering them to nothing, so the spoken name
cannot carry a sentence the reader has no way to see.

**Two other things left these screens the same day**, both for the same reason — a caption on
something the surface already shows. The pool header's *Add somebody to their side and a
running balance appears here* is gone, under a court that draws its own empty seats and above
a list whose every row offers exactly that act; and the Sport moved **out of** the mini court's
7.12 caption band to a centred eyebrow beneath the picture, which leaves the drawing to be a
drawing. `Court`'s caption is untouched and now has no caller.

```
features/play/components/candidate/
  CandidateCard.tsx          competitive · pool     panel-left, one band, no prose
  CandidateCardSocial.tsx    for fun · pool         media-top
  DeckCard.tsx               the deck               media-top, floats
  CandidatePhoto.tsx         photo-or-poster in a box            ← §4, §9
  PhotoPanel.tsx  IdentityRow.tsx  HeadToHeadBand.tsx   competitive only
  SocialTagRow.tsx  RecordBlocks.tsx  StakeBoxes.tsx    competitive only
  StatBox.tsx                the box those last two are made of  ← 7.13, 7.14
  CardHead.tsx               social · the challenge screen's card
  FactRow.tsx  TagRow.tsx  ReasonLine.tsx
```

**[#312](https://github.com/Raketa02/Raketa/issues/312) added two more parts to that column,
and one shared box under them.** `RecordBlocks` is three boxes across — Player Score, Last 5,
Counted — and `StakeBoxes` is two, and they are one shape twice rather than two components with
a `variant`: a `paper2` box with a name over a figure, where the record's figures are counts and
the stake's are signed movements. `StatBox` is that shape, and it is in the kit for the reason
`FactRow` is — the alternative is the padding matching in one file and not the other.

**Neither is a `FactRow`, and the difference is what a reader does with the number.** A fact row
is a label opposite a value: a fact the card **states**, read once. These are five figures the
reader **compares** — against each other, and against the last card they looked at — and five
more rows on a card that is already a panel, a name, a pill, a band and a tag row would have
buried them.

**A block hides itself where its fact is absent**, which is the whole of why the row cannot be
one component taking three optional numbers and drawing three columns: the boxes that remain
fill the width, so a hidden block leaves no hole. And **the stake pair's own hiding is not the
component's**: `domain/atStake` decides it off the sport's seat count, and the component is
handed a pair or nothing (§7).

**Every card takes `(candidate, envelope)` and no global state.** It may also take what the
**screen** owns rather than the person: the competitive card's `sportName` is the *search's*
Sport, and it is a prop precisely because putting it on `player_card` would be twenty copies of
one fact crossing the wire per response. That is the same rule, not an exception to it — what
the sentence refuses is a component reaching for a store, never a screen handing down a fact it
already holds.
[#233](https://github.com/Raketa02/Raketa/issues/233) already fixed the why-fit sheet that
way, and it is the same fix §G6 #8 asks for on the card — *"the Why-fit sheet reads the global
sport and mode rather than the card's own."* Passing the envelope rather than a `mode` string
is what keeps [`the-words.md`](the-words.md) §2's warning intact: `SearchEnvelope.mode` is
null on the deck and `IntentAlignmentEvidence.my_mode` is not, and they are **supposed** to
disagree there.

**Each card exports its own drawn-terms set**, which
[`the-words.md`](the-words.md) §5 requires — *"declared beside each card … so the rule is
checked against the component rather than remembered"* — and `reasonSelection` (§7) consumes
it. The set is a property of the component because it is a statement about what that
component draws; moving it into the selector would be the one place it could go stale
silently.

**The card knows nothing about sending.** It takes `onAction` and a label, which is what lets
one shape serve *Add*, *Challenge* and *Let's play* — §B10's props already had this right, and
§8 is why it matters.

### The social pool card does not float

[#219](https://github.com/Raketa02/Raketa/issues/219) B3 opens by naming `.pcard` as *"the
deck card **and the social candidate card**"* and rules the family out of
[4.3](../../../frontend_player/docs/design-system.md#43-elevation)'s *cards never cast a
shadow*. Every clause of the argument reaches the deck alone: *"it animates in, and translates
and rotates out under the thumb"*, *"a transient object being manipulated"*. The social card
is a row in a scrolling list. It does not float, and 4.3's rule is that the three shadows are
*"all for things that genuinely float."*

> **The social pool card is a card — radius 13, no shadow. The deck card is the only user of
> `deckCard: 18` and the fourth shadow.**

#219's resolution stands and its scope shrinks to the surface its own reasoning covers; the
Part 16 rows it handed the build are narrowed, not withdrawn. The consequence is that **the
pool draws one shape twice** — competitive and social are the same card at the same radius
with different contents — which is what makes three components cheap rather than three
near-duplicates.

---

## 4. The two courts — one drawn object, two feature components

`CourtMini` (§B6) and `CourtBuild` (§B7) share everything that is a **number** and nothing
that is a **behaviour**: the 1,32 aspect, the four line-sets, the seat coordinates, the 150°
gradient at scrim `.93`, the caption, the side labels, the `textOnMedia` shadow. The seat
count is fixed by the Sport — padel and badminton 4, tennis and squash 2 — and **H-25 is the
reason the coordinates cannot be derived**: squash has no net, so both players sit on the same
half, and *seat 3* is not where seat 3 is in padel.

> **`Court` is a design-system drawn object. It takes a sport and a box, renders the ground,
> the chrome and the seat *positions*, and the caller supplies what sits in each one.**

```tsx
<Court sport={sport} width={w}>
  {seats.map(…)}          // children in seat order; the court places them
</Court>
```

Two shapes were refused. A `renderSeat(index, position)` callback is this with an
indirection. A `useCourtGeometry(sport, width)` hook **returns the coordinates**, and geometry
that is returned is geometry that gets adjusted at one call site and not the other — which is
the drift the placement rule in §1 exists to prevent, arriving through the door the rule was
written to close. With children, the positions never leave the module, and the interface is
testable through itself: hand it two children, assert two positions, per sport.

**`CourtMini` and `CourtBuild` stay two components**, on §3's own reasoning — read-only
avatars and interactive seats are *different children*, not a flag on one component.
`CourtBuild` owns the swap truth table, the selection ring and the clear badge; `CourtMini`
owns nothing but its avatars.

**The swap-toggle row and the two guard toasts are gone** (2026-09-09). The toggle was a
`switch` above the court and the only reason a tap on a seat had two meanings — *replace this
player* off, *trade these two* on. The forecast card's names row draws a **face per seated
player** now, each opening that person's record, so the court stopped being where a player
acts on somebody: the seat kept one meaning, the mode had nothing to select between, and both
refusals went with it, because they refused a **replacement** and a tap replaces nobody. What
a seat does is said once as a line of the screen's copy above the court, and replacing
somebody is the clear badge and then the hole it leaves. 6.12 keeps its section and loses its
one consumer.

**The court owns geometry and knows nothing about players; the seat owns its label, its ring,
its badge and its taps.** That is the seam, and it is what makes §5 a question the seat can
answer.

Three things fall out:

- **The seat coordinates become `size.court*` tokens**, on 7.5's precedent and Appendix A's
  contract that the document and `theme.ts` are one thing.
- **The seat-clear badge is not a new component.** [6.9](../../../frontend_player/docs/design-system.md#69-the-photo-tile-and-picker)'s
  remove control already is one: a solid `night` square with a white mark at the `tag` radius,
  a 44pt target, inset by its own slop — and [`the-words.md`](the-words.md) §20.4's label
  *`Remove {name} from {side}`* is 6.9's own rule (*"names which photo it removes"*) applied.
  The prototype's 18px circle at radius 9 offset −4 / −6 is dropped. §G1 loses a row.
- **`CandidatePhoto` is one component at three sizes** — the 74 × 92 on the competitive card,
  the full-bleed media on the social and deck cards, and the 46pt face in a seat. It is the
  photo-or-poster switch, and its radius is **33 % of its own box**, which dissolves §G2's
  33-against-34 split by giving the rule one owner rather than by picking a winner. §G1's
  *"rewriting the photo's declared width to a percentage by string substitution"* is deleted
  by the component existing.

---

## 5. The seat label, and where the names actually are

[`the-words.md`](the-words.md) §20.4 settled that the visible label truncates. It did not
settle to what, and the arithmetic is bad: §15 killed first names — every sentence uses the
**whole handle**, 2 to 64 characters — inside a 46pt seat, and
[#219](https://github.com/Raketa02/Raketa/issues/219) B4 raising 9 → 9,5pt makes an overflow
§G5 already records worse. Truncating a 64-character handle to a 46pt box yields about four
characters, which is not a name. §15 saw this and said §B16's side-name formatter *"is
redrawn, not kept … the 46px seat is the binding constraint and it decides the formatter."*

> **The seat label truncates to the seat's own width, one line, tail ellipsis, and the level
> comes off it. The whole handle is read off the lines already on screen.**

The label is an **identifier under a face**, not the name. Both screens the court appears on
already print the names in full and unavoidably: §B9's figures row on the forecast card, and
§B13's seated-names line on the pool header. So there is no legend to add and no element to
invent — the name is a scroll away on the same screen, whole in the accessible name, and the
truncation invents nothing, which is the only thing ADR-0107 forbids.

The level comes off the visible label because §10's rule is that a surface does not restate
what it already renders: the level is in the card's level row and in the why-fit sheet.

**No `allowFontScaling={false}`.** [`the-words.md`](the-words.md) §20.4 already refused it —
Part 13 permits the escape only *"inside the level bar's drawn geometry"* — and this is
recorded here because that section says it is.

---

## 6. The balance bar — one fixed scale, three sizes

The prototype computes the left segment as *fifty, plus the difference between the two side
strengths times thirty-four*, clamped — to `22–78` on the forecast card and `20–80` on the
pool header and the candidate card. **One formula, three clamps**, which means the same gap
lands in a different place on two screens. That is precisely the defect
[7.5](../../../frontend_player/docs/design-system.md#75-the-level-bar) and
[7.8](../../../frontend_player/docs/design-system.md#78-the-confidence-ring) exist to prevent:
*"a value must land in the same place everywhere or the component means different things on
different screens."*

Drawing the raw shares instead would be honest and invisible — 2,71 against 2,83 is 48,9
against 51,1, a difference no one can see.

> **The amplification ships, as one fixed scale recorded in the design system: one mapping,
> one amplification constant, one clamp at 20–80, three sizes (16 / 18 / 24) with the segment
> labels tied to the size.**

A steep scale is still a fixed scale. What was wrong was three of them.

**The printed evenness percentage stays the server's `pct` and is never derived from the
strengths** — [`the-play-screens.md`](the-play-screens.md) §11.3, *no forecast arithmetic on
the client*. The bar and the number are two different facts: the number says *how even*, the
bar says *which side*. The word beside the bar carries the meaning, which Part 13's *never
colour alone* already forces.

**One thing recorded rather than fixed.** §B9's word breaks at 85 / 70 / 55 and its colour
breaks at 70 / 55, so *Very even* and *Fairly even* share one green. That is correct: Part 13
is satisfied by the word, and a fourth tone would need a fourth **meaning**, which
[15.2](../../../frontend_player/docs/design-system.md#152-adding-a-colour) forbids inventing.
Left unwritten, somebody tidies it into four colours.

---

## 7. Where each rule lives

`CLAUDE.md` is categorical — *business rules live in `domain/` + `use-cases/`, never in a
screen* — while this app's shipped precedent puts number-to-word tables in `components/`:
`radiusPresentation.ts` renders 12 km as *"Across your town"*, and
[`the-words.md`](the-words.md) §1 put every code-to-sentence table in feature-local
`*Presentation.ts`. The line has to be drawn once or it is drawn per file.

> **A rule somebody could be *wrong* about goes to `domain/`. A table mapping a value to the
> words this app chose for it goes to `components/`.**

| `features/play/domain/` | Falsifier |
| --- | --- |
| `reasonSelection.ts` — filter first then take three, `INTENT_ALIGNMENT` never filtered, a concerned term removed from the reason list, fallback to the top `LivenessReason`, hidden rather than blank | [`the-play-screens.md`](the-play-screens.md) §10 |
| `sharedTags.ts` — the intersection, computed client-side and **not** read off `PlayingStyleEvidence.matched`, because that couples the badge to a term that can stand down ([#218](https://github.com/Raketa02/Raketa/issues/218)) | the term standing down |
| `lineup.ts` — origin validity `(sport, mode, week)`, [#228](https://github.com/Raketa02/Raketa/issues/228) §10's three triggers behind one guard, side derivation under H-25, locked seats, §B7's swap truth table | AC-8, AC-70 |

| `features/play/components/` | |
| --- | --- |
| Every code-to-sentence table | [`the-words.md`](the-words.md) §1's two shapes |
| `balancePresentation.ts` — the balance word and its tone | `radiusPresentation.ts`'s precedent: a number, its plain-word reading, and the thresholds between them |

**Two promotions to `shared/`**, on `recoveryMessage.ts`'s own stated third-caller rule, which
[`the-words.md`](the-words.md) §1 already invoked for `SocialTagId`, `DayPart` and `Weekday`:

- **`playerName()`** — §15's one function, used by Play, by `challenges`, and by all eight of
  §F3's toasts that name somebody.
- **§B16's number formatters** — level, distance, the separators. `ratingFormat.ts` sits in
  `onboarding/components/` and ESLint blocks a deep import between features outright, so
  Play's only two options are promotion or a second copy of *two fixed decimals, decimal
  comma, U+2212, em dash for null*. A second copy of that is the drift both `Tick` and the
  design system's *every number is mono and tabular* rule exist to prevent.

**The toast queue is `shared/`, not Play's.**
[9.3](../../../frontend_player/docs/design-system.md#93-layer-order) requires a **single
root-level overlay host**, so a queue living in a feature would mean that feature owning every
other feature's toasts. It is app-wide ephemeral UI state, which is the one row of
`architecture.md`'s ownership table Zustand is for; it holds no server data and no loading
flag, so Part 8's bans are untouched. The **priority rule is not invented here** — it is
[`the-words.md`](the-words.md) §20.10's, read off announcement politeness, with the send
confirmation as the single interrupting exception.

---

## 8. The seam with `challenges`

[#228](https://github.com/Raketa02/Raketa/issues/228) §13 split the client in two, at *the one
action in this tab that reaches another person*. Four surfaces have to be placed against that
line, and one of them reads the wrong way round.

| | Owner |
| --- | --- |
| The card's primary button | **Play** — it takes `onAction` and a label and knows nothing about sending (§3) |
| `SH.propose`, and the send's use-case | **`features/challenges/`** |
| The court screen's pinned CTA | **the screen's** own 10.1 slot, *calling* a challenges use-case |
| The send toast | the host is shared (§7); the sentence is `challenges`' |
| `GET /challenges` | **`features/challenges/`** — [#229](https://github.com/Raketa02/Raketa/issues/229) put the route on the player surface |

> **The deck's two buttons are Play's, not `challenges`'.**

A deck yes is `POST /interest`, a matchmaking write. The challenge a mutual yes opens is
minted **server-side and inline through a port**
([#222](https://github.com/Raketa02/Raketa/issues/222)), so nothing on the deck reaches
another person directly. Left unstated, the deck lands in `challenges/` because *Let's play*
sounds like a send.

---

## 9. The finding: the card's photo has no URL, and the route that mints one refuses it

`CandidatePhoto`'s interface could not be written without answering this, and the answer is
that it cannot be drawn at all today.

**Four places say the same thing.** `PlayerCardSchema.photo_id` — *"An id, never a URL: a
presigned link cannot live in a record kept forever, so the link is minted per response"*;
`cards.py`, `searches.py` and `search_model.py` repeat it. `rendering.py`'s module docstring
names that minting as one of **the two departures the round trip allows itself**:
*"a row the live gates now withhold, and a photo link minted per response."*
[`the-play-screens.md`](the-play-screens.md) §8 writes the round-trip test against it —
*"asserted over the record's fields, not over a byte-identical payload, since the photo URL is
re-minted per response by design."* ADR-0107 says *"on the `POST` and again on every `GET`."*

**It does not exist.** `player_card_source.py` states the opposite in writing — *"A URL is
never minted"* — and `_card()` passes `photo_id` through untouched. No field on any response
carries a link.

**And the client cannot mint one either.** `GET /api/v1/photos/{photo_id}` is *"A signed URL
for one of **your** photos"*, and refuses another player's id deliberately: *"the alternative
is an endpoint that confirms whether a stranger's id is real."* A card photo is by definition
another player's. As the contract stands, **every card in Play draws the poster and no
photograph can ever reach a Play screen.**

> **`player_card` gains a minted `photo_url` beside `photo_id`. The id is what is stored; the
> URL is what is rendered.**

That is the split all four docstrings already describe, and it is why they can coexist:
ADR-0104's dead-link argument is about the **record**, and a URL that never enters the record
does not touch it. The photo route's refusal does not reach here either — it refuses an
arbitrary id because an arbitrary id is an *oracle*, whereas a card's photo id was handed to
this caller by a search the server itself answered. The disclosure already happened, and what
was disclosed was a whole person, not a link.

Two alternatives, both refused. **Widening `GET /photos/{id}`** to serve any id the caller has
been shown needs an origin check in `POST /interest`'s shape, and rebuilds the *is a stranger's
id real* oracle the route refuses in writing. **Leaving it** is not the free option it looks:
it deletes the photograph from the deck, whose entire card is a photograph, and it
retroactively makes [#220](https://github.com/Raketa02/Raketa/issues/220)'s poster the product
rather than the fallback it argued itself into being.

> **Built by [#245](https://github.com/Raketa02/Raketa/issues/245).** The finding above is
> written in the present tense and is now history: `player_card` carries `photo_url` beside
> `photo_id`, minted per response by a `CardPhotoLinks` port over the photo provider's own
> store and recorded nowhere. The link is signed as the **candidate's own** — a link signed
> under the searcher's id would reach an object that does not exist — for the platform's one
> photo window, and it is **not** checked for existence: that would be twenty round trips
> before a response, to turn a photo removed since into the poster the client already draws.
> The two fields are omitted together. A **withheld** row's photograph is signed for nobody:
> the read-back mints over the rows it still puts a person on. `GET /photos/{id}` is
> untouched, and a test asserts it still refuses a card's own photo id — which is the whole
> shape of the argument above.

**One contract change** — the card audit's third, after
[#233](https://github.com/Raketa02/Raketa/issues/233)'s `degraded_terms` and
[#235](https://github.com/Raketa02/Raketa/issues/235)'s `range` — one backend ticket and one
client ticket on [#232](https://github.com/Raketa02/Raketa/issues/232), and argued again in
its pull request. [#218](https://github.com/Raketa02/Raketa/issues/218) read this field and
marked it ✅; that row is corrected rather than left standing.

---

## 10. §G1 and §G2, disposed

Twenty-seven inline styles and fifteen inconsistent values, one line each. **Dissolved** means
the thing the row is about no longer exists.

| §G1 row | Disposition |
| --- | --- |
| Fit-pill height and text overridden at all five call sites | **Token.** 7.10 takes the used values, not the unused class defaults |
| 11 / 11 / 9 and 0 / 11 / 11 padding on the competitive card | **Token**, from the 3pt grid — 12 / 12 / 9 and 0 / 12 / 12 |
| `--paper2` stat block, its radius, padding and 1 / 1,3 / 1,1 weights | **Dissolved** — Decision 3 (§0) |
| 18 and 16px balance-bar heights; 8,5 and 8px segment labels | **Prop.** One `size` on 7.11 (§6); labels tied to it |
| The ×34 amplification and its three clamps | **Token.** One mapping, one clamp at 20–80 (§6) |
| 2px coral and 2px volt borders | **Dissolved** — [#219](https://github.com/Raketa02/Raketa/issues/219) B1 dropped every on-paper volt stroke; the interest signal is the volt **tag** |
| The 40 × 23 track and knob | **6.12** (§2) |
| The 18 × 18 seat-clear badge at radius 9 | **Dissolved** — it is 6.9's remove control (§4) |
| Face size and the 34 %-against-33 % radius helpers | **Dissolved** — one `CandidatePhoto`, one rule (§4) |
| The `.92`-against-`.94` court gradient | **Dissolved** — [#219](https://github.com/Raketa02/Raketa/issues/219) B6 pinned it at `.93` |
| White at `.68`, `.7`, `.75` inside the dark card | **Dissolved** — 5.2's own rule supplies `.68`; delete the overrides |
| The 0 / 1 / 3 seat-label text shadow | **Dissolved** — [#219](https://github.com/Raketa02/Raketa/issues/219) B6's `textOnMedia`, on both label sets |
| The −4 / −15 / 0 bleed on sheet media | **Token** — a sheet-media slot bleeding by the sheet's own gutter |
| Rewriting the photo's width by string substitution | **Dissolved** — `CandidatePhoto` (§4) |
| 70px of top padding on the search screen | **Dissolved** — a centred layout; C2 stopped being a route ([#239](https://github.com/Raketa02/Raketa/issues/239)) |
| The −4 / 0 / 10 sort-caveat margin | **Dissolved** — [#231](https://github.com/Raketa02/Raketa/issues/231) struck the caveat with the sort it explained |

| §G2 row | Disposition |
| --- | --- |
| Balance-bar clamp | **20–80**, one constant (§6) |
| Hero figure family | **Dissolved** — [#219](https://github.com/Raketa02/Raketa/issues/219) B5: the code wins, mono **600**, mono 700 is not loaded |
| Body text size, six steps | **Dissolved** — [#219](https://github.com/Raketa02/Raketa/issues/219) B4: everything under 9,5 rounds up to `eyebrow` or `tag`; the DS roles are the scale |
| Sport chip presentation | **Small chips in a scrolling row on both screens** — Part 8's *square row*, which handles §G5's *more than four sports* by construction |
| *"No overlap"* wording | **Dissolved** — [`the-words.md`](the-words.md) |
| Slot vocabulary, three registers | **One definition** — `DayPart`, promoted to `shared/` by [`the-words.md`](the-words.md) §1 |
| Day ordering | **Monday-first in the interface**, one day-name helper; the Sunday-first array is an index and never reaches a component |
| Avatar radius factor | **33 %**, owned by `CandidatePhoto` (§4) |
| Three orphaned tokens | **Dissolved** — RN has no CSS custom properties; `theme.ts` is the only source and a literal is a lint error |
| Sport hue against semantic colour | **Dissolved** — [#219](https://github.com/Raketa02/Raketa/issues/219) B2 upheld the aliasing on a checked premise |
| Soft-coral border | **Dissolved** — Decision 3 removes the account-hold card, so there is one value |
| Card radius | **Named for roles** — card 13, dark card 15, deck card 18 ([#219](https://github.com/Raketa02/Raketa/issues/219)), sheet 22; and only the deck card floats (§3) |
| Empty-state titles | **Keep** — each is specific, which is the house style |

---

## 11. What this hands the build

| To | What |
| --- | --- |
| [#232](https://github.com/Raketa02/Raketa/issues/232) — design system | Five arrivals through 15.1 with Part 16 rows: **6.12** switch, **7.10** fit pill, **7.11** balance bar, **7.12** court, and 6.8's **diff** variant. `design-system.md` and `theme.ts` in one commit (15.3), in order behind [#219](https://github.com/Raketa02/Raketa/issues/219)'s outstanding rows and [`the-words.md`](the-words.md) §20.12's Part 13 amendment. |
| [#232](https://github.com/Raketa02/Raketa/issues/232) — design system | Build 9.2's toast: the queue, the live region, the dismiss, mounted once at 9.3's overlay host. |
| [#232](https://github.com/Raketa02/Raketa/issues/232) — backend | **`player_card.photo_url`** — minted per response, never recorded (§9). Regenerate `openapi.player.json`. |
| [#232](https://github.com/Raketa02/Raketa/issues/232) — client | Consume `photo_url`; `CandidatePhoto` draws the photograph and falls back to `CourtPoster` on the omitted id. |
| [#232](https://github.com/Raketa02/Raketa/issues/232) — client | Two promotions to `shared/`: `playerName()` and §B16's number formatters (§7). |
| [#232](https://github.com/Raketa02/Raketa/issues/232) — client | The tree of §3, §4 and §7, and the `challenges` seam of §8. |
| The map | [#231](https://github.com/Raketa02/Raketa/issues/231)'s out-of-scope entry gains its third `would_be_forecast` consumer (§0). |

## 12. What this file does not decide

- **Every seam outside Play.** [#321](https://github.com/Raketa02/Raketa/issues/321) added two
  client features — `conversations` and `plans` — grew `challenges` a screen, and pointed one
  one-way arrow between `plans` and `games`. Its counterpart of this file is
  [`the-loop-components.md`](../the-loop/the-loop-components.md), and **§8's table is extended
  there rather than rewritten here**: `GET /challenges` finally has consumers, the two seat answers
  arrive with the screen that answers one, and the challenge screen's card block is `challenges`'
  rather than a fourth candidate card.
- **What each surface draws** — UI spec §B and [`the-play-screens.md`](the-play-screens.md).
- **What each surface says** — [`the-words.md`](the-words.md).
- **What each control announces** — [`the-words.md`](the-words.md) §20. Independent of this
  tree by §20.1's own statement.
- **The four line-sets and the three poses** — vector path data the UI spec's own self-check
  says is *"best copied across verbatim"*. A build fact, not a decision.
- **`play` and `challenges`' client vocabulary** — *Play session*, *working copy*, *origin
  search*, and now the parts kit's names. [#228](https://github.com/Raketa02/Raketa/issues/228)
  deliberately left these to the build ticket that creates the stores, and this file leaves
  them there rather than starting a second half.
