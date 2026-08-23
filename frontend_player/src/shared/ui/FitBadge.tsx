/**
 * The fit badge, per design-system 7.1 — `✦ 93`.
 *
 * ```
 * height 23   paddingHorizontal 9   radius 7
 * background night   label #fff 11 / 700
 * emphatic: background coralInk
 * ```
 *
 * **`emphatic` is a prop and never a comparison.** 7.1 says the threshold *"lives
 * in the domain layer, not in the component"*, and
 * [ADR-0037](../../../../docs/adr/0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)
 * moved it further out still: emphasis depends on the **other cards on the screen**
 * — fit ≥ 90 *and* coverage ≥ 80 % *and* a seat open, at most one card per screen —
 * so it is a property of the composed screen and arrives as a server flag. A
 * component that compared its own score would be the second opinion that decision
 * exists to remove, and would light up every 90 on the board.
 *
 * **The number is printed exactly as given.** The 20–99 clamp is ADR-0037's display
 * rule and is applied where the wire is read, so nothing that draws a badge holds a
 * bound it could disagree about.
 *
 * **The high band is `coralInk` rather than `coral`.** The prototype's `.fit.hi`
 * fills with `coral`, on which white is 3.89:1 — the app-wide Rule C failure the
 * design system's own colour table already corrects for the primary button. `coralInk`
 * carries white at 5.89:1 and is the same fill that button uses.
 *
 * **`✦` is part of the badge and not decoration** (`1-now_screen_production_spec.md`
 * §3.9): it marks the number as something the platform computed rather than a rating
 * anybody gave. The badge is one accessibility element carrying a **sentence**, so
 * nothing announces the glyph — *"black four pointed star, 93"* is worse than
 * silence.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

/** The mark, per §3.9. Not an icon: it is set in the label's own type. */
const MARK = '✦';

export const FIT_BADGE_ID = 'fit-badge';

export interface FitBadgeProps {
  /** Already clamped by whoever read it off the wire. Printed verbatim. */
  readonly score: number;
  /** The composed screen's flag. At most one card on a screen carries it. */
  readonly emphatic?: boolean;
  /** What a screen reader is told, since `✦ 93` is two symbols and no sentence. */
  readonly accessibilityLabel: string;
}

export function FitBadge({ score, emphatic = false, accessibilityLabel }: FitBadgeProps) {
  return (
    <View
      testID={FIT_BADGE_ID}
      style={[s.badge, emphatic ? s.emphatic : undefined]}
      accessibilityLabel={accessibilityLabel}
      accessible
    >
      <Text style={s.label} numberOfLines={1}>
        {`${MARK} ${score}`}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  badge: {
    height: theme.size.fit,
    paddingHorizontal: theme.space.sm,
    borderRadius: theme.radius.fit,
    backgroundColor: theme.color.night,
    alignItems: 'center',
    justifyContent: 'center',
    // A badge in a row is its own width, exactly as a tag is.
    alignSelf: 'flex-start',
  },
  emphatic: { backgroundColor: theme.color.coralInk },
  label: { ...theme.type.fit, ...theme.tabular, color: theme.color.surface },
});
