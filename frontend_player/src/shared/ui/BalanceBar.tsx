/**
 * The balance bar — [7.11](../../../docs/design-system.md#711-the-balance-bar).
 *
 * Two segments in one track, saying **which side** a game leans to. The figure beside it says
 * *how even*, and the two are different facts: the figure is the server's and is never
 * derived here.
 *
 * ```
 * bar    height 16 / 18 / 24, radius.balanceBar, overflow hidden
 * yours  night          (on a dark card: `surface`, with the label in `night`)
 * theirs ok mintInk  |  warn amber  |  bad red        <- Rule C: white sits on all three
 * labels tag, white, centred — drawn at md and lg, absent at sm
 * ```
 *
 * **The on-dark repaint is a repaint and not a second scheme** — the same one
 * [7.5](../../../docs/design-system.md#75-the-level-bar) takes, for the same reason: React
 * Native has no colour cascade, and the pool header draws this bar inside a dark card, where
 * a `night` segment against a `night` card is one segment. The two sides swap which of them
 * is the dark one; the tone, the scale and the clamp are untouched.
 *
 * **This is not the deleted 7.2 returning under its old number.** That section went with the
 * balance-forecast engine in the reset; the engine ships again and the component comes back
 * at a new number, because a section number in this document never moves.
 *
 * ## One fixed scale, because three clamps were the defect
 *
 * The prototype computed the left segment as *fifty plus the difference between the two side
 * strengths times thirty-four*, and then clamped it to **22–78 on the forecast card** and
 * **20–80 on the pool header and the candidate card**. One formula, three clamps: the same
 * gap landed in a different place on two screens, which is exactly what
 * [7.5](../../../docs/design-system.md#75-the-level-bar) and
 * [7.8](../../../docs/design-system.md#78-the-confidence-ring) exist to prevent — *"a value
 * must land in the same place everywhere or the component means different things on different
 * screens."*
 *
 * Drawing the raw shares instead would be honest and invisible: 2,71 against 2,83 is 48,9
 * against 51,1, a difference nobody can see at 24pt.
 *
 * > **The amplification ships as one fixed scale: one mapping, one constant, one clamp.**
 * > A steep scale is still a fixed scale. What was wrong was three of them.
 *
 * The scale lives here rather than in `theme.ts` for 7.5's reason — the level bar's fixed
 * 1,00–5,00 lives in the component that draws it, and `theme.size.balanceBar` holds the
 * geometry alone.
 *
 * ## The word carries the meaning, and the bar is a colour
 *
 * [Part 13](../../../docs/design-system.md#part-13--accessibility) forbids colour as the only
 * signal, so the tone is never the whole story: the caller draws the balance word beside the
 * bar, and `the-words.md` §20.4 makes the bar one `image` element whose name is that word and
 * its figure. **Recorded rather than fixed:** the word breaks at 85 / 70 / 55 and the tone
 * breaks at 70 / 55, so *Very even* and *Fairly even* share one green. That is correct — Part
 * 13 is satisfied by the word, and a fourth tone would need a fourth **meaning**, which
 * [15.2](../../../docs/design-system.md#152-adding-a-colour) forbids inventing.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

/**
 * The one mapping, the one amplification constant and the one clamp.
 *
 * `centre` is an even game. `amplification` is the prototype's ×34, kept: at the scale a
 * level difference actually varies over, nothing smaller is visible. `min` / `max` is the
 * clamp both the pool header and the candidate card already used — the forecast card's
 * 22–78 is the one that goes.
 */
export const BALANCE_SCALE = { centre: 50, amplification: 34, min: 20, max: 80 } as const;

/**
 * Where the fold sits, as a percentage of the bar, for a given advantage.
 *
 * `advantage` is *your* side's strength minus theirs. Exported because it is the scale, and a
 * scale nothing can cite is a scale that gets re-derived at the next call site.
 */
export function balanceShare(advantage: number): number {
  const raw = BALANCE_SCALE.centre + advantage * BALANCE_SCALE.amplification;
  return Math.min(BALANCE_SCALE.max, Math.max(BALANCE_SCALE.min, raw));
}

export type BalanceBarSize = keyof typeof theme.size.balanceBar;

