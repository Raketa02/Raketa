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
`#071C24` `#0B2B36` `#24505E`) — they are not in the theme. **The dark screens are two: _It's a
game!_**, on two colours of its own (`yesGroundCentre`, `yesGroundEdge`) that ADR-0167 fences
as the yes screen's alone — the moment that inherited them — **and the drawn splash** every cold
open starts on, on its own pair (`splashGroundCentre`, `splashGroundEdge`) that ADR-0209 fences
as the splash's alone. Neither is a dark mode, and neither is a licence for another dark surface.

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
  no peek has no affordance until something else carries it — always, but for Needs your
  answer's FRIENDS GAME, which draws them from two (`dotsAlone`, #817). The one wider peeking card is
  Needs your answer's request tile, `requestCardRatio` (0.83, the `wide` rail, #816).
- **Two envelopes, one meaning — _someone asked you_.** The round friend button's is `volt`
  with a halo; Home's header's is `ink` Feather `mail` (10.3, #816). Never a third.
- **Colour is picked by meaning:** coral = the one accent · mint = settled · amber =
  reversible, not yet wrong · red = ended badly · info = explanation, not status.
- **§1.2's coral list is closed at six** — primary button, active tab (the tab bar's **selection
  marker**: an opaque `coralSoft` capsule under the lit tab's `coral` icon and `coralInk` label —
  a `coralSoft` fill means _where you are_ on the bar only, ADR-0210 §4, #883), level mark, onboarding
  progress fill, hot tag, the tab bar's badge (the same mark at a segment's size, `CornerBadge`,
  counts a group page's Games, Fill in and You’re in and an Owner's requests on the group's tile —
  one meaning, every surface; on Games, Fill in and You’re in it counts what is **new since you
  last looked**, and the tab on screen draws none, #849, #850). **The tab's menu's selected mark**
  — a `coralInk` circle with `Tick`'s drawn white tick (`TabMenu`, 9.5, #861) — is the _active
  tab_ entry one level down, the current kind being the active sub-tab; not a seventh. A sixth-and-a-half is not a
  taste call: pick the meaning and you will land on `amber` or on `ink`, which is where the
  row stripe and the rail's current dot both landed.
- **The tab bar is the one glass surface** (1.1's exception, 10.2, ADR-0210 §2): `color.glass`
  over a blur on the iPhone, opaque `surface` on Android while `theme.glass.android` is off. It
  draws Ionicons; **every other mark in the app stays Feather**. Neither is a licence for a second
  glass surface or a second family.
- **A `Tag`'s dot is the sport's and only the sport's — except on Home's game card, where it is
  the status's** and the sport is the word beside it (`STATUS_INK`, 6.4 as amended by #413). Under
  both: a dot is always accompanied by its name in text, and one surface gives the token one
  meaning. Urgency elsewhere is the tag's `warn` / `ok` variant, carried by the whole pill.
- **Rule C — white text never sits on `coral` or `mint`** (3.89:1 and 4.07:1). Use
  `coralInk` / `mintInk`. `ink` is the only dark that may sit on coral (4.50:1).
- **`volt` is a fill anywhere and a stroke only on dark.** `ink` on a volt fill is
  13.96:1; volt as a foreground on paper is ~1.3:1, so a volt line, ring or border there
  is invisible.
- **Every number is mono and tabular** — that is what stops a row reflowing when a level goes
  from 2,71 to 2,80. Polish formatting: `38,00 zł`, `2,71`, `65%`, `18:30`.
- **Cards never cast a shadow — with two named exceptions.** Seven shadows exist; five are for
  things that float, and the deck card is one of them because it is not a card. The sixth is
  the club result both group searches draw (`ClubCard`, `shadow.clubResult`, 4.3,
  2026-09-27); the seventh is FOR YOU's line **while it is open** (`FoldingLine`,
  `shadow.openLine`, 4.3, 7.37, #820). Neither is a licence for cards in general. **None is
  tinted**: the tab bar's dock (`shadow.dock`, the deck card's values) took the retired ⚡Play
  disc's coral-tinted slot (#883, ADR-0210 §6).
- **A FOR YOU line draws its content only while open** (`FoldingLine`, 7.37, #820): its size
  changes once and a layout transition moves the frames — never a height animated per frame —
  and a rail inside takes the line's bounds, snapping to its cards.
- **Band `ink` for text and rails**, `tint`/`deep` for the bar only. A printed level range
  always comes from the model's `bandLo`/`bandHi`, never the bar's drawing values.
- **Every state carries a word or a shape**, never colour alone.
- **`eyebrow` labels a region you are reading; `flab` labels a control you are about to
  operate.** They are not interchangeable — and **`eyebrow` is the section heading**, in
  `muted`, uppercase. `h2` titles a card and never a section; five shipped surfaces got this
  wrong before the rule was written down.
- **There is no sans role above `h1` to reach for.** `display` (26/700) existed for the Now
  card's weekday figure and retired with it (#413, Part 16); `yesWord` (32/800) exists for
  _It's a game!_'s one word — the yes screen's, which it inherited — and nothing else (ADR-0167,
  Part 16). A word that wants to be that
  large is a Part 16 decision, not a `fontSize` and not a second use of `yesWord`. `numeral`
  (108/800) is no exception to reach for: it is Top 10's place, a picture of a number behind each
  card and hidden from a listener (#805, 3.3, 7.36) — one use. Nor is `splashWord` (42/800): the
  drawn splash's _Rakieta_, seven letters placed by its geometry, a fixed size whatever the OS
  text size (#855, ADR-0209 §5, 3.3, Part 13) — one use.
- **The pill is the chip's**, and _It's a game!_'s two buttons and the friend pills — Members'
  (#753), the Friends page's (#754), the picker's ask (#758) and the worded friend button's _+ Add
  friend_ (#801) — and Home's Hottest groups chips (#800), through
  `Button`'s `shape`: exceptions, each fenced by a Part 16 row. Everywhere else a button is 10pt.
  **FOR YOU's count pill** (#822, 7.37) is the chip's shape and no control — a figure, `line2`
  under `muted` mono — fenced to FOR YOU's lines; it is not `CountBadge`, which says _new_.

This design system covers `frontend_player/` **only.** The club app has its own; the palettes
converge because it is one brand, but the values are never shared.
