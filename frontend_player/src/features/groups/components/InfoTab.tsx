/**
 * **Info** — the group itself rather than a sport of it (play 57–60, club 20;
 * [#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 71–79). Top to bottom:
 *
 * - **The link card** — dark, the link in mono, and **Share** and **Copy** beside it: the link is
 *   always one tap away (story 71).
 * - **Want to join · N** — the Owner's, and only while somebody is waiting (`WantToJoin`).
 * - **The members row** — up to five stacked faces and *+N*, *N members*, the sport dots and who
 *   approves joins, and a chevron: the door to **Members** (story 72).
 * - **Edit group** — the Owner's, a door row above the way out (story 75).
 * - **Delete the group** or **Leave the group** — whichever the reader can take (`ExitDoor`).
 *
 * **Info is not drawn for a sport**: the members row counts everybody, and Members opens on the
 * filter's sport. Nothing on it is computed on the phone — who owns the group, who has been in
 * longest, who a block hides and which faces come first are all the server's.
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Card, DarkCard, DoorRow, PressableCard, theme } from '@/shared/ui';

import type { Group } from '../domain/group';
import { membersRow, readerFace } from '../domain/groupInfo';
import { useReaderId } from '../hooks/useReaderId';

import { ExitDoor } from './ExitDoor';
import { FaceStack } from './FaceStack';
import { GroupLinkActions } from './GroupLinkActions';
import { groupEditRoute, groupMembersRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import {
  infoPolicyLine,
  linkLabel,
  linkShown,
  membersLine,
  membersRowLabel,
} from './groupsPresentation';
import { SportDots } from './SportDots';
import { WantToJoin } from './WantToJoin';

const COPY = GROUPS_COPY.info;

export function InfoTab({ group }: { readonly group: Group }) {
  return (
    <>
      <InfoLinkCard group={group} />
      {group.isOwner ? <WantToJoin groupId={group.id} /> : null}
      <MembersRow group={group} />
      {group.isOwner ? (
        <Card>
          <DoorRow
            glyph="edit-2"
            title={COPY.editGroup}
            line={COPY.editGroupLine}
            onPress={() => router.push(groupEditRoute(group.id))}
          />
        </Card>
      ) : null}
      <ExitDoor group={group} />
    </>
  );
}

/**
 * **Info's link card** (play 57, 60) — not the tabs' `LinkCard`, which heads a starting state:
 * the link on one line in mono, cut in the middle where it will
 * not fit so its code stays in view, and the two doors beside it.
 */
function InfoLinkCard({ group }: { readonly group: Group }) {
  return (
    <DarkCard style={s.linkCard}>
      <Text
        style={s.link}
        numberOfLines={1}
        ellipsizeMode="middle"
        accessibilityLabel={linkLabel(group.link)}
      >
        {linkShown(group.link)}
      </Text>
      <GroupLinkActions group={group} short />
    </DarkCard>
  );
}

/**
 * **The members row** (play 58–60) — one element, the door to Members, spoken whole with the
 * sports by name. The faces overlap, each over the one before it; a reader alone sees their own.
 */
function MembersRow({ group }: { readonly group: Group }) {
  const readerId = useReaderId();
  const row = membersRow(group, readerFace(group, readerId));

  return (
    <PressableCard
      accessibilityLabel={membersRowLabel(group)}
      accessibilityHint={COPY.membersHint}
      onPress={() => router.push(groupMembersRoute(group.id))}
      style={s.membersCard}
    >
      <FaceStack faces={row.faces} more={row.more} testIDPrefix="members-row-face-" />

      <View style={s.words}>
        <Text style={s.count} numberOfLines={1}>
          {membersLine(group.memberCount)}
        </Text>
        <View style={s.meta}>
          <SportDots sports={group.sports} />
          <Text style={s.policy} numberOfLines={1}>
            {infoPolicyLine(group)}
          </Text>
        </View>
      </View>

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
  linkCard: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  link: { ...theme.num.s, color: theme.color.surface, flex: 1 },
  membersCard: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  words: { flex: 1, gap: theme.space.xxs },
  count: { ...theme.type.cardTitle, color: theme.color.ink },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  policy: { ...theme.type.tiny, color: theme.color.muted, flexShrink: 1 },
});
