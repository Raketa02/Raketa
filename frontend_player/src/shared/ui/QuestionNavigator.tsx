/**
 * The question navigator, per design-system 7.9 — a drawn object, like the level bar and
 * the ring, and the questionnaire's progress indicator.
 *
 * **It claims no total, and that is the whole design.** An adaptive questionnaire has no
 * denominator: the engine decides it has heard enough only after an answer arrives. So the
 * segments are a fixed width in a left-aligned row — the row grows rightward and never
 * arrives, where a flex-filled track would put the last segment at the right edge and
 * assert a length nobody knows.
 *
 * **Two independent facts, two properties.** `answered` fills a segment; `at` makes one
 * tall. A player standing on an answer they gave four questions ago is on a segment that is
 * both filled and tall, and the outstanding question is a segment that is tall and empty.
 * Height rather than opacity carries where the player is, because a state that exists only
 * as a shade excludes whoever cannot see it.
 *
 * **It indicates; it does not navigate.** Ten segments across the content width is a 26pt
 * target against the 44pt minimum (design-system 6.5, Part 13), and selecting the wrong one
 * would be the most destructive tap in the flow. Movement is the screen header's back
 * control and the screen's own forward control (ADR-0020).
 *
 * There is no `progressbar` role: that role carries a max. One element, one label — never
 * one per segment — and the caller writes the label, because copy is the screen's.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from './theme';

export interface QuestionNavigatorProps {
  /** How many questions have been answered — the served transcript's length. */
  readonly answered: number;
  /** Whether a question is outstanding: it gets a segment of its own, unfilled. */
  readonly outstanding: boolean;
  /**
   * The 1-based position the player is standing on. A position past the drawn segments
   * makes none of them tall, which is what the stopped questionnaire looks like.
   */
  readonly at: number;
  /** States the position and the count in words, and never a total. */
  readonly accessibilityLabel: string;
}

export function QuestionNavigator({
  answered,
  outstanding,
  at,
  accessibilityLabel,
}: QuestionNavigatorProps) {
  // One segment per question that exists: the answers given, plus the one being asked.
  // Never a segment for a question the engine has not decided to ask.
  const drawn = Math.max(answered, 0) + (outstanding ? 1 : 0);

  return (
    <View style={s.row} accessibilityLabel={accessibilityLabel} accessible>
      {Array.from({ length: drawn }, (_unused, index) => {
        const position = index + 1;
        return (
          <View
            key={position}
            style={[
              s.segment,
              position <= answered ? s.answered : s.unanswered,
              position === at ? s.current : undefined,
            ]}
          />
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  // Left-aligned and never stretched: the row's length is its only claim.
  row: { flexDirection: 'row', alignItems: 'flex-end', gap: theme.size.navigator.gap },
  segment: {
    width: theme.size.navigator.segmentWidth,
    height: theme.size.navigator.segmentHeight,
    borderRadius: theme.size.navigator.segmentRadius,
  },
  answered: { backgroundColor: theme.color.coral },
  // The same track colour the bar uses — a fold inside one thing, not a boundary.
  unanswered: { backgroundColor: theme.color.line2 },
  current: {
    height: theme.size.navigator.currentHeight,
    borderRadius: theme.size.navigator.currentRadius,
  },
});
