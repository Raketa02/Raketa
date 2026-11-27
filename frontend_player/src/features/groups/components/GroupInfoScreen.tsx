/**
 * **Info** — the group itself rather than a sport of it (play 57–60, club 20;
 * [#514](https://github.com/Raketa02/Raketa/issues/514), PRD #500 stories 71–79), **its own screen
 * since Q125**: pushed over the group's page from the page's header, so *back* is the page, on the
 * tab the player left. Its header is the page's without the sport pill, and presses nothing
 * (`GroupHeader`). Top to bottom:
 *
 * - **The link card** — dark, the link in mono, and **Share** and **Copy** beside it: the link is
 *   always one tap away (story 71).
 * - **Want to join · N** — the Owner's, and only while somebody is waiting (`WantToJoin`).
 * - **The members row** — up to five stacked faces and *+N*, *N members*, the sport dots and who
 *   approves joins, and a chevron: the door to **Members** (story 72).
 * - **Edit group** — the Owner's, a door row (story 75).
 *
 * **The way out stands at the screen's foot**: *Delete the group* or *Leave the group* (`ExitDoor`),
 * outside what scrolls, so it is always in the same place however long the queue above it is
 * (#529). Success lands on the Groups list, past the page.
 *
 * **Info re-reads when it opens, on a pull, and each time it is come back to** from Members or Edit
 * group (#529, Q125; `useGroupInfo`) — the group, who is waiting and the members row with it — so
 * what another phone changed meanwhile is on it without a pull. The page it was opened from does not re-read on
 * the way back: what Info writes, it writes into the group's read, which the page draws too.
 *
 * **Info is not drawn for a sport**, so it never waits for the filter: the members row counts
 * everybody, and Members opens on the filter's sport. A member who must add a sport to see an
 * official group's games reaches it — and the way out — as every member does. Nothing on it is
 * computed on the phone — who owns the group, who has been in longest and which faces come first
 * are all the server's — and a block hides nobody on it (ADR-0193 §2). Every state has its drawing,
 * as the page's: while the read is on its way the header has only its way back, and a failure says
 * why and offers the retry.
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useReaderId } from '@/features/auth/types';
import { codeMessage } from '@/shared/errors';
import { Card, DarkCard, DoorRow, PressableCard, theme, useTabBarReach } from '@/shared/ui';

import type { Group } from '../domain/group';
import { membersRow, readerFace } from '../domain/groupInfo';
import { useGroupInfo } from '../hooks/useGroups';
import { usePull } from '../hooks/usePull';

import { ExitDoor } from './ExitDoor';
import { FaceStack } from './FaceStack';
import { GroupHeader } from './GroupHeader';
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
import { ReadFailure } from './ReadFailure';
import { SportDots } from './SportDots';
import { WantToJoin } from './WantToJoin';

const COPY = GROUPS_COPY.info;

export function GroupInfoScreen({ groupId }: { readonly groupId: string }) {
  // The way out is pinned at the foot, so the screen ends at the bar's reach and the door sits
  // above the bar in flow (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  // Re-read as it opens and as it is come back to — `useGroupInfo`'s.
  const { read, reread } = useGroupInfo(groupId);
  const group = read.data;
  const { refreshing, pull } = usePull(reread);

  return (
    <SafeAreaView style={[s.screen, { paddingBottom: reach }]} edges={['top']}>
      <GroupHeader groupId={groupId} group={group} backLabel={COPY.back} />
      {group === undefined ? (
        read.error === null ? null : (
          <View style={s.body}>
            <ReadFailure
              error={read.error}
              message={codeMessage(GROUPS_COPY.group.refused, read.error)}
              onRetry={() => void read.refetch()}
            />
          </View>
        )
      ) : (
        <>
          <ScrollView
            testID="group-info-body"
            contentContainerStyle={s.body}
            refreshControl={
              // The Shell's control, drawn as the Shell draws it.
              <RefreshControl
                refreshing={refreshing}
                onRefresh={pull}
                tintColor={theme.color.muted}
                colors={[theme.color.muted]}
                progressBackgroundColor={theme.color.paper}
              />
            }
          >
            <InfoBody group={group} />
          </ScrollView>
          {/* The way out, at the screen's foot and never scrolled away (#529). */}
          <View style={s.exit}>
            <ExitDoor group={group} />
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

function InfoBody({ group }: { readonly group: Group }) {
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
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  // Under the scroll rather than over it, so nothing on Info is ever behind the door.
  exit: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.sm,
    paddingBottom: theme.size.gutter,
  },
  linkCard: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  link: { ...theme.num.s, color: theme.color.surface, flex: 1 },
  membersCard: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  words: { flex: 1, gap: theme.space.xxs },
  count: { ...theme.type.cardTitle, color: theme.color.ink },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  policy: { ...theme.type.tiny, color: theme.color.muted, flexShrink: 1 },
});