/** The three the palette already means. `ok` is `mintInk` and not `mint`, per Rule C. */
export type BalanceBarTone = 'ok' | 'warn' | 'bad';

/**
 * The same three as **ink**, for a screen printing the figure rather than drawing the bar.
 *
 * 7.11's finding is *one formula, three clamps* — a value landing in a different place on two
 * screens — and the thresholds are already asked for rather than restated (`balanceTone`). This
 * is the other half of that: which colour each tone is, in one place, so a second screen
 * printing a tinted percentage cannot pick a different amber. Rule C is why it is `mintInk`
 * rather than `mint`.
 */
export const BALANCE_INK: Readonly<Record<BalanceBarTone, string>> = {
  ok: theme.color.mintInk,
  warn: theme.color.amber,
  bad: theme.color.red,
};

/**
 * The same three as a **bed**, for a surface that tints a box rather than drawing the bar.
 *
 * `BALANCE_INK`'s argument, one register over: which colour each tone is belongs in one place,
 * so a second surface tinting a panel cannot pick a different amber from the bar sitting four
 * lines above it. The softs are the palette's own beds
 * ([2.2](../../../docs/design-system.md#22-accent-and-semantics)), and each carries its
 * `BALANCE_INK` partner at 5:1 or better — which is what makes the pair usable together.
 */
export const BALANCE_SOFT: Readonly<Record<BalanceBarTone, string>> = {
  ok: theme.color.mintSoft,
  warn: theme.color.amberSoft,
  bad: theme.color.redSoft,
};

export type BalanceBarVariant = 'base' | 'onDark';

export interface BalanceBarProps {
  /** Your side's strength minus theirs. The bar maps it; it never receives a percentage. */
  readonly advantage: number;
  readonly tone: BalanceBarTone;
  readonly size?: BalanceBarSize;
  readonly variant?: BalanceBarVariant;
  /** Yours, then theirs. Drawn at `md` and `lg`, and never at `sm`. */
  readonly labels?: readonly [string, string];
  /**
   * One element, one name (`the-words.md` §20.4): the balance **word** and its figure. The
   * word is the point, because the bar itself is a colour.
   */
  readonly accessibilityLabel: string;
}

export function BalanceBar({
  advantage,
  tone,
  size = 'lg',
  variant = 'base',
  labels,
  accessibilityLabel,
}: BalanceBarProps) {
  const height = theme.size.balanceBar[size];
  const share = balanceShare(advantage);
  // At `sm` there is no room beside the fold for a 9,5pt line, and #219 B4 put the floor
  // there — so the size decides WHETHER there is a label, not how small it is.
  const drawn = size === 'sm' ? undefined : labels;

  return (
    <View accessible accessibilityRole="image" accessibilityLabel={accessibilityLabel}>
      <View style={[s.bar, { height }]}>
        <View style={[s.segment, YOURS[variant], { width: `${share}%` }]}>
          {drawn === undefined ? null : (
            <Text style={[s.label, YOURS_LABEL[variant]]} numberOfLines={1}>
              {drawn[0]}
            </Text>
          )}
        </View>
        <View style={[s.segment, THEIRS[tone], { width: `${100 - share}%` }]}>
          {drawn === undefined ? null : (
            <Text style={[s.label, s.labelOnTone]} numberOfLines={1}>
              {drawn[1]}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    borderRadius: theme.radius.balanceBar,
    overflow: 'hidden',
    backgroundColor: theme.color.line2,
  },
  segment: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  label: { ...theme.type.tag, paddingHorizontal: theme.space.xxs },
  labelOnTone: { color: theme.color.surface },
});

const YOURS = StyleSheet.create({
  base: { backgroundColor: theme.color.night },
  // On a dark card the night segment would be the card, so the sides swap which one is dark.
  onDark: { backgroundColor: theme.color.surface },
});

const YOURS_LABEL = StyleSheet.create({
  base: { color: theme.color.surface },
  onDark: { color: theme.color.night },
});

const THEIRS = StyleSheet.create({
  ok: { backgroundColor: theme.color.mintInk },
  warn: { backgroundColor: theme.color.amber },
  bad: { backgroundColor: theme.color.red },
});
