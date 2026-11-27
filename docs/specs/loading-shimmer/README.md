# The loading shimmer: the record

**What PRD [#867](https://github.com/Raketa02/Raketa/issues/867) is drawn from.** Where a screen
has nothing to draw yet, grey shapes stand where its content will be, at its real sizes, and one
soft band of light sweeps across the whole screen. This covers Home, Rankings, the four See all
screens and the group page. The content is revealed with one 200 ms cross-fade: all together, or
from the top down once a 2.5 s ceiling has passed. Home's reads set out while the splash plays, and
Rankings' *You · 212th* button says *Finding you…* while it reads the page around the player. The
PRD comes from a grilling held on 2026-11-24 (Q1–Q27: three rounds, then one late question on the
shimmer's own frame cost). The log is copied here from the product owner's own folder,
`6.loading_shimmer`, so every session can read it. Landed by
[#868](https://github.com/Raketa02/Raketa/issues/868) on 2026-11-24.

**There is no brief, and there are no mocks.** The request was three sentences, quoted at the top
of the log, and the grilling worked from those. **The log is the source.** Every look, number and
rule in the PRD comes from it. Its ground rules say where each number comes from: the code, the
theme, a primary source, or a measurement still owed. None was picked by taste.

| File | What it holds |
| --- | --- |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6). It holds every ruling with its reason, and the facts the rulings rest on (§2, with `file:line` positions as of 2026-11-24). It also holds the research behind the reveal (§2.7, Q11), with Facebook Shimmer's defaults read from its source, plus the tests the work reaches (§15), the checks owed on a phone (§16) and the question index Q1–Q27. Its status line and its delivery section (§14) predate PRD #867. Its §2.4 and §13 find ADR-0209's first 2026-11-24 amendment uncommitted; #868 committed that amendment before adding its own. Its §12 lists three calls made while writing, and PRD #867 takes up all three |

**What it changes in the records:**

- **[ADR-0209](../../adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md) §2** gains
  a second dated amendment of 2026-11-24, below the first: **the startup sequence gains a step that
  warms Home**. The step is started and never awaited, runs only for an account headed for the tabs,
  and is skipped when the phone already knows it is offline. The splash never waits for it. Built
  by [#874](https://github.com/Raketa02/Raketa/issues/874).
- **The player app's [theme](../../../frontend_player/src/shared/ui/theme.ts) and
  [design system](../../../frontend_player/docs/design-system.md)** gain the shimmer's tokens:
  `skeleton` (`paper3`'s value), `skeletonSheen` (`paper`'s value), and `motion.skeleton` (the
  1000 ms sweep and its 20° tilt). §1.5 gains the loop, Part 13 gains its third reduced-motion
  exception, and Part 15 and Part 16 record both. All of this landed with #868. No code reads them
  until [#870](https://github.com/Raketa02/Raketa/issues/870) builds `Skeleton`.
- **[The tab menu's log](../tab-menu/decisions.md) §5.2**, *When the new kind isn't read yet*,
  carries a dated note (Q26): a kind not read yet shows the deck-card skeleton, not the spinner. So
  does the same rule in [the Games and Fill in screens](../games-and-fill-in/the-screens.md) A1.
  Built by [#876](https://github.com/Raketa02/Raketa/issues/876).

**This folder holds the record, not the spec.** The player app's own docs say how each screen loads
today. The ticket that changes a part amends its feature record and its module notes:

- [#869](https://github.com/Raketa02/Raketa/issues/869): the jump button's *Finding you…*;
- [#870](https://github.com/Raketa02/Raketa/issues/870): the `Skeleton` primitive, the reveal rule,
  and Rankings;
- [#871](https://github.com/Raketa02/Raketa/issues/871): Home, with its two parts and the ceiling;
- [#872](https://github.com/Raketa02/Raketa/issues/872): the four See all screens;
- [#874](https://github.com/Raketa02/Raketa/issues/874): Home's warm-up during the splash;
- [#875](https://github.com/Raketa02/Raketa/issues/875): the group page and its offline notes;
- [#876](https://github.com/Raketa02/Raketa/issues/876): the kind swap's skeleton.

[#873](https://github.com/Raketa02/Raketa/issues/873) measures the shimmer's frame cost on the A32
(the log's §7.1, Q27), and [#877](https://github.com/Raketa02/Raketa/issues/877) is the phone walk.
That walk includes the 2.5 s ceiling, which the log (§5) asks to check against a measured cold
open. Until a ticket amends a doc, that doc describes today's spinners and blank bodies.

**Where the log and PRD #867 disagree, PRD #867 wins.** *Skeleton* and *warm-up* are UI and
startup words, not domain terms. Whether they enter the player app's
[`CONTEXT.md`](../../../frontend_player/CONTEXT.md) is the building tickets' call.
