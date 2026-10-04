/**
 * **Play › Groups** — the groups the player belongs to, newest joined first, and the two ways to
 * another: **+ New** and **Join** (play 1, 38; stories 1, 5–8).
 *
 * Drawn under Play's segment, which is the tab's and the shell's; this is the page the *Groups*
 * segment shows. It scrolls on its own, below the pinned segment.
 *
 * **Every state has its drawing.** Nothing while the first read is on its way — the list is local
 * and quick, and a spinner that flashed for a frame would be the only thing on screen that moved.
 * A failed read says why and offers the retry, above the buttons that still work. An empty list is
 * one card saying what to do (story 8) — a card, and *No groups yet*, because the ticket names
 * both; 10.1's own line is one `tiny` sentence that never says nothing is here, and Part 16
 * records the departure. The buttons are there in every state: creating or joining
 * never waits on the list.
 *
 * **A pull reads the list again** (#529), drawn as the Shell draws its pull — a group joined or
 * left on another phone is on it when the spinner stops, without leaving the list and coming back.
 */

import { router } from 'expo-router';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Button, Card, theme } from '@/shared/ui';

import { useGroupsList, useMyGroupsReread } from '../hooks/useGroups';
import { usePull } from '../hooks/usePull';

import { GroupCard } from './GroupCard';
import { JOIN_GROUP_ROUTE, NEW_GROUP_ROUTE } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { ReadFailure } from './ReadFailure';

const COPY = GROUPS_COPY.list;

export function GroupsSection() {
  const groups = useGroupsList();
  const { refreshing, pull } = usePull(useMyGroupsReread());

  return (
    <ScrollView
      testID="groups-list"
      contentContainerStyle={s.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={pull}
          tintColor={theme.color.muted}
          colors={[theme.color.muted]}
          progressBackgroundColor={theme.color.paper}
        />
      }
    >
      <View style={s.actions}>
        <Button
          label={COPY.newGroup}
          accessibilityLabel={COPY.newGroupLabel}
          variant="secondary"
          onPress={() => router.push(NEW_GROUP_ROUTE)}
        />
        <Button
          label={COPY.join}
          accessibilityLabel={COPY.joinLabel}
          onPress={() => router.push(JOIN_GROUP_ROUTE)}
        />
      </View>

      {groups.error !== null && groups.data === undefined ? (
        <ReadFailure error={groups.error} onRetry={() => void groups.refetch()} />
      ) : null}

      {groups.data !== undefined && groups.data.length === 0 ? (
        <Card>
          <Text style={s.empty}>{COPY.empty}</Text>
        </Card>
      ) : null}

      {groups.data?.map((group) => (
        <GroupCard key={group.id} group={group} />
      ))}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: theme.space.sm,
  },
  // 10.1's empty line — `tiny` in `muted` — inside the card #512 and story 8 name.
  empty: { ...theme.type.tiny, color: theme.color.muted },
});
