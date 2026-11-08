/**
 * **The list** (rankings 5, 7–11; the screens §5.2; [#775](https://github.com/Raketa02/Raketa/issues/775)):
 * one row per listed player the reader can see, best first, on one white card.
 *
 * - **The place** — `coralInk` for 1–3 and `muted` after (rankings 7). A true place, so a hidden or
 *   blocked row leaves a gap. Coral is §1.2's closed list's mark; drawn as a figure it is the text
 *   form, `coralInk`, which keeps 4,5:1 on white where `coral` would not (Part 16, 2026-11-08).
 * - **The face and the nickname**, the reader's own reading *You* on a `coralSoft` tint (rankings 11).
 * - **The form** — the record's own *Run of form*: the last five results with a winner, oldest
 *   first, a mint square for a win and a grey one for a loss, never padded.
 * - **The chip**, and **the level**, right-aligned and mono.
 *
 * **A tap on the row opens the record** — the face is in the row, so it opens it too. The reader's own
 * row opens their own record.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ROW_FACE } from '@/features/groups/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { Card, PlayerPhoto, RunOfForm, theme } from '@/shared/ui';

import type { RankedRow } from '../domain/ranking';

import { RankChip } from './RankChip';
import { RANKINGS_COPY, rankedRowLabel, rowName } from './rankingsCopy';

/**
 * **The true places drawn in coral** (rankings 7; the screens §5.2: *coral for places 1–3*) — by the
 * place, not by the row's position: with second hidden the coral reads 1 and 3. The podium is the
 * first three rows the reader sees (`podiumOf`), a different count on purpose.
 */
const CORAL_PLACES = 3;

export function RankingList({
  rows,
  onOpen,
}: {
  readonly rows: readonly RankedRow[];
  readonly onOpen: (row: RankedRow) => void;
}) {
  return (
    <View testID="ranking-list">
      <Card style={s.card}>
        {rows.map((row, at) => (
          <RankingRow key={row.playerId} row={row} divided={at > 0} onOpen={onOpen} />
        ))}
      </Card>
    </View>
  );
}

function RankingRow({
  row,
  divided,
  onOpen,
}: {
  readonly row: RankedRow;
  readonly divided: boolean;
  readonly onOpen: (row: RankedRow) => void;
}) {
  return (
    <Pressable
      testID={`ranked-row-${row.playerId}`}
      accessibilityRole="button"
      accessibilityLabel={rankedRowLabel(row)}
      accessibilityHint={row.isYou ? RANKINGS_COPY.openOwnRecord : RANKINGS_COPY.openRecord}
      onPress={() => onOpen(row)}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        row.isYou ? s.you : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <Text
        testID={`ranked-place-${row.place}`}
        style={[s.place, row.place <= CORAL_PLACES ? s.podiumPlace : undefined]}
      >
        {row.place}
      </Text>
      <PlayerPhoto
        playerId={row.playerId}
        {...(row.photoUrl === undefined ? {} : { photoUrl: row.photoUrl })}
        box={{ kind: 'face', size: ROW_FACE }}
      />
      <View style={s.words}>
        <Text style={s.name} numberOfLines={1}>
          {rowName(row)}
        </Text>
        <RunOfForm results={row.form} />
      </View>
      {row.chip === undefined ? null : <RankChip chip={row.chip} />}
      <Text style={s.level}>{formatLevel(row.level)}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // One white card, its rows edge to edge so the reader's tint reaches both sides (rankings 11).
  card: { padding: 0, overflow: 'hidden' },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
    paddingHorizontal: theme.space.lg,
  },
  // 5.3: `line2` folds one card into rows.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  you: { backgroundColor: theme.color.coralSoft },
  pressed: { opacity: 0.7 },
  place: {
    ...theme.num.s,
    ...theme.tabular,
    width: theme.size.rankings.place,
    color: theme.color.muted,
  },
  podiumPlace: { color: theme.color.coralInk },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  level: { ...theme.num.m, ...theme.tabular, color: theme.color.ink, textAlign: 'right' },
});
