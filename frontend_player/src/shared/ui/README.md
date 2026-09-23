# `src/shared/ui/` — design-system primitives

The player app's design system, in code. Generic and feature-agnostic: if something here
starts to know about courts, bookings or matches, it belongs in a feature instead.

**The rules live in [`../../../docs/design-system.md`](../../../docs/design-system.md).**
Read it before adding anything here — in particular its Part 0, which separates the
prototype's _harness_ from the product. The decision is
[ADR-0012](../../../../docs/adr/0012-player-app-design-system.md).

## `theme.ts` — the source of values

Every colour, type role, spacing step, radius, metric, shadow and duration. Frozen,
typed, and imported directly by components:

```tsx
import { StyleSheet } from 'react-native';
import { theme } from '@/shared/ui/theme';

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    padding: theme.space.md,
    marginBottom: theme.space.sm,
  },
});
```

A literal in a component — `'#E8482B'`, `fontSize: 12`, `padding: 10` — is a bug. If a
value you need genuinely does not exist, that is a change to `theme.ts` **and** to the
design-system doc, in the same commit.

## Four React Native traps this system exists to prevent

1. **`fontWeight` is ignored on Android** when a custom `fontFamily` is set. Weight is a
   _family name_: use `theme.font.sans[700]`, never `fontWeight: '700'`. This is the most
   common way an RN app silently loses its typography on one platform.
2. **`letterSpacing` and `lineHeight` are in points**, not em or multiples. `theme.type`
   and `theme.num` carry pre-converted values — never re-derive them.
3. **Touch targets.** Nothing tappable may have a reachable area under **44 × 44pt**. The
   visual stays small; use `theme.hit.*` to grow the target.
4. **There is no hover.** Every pressable declares its pressed appearance explicitly —
   see the design system's 6.6.

## Non-negotiables

- `line` **bounds a thing**; `line2` is a **fold inside one thing**.
- **9 between stacked cards, 15 at the gutter.** Everything else from the 3pt grid.
- **Rule C:** white text never sits on `coral` or `mint` — it needs `coralInk` or
  `mintInk`. `ink` is the only dark permitted on `coral`.
- `volt` is a fill anywhere and a stroke only on dark — on paper it is ~1.3:1 as a
  foreground and 13.96:1 as a bed for `ink`. A stroke on paper that **means** volt is
  `voltStroke`, which is `coralInk`'s relationship to `coral`: one meaning, a second value,
  because the base colour cannot carry the role. It is not a `*Line`, which in this palette is
  a soft's border, and volt has no soft.
- **Cards never cast a shadow.** Five shadows exist; all are for things that float, and
  the deck card is one of them because it is not a card. The fifth, the ⚡Play disc's, is
  the only one that is a colour rather than a dimming — and only on iOS.
- **Every number is mono and tabular.** That is the mechanism that stops a row reflowing
  when a level changes from 2,71 to 2,80.
- **Every state carries a word or a shape**, never colour alone.
- **Content width is screen width − 30.** Never a fixed 362 or 392 — those are the
  prototype's phone picture.
- Band **`ink`** for text and rails; `tint`/`deep` for the bar only.

## Fonts

Archivo (400–800) and IBM Plex Mono (400–600), loaded with `expo-font` in the root layout
and **awaited before the splash screen hides** — a font that arrives late reflows every
number on screen.

## Components are built with the features that need them

This folder is deliberately not pre-populated, with one exception worth knowing: the
**match card**, the **state card**, the **level bar** and the **popover** are shared
components from the start. The prototype maintained a second copy of each in its deck and
recorded that they had drifted — one implementation, used everywhere.

