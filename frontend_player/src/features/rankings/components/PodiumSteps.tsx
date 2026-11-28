/**
 * **The podium** (rankings 4, 6; the screens §5.1; [#775](https://github.com/Rakieta02/Rakieta/issues/775)):
 * the first three rows, on three steps — first in the middle on the tallest, volt;
 * second on the left, white; third on the right, white and slightly lower than second. Each shows the
 * face, the nickname and the level, and its step reads the **true** place — a player the reader
 * blocked stands on theirs, and a tap reads *This record isn't available* (ADR-0204 §2, #799).
 *
 * Drawn only with three rows (`podiumOf`); the server sends none with fewer. A step names its player
 * by nickname, the reader's own included (§30.7) — only a row reads *You*. **A tap on a step opens
 * the record** — the whole column is the press, so the face is part of it.
 *
 * The steps stand on `paper2`, the recess rankings 6 draws, and the volt step is a fill, which volt
 * may be anywhere; its number is `ink` on it.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';
import { PlayerPhoto, theme } from '@/shared/ui';

import type { Podium, RankedRow } from '../domain/ranking';

import { RANKINGS_COPY, rankedRowLabel } from './rankingsCopy';

type Step = 'first' | 'second' | 'third';

const STEP_HEIGHT: Readonly<Record<Step, number>> = {
  first: theme.size.rankings.stepFirst,
  second: theme.size.rankings.stepSecond,
  third: theme.size.rankings.stepThird,
};

export function PodiumSteps({
  podium,
  onOpen,
}: {
  readonly podium: Podium;
  readonly onOpen: (row: RankedRow) => void;
}) {
  return (
    <View testID="podium" style={s.podium}>
      <StepColumn row={podium.second} step="second" onOpen={onOpen} />
      <StepColumn row={podium.first} step="first" onOpen={onOpen} />
      <StepColumn row={podium.third} step="third" onOpen={onOpen} />
    </View>
  );
}

function StepColumn({
  row,
  step,
  onOpen,
}: {
  readonly row: RankedRow;
  readonly step: Step;
  readonly onOpen: (row: RankedRow) => void;
}) {
  const first = step === 'first';
  const face = first ? theme.size.rankings.podiumFirstFace : theme.size.rankings.podiumFace;

  return (
    <Pressable
      testID={`podium-${step}`}
      accessibilityRole="button"
      // Named as drawn: the nickname, the reader's own too (§30.7).
      accessibilityLabel={rankedRowLabel({ ...row, isYou: false })}
      accessibilityHint={row.isYou ? RANKINGS_COPY.openOwnRecord : RANKINGS_COPY.openRecord}
      onPress={() => onOpen(row)}
      style={({ pressed }) => [s.column, pressed ? s.pressed : undefined]}
    >
      <PlayerPhoto
        playerId={row.playerId}
        {...(row.photoUrl === undefined ? {} : { photoUrl: row.photoUrl })}
        box={{ kind: 'face', size: face }}
      />
      <View style={s.who}>
        {/* §30.7: a step names the player by nickname — the reader's own too; only a row reads You. */}
        <Text style={s.name} numberOfLines={1}>
          {row.nickname}
        </Text>
        <Text style={s.level}>{formatLevel(row.level)}</Text>
      </View>
      <View style={[s.step, first ? s.voltStep : undefined, { height: STEP_HEIGHT[step] }]}>
        <Text style={s.place}>{row.place}</Text>
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // The recess the steps stand in: its foot is the steps' own, so it has no bottom padding.
  podium: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
    paddingTop: theme.space.lg,
    paddingHorizontal: theme.space.lg,
    backgroundColor: theme.color.paper2,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
  },
  column: { flex: 1, alignItems: 'center', gap: theme.space.xs },
  pressed: { opacity: 0.7 },
  who: { alignItems: 'center' },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  level: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  step: {
    alignSelf: 'stretch',
    alignItems: 'center',
    paddingTop: theme.space.sm,
    backgroundColor: theme.color.surface,
    borderTopLeftRadius: theme.radius.card,
    borderTopRightRadius: theme.radius.card,
  },
  voltStep: { backgroundColor: theme.color.volt },
  place: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
});
