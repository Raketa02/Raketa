/**
 * The photo panel's **ON COURT** mark — what the on-court check concluded, in two words
 * ([#313](https://github.com/Raketa02/Raketa/issues/313)).
 *
 * Drawn on *checked and passed* and on nothing else. *Checked and flagged* and *nobody
 * looked* draw **identically**, which is `domain/onCourtMark`'s rule and not this
 * component's: a card must not tell one player that another player's photograph was doubted,
 * so what crosses is the positive alone
 * ([ADR-0138](../../../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
 *
 * ## It is a label rather than a shield, and the panel's own width is why
 *
 * #302 and #313 both draw it as a small shield top right, carrying a ✓ beside the words.
 * Neither survives a 74pt panel, and both were struck on arithmetic rather than on taste:
 *
 * - **The tick.** Archivo Bold **does not draw U+2713** — the app's own face has no glyph for
 *   it, so `<Text>✓</Text>` renders in a per-platform fallback whose face, weight and advance
 *   this app neither controls nor can measure. That is
 *   [ADR-0135](../../../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)'s
 *   finding about `U+26A1` arriving one surface over: *the one mark in the bar whose colour
 *   this app would not control*. The app's own drawn tick (`shared/ui/Tick`) is a fixed
 *   12 × 12 geometry, and 12pt beside the words does not cost them their headroom — it costs
 *   them the drawing: **45,2pt left for a 51,19pt word**, at the system's own text size and
 *   before any scaling is asked for. So the words carry the mark alone.
 * - **The shield.** A chip inset from the corner has **39,2pt** for that word: the panel's
 *   radius is 33 % of its own width, so at the mark's own top edge the box is 57,2pt wide and
 *   not 74, and a chip's inset and its two paddings come out of that. Centred and unbounded,
 *   the same word fits with 3pt clear on each side. *Top right* is not available at this size,
 *   and the arithmetic is in `onCourtMarkFit.test.ts` rather than in this sentence.
 *
 * **The words are what a reader can act on, and that is why they are the half that survives.**
 * A green tick alone on a stranger's photograph is a mark whose meaning nobody has been told —
 * and the meaning it would be assumed to have, in 2026, is *verified account*, which this
 * platform does not do and has never claimed. [6.9](../../../../../docs/design-system.md#69-the-photo-tile-and-picker)
 * already refuses the mirror of that for the poster: *nobody should have to see a poster to
 * know they are not looking at the player.*
 *
 * ## Mint over the pinned scrim, and no ground of its own
 *
 * `mintSoft` and not `mint`: as a foreground over the panel's scrim, `mint` is **1,29:1** and
 * simply not there — volt's own problem, in the other hue. `mintSoft` is **4,55:1** against
 * the worst photograph there can be, which is AA and is the tightest pair on this panel; it is
 * the pinned scrim that makes it computable at all, exactly as the white Level beside it is,
 * and it is derived in [`textOnMedia.test.ts`](../../../../shared/ui/textOnMedia.test.ts)
 * rather than asserted here.
 *
 * It carries `textOnMedia` for the panel's own reason: the ratio is the ground's brightest
 * case and a label can sit anywhere on a photograph.
 *
 * **Colour is not the signal.** The words carry it and the mint reinforces it, which is
 * [Part 13](../../../../../docs/design-system.md#part-13--accessibility)'s *never colour
 * alone* answered by the copy rather than by a second cue — and the spoken half is
 * {@link ON_COURT_CLAUSE}, in the drawing surface's own name, because the panel announces
 * nothing (§20.1).
 */

import { StyleSheet, Text } from 'react-native';

import type { PhotoPanelSize } from './PlayerPhoto';
import { theme } from './theme';

/**
 * **The mark itself** — what the on-court check concluded, in two words.
 *
 * Sentence case here and capitalised by the panel, exactly as the Sport beneath it is: the
 * capitals are a treatment the two labels share, and a string that arrived pre-shouted would
 * be the one place in this system where a style decision is spelled into the copy.
 *
 * **There is no figure in it and none to put in it.** ADR-0133's clause survives ADR-0138
 * untouched — the check's own confidence crosses on no route — so the mark says a thing
 * happened and never how sure anybody was.
 */
