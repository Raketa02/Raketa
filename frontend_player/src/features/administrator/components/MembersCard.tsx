/**
 * **The members card** — how many, and how much of the group has arrived (club 11, 18, 19; PRD
 * #500 story 130; #529).
 *
 * Info's members row's drawing — the door to **Members** a member has on a player group's Info tab
 * — on the Administrator's page: up to five stacked faces, the newest first, *+N* for everybody
 * else, *N members*, and a chevron. **A tap opens Members**, the member's own screen (the rows, the
 * score tags, a tap on a row opening the record), so the Administrator sees who is in by sport and
 * Level rather than by when they joined; the list of names and join dates that stood under this
 * card went with it (#529). Nobody can be removed from either (PRD #500: nobody removes a Group
 * member).
 *
 * **The count says *members*, as Info's does** (#529, the product owner's ask): the people in an
 * official group are its members exactly as a player group's are, and a member opening Info reads
 * *N members* on the same card. It said *N players*, club 18–19's word.
 *
 * **The ring on the right is how much of the group has arrived** (`ArrivedRing`): the members over
 * the group size the Administrator gave the group, filling as people join. It replaced club 11's
 * line — *you approve joins · 6% of the WhatsApp group* — whose rule half is the settings' to say.
 *
 * *N members* is the group's member count, and the faces are the newest of its players — a block
 * hides nobody here (ADR-0193 §2). *+N* counts from the count, not from the faces
 * (`playersStack`). The stack is Info's members row's own drawing (`groups`'
 * `FaceStack`).
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { FaceStack, membersLine } from '@/features/groups/types';
import { PressableCard, theme } from '@/shared/ui';

import type { OfficialGroup } from '../domain/officialGroup';
import { playersStack, whatsAppShare } from '../domain/officialGroupRules';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { membersCardLabel } from './administratorPresentation';
import { officialGroupMembersRoute } from './administratorRoutes';
import { ArrivedRing } from './ArrivedRing';

export interface MembersCardProps {
  readonly clubId: string;
  readonly group: Pick<OfficialGroup, 'id' | 'memberCount' | 'whatsAppSize' | 'players'>;
}

export function MembersCard({ clubId, group }: MembersCardProps) {
  const stack = playersStack(group.players, group.memberCount);
  const share = whatsAppShare(group.memberCount, group.whatsAppSize);

  return (
    <PressableCard
      accessibilityLabel={membersCardLabel(group.memberCount, share)}
      accessibilityHint={ADMINISTRATOR_COPY.group.membersHint}
      onPress={() => router.push(officialGroupMembersRoute(clubId, group.id))}
      style={s.card}
    >
      {stack.faces.length > 0 ? (
        <FaceStack faces={stack.faces} more={stack.more} testIDPrefix="members-face-" />
      ) : null}
      <Text style={s.count} numberOfLines={1}>
        {membersLine(group.memberCount)}
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
