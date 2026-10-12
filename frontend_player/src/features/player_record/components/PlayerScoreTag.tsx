/**
 * **Player reliability as a tag** — a four-pointed spark and the points, on a soft tint that says
 * which band the server put them in. Members' rows draw it beside the name, where the row used to
 * end in *· score 92*.
 *
 * ```
 * ✦ 92   mintInk on mintSoft   VERY_HIGH  (90–100)
 * ✦ 84   ink on line2          HIGH       (75–89)
 * ✦ 64   amber on amberSoft    MEDIUM     (50–74)
 * ✦ 48   red on redSoft        LOW        (below 50)
 * ```
 *
 * **The tint is the served band's, never the figure's** ([#660](https://github.com/Raketa02/Raketa/issues/660),
 * ADR-0195 §1). The ranges above are the backend's and are written here only to explain the
 * drawing: this client holds no threshold, so the day the floors move the tag moves with them.
 * A band this build cannot name is drawn on the neutral tint — the figure, and no claim.
 *
 * **The palette's text-safe inks, not the marks.** The mocks drew the top band in `mint` and
 * the amber one in amber's old `#9A6A0B`; both fall short of 4,5:1 on their own tints at the
 * tag's 9,5pt, which is why the palette already carries `mintInk` and today's `amber` for text.
 * The neutral band is `ink` rather than the base tag's `muted` because the figure is the point of
 * the tag, where a status word beside it is not.
 *
 * **Shaped as 6.4's tag** — its padding, corner and 9,5 / 12 box — so it sits level with the
 * *admin* tag beside it on the same row. The figure is `num.tag`, the tag's box in the mono family,
 * because every number is mono and tabular. It is not a `Tag`, because a tag is a word in a status
 * colour and this is a figure with a mark in front of it.
 *
 * **Never the only carrier**: the figure is printed, and the row it sits in speaks it with the
 * band's word.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

import type { ReliabilityBand } from '../domain/playerRecord';

/** The spark's own box, scaled by the `viewBox`. */
const SPACE = 24;

/** Four points on the box's axes, each side drawn in to a curve — the ✦ the mocks typed. */
const SPARK =
  'M 12 0 C 12.8 6.6 17.4 11.2 24 12 C 17.4 12.8 12.8 17.4 12 24 ' +
  'C 11.2 17.4 6.6 12.8 0 12 C 6.6 11.2 11.2 6.6 12 0 Z';

const INK: Readonly<Record<ReliabilityBand, string>> = {
  VERY_HIGH: theme.color.mintInk,
  HIGH: theme.color.ink,
  MEDIUM: theme.color.amber,
  LOW: theme.color.red,
};

export interface PlayerScoreTagProps {
  /** Points, 0 to 100, as the server published them. */
  readonly score: number;
  /** The band the server put them in. Absent where this build cannot name it. */
  readonly band?: ReliabilityBand;
}

export function PlayerScoreTag({ score, band }: PlayerScoreTagProps) {
  // An unnamed band is drawn on HIGH's neutral tint: no tone, which is all it may claim.
  const tint = band ?? 'HIGH';
  const ink = INK[tint];
  const spark = theme.num.tag.fontSize * theme.size.scoreSpark.share;

  return (
    <View
      testID={band === undefined ? 'score-tag' : `score-tag-${band}`}
      style={[s.tag, SURFACE[tint]]}
    >
      <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <Svg width={spark} height={spark} viewBox={`0 0 ${SPACE} ${SPACE}`}>
          <Path d={SPARK} fill={ink} />
        </Svg>
      </View>
      <Text style={[s.figure, { color: ink }]} numberOfLines={1}>
        {score}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  // 6.4's tag, so the two tags on one row are one height and one corner.
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    paddingVertical: theme.space.xxs,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.tag,
    alignSelf: 'flex-start',
  },
  figure: { ...theme.num.tag, ...theme.tabular },
});

const SURFACE = StyleSheet.create({
  VERY_HIGH: { backgroundColor: theme.color.mintSoft },
  HIGH: { backgroundColor: theme.color.line2 },
  MEDIUM: { backgroundColor: theme.color.amberSoft },
  LOW: { backgroundColor: theme.color.redSoft },
});
