/**
 * **A group inside a club's card** — its tile, its name, its size and who approves, and what the
 * reader can do about it (play 9, 10, 24, 35–37).
 *
 * Drawn in two places that differ in one thing each, as the mocks draw them:
 *
 * - **Join a group** draws the sport dots before the count, and keeps the second line to one line,
 *   truncated — *11 members · Coach Andrzej a…* (play 35).
 * - **New group's home-club search** draws no dots and lets the line wrap to a second (play 9):
 *   the row there sits in a narrower strip under a club that is itself the thing being chosen.
 *
 * The name and the line are **one element**, spoken whole with the sports by name — the dots have
 * no words of their own — and the action beside it is the row's one control.
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { theme } from '@/shared/ui';

import type { GroupAtClub } from '../domain/group';

import { GroupActionControl } from './GroupActionControl';
import { GroupMonogram } from './GroupMonogram';
import { groupRowMeta } from './groupsPresentation';
import { SportDots } from './SportDots';

export interface GroupAtClubRowProps {
  readonly group: GroupAtClub;
  /** Join a group's row: dots before the count, the line on one line. */
  readonly dots: boolean;
}

function rowLabel(group: GroupAtClub): string {
  const plays = group.sports.length > 0 ? [`plays ${group.sports.map(sportLabel).join(', ')}`] : [];
  return [group.name, groupRowMeta(group), ...plays].join(', ');
}

export function GroupAtClubRow({ group, dots }: GroupAtClubRowProps) {
  return (
    <View style={s.row}>
      <GroupMonogram monogram={group.monogram} size="row" />

      <View style={s.words} accessible accessibilityLabel={rowLabel(group)}>
        <Text style={s.name} numberOfLines={1}>
          {group.name}
        </Text>
        <View style={s.meta}>
          {dots ? <SportDots sports={group.sports} /> : null}
          <Text style={s.line} numberOfLines={dots ? 1 : 2}>
            {groupRowMeta(group)}
          </Text>
        </View>
      </View>

      <GroupActionControl group={group} />
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  line: { ...theme.type.tiny, color: theme.color.muted, flexShrink: 1 },
});
