/**
 * The fit pill — [7.10](../../../docs/design-system.md#710-the-fit-pill).
 *
 * One number and one glyph, drawn on four surfaces: the competitive card, the social card,
 * the deck card and the why-fit sheet's head.
 *
 * ```
 * pill   height 26, radius.fit, padding 0 x 9, row, gap 3
 * base   background night   · label #fff        13,29:1
 * hi     background coral   · label ink          4,50:1   <- Rule C
 * number num.xs, mono, TABULAR — the pill sits in a scrolling list of them
 * ```
 *
 * **This is not the deleted 7.1 returning under its old number.** The reset removed the fit
 * badge because the Match Fit engine it drew was removed, and
 * [Part 17](../../../docs/design-system.md#part-17--what-the-reset-removed) says why its 90
 * threshold in particular must not be restored: it *"named a scale the deleted engine
 * defined."* The engine ships again, so the arrival **states the scale it is against** rather
 * than inheriting one:
 *
 * > **Fit is out of 100**, and `hi` is Fit >= 90 — the top tenth of the scale.
 *
 * `CONTEXT.md` defines Fit as *"how good the game would be, printed on the card as one number
 * out of a hundred"*, which is where the denominator comes from; the step at 90 is the top
 * tenth of that hundred, and it is a **step in a fill, not a fourth meaning** — 15.2 forbids
 * inventing one of those, and `coral` is the app's one accent used exactly as 1.2 describes.
 *
 * **`ink` on coral, not white.** The prototype drew `#fff` on `var(--coral)`, which is
 * **3,89:1** and the one pairing Rule C refuses outright. `ink` on coral is 4,50:1 and is the
 * only dark the system permits there.
 *
 * **26 tall, which is what every call site drew.** UI §G1 records that the class defaults
 * were overridden inline at all five of them, so the arrival takes the used values and the
 * unused ones stop existing.
 *
 * **The pill is not its own accessibility element.** `the-words.md` §20.3 merges it into the
 * card body's label — `Fit {n} out of 100` — and the glyph *"is hidden by the merge rather
 * than by a separate rule"*, so there is no rule here either.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

/** The scale the number is against. Stated, never inherited — Part 17's warning. */
export const FIT_SCALE = 100;

/** The top tenth of that scale, and the pill's one threshold. */
export const FIT_HIGH = 90;

/** The mark. A glyph and not a word, because the word is in the accessible name the card
 *  composes; nothing here is announced. */
const SPARK = '✦';

export interface FitPillProps {
  /** Fit, out of {@link FIT_SCALE}. Drawn as served — nothing here rounds or rescales. */
  readonly fit: number;
}

export function FitPill({ fit }: FitPillProps) {
  const high = fit >= FIT_HIGH;

  return (
    <View style={[s.pill, high ? s.pillHigh : s.pillBase]}>
      <Text style={[s.glyph, high ? s.labelHigh : s.labelBase]}>{SPARK}</Text>
      <Text style={[s.value, high ? s.labelHigh : s.labelBase]}>{fit}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  pill: {
    height: theme.size.fit,
    paddingHorizontal: theme.space.sm,
    borderRadius: theme.radius.fit,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    // Its own width in a row, never the row's — the tag's rule, for the tag's reason.
    alignSelf: 'flex-start',
  },
  pillBase: { backgroundColor: theme.color.night },
  pillHigh: { backgroundColor: theme.color.coral },
  glyph: { ...theme.type.inlineTitle },
  // Tabular, because twenty of these scroll past one another and a 78 that is wider than a
  // 90 is a column that breathes.
  value: { ...theme.num.xs, ...theme.tabular },
  labelBase: { color: theme.color.surface },
  labelHigh: { color: theme.color.ink },
});
