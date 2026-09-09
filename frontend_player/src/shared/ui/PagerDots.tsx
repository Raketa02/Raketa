/**
 * The paging rail's page indicator, per design-system 7.18 — **the fourth drawn object.**
 *
 * ```
 * dot      size.pagerDot 5 × 5, radius.pill, fill color.line
 * current  size.pagerDotActive 14 wide × size.pagerDot tall, radius.pill, fill color.ink
 * gap      space.xxs 3        row  centred under the rail, marginTop space.md
 * ```
 *
 * **They are the affordance where 7.9's segments indicate one.** The question navigator says of
 * itself *"it indicates; it does not navigate"* and can afford to, because the questionnaire's
 * movement controls are elsewhere on the screen. A **paging** rail has no elsewhere: taking the
 * content width spends the peek that said *there are more*, so the dots are the only thing on the
 * screen saying a second card exists — which is why they **track the scroll**, since a page
 * indicator that does not move is a picture of a control.
 *
 * **Not pressable, on 7.9's own arithmetic.** A row of dots across the content width is far under
 * 44pt each, and 6.5 bounds horizontal `hitSlop` by the neighbour — at a 3pt gap that is 1,5pt a
 * side. The rail is already scrollable by the gesture a finger is making on it, so a pressable dot
 * would be a second and less reliable way to do the thing being done anyway.
 *
 * **The state has a shape as well as a tone.** The current dot keeps its height and grows to 14,
 * which is Part 13's *never colour alone* discharged by geometry — and `ink` rather than the
 * `coral` Part 8 wrote, because 1.2 closes its list of coral uses and a page indicator is not *a
 * thing to attend to*. `ink` is already this app's word for *the one you are on*.
 *
 * ## It is hidden, and that is 7.18 read against `the-words.md` §24.5
 *
 * 7.18: *"The row is hidden, and there is no element per dot … the rail under it is a list, and
 * the position and the count belong to that list's own accessibility."* §24.5 asks instead for one
 * element saying `Game {i} of {n}`. **The design system wins**, on its own rule and on the later
 * date: a hidden row leaves the count on the heading above the rail, where it is announced once
 * and by the thing it is a count of, and a spoken position that only changes when a sighted finger
 * moves is a fact about the drawing rather than about the games. The disagreement is recorded here
 * rather than resolved silently, because it is the kind a reader will come looking for.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from './theme';

export interface PagerDotsProps {
  /** How many cards the rail holds. */
  readonly count: number;
  /** Which card is on screen, zero-based. Clamped by the caller's own scroll arithmetic. */
  readonly current: number;
}

export function PagerDots({ count, current }: PagerDotsProps) {
  // **A paging rail takes the dots always**, which is 7.7's own word read literally: *a paging
  // rail with neither peek nor dots says nothing at all about there being a second card*, and a
  // row that appeared on the second card would be the affordance arriving after it was needed. So
  // a rail of one draws one dot, and only a rail of none draws nothing — because there is no rail.
  if (count < 1) return null;

  return (
    <View style={s.row} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      {Array.from({ length: count }, (_, at) => (
        <View key={at} style={[s.dot, at === current ? s.current : undefined]} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: theme.space.xxs,
    marginTop: theme.space.md,
  },
  dot: {
    width: theme.size.pagerDot,
    height: theme.size.pagerDot,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.line,
  },
  current: { width: theme.size.pagerDotActive, backgroundColor: theme.color.ink },
});
