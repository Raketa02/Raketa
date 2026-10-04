/**
 * **A club in Join a group's answer** — its header, and every group the search found there
 * (play 24, 30–37; stories 33–40), drawn as New group's club result is (`ClubCard`, the 2026-09-27
 * review): a raised card per club, the groups on the band under its head.
 *
 * **The header is context, not a choice** (story 39): the club's name over *district · distance ·
 * sports*, one spoken element with no button role, because nothing happens when it is touched.
 * The distance is absent for a reader with no Location area. On the band, a row per group with its
 * dots, count and approver, and the one control that joins it — or, for a club with none, *No
 * groups here yet* (story 34).
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

import type { SearchedClub } from '../domain/group';

import { ClubCard } from './ClubCard';
import { GroupAtClubRow } from './GroupAtClubRow';
import { GROUPS_COPY } from './groupsCopy';
import { clubCardLabel } from './groupsPresentation';

/** How a walk finds one club's card, to look inside it. */
export function clubCardTestId(clubId: string): string {
  return `club-card-${clubId}`;
}

export function ClubResultCard({ club }: { readonly club: SearchedClub }) {
  return (
    <ClubCard club={club} headLabel={clubCardLabel(club)} testID={clubCardTestId(club.id)}>
      {club.groups.length === 0 ? (
        <Text style={s.none}>{GROUPS_COPY.joinGroup.noGroupsHere}</Text>
      ) : (
        club.groups.map((group) => <GroupAtClubRow key={group.id} group={group} variant="join" />)
      )}
    </ClubCard>
  );
}

const s = StyleSheet.create({
  none: { ...theme.type.tiny, color: theme.color.muted2 },
});
