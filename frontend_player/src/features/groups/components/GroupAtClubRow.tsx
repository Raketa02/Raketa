/**
 * **A group on a club card's band** — its tile, its name with the official mark beside it on an
 * official group (`OfficialMark`, which replaced the mocks' *official* tag, #529), its sport dots
 * and size, and what the reader can do about it (play 9, 10, 24, 35–37; the 2026-09-27 mocks).
 *
 * Drawn in two places that differ in one thing, the line after the count:
 *
 * - **Join a group** says whether joining needs a yes — *11 members · Needs approval* or
 *   *anyone can join* (play 35, shortened in #529): the reader is deciding whether to ask.
 * - **New group's home-club search** stops at the count: the row sits under a club that is itself
 *   the thing being chosen, so it says only enough to recognise the group.
 *
 * The name and the line are **one element**, spoken whole with *official* and the sports by name —
 * neither the mark nor the dots have words of their own — and the action beside it is the row's
 * one control. An official group's dots are the sports it declares, as served (#519).
 */

import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { theme } from '@/shared/ui';

import type { GroupAtClub } from '../domain/group';

import { GroupActionControl } from './GroupActionControl';
import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { groupRowMeta, membersLine } from './groupsPresentation';
import { OfficialMark } from './OfficialMark';
import { SportDots } from './SportDots';

/** Which screen's row: Join a group's, or New group's home-club search's. */
export type GroupAtClubRowVariant = 'join' | 'homeClub';

export interface GroupAtClubRowProps {
  readonly group: GroupAtClub;
  readonly variant: GroupAtClubRowVariant;
}

/** The second line: Join a group's says whether it needs a yes; home-club search's stops at the count. */
function rowLine(group: GroupAtClub, variant: GroupAtClubRowVariant): string {
  return variant === 'join' ? groupRowMeta(group) : membersLine(group.memberCount);
}

function rowLabel(group: GroupAtClub, line: string, official: boolean): string {
  const tagged = official ? [GROUPS_COPY.official] : [];
  const plays = group.sports.length > 0 ? [`plays ${group.sports.map(sportLabel).join(', ')}`] : [];
  return [group.name, ...tagged, line, ...plays].join(', ');
}

export function GroupAtClubRow({ group, variant }: GroupAtClubRowProps) {
  const line = rowLine(group, variant);
  const official = group.kind === 'OFFICIAL';

  return (
    <View style={s.row}>
      <GroupMonogram monogram={group.monogram} size="row" />

      <View style={s.words} accessible accessibilityLabel={rowLabel(group, line, official)}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {group.name}
          </Text>
          {official ? <OfficialMark fontSize={theme.type.cardTitle.fontSize} /> : null}
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
  // The mark sits on the name's line, centred on it, a `space.xxs` after its last letter.
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // The row is only ever drawn on a club card's tray, where `muted` falls short of 4,5.
  line: { ...theme.type.tiny, color: theme.color.muted2, flexShrink: 1 },
});
