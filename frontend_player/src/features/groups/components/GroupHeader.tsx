/**
 * **A group's header** — back, the group's tile, its name with the official mark, *N members ·
 * Home club* — drawn by its page and by Info (play 39, 40, 57; Q125). While the group is being
 * read it has only its way back.
 *
 * **On the page it is the door to Info** (Q125): the tile, the name and the line under it are one
 * button (`ScreenHeader`'s `onPress`), and the back arrow and the sport pill keep their own taps.
 * While the filter's bar is open it covers the tile, and a tap there is the bar's. **On Info it is
 * the same header without the pill, and presses nothing.**
 *
 * **The Owner's count of waiting requests is on the tile's corner** (#529, the Info tab's count
 * until Q125): `CornerBadge`, the segment's mark, off the read *Want to join* draws, so an answer
 * that takes a row takes it off the tile in the same frame — and spoken with the header. Nobody
 * else's page reads the requests, so nobody else's tile carries a count.
 */

import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { CornerBadge, ScreenHeader, theme, type ScreenHeaderProps } from '@/shared/ui';

import type { Group } from '../domain/group';
import { useJoinRequests } from '../hooks/useGroups';

import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { groupHeaderLabel, membersAtClub } from './groupsPresentation';
import { OfficialMark } from './OfficialMark';

/** Info's header has no filter, and nothing to cover. */
const uncovered = (node: ReactNode) => node;

export interface GroupHeaderProps {
  readonly groupId: string;
  /** `undefined` while the read is on its way. */
  readonly group: Group | undefined;
  readonly backLabel: string;
  /** The sport pill — the page's; Info has none. */
  readonly pill?: ReactNode;
  /** The filter's cover (`SportPillFrame` measures it), round the tile, so the open bar covers it whole. */
  readonly cover?: (node: ReactNode) => ReactNode;
  /** Opens Info — the page's header is its door; Info's own presses nothing. */
  readonly onOpen?: () => void;
}

export function GroupHeader({
  groupId,
  group,
  backLabel,
  pill,
  cover = uncovered,
  onOpen,
}: GroupHeaderProps) {
  const isOwner = group?.isOwner === true;
  const requests = useJoinRequests(groupId, isOwner);
  // The Owner's alone: a page read after the reader stopped owning the group keeps no count, even
  // with an old answer still cached under the key.
  const waiting = isOwner ? (requests.data?.length ?? 0) : 0;

  const back = { compact: true, onBack: () => router.back(), backLabel } as const;
  if (group === undefined) return <ScreenHeader {...back} />;

  const label = groupHeaderLabel(group, waiting);
  const drawn = {
    ...back,
    // The open bar covers the tile whole or not at all (#529) — its badge with it.
    lead: cover(
      <View testID="group-header-tile" style={s.tile}>
        <GroupMonogram monogram={group.monogram} size="header" />
        {waiting > 0 ? <CornerBadge count={waiting} /> : null}
      </View>,
    ),
    title: group.name,
    subline: membersAtClub(group.memberCount, group.homeClub.name),
    ...(group.kind === 'OFFICIAL'
      ? { titleMark: <OfficialMark fontSize={theme.type.h2.fontSize} /> }
      : {}),
    ...(label === undefined ? {} : { titleLabel: label }),
    right: pill,
  } satisfies ScreenHeaderProps;

  return onOpen === undefined ? (
    <ScreenHeader {...drawn} />
  ) : (
    <ScreenHeader {...drawn} onPress={onOpen} pressHint={GROUPS_COPY.group.openInfo} />
  );
}

const s = StyleSheet.create({
  // Android clips a child drawn outside its parent, and the badge overhangs the tile's corner.
  tile: { overflow: 'visible' },
});