Built so far, by the onboarding slice: `Button`, `Card` (+ `PressableCard`), `Note`,
`Bar`, `ScreenHeader`, `Tag`, `Chip`, `Hairline`, `BottomSheet`, `CloseControl`,
`DarkCard`, `Row`, `LevelBar`, `ConfidenceRing`, `Popover` (+ `InfoMark`), `InfoGlyph`,
and by the second part's photos step: `PhotoRow` with `PhotoTile`, `PhotoAddTile` and
`PhotoPosterTile`, plus `CourtPoster`; and by its availability step: `AvailabilityGrid`
with `Tick`; and by sign-up's age question: `TickBox`; and by Play: `TabBar`, `Switch`,
`FitPill`, `BalanceBar`, `Court`, `Meter`, `Segment` and `Toast` with `ToastHost`; by the
chat map: `TextField` (6.13, which auth's four boxes moved onto in the same commit) and
`PagerDots` (7.18, Now's rail); ahead of the record sheet: `SocialTagRow`, `RunOfForm`, and
`PhotoPanel` with `PlayerPhoto`, `OnCourtMark` and `courtPosterFor` under it; and by the
sportsmanship card: `StarRow` with `Star`; and by the Chats list's _Leave the game_: `SwipeRow`
(6.15), a row that slides left on `PanResponder` to reveal one control, with its arithmetic in
`swipeRowGeometry.ts`; and by the You tab: `DoorRow` (5.5 as amended, Part 16 2026-09-17), a
fact with a screen behind it — a `paper2` lead square with a Feather glyph, a title, a **live**
line off a read and a chevron, spoken as _title, live line_; what a row says while its read is
on its way or has failed is `shared/errors`' `liveLine`, because a read's standing turned into a
sentence is an errors concern and not a drawing. `DarkCard` gained `PressableDarkCard` for the
tab's header card, as `Card` has `PressableCard`. Import them from `@/shared/ui`.

**`ConfidenceRing` is drawn at three diameters now, and it is one ring.** 7.8's 72 on the result
card and the passport; `ringSm` (56) in the You tab's header card, printing the Player Score with
`SCORE` beneath; `ringLg` (74) on the reliability screen, with the tone ladder's word beside it
and nothing beneath (Part 16, 2026-09-17; ADR-0179 §1–§2). The `size` changes the diameter and
nothing else — one stroke, one tick, one overshoot, one type role for the figure — and the
caller may hand the `figure` to print, because a Player Score is out of a hundred and not a
percentage. The `label` beneath became optional for the reliability screen's reason.

**Six of those arrived by promotion rather than by being built here**, and the promotion is the
interesting half ([#375](https://github.com/Raketa02/Raketa/issues/375),
[#384](https://github.com/Raketa02/Raketa/issues/384)). Five were the competitive candidate
card's and one was the profile photos step's, and the record sheet draws all six
([#373](https://github.com/Raketa02/Raketa/issues/373)): copying any of them would be a second
thing to keep in step — `RunOfForm`'s three contrast ratios are **pinned** in
`recordSquares.test.ts` and `OnCourtMark`'s cap is derived per panel in `onCourtMarkFit.test.ts`,
and a second copy of either would be values those tests never see — and importing them out of
`features/play/` would point the arrow the wrong way for a feature that is not Play's sibling by
accident. `PlayerPhoto` also **lost the word _candidate_ on the way down**: a candidate is Play's
name for a row a search returned, and what the switch draws is a player. **What came down is the drawing and the shape it takes; what stayed is the
rule.** `play/domain/socialTagOverlap` reads the row's four answers off a **candidate**, which is
a search result and Play's alone, and hands the value down — so a second surface serves its own
and neither re-derives the other's. `RUN_OF_FORM_FILL` is exported for the same reason
`BALANCE_INK` and `FIT_HIGH` are: the ratio a drawn object is held to is derived off the drawn
object, never off the token it happens to use today.

**`StarRow` is 6.13, and it is here for the reason `Tick` is rather than for a second
caller's.** It is the sportsmanship card's alone today
([#386](https://github.com/Raketa02/Raketa/issues/386)), and a control with a touch rule, a
press state, a fill pair and three pinned contrast ratios is a design-system object whether or
not two features draw it — the same standing `AvailabilityGrid`, `RadiusSlider` and `TickBox`
have, each with one caller. `STAR_FILL` is exported for `RUN_OF_FORM_FILL`'s reason, and it is
**that same pair**: `ink` given against `muted` blank, taken deliberately so that _tell two
states of one mark apart_ has one answer in this system rather than two, with its three ratios
re-derived on `surface` in `starRow.test.ts` because 2.5 states fixed pairs and a ground is
half of one. The star is **drawn** rather than typed, which `Tick` already argued — geometry
does not scale with Dynamic Type and does not vary by platform font — with one addition that is
this component's own: **Archivo ships no U+2605** and ADR-0135 fixed the icon family as Feather,
which has no filled counterparts, so a five-star row is precisely the case where there was
nothing to type. What it deliberately does **not** own is what a second press means: it reports
every press with the value pressed, exactly as 6.8's cell fires whether or not it is ticked, and
clearing is a rule about what an answer is.

**`Segment` is 6.3, specified since the document was locked and built only now.** Its own
closing line is why it exists in that shape — _"nothing uses it today; it is specified so the
first screen that needs one does not invent a second shape"_ — and Play's two ways through the
tab are that screen. It is a **`button` carrying `selected`**, exactly as the chip is, and
never a `switch` carrying `checked`: nothing in Part 6 carries `checked` on a _mode_, and 6.3
_"picks one of several"_. The selection is a **lightness** step on the surface with a matching
one on the label, so it is not colour alone, and every press is reported including a press on
the segment already chosen — Play's _Find a game_ half re-enters the tab, which is arriving
rather than doing nothing. Its label is a whole string rather than a name plus a count slot,
because anything beyond a name is copy and belongs to the feature that has something to say —
Play drew _Match me · 3_ through that string and has since struck the number, which is a change
of copy and not of this primitive.

**The five Play arrivals** are `Switch` (6.12), `FitPill` (7.10), `BalanceBar` (7.11),
`Court` (7.12) and the availability grid's **diff variant** — and none of them reclaims a
deleted section number, because a number in the design system never moves. Two of them are
returns: the fit badge and the balance bar went with the engines that fed them in the
2026-08-25 reset, and both engines ship again. **7.10 restates the scale it is against** —
Fit is out of 100, and the step at 90 is the top tenth of it — because Part 17 warns in
writing that the deleted 7.1's threshold named a scale the deleted engine defined.
**7.11 ships one scale where the prototype had three clamps**, which is the same defect the
level bar and the confidence ring exist to prevent. **The court takes children in seat
order**: a hook returning the coordinates is geometry that gets adjusted at one call site and
not the other, and squash's seats are why they cannot be derived at all — there is no net, so
the far side is not the near side reflected. **The diff variant is the grid, not a second
file**, with three shapes where the prototype had a volt ring and 45% opacity: colour as the
only signal twice over, and volt on paper is 1,3:1 besides. `Tick.tsx` grew `Plus` and `Dash`
for it, in the same 12 × 12 box at the same 2pt stroke.

**Meter and bar are 7.3's two rows, and they are opposite objects.** A `Bar` states a
fraction to a screen that names its denominator, and reports one through
`accessibilityValue`. A `Meter` visualises a number the row beside it has **already
printed** — the why-fit row draws `×{weight} → {value}` two words earlier — so it is
**hidden from assistive technology and takes no label at all**: a bar over a printed number
is the double announcement 6.8 hides its column heads to avoid (`the-words.md` §20.8). There
is no prop to pass one through, which is what stops somebody helpfully adding
`accessibilityRole="progressbar"` and having every row announced twice.

**The meter's fill takes a `tone` and the ladder does not come with it.** Three steps in an
existing fill — `mint` · `night` · `red` — because the record card stacks three metered rows in
one column where the why-fit sheet draws one fill for all of them
([#385](https://github.com/Raketa02/Raketa/issues/385)). What the component deliberately does
not hold is **where** a figure turns poor: that is a fact about the figure and belongs to
whoever knows what it means, which on the record sheet is the same rule that tints the
reliability pill above the card. A meter that banded its own share would be a second opinion,
and the screen would eventually show a green bar under a red pill for one ratio. `METER_TONE_FILL`
is exported so `meterTone.test.ts` derives the ratios off the component rather than off the
theme — and the pair bound there is stated in `L*` rather than as a contrast ratio, because
three fills that each clear their track cannot also be 3:1 from one another.

**Two OS questions, one collapse.** `overlay.tsx` reads reduced motion **and** whether a
screen reader is running, and `useCollapsedPresentation()` is the single condition either
satisfies. They are not synonyms: a player may have VoiceOver on and reduced motion off,
which is the common case, and a surface that asked only about motion would run its full
animation in front of the one person who gets none of the craft and all of the latency
(`the-words.md` §20.11). `useLiveRegion()` beside them is the same announcement mechanism
`ToastHost` uses, for a value that changes while focus is somewhere else — §20.9 names three
such regions in the Play tab and no fourth.

**Reduced motion is a context, and the screen reader is not.** `ReducedMotionProvider` is
mounted once in `src/app/_layout.tsx` and `useReducedMotion()` reads it — a hook per consumer
meant an `AccessibilityInfo` listener per consumer, which was fine for two overlays and is not
for the Play tab's always-mounted surfaces (a press transform, the fill's staggered seats).
Outside a provider it reads `false`, which is what the app looked like before anybody asked for
calm; a test that wants a tree in reduced motion passes `value` rather than mocking the OS,
which is Part 13's own shape for a port's context.

**Overlays.** `BottomSheet` and `Popover` are both real modals, and 9.1's and 7.6's "it is
a real modal" is three separate obligations rather than one prop — read `overlay.tsx` and
either docblock before adding another. Play's `SearchingLatch` is the third and lives in its
feature rather than here, because it is one screen's wait rather than a primitive; it answers
the same three obligations and records the one it answers differently — it moves no focus,
having nothing to focus and nobody choosing to leave it. Two of them are the caller's: the screen behind
spreads `behindOverlay(open)`, and the overlay is rendered as that screen's _sibling_,
never inside it. `CloseControl` is 9.1's close circle, shared because the header control
that opens a sheet, the sheet's own close and the popover's are the same 28pt object;
`InfoGlyph` is shared for the same reason between the info note and the popover's mark.

**The toast is the third overlay and the first that needs 9.3's host.** `ToastHost` is mounted
**once**, as a sibling of the route tree in `src/app/_layout.tsx` — `zIndex` is scoped to the
parent in React Native, so a toast raised from inside a card renders inside that card. The
queue is `shared/store/toast.store.ts` rather than a feature's, because a queue inside a
feature is that feature owning every other feature's toasts. It shows **one message at a
time**: the announcement is queued, and three sentences on screen while a listener is read one
is the two channels disagreeing. The **dismiss is the hold** — 9.2's `pointerEvents: 'none'`
is what keeps a toast from eating a press, and a close control inside one is exactly that
press. Nothing about it animates, so there is no reduced-motion branch. `announce()` in
`overlay.tsx` is Part 13's amendment: every toast announces **queued**, and the send
confirmation is the one message that interrupts.

**Drawn objects.** `LevelBar` (7.5) and `ConfidenceRing` (7.8) are geometry, not styling —
their values are `theme.size.levelBar` and `theme.size.ring*`, and both keep a fixed scale
(1,00–5,00 and 0–100) so a value lands in the same place on every screen that draws one.
Both take a `variant`/repaint for the dark card, because React Native has no colour
cascade.

**The tick box** (6.11) is one box and one claim beside it, for a statement a player either
makes or does not. It **borrows the availability cell rather than inventing a second ticked
thing** — same 20 → 12 geometry, same `Tick`, same fill inversion — and the whole row is the
target, because a 20pt square is well under the touch minimum and a label outside the
control is a word beside the thing to hit. It takes `checked` and **has no default for it**:
a box that arrives ticked is a claim the player never made, and that is the entire reason the
component exists. The words are the caller's.

`Tick` is 6.8's mark extracted, because two controls now draw it and a second copy of a
12 × 12 path is exactly the drift this folder exists to prevent. It takes **no props**: a
tick is only ever drawn on the `ink` fill 6.8's selected state inverts to, so `surface` is
the only colour there has ever been, and it is held there once with its contrast figure.

`CourtPoster` (6.9) is the third, and the one with **no size at all**: the composition is
described in `viewBox` units and the caller gives it a box, so one drawing serves a 90pt
tile and a 27pt avatar. It draws a player — three poses, flat, in `ink`, with **no face and
no likeness** — over a two-stop gradient on one of the sixteen hues in `POSTER_HUES`, and
`hue` is the **one colour prop in this system that does not come from `theme.color`**
(ADR-0134). Both choices are `courtPosterFraming`'s, beside it: the design system's contract
is that one player id produces one poster, and the hash that decides which is a promotion out
of `player_profile/` made once four surfaces drew other people's posters — one person in two
colours on two screens is exactly the drift a second copy of that hash would produce. Its
gradient id comes from `useId()` and never from data — the prototype composed it from the
player id and the width, so a screen drawing one person twice emitted duplicates. It,
`ConfidenceRing` and `Tick` are what need `react-native-svg`.

**The photo tile** (6.9) is a row before it is a tile: `PhotoRow` is always three slots
wide and pads itself with undrawn space, which is where the ceiling lives — at three photos
there is no add control on screen rather than a disabled one. Every word on it is the
caller's, because the step that collects photos and the profile editor that will change
them do not say the same things.

**The availability grid** (6.8) is seven days by three parts of the day on a card that also
holds its footnote, and **days are rows because seven columns cannot be reached** — seven cells
at the 44pt minimum want 308pt against the 290pt of content the narrowest phone has, and the
widest phone in the population does not close it either. Turned this way a cell is 44 tall by
its own geometry and 59,5 wide inside the card, the first control in the app that reaches the
touch minimum in both axes without being granted a `hitSlop`; `profileControlGeometry.test.ts`
pins that division **and the 15,5pt of margin the card left**, because that margin is small
enough that padding added elsewhere could spend it. A cell is the only pressable thing on it —
there is no row, column or _weekends_ shortcut anywhere in the component — and its selected
state is a fill **and** a tick: `paper2` to `mint` is a 3,39:1 luminance step rather than a
change of hue, and the tick is what stops twenty-one squares differing only in lightness
reading as a texture. Every word is the caller's.

**The radius slider** (6.10) is one number on a track, and **the row is the control rather
than the thumb**: a press anywhere on its 44pt reaches the value at that point, which is
what gets it to the touch minimum with no `hitSlop` and what stops a tap at the far end of
the track doing nothing. It is `adjustable` with an `increment` and a `decrement`, because a
drag-only slider is unusable with a screen reader and with a keyboard, and it announces the
figure and the plain words as **one** value — the two are one fact drawn twice, and both are
hidden from assistive technology here so they are not read a second and a third time. It knows
**no step and no default, and no bound of its own**: the range it announces and the position
it draws both arrive as props, because those four numbers are served and product's to
retune — what reaches the component is where the thumb goes and what the figure says.

**The text field** (6.13) is one control in two shapes — a **one line** capped by the caller's
`maxLength`, and one that **grows an `rlValue` line at a time to a cap** and then scrolls — and
they are one component because they differ by a number rather than by what they take. Its cap is
a count of **lines** and it belongs to the caller: neither surface that needs a growing field has
been drawn on a phone, so what the design system owns is the arithmetic, one line per step with
the box's padding derived so that one grown line **is** the one-line box. The **field** is the
touch surface, not the input — the box alone is 42 against a 44 minimum, and a grown box's value
is 16pt tall inside 13pt of padding — so a press anywhere on the label, the box or the message
moves the caret in, and at 57 the control clears the minimum on its own geometry with no
`hitSlop` granted. The label is a real `Text` bound by `accessibilityLabel` and never a
placeholder, and it is always drawn: the field that wants the **name without the drawing** is the
composer, and that prop arrives with it. **The reveal is the field's**, named for the field it
operates on, so a sign-up form's two password boxes are not two buttons both called _Show_, and
it dims by 6.6's `.7` rather than the `.6` it was drawn with in `features/auth/`. Android is told twice
— `includeFontPadding: false` and `textAlignVertical: 'top'` — because a line box is taller there
than `lineHeight` and a multiline value is centred rather than topped, and both are properties
iOS ignores.

**A feature never keeps a second copy of one of these.** If a primitive does not do what
a screen needs, extend the primitive — the one auth-form control that remains in
`features/auth/components/AuthNotice.tsx` is there because the design system genuinely
specifies no _ended badly_ note variant, and it says so in place. The field beside it left
for 6.13, and the placeholder button before that for `Button`.

**The tab bar** (10.2) is the app's bottom chrome, and it is the drawn object only — it
takes the active tab and a press handler and knows nothing about routes or stacks. **Its
inventory of five is its own** rather than a prop, because
[ADR-0135](../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)
fixes the family and the five names, and because `theme.size.tabBar.labelMaxScale` is derived
from exactly those five words in exactly five columns — a caller that could pass a sixth tab
could invalidate the cap without anything saying so. Feather from `@expo/vector-icons`,
selection **in tone alone**, and the ⚡ is Feather `zap` rather than the character `⚡`,
which carries `Emoji_Presentation=Yes` and would render in a colour this app does not choose.
The bar owns the bottom safe-area inset; a CTA above it owns none.
