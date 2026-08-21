# ADR-0088 — The action row is three slots, and the clock takes the first

- **Status:** Accepted
- **Date:** 2026-08-22
- **Resolves:** [`Raketa02/Raketa#60`](https://github.com/Raketa02/Raketa/issues/60)
- **Completes:** [ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md), [ADR-0086](0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md) and [ADR-0087](0087-leaving-standby-is-the-seventh-act.md), each of which changed this row and each of which left the anatomy question where it found it
- **Draws:** [ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md)'s clock, which has had a rule since it was written and never had a place on the card
- **Overrides:** `UI` §B6.3's action row — **genuinely, not as a forced consequence**, and it is the first override on this map recorded as one

## Context

Three decisions in three days pulled this row apart, and none of them owned it. `UI` §B6.3 draws
every state card with one row — a `.btn.p` at `flex:1`, then two 40 × 34 `.btn.w` icons, `✉` to
Inbox and `⌘` to the Getting-in sheet, with `⌘` omitted when `post` is set. One variant plus one
omission.

[ADR-0083](0083-a-card-names-one-act-and-twenty-seven-name-none.md) removed the primary button from
twenty-seven of thirty-six cards and dropped `⌘` from `ready` as well.
[ADR-0086](0086-a-departure-is-a-route-and-the-card-points-at-it-without-naming-it.md) added a
third, member-only control. [ADR-0087](0087-leaving-standby-is-the-seventh-act.md) gave
`waitlisted` a primary button, placing a correct control immediately beside the `⌘` ADR-0083 had
already found *"visibly wrong on a card you have not joined"*. A build agent drawing a card today
chooses between five shapes with no authority to read, and
[#60](https://github.com/Raketa02/Raketa/issues/60) is explicit about why that cannot be left to
them: *"A build agent meeting five undrawn variants will invent a sixth."*

Walking the row found a sixth already, and three facts that dissolve the question rather than
adjudicate it.

**`⌘`'s sheet is empty until the exact moment `⌘` is dropped.** `UI` §B16: the door code shows
`4417#` when `now ≥ start − 15 min`, and `••••` otherwise. `UI` §B6.1's rung 11 makes `ready`
precisely `isFull && now ≥ T−15m` — the same instant. ADR-0083 already dropped `⌘` on `ready` and
gave the primary button that sheet. So on every card where `⌘` survives it opens four dots, and on
the one card where the sheet has something to say `⌘` is already gone. It is never simultaneously
present and useful.

**`✉` is not a card control.** `UI` §1010: `data-go="inbox"` is special-cased to
`S.tab='msg'; reset('inbox')`. It carries no match id and does nothing about the card it sits on —
it switches to a tab that is permanently visible in the tab bar with its own unread badge
([ADR-0082](0082-the-tab-bar-is-one-outline-family-and-coral-is-the-only-selected-cue.md)). On a
screen holding a dozen cards it is a dozen copies of one tab-bar button.

**The clock's only drawn home was dead code, and ADR-0083 has now removed it.** `UI` §B6.3 renders
the countdown as a suffix inside the primary button — `st.cta.label + ' · ' + st.left` — and
§B6.3's own `[GAP]` records that *"`cta` and `left` are read by `stateCard` but no state in the
table ever sets them"*. The prototype never drew a countdown at all. Every countdown on this screen
was constructed afterwards, by
[ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) (the phone subtracts from an
instant), [ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md) (exactly one clock slot
per card) and [ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md) (which
moment fills it) — and none of the three said where it renders, because §B6.3 appeared to have a
slot for it.

The overlap with ADR-0083's silent list is not partial. `rescue`, `rescueLate`, `heldSoft`,
`heldStale`, `heldExtended`, `formingLate`, `full`, `confirmed` and `replacement` all have live
deadlines and all lost the primary button. ADR-0073 argues its own rule on `rescue` specifically —
*"a seat being rescued is precisely when a player can do nothing and precisely when they most need
to see the deadline. The clock is the app's warning, not its to-do list."* Under §B6.3 as amended,
that warning has nowhere to print on the card it was written for.

**And the sixth shape is the shelf card.** ADR-0083 routes `takeSeat` to *"every shelf card whose
seat is takeable"* and `finishPaying` to *"any card, whenever the viewer holds a live claim on it"*,
but `UI` §B8 `MatchCard` has **no action row at all** — it is a `.card.tap` carrying
`data-go="match"`, and that destination is the match-detail screen this map ruled out. ADR-0083's
consequence note reads *"a shelf card's `⌘` is now visibly wrong"*; §B8 says a shelf card never had
one. So the shelf card has an act with nowhere to put it and a dead whole-card tap.

## Decision

**We will draw one action row of three optional slots — a clock, an act, and an exit — remove both
of the prototype's icons, and let a shelf card reach the same act through its body rather than
through a button of its own.**

### The row is three slots and has no variants

| Slot | Present when | Drawn as |
|---|---|---|
| **Clock** | the card's one clock slot holds a moment | `.mono`, fixed width, never shrinks, leftmost |
| **Act** | the spine carries an act code (ADR-0083, ADR-0087) | `.btn.p` at `flex: 1` — the only flexible element |
| **Exit** | `mayDepart` is true (ADR-0086) | the stock outline glyph, 44 × 44 hit slop, rightmost |

`#60` asked *how many variants the client is allowed to hold*, having counted two conditions
already and expecting a third and a fourth. The answer is **zero**. There is one row, and each slot
appears exactly when its own field is present. `post` stops being a structural variant at all: what
it dropped was `⌘`, and `mayDepart` is false after the match starts for every one of the six
post-match situations anyway.

**Vacant slots do not stretch.** The act is the only flexible element; with no act the clock stays
left and the exit stays right, and nothing grows to fill the gap. A stretched icon reads as a
primary button that has forgotten its label. Right and left are not arbitrary: the identity row's
right column already establishes that edge with the seat glyph and `filled/n`, and the left edge is
the fact list's `✓`/ring column.

**The empty row still renders**, as a zero-height spacer. `native-kit.md` §3 gives the action row
`marginTop: auto` so footers align across cards of differing height and short cards stop floating
in a *"slab of empty night"* — and an element that is not rendered pushes nothing, so twenty-six
cards would get the slab back. One view and no pixels keeps that fix true verbatim rather than
reopening it. Making `.hstrip` `align-items: flex-start` instead was refused: it changes the
strip's height on every swipe and moves the shelves below.

### `⌘` is dropped, and the Getting-in sheet keeps its one door

Not made member-only. `#60` proposed that and named its cost correctly — it puts the row's shape on
a viewer axis §B6.3 does not have — but the choice was never really member against non-member. The
sheet is useful in one window, `now ≥ T−15m`, and in that window the situation is `ready`, whose
primary button ADR-0083 already pointed at it. Member-only would preserve `⌘` on `confirmed`,
`full`, `heldSoft` and twenty others so that it can show four dots.

The sheet stays in scope (`UI` §C6) and stays reachable. It has one door instead of two, and the
door is on the card where the code is legible.

**This resolves the defect ADR-0083 found and left where it found it.** The Getting-in sheet on a
match you hold no seat in is no longer wrong, because it is no longer reachable from a card at all.

### `✉` is dropped, and this is a genuine override

**Recorded as one, deliberately.** ADR-0083 and ADR-0086 both departed from a UI authority and both
argued the same defence: *a forced consequence of an out-of-scope ruling, not an override* — the UI
documents are final on what a card looks like and silent on a control whose destination was not
built. ADR-0086 closed by fixing what the other case would require: if the primary slot is ever
taken for a departure, *"it must be recorded as a genuine override."*

Neither half of this decision qualifies for that defence. The Inbox exists, the Getting-in sheet
exists, and no scope ruling touches either. What forces both is an internal finding — §B16's unmask
rule against §B6.1's rung 11, and §1010's tab switch against ADR-0082's tab bar. So this is an
override of a UI authority, on the ground that both controls are **duplicates rather than
casualties**: one duplicates a tab-bar button once per card, and the other duplicates `ready`'s
primary button at the only moment it has content.

The distinction is worth the paragraph. ADR-0083 recorded its own reasoning for keeping it —
reading a departure as an override *"would make every later scope ruling look like a licence to
redraw the UI"*. The converse matters as much: calling a genuine redraw a forced consequence
teaches the next session that the resolution rule has no teeth.

### The clock takes the first slot

One home, whether or not the card has an act. The alternative — *in the button when there is one, on
a line of its own when there is not* — is two homes for one fact, which is the shape this map has
refused for *where*, for *which situation*, and for the act's `target`.

Three other homes were available and refused. The header eyebrow already holds `{sport} · {fmt}` at
`nowrap`. The tag is the tone dot's. The alert slot is conditional and red — routing every counting
card through it would make an ordinary hold expiry look like an alarm.

At 268 px a `ready` card's row is roughly 40 + 168 + 44 with gaps, which fits. On a silent `rescue`
card it is a lone countdown at the left of an otherwise empty footer, which is exactly what ADR-0073
asked for. And it reads correctly in the case
[ADR-0081](0081-a-seat-is-never-taken-until-it-is-paid.md) worried about — *"a card counting 1:30 to
pay under a button offering anything else is two instructions"*. `1:30` immediately left of *Finish
paying* is one instruction.

### The countdown repaints; it never fetches

**One second while under ten minutes remain, one minute above it.** `UI` §G Open Decision 17
recommended *"60 s tick, minute-aligned, driven by server time + monotonic elapsed"*; ADR-0053
already killed half of it — *"`serverTime` has no reader either"* — and the surviving half is wrong
for ADR-0081's five minutes, where `1:30` frozen for a minute at a time is precisely the *"frozen
number reads as broken rather than static"* failure ADR-0053 names. Ten minutes rather than five so
the boundary does not sit on top of the claim's own lifetime.

**It is a repaint, and never a fetch.** [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md)
owns refreshing and names reaching zero as one of its four occasions; a repaint interval must not
become a fifth. The phone still derives nothing but a subtraction, exactly as ADR-0053 permits, and
the format was always the client's under
[ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md).

One screen-wide timer, not one per card, is an implementation note rather than a decision — recorded
because a dozen cards each holding their own interval is the version that gets built by accident.

### The shelf card reaches its act through its body

ADR-0083 fixed that a card with no act has no primary button and *"its body is not a tap target
either"*. The converse was left unstated, and is stated here: **a card's body is a tap target
exactly when the card names an act, and the act code decides where the tap goes.**

So `UI` §B8's `MatchCard` gains no button. Its `data-go="match"` target dies with the match-detail
screen, and `takeSeat` — or `finishPaying`, when a claim is live — replaces it on the same whole-card
target. A button was refused on two grounds: it roughly doubles a compact light-surface row, and
ADR-0068 already records a shelf card as *"nearly full"* on depth at 320pt; and `finishPaying`
overriding `takeSeat` is then one destination swap on one target rather than a second control
appearing.

**The cost is accepted rather than hidden.** The state card reaches its act through a labelled
button and the shelf card reaches the same act through its whole body. That is a real inconsistency
and it is the strongest argument for giving §B8 a button instead. What makes it bearable is that the
two cards were never the same component and never looked alike — one is a dark 268 px status card in
a pager, the other a light row in a feed — and ADR-0070 already fixed that a card is identified by
the thing it is about, so one answer corrects every copy of a match on the screen.

### The shelf card's clock is a claim's clock, and nothing else

ADR-0070's *"every card carries exactly one clock slot"* is unqualified and covers all three card
types; §B8 draws no countdown. No new rule is needed to settle what it should draw, because
ADR-0073's rule already answers it: the clock is *"the next moment at which something happens **to
the viewer** whether they act or not"*, and on a match the viewer holds no stake in, nothing does.
The server already sends an empty slot for an ordinary shelf card. ADR-0081's override already fills
it when a claim is live.

**When it is filled, it replaces the state tone tag** in §B8's footer hairline, rather than joining
it. That row is already two crowded groups — `[fit badge][state tone tag]` left, `[strike
price][payable][· 0 fee]` right — and a third left-hand chip wraps it at 320pt. Replacing is also
the honest reading: while a player holds `1:30` to pay, *Forming* is not the news. The fit badge is
the one element that cannot go, since it is why the shelf ordered the card at all.

### Nothing new crosses the wire

The row's three slots are driven by three fields that **already cross for their own reasons**: the
act code in the spine (ADR-0083, ADR-0087), `mayDepart` in the spine (ADR-0086), and the card's one
clock instant (ADR-0070). No variant flag, no shape code, no new field.

`#60` asked whether the row's shape crosses the wire at all, or is derived from facts the spine
already carries, and named ADR-0053 as the constraint. The line is drawn as a test rather than as an
answer:

> **The server decides whether a control exists. The client decides where it sits.**

This is ADR-0070's own precedent, granted for the tail card in almost these words — *"it derives
nothing about matches, it decides where a tap goes, which it already does for every button on the
screen."* Composing a row from fields the server already sent is layout. Concluding that a player
may leave, or may take a seat, would be a rule, and the phone still holds none.

## Considered options

- **`⌘` member-only, as `#60` proposed.** The obvious answer, and refused above because it preserves
  a control whose content is four dots everywhere it survives. It also buys the second axis for
  nothing: ADR-0086 puts one control on a viewer axis regardless, but that control has something to
  do.
- **Keeping `✉`.** It is the prototype's shape and the UI documents draw it, and dropping it leaves
  twenty-six cards with a completely empty action row — a starker statement of ADR-0083's *"Now
  ships with twenty-seven cards a player cannot press"* than anyone has yet seen on a screen. Taken
  anyway: that is the truth becoming visible, and papering it with a duplicate of the tab bar is the
  patch ADR-0083 explicitly refused — *"it should not be patched with a button that opens something
  irrelevant."*
- **The clock in the header eyebrow.** Refused: `{sport} · {fmt}` is there at `nowrap`, and the
  eyebrow is the one line on the card that stays on the device's clock rather than the club's
  (ADR-0070), so it is the wrong neighbourhood for a moment about the match.
- **A button on the shelf card.** Refused above on depth, and because it would make `finishPaying`'s
  override a control appearing rather than a destination changing.
- **`align-items: flex-start` on the strip.** Refused: a strip whose height changes on every swipe
  moves the shelves below it.

## Consequences

**Easier**

- **The variant question is dead, not answered.** Three optional slots driven by three fields
  replace a shape that had grown from one variant to five in three days. A seventh act or a fourth
  spine boolean changes what is *in* a slot, not how many rows exist.
- **ADR-0073's warning can finally be drawn.** The clock has a fixed place on both card types, and
  it is on the silent cards — `rescue`, `heldSoft`, `formingLate` — that the ADR was argued from.
- **Two defects found and deliberately left by earlier ADRs are closed**, rather than inherited: the
  wrong `⌘` on a card you have not joined (ADR-0083, restated by ADR-0087), and the shelf card's
  act with nowhere to live.
- **The accessibility debt shrinks by removal.** `UI` §1087 records that `✉` and `⌘` have **nothing**
  for a label, and §1042 flags both as 40 × 34, *"under 44 in both axes"*. Both problems leave with
  the controls; the exit control already arrives with a real label and 44 × 44 hit slop under
  ADR-0086.

**Harder**

- **Twenty-six cards now have a visibly empty footer.** Not a button that does nothing — nothing at
  all, held open by a spacer. This is the honest shape of a v1 with no match-detail screen, and it
  is the most conspicuous statement of that cost the product has made so far.
- **This map has now overridden a UI authority outright**, having twice argued that its departures
  were not overrides. The defence is recorded above and it is narrower than it looks — both controls
  were duplicates — but a future session will find three departures and one override and must read
  which is which.
- **The state card and the shelf card reach the same act by different means.** A labelled button on
  one, the whole body on the other. Accepted above; it is the sharpest inconsistency in this ADR.
- **`UI` §B6.3 is now wrong in every element of the action row.** ADR-0083 already made
  `cta?: { label, target }` wrong in both halves; the row's icons, its one structural variant and
  its countdown suffix all go here. Anyone reading §B6.3 for the row will find a description of a
  prototype and nothing that ships.
- **A repaint cadence is now a thing the client owns**, and ADR-0054's *"never on a timer"* is one
  reading away from being contradicted by it. The distinction — repaint against fetch — is stated
  here and nowhere else, and a build agent who conflates them will put Now on a 60-second poll.
