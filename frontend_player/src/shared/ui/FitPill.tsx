/**
 * The fit pill — [7.10](../../../docs/design-system.md#710-the-fit-pill).
 *
 * One number and one glyph, drawn on five surfaces: the competitive card, the social card,
 * the deck card, the why-fit sheet's head, and — **with a word in front of it** — the player
 * record's one control.
 *
 * ```
 * pill   height 26, radius.fit, padding 0 x 9, row, gap 3
 * base   background night   · label #fff        13,29:1
 * hi     background coral   · label ink          4,50:1   <- Rule C
 * number num.xs, mono, TABULAR — the pill sits in a scrolling list of them
 * label  inlineTitle, optional, BEFORE the glyph — the record sheet's alone
 * ```
 *
 * ## The figure is a whole number, and the pill is where it is made one
 *
 * Fit crosses the wire as a `number` and the engine serves it with its decimals on. Printed as
 * served, `✦ 78.42131` is five characters of precision nobody can act on, in a pill 26pt tall
 * on twenty scrolling rows — and worse, it **disagreed with the card around it**:
 * `whyFitControlWord` has always drawn `Why 78?` from `Math.round`, so the same number appeared
 * twice on one card in two spellings.
 *
 * So it is rounded **here**, once, rather than at each of the five call sites: a component that
 * printed whatever it was handed left every caller to remember, and the record sheet was
 * already passing `Math.round(fit)` by hand for exactly this reason.
 *
 * **The threshold reads the rounded figure**, so the fill and the number are two views of one
 * value. A pill drawn `hi` beside an 89 — because 89,6 crossed a line the reader cannot see —
 * is Part 13's *never colour alone* failing in the one direction the word cannot rescue.
 *
 * ## The optional label, and why it is a prop rather than a second component
 *
 * On the three cards and the sheet head the pill sits **inside something that has already said
 * what the number is** — a card whose body names it, a sheet whose title is it. The record
 * sheet has no such surround: the pill is a control there, on its own under the sport pills,
 * and a bare `✦ 80` floating in a header is a number with no noun.
 *
 * So it takes a word, and the word goes **first** — `Player fit ✦ 80` — which is the order the
 * accessible name uses and the order somebody would say it. The glyph keeps its place
 * immediately before the figure it marks, so the pill a reader already knows from the shortlist
 * is the same object with a name on it rather than a new one.
 *
 * It is a prop and not a second component because everything that makes this pill legal is
 * here: the two fills, the 90 step, Rule C's `ink`-on-coral, and the tabular figure. A copy
 * with a word in it would be a second place for all four to be true.
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
  /**
   * Fit, out of {@link FIT_SCALE}, **as served** — decimals and all.
   *
   * Rounded to a whole number for both the figure and the threshold; nothing here rescales.
   * See the module note.
   */
  readonly fit: number;
  /**
   * What the number is, drawn before the glyph. Omitted on every surface whose surround
   * already says it — see the module note.
   *
   * **It is not an accessible name and never becomes one.** The pill is merged into whatever
   * names it (§20.3): a card body on three surfaces, a control's own label on the fourth.
   */
  readonly label?: string;
}

export function FitPill({ fit, label }: FitPillProps) {
  // Once, and read by both: the figure printed and the fill behind it are the same number.
  const whole = Math.round(fit);
  const high = whole >= FIT_HIGH;
  const ink = high ? s.labelHigh : s.labelBase;

  return (
    <View style={[s.pill, high ? s.pillHigh : s.pillBase]}>
      {label === undefined ? null : <Text style={[s.label, ink]}>{label}</Text>}
      <Text style={[s.glyph, ink]}>{SPARK}</Text>
      <Text style={[s.value, ink]}>{whole}</Text>
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
  label: { ...theme.type.inlineTitle },
  // Tabular, because twenty of these scroll past one another and a 78 that is wider than a
  // 90 is a column that breathes.
  value: { ...theme.num.xs, ...theme.tabular },
  labelBase: { color: theme.color.surface },
  labelHigh: { color: theme.color.ink },
});
