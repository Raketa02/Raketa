/**
 * **The chip** — places moved in the last 7 days (rankings 8–10; the screens §5.2; the words §30.3,
 * §30.7): *▲ 2* on mint, *▼ 1* on a red tint, *—* on grey, or *New*.
 *
 * **The marks are drawn**, never characters (§30's preamble — Archivo ships neither triangle): a
 * filled triangle up or down at `size.rankings.chipMark`, and a short rule for *no change*. The count
 * is mono, as every number is.
 *
 * **Mint and red mean up and down here** (the screens §10; Part 16, 2026-11-08): the tints a row
 * already reads as *went well* and *went badly*, each with its word or shape beside it, never the
 * colour alone.
 *
 * Drawn on a white row and on the dark card alike: every ground here is a soft tint, which reads on
 * both. It announces nothing — the row or the card it sits in names it (`chipSpoken`).
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { theme } from '@/shared/ui';

import type { Chip } from '../domain/ranking';

import { chipFace } from './rankingsCopy';

/** The triangles' own 10-unit box. */
const SPACE = 10;
const UP = 'M5 1.5 L9 8.5 L1 8.5 Z';
const DOWN = 'M1 1.5 L9 1.5 L5 8.5 Z';

const TONE: Readonly<Record<Chip['kind'], { readonly ground: string; readonly ink: string }>> = {
  UP: { ground: theme.color.mintSoft, ink: theme.color.mintInk },
  DOWN: { ground: theme.color.redSoft, ink: theme.color.red },
  SAME: { ground: theme.color.line2, ink: theme.color.muted },
  NEW: { ground: theme.color.paper2, ink: theme.color.ink },
};

export function RankChip({ chip }: { readonly chip: Chip }) {
  const face = chipFace(chip);
  const tone = TONE[chip.kind];

  return (
    <View
      testID={`rank-chip-${chip.kind}`}
      style={[s.chip, { backgroundColor: tone.ground }]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {'word' in face ? (
        <Text style={[s.word, { color: tone.ink }]}>{face.word}</Text>
      ) : face.mark === 'same' ? (
        <View testID="rank-chip-same" style={[s.dash, { backgroundColor: tone.ink }]} />
      ) : (
        <>
          <Svg
            testID={`rank-chip-${face.mark}`}
            width={theme.size.rankings.chipMark}
            height={theme.size.rankings.chipMark}
            viewBox={`0 0 ${SPACE} ${SPACE}`}
          >
            <Path d={face.mark === 'up' ? UP : DOWN} fill={tone.ink} />
          </Svg>
          <Text style={[s.count, { color: tone.ink }]}>{face.count}</Text>
        </>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  // A tag's height and corner (6.4): it labels a row, and it is not pressed.
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.space.xxs,
    height: theme.size.tag,
    minWidth: theme.size.tag + theme.space.md,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.tag,
  },
  count: { ...theme.num.tag, ...theme.tabular },
  word: { ...theme.type.tag },
  dash: {
    width: theme.size.rankings.chipDash,
    height: theme.size.rankings.chipDashWeight,
    borderRadius: theme.radius.bar,
  },
});
