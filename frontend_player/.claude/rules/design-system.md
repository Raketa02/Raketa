---
paths:
  - 'src/shared/ui/**'
  - 'src/features/*/components/**'
  - 'src/app/**'
---

# Design system — locked

The visual language was designed and audited before the app existed. Full rules:
[`docs/design-system.md`](../../docs/design-system.md) (3300+ lines). The decision and its
corrections: [ADR-0012](../../../docs/adr/0012-player-app-design-system.md).

Three artefacts that **change together, in the same commit**:

| File                                        | Is                                                            |
| ------------------------------------------- | ------------------------------------------------------------- |
| `src/shared/ui/theme.ts`                    | The source of every value. Read via `StyleSheet.create`.      |
| `docs/design-system.md`                     | The rules.                                                    |
| `docs/design-system-v34-prototype-audit.md` | Archived measurement of the web prototype. **Not the rules.** |

## What to read, and when

You are not expected to read the rules document end to end — and "it was long" is not a
reason to skip it.

| When                                        | Read                                                                                                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Every time you touch a rendered surface** | [Appendix B — quick reference card](../../docs/design-system.md#appendix-b--quick-reference-card). ~20 lines. The floor.                             |
| **Once, before your first component**       | [Part 0](../../docs/design-system.md#part-0--reading-a-web-prototype-as-a-native-app) and [`src/shared/ui/README.md`](../../src/shared/ui/README.md) |
| **Building a specific surface**             | Part 5 primitives · 6 controls · 7 data display · 9 overlays · 12 screens                                                                            |
| **A value you need does not exist**         | [Part 15 — extension guide](../../docs/design-system.md#part-15--extension-guide). Extend deliberately; never invent beside the system.              |

ESLint rejects hex and `rgb()`/`rgba()` literals and the `fontWeight` property outright, so a
component that ignores the theme fails `pnpm lint` rather than review.

## The prototype is a web page. This app is not.

The audit describes an HTML file, and **its phone frame, dark stage, scenario rail, time bar
and 900px breakpoint are harness — they do not ship.** The app _is_ the phone. Never build a
frame, a stage or a scenario switcher, and never use the four stage colours (`#08222B`
`#071C24` `#0B2B36` `#24505E`) — they are not in the theme. **The one dark screen is the yes
screen**, on two colours of its own (`yesGroundCentre`, `yesGroundEdge`) that ADR-0167 fences
as that screen's alone; it is not a dark mode and not a licence for a second dark surface.

## The four React Native traps

1. **`fontWeight` is ignored on Android** with a custom `fontFamily`. Weight is a family
   name: `theme.font.sans[700]`, never `fontWeight: '700'`.
2. **`letterSpacing` and `lineHeight` are points**, not em and multiples. `theme.type` and
   `theme.num` carry pre-converted values — never re-derive from the audit's em figures.
3. **44 × 44pt minimum reachable area** on everything tappable. Keep the visual small, grow
   the target with `theme.hit.*`.
4. **There is no hover.** Every pressable declares its pressed appearance explicitly.

## The rules an agent gets wrong

- **`line` bounds a thing; `line2` is a fold inside one thing.**
- **9 between stacked cards · 15 at the gutter.** Everything else from the 3pt grid.
- **Content width is screen width − 30**, and a **peeking** rail card is
  `0.74 × content width` — never a fixed 362 or 268. Those are the prototype's phone picture.
  A **paging** rail takes the content width whole and draws 7.18's dots, because a card with
  no peek has no affordance until something else carries it.
- **Colour is picked by meaning:** coral = the one accent · mint = settled · amber =
  reversible, not yet wrong · red = ended badly · info = explanation, not status.
- **§1.2's coral list is closed at six** — primary button, active tab, level mark, onboarding
  progress fill, hot tag, Chats badge. A sixth-and-a-half is not a taste call: pick the meaning
  and you will land on `amber` or on `ink`, which is where the row stripe and the rail's
  current dot both landed.
- **A `Tag`'s dot is the sport's and only the sport's — except on the Now card, where it is the
  stage's** and the sport is the word beside it (`STAGE_DOT`, 6.4 as amended by #413). Under
  both: a dot is always accompanied by its name in text, and one surface gives the token one
  meaning. Urgency elsewhere is the tag's `warn` / `ok` variant, carried by the whole pill.
- **Rule C — white text never sits on `coral` or `mint`** (3.89:1 and 4.07:1). Use
  `coralInk` / `mintInk`. `ink` is the only dark that may sit on coral (4.50:1).
- **`volt` is a fill anywhere and a stroke only on dark.** `ink` on a volt fill is
  13.96:1; volt as a foreground on paper is ~1.3:1, so a volt line, ring or border there
  is invisible.
- **Every number is mono and tabular** — that is what stops a row reflowing when a level goes
  from 2,71 to 2,80. Polish formatting: `38,00 zł`, `2,71`, `65%`, `18:30`.
- **Cards never cast a shadow.** Five shadows exist; all are for things that float, and
  the deck card is one of them because it is not a card. The ⚡Play disc's is the only
  tinted one, and only on iOS — Android's `elevation` cannot be coloured.
- **Band `ink` for text and rails**, `tint`/`deep` for the bar only. A printed level range
  always comes from the model's `bandLo`/`bandHi`, never the bar's drawing values.
- **Every state carries a word or a shape**, never colour alone.
- **`eyebrow` labels a region you are reading; `flab` labels a control you are about to
  operate.** They are not interchangeable — and **`eyebrow` is the section heading**, in
  `muted`, uppercase. `h2` titles a card and never a section; five shipped surfaces got this
  wrong before the rule was written down.
- **There is no sans role above `h1` to reach for.** `display` (26/700) existed for the Now
  card's weekday figure and retired with it (#413, Part 16); `yesWord` (32/800) exists for the
  yes screen's one word and nothing else (ADR-0167, Part 16). A word that wants to be that
  large is a Part 16 decision, not a `fontSize` and not a second use of `yesWord`.
- **The pill is the chip's**, and the yes screen's two buttons through `Button`'s `shape` —
  the one exception, fenced. Everywhere else a button is 10pt.

This design system covers `frontend_player/` **only.** The club app has its own; the palettes
converge because it is one brand, but the values are never shared.
