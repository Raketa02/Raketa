/**
 * **A group on a club card's band** — its tile, its name with an **official** tag on an official
 * group, its sport dots and size, and what the reader can do about it (play 9, 10, 24, 35–37; the
 * 2026-09-27 mocks).
 *
 * Drawn in two places that differ in one thing, the line after the count:
 *
 * - **Join a group** names who approves, on one line, truncated — *11 members · Coach Andrzej a…*
 *   (play 35): the reader is deciding whether to ask, and that is who answers.
 * - **New group's home-club search** stops at the count: the row sits under a club that is itself
 *   the thing being chosen, so it says only enough to recognise the group.
 *
 * The name and the line are **one element**, spoken whole with the sports by name — the dots have
 * no words of their own — and the action beside it is the row's one control. An official group's
 * dots are the sports it declares, as served (#519).
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { Tag, theme } from '@/shared/ui';

import type { GroupAtClub } from '../domain/group';

import { GroupActionControl } from './GroupActionControl';
import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { groupRowMeta, membersLine } from './groupsPresentation';
import { SportDots } from './SportDots';

/** Which screen's row: Join a group's, or New group's home-club search's. */
export type GroupAtClubRowVariant = 'join' | 'homeClub';

export interface GroupAtClubRowProps {
  readonly group: GroupAtClub;
  /** The club whose card the row sits in — who approves an official group that needs an administrator. */
  readonly clubName: string;
  readonly variant: GroupAtClubRowVariant;
}

/** The second line: Join a group's names who approves; home-club search's stops at the count. */
function rowLine(group: GroupAtClub, clubName: string, variant: GroupAtClubRowVariant): string {
  return variant === 'join' ? groupRowMeta(group, clubName) : membersLine(group.memberCount);
}

function rowLabel(group: GroupAtClub, line: string, official: boolean): string {
  const tagged = official ? [GROUPS_COPY.official] : [];
  const plays = group.sports.length > 0 ? [`plays ${group.sports.map(sportLabel).join(', ')}`] : [];
  return [group.name, ...tagged, line, ...plays].join(', ');
}

export function GroupAtClubRow({ group, clubName, variant }: GroupAtClubRowProps) {
  const line = rowLine(group, clubName, variant);
  const official = group.kind === 'OFFICIAL';

  return (
    <View style={s.row}>
      <GroupMonogram monogram={group.monogram} size="row" />

      <View style={s.words} accessible accessibilityLabel={rowLabel(group, line, official)}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {group.name}
          </Text>
          {official ? <Tag label={GROUPS_COPY.official} variant="ok" /> : null}
        </View>
        <View style={s.meta}>
          <SportDots sports={group.sports} />
          <Text style={s.line} numberOfLines={1}>
            {line}
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
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // The row is only ever drawn on a club card's tray, where `muted` falls short of 4,5.
  line: { ...theme.type.tiny, color: theme.color.muted2, flexShrink: 1 },
});
