/**
 * **A Player Score as a tag** — a four-pointed spark and the figure, on a soft tint that says
 * which of `scoreBand`'s four bands it is in. Members' rows draw it beside the name, where the
 * row used to end in *· score 92*.
 *
 * ```
 * ✦ 92   mintInk on mintSoft   90–100  the best partners
 * ✦ 84   ink on line2          70–89   nothing to flag
 * ✦ 64   amber on amberSoft    50–69   worth a look first
 * ✦ 48   red on redSoft        0–49    risky
 * ```
 *
 * **The palette's text-safe inks, not the marks.** The mocks drew the strong band in `mint` and
 * the wobbly one in amber's old `#9A6A0B`; both fall short of 4,5:1 on their own tints at the
 * tag's 9,5pt, which is why the palette already carries `mintInk` and today's `amber` for text.
 * The neutral band is `ink` rather than the base tag's `muted` because the figure is the point of
 * the tag, where a status word beside it is not.
 *
 * **Shaped as 6.4's tag** — its padding, corner and 9,5 / 12 box — so it sits level with the
 * *admin* tag beside it on the same row. The figure is `num.tag`, the tag's box in the mono family,
 * because every number is mono and tabular. It is not a `Tag`, because a tag is a word in a status
 * colour and this is a figure with a mark in front of it.
 *
 * **Never the only carrier**: the figure is printed, and the row it sits in speaks it.
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

import { scoreBand, type ScoreBand } from '../domain/scoreTone';

/** The spark's own box, scaled by the `viewBox`. */
const SPACE = 24;

/** Four points on the box's axes, each side drawn in to a curve — the ✦ the mocks typed. */
const SPARK =
  'M 12 0 C 12.8 6.6 17.4 11.2 24 12 C 17.4 12.8 12.8 17.4 12 24 ' +
  'C 11.2 17.4 6.6 12.8 0 12 C 6.6 11.2 11.2 6.6 12 0 Z';

const INK: Readonly<Record<ScoreBand, string>> = {
  strong: theme.color.mintInk,
  ordinary: theme.color.ink,
  wobbly: theme.color.amber,
  risky: theme.color.red,
};

export interface PlayerScoreTagProps {
  /** Out of a hundred, as the server published it. */
  readonly score: number;
}

export function PlayerScoreTag({ score }: PlayerScoreTagProps) {
  const band = scoreBand(score);
  const ink = INK[band];
  const spark = theme.num.tag.fontSize * theme.size.scoreSpark.share;

  return (
    <View testID={`score-tag-${band}`} style={[s.tag, SURFACE[band]]}>
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
  strong: { backgroundColor: theme.color.mintSoft },
  ordinary: { backgroundColor: theme.color.line2 },
  wobbly: { backgroundColor: theme.color.amberSoft },
  risky: { backgroundColor: theme.color.redSoft },
});
