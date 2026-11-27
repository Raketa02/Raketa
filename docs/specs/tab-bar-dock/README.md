# The tab bar dock: the record, its brief and its mocks

**What PRD [#878](https://github.com/Raketa02/Raketa/issues/878) is drawn from.** The player app's
tab bar stops ending the screen and floats over it as a rounded piece of frosted glass. Its three
tabs are equal: **Home**, **Play** and **You**. The lit one sits in a soft coral capsule, **the
selection marker**, which travels to the tab you press.

The PRD comes from three sources:
- the product owner's brief;
- its three mocks;
- the grilling held on them on 2026-11-24 (Q1–Q26).

They are copied here from the product owner's own folder, `7.refactor_menu`, so every session can
read them. Landed by [#879](https://github.com/Raketa02/Raketa/issues/879) on 2026-11-25.
**Decided, not yet built.**

| File | What it holds |
| --- | --- |
| [menu_refactor.md](menu_refactor.md) | The product owner's brief, verbatim. Its mock paths point at their own desktop, so read each mock by the [index](#index)'s original name. The folder's `menu_refactor.pdf` holds the same text and isn't copied |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim. It holds every ruling with its reason; the facts it rests on (§2, with `file:line` positions as of 2026-11-24, the A32 measurements, and the contrast and overshoot computations); the docs and tests it reaches; and the question index Q1–Q26. Its status line and delivery section (§15) predate PRD #878. Its §12 lists five calls made while writing, all taken up by the PRD; the spec folder its call 5 suggests is this one |
| [`mocks/`](mocks/) | The 3 mocks, renamed by what they show and numbered 1 to 3 (the [index](#index) gives each original name) |
| [a32_spike.md](a32_spike.md) | The A32 spike's record ([#880](https://github.com/Raketa02/Raketa/issues/880), 2026-11-25): T1–T3 on debug native and release builds, with every A/B's numbers and run counts, the blur's strength, and what the spike learned for #883–#885. Its renders are in [`spike/`](spike/). They are measurement evidence, not mocks |

**The record is [ADR-0210](../../adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md)**,
*the tab bar floats as glass, and its selection travels*. It changes four things in the design
system:
- **§1.1**, *Paper, not glass*, gains an exception: the bar is the one glass surface;
- **§1.2** gains a third line: a `coralSoft` fill means *where you are*, on the bar only;
- **§10.1**'s flex sibling is reversed;
- **[ADR-0135](../../adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)** is superseded for
  the bar only: Ionicons, with selection shown by marker, shape and tone.

It also retires the ⚡Play disc, adds the app's first spring, and stands the bar down on Android
while the keyboard is up.

**Its §7, Android's material, was completed by the A32 spike**
([#880](https://github.com/Raketa02/Raketa/issues/880)) on 2026-11-25: **Android draws no glass**,
so its dock is opaque `surface`, and the blur's strength is intensity 100. The slide's stutter
while a tab mounts was confirmed, and its remedy is
[#886](https://github.com/Raketa02/Raketa/issues/886). The spike's numbers, its builds and its run
counts are in [a32_spike.md](a32_spike.md). Where the log and PRD #878 disagree, PRD #878 wins. Where either
disagrees with ADR-0210, the ADR wins.

**The ADR corrects the log in four places**, and the log is left verbatim:
- **The fit (§4):** the log takes the label's line at the 1.6 cap as 20.4, which is the old 1.7
  cap's figure. At 1.6 it is 19.2, so the sums are 38.2, 40.2 and 42.2, and the badge's top at the
  cap is 2.9, not 2.3. The verdict, 18 with 16 as the fallback, is the same.
- **The glass (§5):** the log takes `night` as the darkest thing under the dock. An `ink`-filled
  control or a dark photograph is darker, and over those 88% gives 4.49 and 4.44. 90% clears black.
  That is left to the product owner.
- **The keyboard (§7):** `shared/lib/platform/keyboard.ts` already exists. The reading joins it
  rather than a new port.
- **The Administrator:** the Administrator's area shell writes the reach and stands down for the
  keyboard too.

**This folder holds the record, not the spec.** The design system's §1.1, §1.2, §10.1 and §10.2
carry a *decided, not yet built* note today. Their text is rewritten with `theme.ts` by the tickets
that build each part:
- [#881](https://github.com/Raketa02/Raketa/issues/881), the bar floating with today's look, and
  every tab screen ending at its reach;
- [#882](https://github.com/Raketa02/Raketa/issues/882), Android's keyboard stand-down;
- [#883](https://github.com/Raketa02/Raketa/issues/883), the glass dock with the marker standing
  still;
- [#884](https://github.com/Raketa02/Raketa/issues/884), the marker's motion.

[#885](https://github.com/Raketa02/Raketa/issues/885) is the phone walk.

The player glossary ([`frontend_player/CONTEXT.md`](../../../frontend_player/CONTEXT.md)) has
**selection marker**, and its **The shell** carries the note. The root glossary's *Home — the first
tab of the bottom bar* is unchanged. *Tab bar* and *selection marker* are UI vocabulary, not domain
terms.

## The ground rule: the mocks lead the design, but no number is taken from a mock

**The mocks lead on design.** In the brief's words:

> *"The design from the mock references is priority so if you have to create new adr or update
> then do it."*

**No number rests on a mock.** Also in the brief's words:

> *"Do not take decisions based on mocked data and mock sizes. Any decision is based on real
> evidences."*

1. **The mocks show intent:**
   - a rounded dock floating clear of three edges;
   - three equal columns of an icon over a label;
   - outlined idle icons;
   - the lit tab filled and coral in a soft capsule;
   - the bolt drawn filled in both states;
   - Play as an ordinary column, without the raised disc.
2. **Every size, colour and timing comes from the evidence the log records.** That evidence is the
   brief's text, today's code, the theme, a computation shown in the log, or a measurement owed to
   the spike. Where the brief's own text gave a number that the evidence moved, the evidence won,
   and the user agreed:
   - lifted 10 → **12**;
   - pill 76 → **75**;
   - two-thirds glass → **88%**;
   - coral at 13% → **opaque `coralSoft`**;
   - a coral label → **`coralInk`**.
3. **Their data is only data.** No rule is read off mock 2's screen: its game card, *Ogrody 33*,
   *Kuba*, the result, the counts, *#7*, the FOR YOU rows and the *New in Rakieta* line. The brief
   says so itself: *"Do not take anything into account from the following mock apart from the
   bottom menu."*
4. **What the mocks draw that is not built:**
   - **the selected label in bright `coral`.** It is `coralInk`, because `coral` on `coralSoft` is
     3.38:1, below 4.5:1 for a 9.5pt word (the log's §6);
   - **the mocks' own sizes**, which are pixels in an image, not points on a phone.
5. **Cite a mock by this folder's number**, for example *dock mock 3*.

## Which mock shows what

| # | Mock | What it illustrates | What is not built |
| --- | --- | --- | --- |
| 1 | The dock | The dock on its own, **Home** lit: a rounded slab clear of the edges, a filled coral house in a soft coral capsule, and Play's bolt and You's figure in grey. Play's bolt is filled though Play isn't lit | The bright coral label; the drawing's sizes |
| 2 | The Home screen | The dock on a whole screen, to show its size and place against a real page: inset from both sides and lifted off the bottom | Everything above the dock, which is mock data (the brief's own words) |
| 3 | Play selected | **Play** lit: the bolt coral in the capsule, Home's house and You's figure as outlines. There is no disc. Added during the grilling's Q6, which retired the disc | The bright coral label; the drawing's sizes |

**No mock draws:**
- content passing under the dock, light or dark (Home's game card under the glass);
- Home's badge on the house;
- the marker in motion: the slide, the stretch, the overshoot, a retarget or the colour-in;
- Reduce motion;
- the dock standing down for the chat or the Android keyboard;
- the opaque Android fallback;
- the Administrator's two-column dock;
- a 320 phone or the largest text size.

Each is decided in the log and PRD #878, and designed by the ticket that builds it.

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_dock.png`](mocks/01_dock.png) | `1_menu component.png` |
| 2 | [`02_home_screen.png`](mocks/02_home_screen.png) | `2_bottom_menu_home_sceen.png` |
| 3 | [`03_play_selected.png`](mocks/03_play_selected.png) | `3_bottom_menu_play_selected.png` |

The log's §12 call 5 suggested `01-dock.png`, `02-home-screen.png` and `03-play-selected.png`.
The files follow the other spec folders' `01_name.png` instead.
