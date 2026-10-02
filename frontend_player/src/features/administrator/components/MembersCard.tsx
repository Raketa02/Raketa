/**
 * **The players card** — how many, and how much of the group has arrived (club 11, 18, 19; PRD
 * #500 story 130; #529).
 *
 * Info's members row's drawing — the door to **Members** a member has on a player group's Info tab
 * — on the Administrator's page: up to five stacked faces, the newest first, *+N* for everybody
 * else, *N players*, and a chevron. **A tap opens Members**, the member's own screen (the rows, the
 * score tags, a tap on a row opening the record), so the Administrator sees who is in by sport and
 * Level rather than by when they joined; the list of names and join dates that stood under this
 * card went with it (#529). Nobody can be removed from either (PRD #500: nobody removes a Group
 * member).
 *
 * **The ring on the right is how much of the group has arrived** (`ArrivedRing`): the players over
 * the group size the Administrator gave the group, filling as people join. It replaced club 11's
 * line — *you approve joins · 6% of the WhatsApp group* — whose rule half is the settings' to say.
 *
 * *N players* is the group's member count, which a block does not change; the faces are the players
 * the server may show this reader, a blocked pair left out. So *+N* counts from the count, not from
 * the faces (`playersStack`). The stack is Info's members row's own drawing (`groups`' `FaceStack`).
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { FaceStack } from '@/features/groups/types';
import { PressableCard, theme } from '@/shared/ui';

import type { OfficialGroup } from '../domain/officialGroup';
import { playersStack, whatsAppShare } from '../domain/officialGroupRules';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { playersCardLabel, playersLine } from './administratorPresentation';
import { officialGroupMembersRoute } from './administratorRoutes';
import { ArrivedRing } from './ArrivedRing';

export interface PlayersCardProps {
  readonly clubId: string;
  readonly group: Pick<OfficialGroup, 'id' | 'memberCount' | 'whatsAppSize' | 'players'>;
}

export function PlayersCard({ clubId, group }: PlayersCardProps) {
  const stack = playersStack(group.players, group.memberCount);
  const share = whatsAppShare(group.memberCount, group.whatsAppSize);

  return (
    <PressableCard
      accessibilityLabel={playersCardLabel(group.memberCount, share)}
      accessibilityHint={ADMINISTRATOR_COPY.group.playersHint}
      onPress={() => router.push(officialGroupMembersRoute(clubId, group.id))}
      style={s.card}
    >
      {stack.faces.length > 0 ? (
        <FaceStack faces={stack.faces} more={stack.more} testIDPrefix="players-face-" />
      ) : null}
      <Text style={s.count} numberOfLines={1}>
        {playersLine(group.memberCount)}
      </Text>
      <ArrivedRing share={share} />
      <Feather
        name="chevron-right"
        size={theme.size.tabIcon}
        color={theme.color.muted}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </PressableCard>
  );
}

const s = StyleSheet.create({
  // Info's members row: one line of faces and words, the door's chevron at the end.
  card: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  count: { ...theme.type.cardTitle, color: theme.color.ink, flex: 1 },
});
