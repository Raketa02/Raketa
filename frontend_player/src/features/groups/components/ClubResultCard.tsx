/**
 * **A club in Join a group's answer** — its header, and every group the search found there
 * (play 24, 30–37; stories 33–40).
 *
 * **The header is context, not a choice** (story 39): the club's name over *district · distance ·
 * sports*, one spoken element with no button role, because nothing happens when it is touched.
 * The distance is absent for a reader with no Location area. Under it, a row per group with its
 * dots, count and approver, and the one control that joins it — or, for a club with none,
 * *No groups here yet* (story 34).
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Hairline, theme } from '@/shared/ui';

import type { SearchedClub } from '../domain/group';

import { GroupAtClubRow } from './GroupAtClubRow';
import { GROUPS_COPY } from './groupsCopy';
import { clubCardLabel, clubLine } from './groupsPresentation';

/** How a walk finds one club's card, to look inside it. */
export function clubCardTestId(clubId: string): string {
  return `club-card-${clubId}`;
}

export function ClubResultCard({ club }: { readonly club: SearchedClub }) {
  return (
    <View testID={clubCardTestId(club.id)}>
      <Card>
        <View style={s.head} accessible accessibilityLabel={clubCardLabel(club)}>
          <Text style={s.name} numberOfLines={1}>
            {club.name}
          </Text>
          <Text style={s.line} numberOfLines={1}>
            {clubLine(club, { distance: true })}
          </Text>
        </View>

        {club.groups.length === 0 ? (
          <Text style={s.none}>{GROUPS_COPY.joinGroup.noGroupsHere}</Text>
        ) : (
          club.groups.map((group) => (
            <Hairline key={group.id}>
              <GroupAtClubRow group={group} dots />
            </Hairline>
          ))
        )}
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  head: { gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  none: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.md },
});