export const ON_COURT_MARK = 'On court';

/**
 * `Photo checked: on court` — the mark, for a listener, and **it leads with the photograph**.
 *
 * The drawing can rely on where it sits: two words over somebody's picture, above their Level,
 * are plainly about the picture. A clause in a run of sentences cannot, and *on court* alone
 * arriving between a Level and a forecast is one comma away from **activity recency** — the
 * one thing every card and every record on this platform refuses at every granularity.
 *
 * The panel announces nothing of its own (§20.1), so this is composed by whichever surface
 * draws the panel — the candidate card's spoken body, and the record header's.
 */
export const ON_COURT_CLAUSE = 'Photo checked: on court';

/**
 * How far the mark's words may grow, and **derived rather than chosen**.
 *
 * Part 13 requires text to scale with the OS setting, and the panel is a fixed 74 × 92 box —
 * so the label may neither be frozen nor grow without bound, and `maxFontSizeMultiplier` is
 * what is left. That is the tab bar's mechanism, second instance
 * ([`tabBarLabelCap.test.ts`](../../../../shared/ui/tabBarLabelCap.test.ts)), and the number
 * comes from the same place: the real Archivo Bold advance widths, against the width the
 * panel's own corner leaves at the mark's own top edge.
 *
 * **It is a bound and not a licence** — `ON COURT` truncated is `ON COU…`, a mark that has
 * stopped saying anything, where the Sport label under it survives its own ellipsis legibly
 * and is therefore left uncapped.
 *
 * **One per panel size, re-derived and never scaled.** The panel's corner is a third of its
 * own width, so what is left for the words at the mark's own top edge is a different fraction
 * of a different width at each size — 57,22 of 74 on a card and 78,45 of 112 on the record
 * sheet. Multiplying the card's cap by the widths' ratio would be arithmetic over the wrong
 * quantity; both come out of `largestStepThatFits` against the real Archivo advances, and a
 * third size that arrives without a row here fails to compile.
 *
 * **Kept here rather than in `theme.ts`, and the split is the same one `PHOTO_PANEL`
 * already draws.** The tab bar's twin lives in `theme.ts` because the bar is a design-system
 * primitive and its cap is a fact about that primitive; this cap is a fact about *these two
 * words in this one composition*, and it changes when the copy changes.
 */
export const ON_COURT_MAX_SCALE = {
  card: 1.1,
  record: 1.5,
} as const satisfies Readonly<Record<PhotoPanelSize, number>>;

export interface OnCourtMarkProps {
  /** Which panel it is standing in — the cap is that panel's, and never scaled from another's. */
  readonly size: PhotoPanelSize;
}

export function OnCourtMark({ size }: OnCourtMarkProps) {
  return (
    <Text style={s.mark} numberOfLines={1} maxFontSizeMultiplier={ON_COURT_MAX_SCALE[size]}>
      {ON_COURT_MARK}
    </Text>
  );
}

const s = StyleSheet.create({
  /**
   * Centred, and that is geometry rather than composition.
   *
   * Left-aligned at the panel's own padding the first letter sits **inside the corner's
   * curve** — the radius is a third of the width, so at the mark's top edge the box has
   * narrowed by 8,4pt on each side. Centred, the word takes the middle of what is left and
   * clears both curves. The Level and the Sport underneath are left-aligned because they sit
   * well below the corner's influence.
   *
   * `tag` uppercased rather than `eyebrow`, which is the Sport's decision one line down and
   * the same one: the tracking is what does not fit.
   */
  mark: {
    ...theme.type.tag,
    textAlign: 'center',
    textTransform: 'uppercase',
    color: theme.color.mintSoft,
    ...theme.shadow.textOnMedia,
  },
});
