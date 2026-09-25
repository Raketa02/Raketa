/**
 * **A group's page** — its header with the sport filter, the four tabs, and Games, Fill in and
 * Friends in the state of a group that is just starting (play 14–17, 39–55; #512, #513). Info is
 * [#514](https://github.com/Raketa02/Raketa/issues/514)'s and is empty here.
 *
 * Reached from a card on the Groups list, and **replacing** New group once a group is created, so
 * *back* from here is the list either way. A group created a moment ago is drawn at once — the
 * create's answer seeded its read — with *Group created* over it.
 *
 * **It always opens on Games** (story 51) — which tab it was on is not kept (ADR-0188 §5) — and
 * **on the sport last picked anywhere in Play**, which is (`useGroupSport`). Games, Fill in and
 * Friends are all drawn for that sport, and the pill in the header changes it for every one of
 * them at once.
 *
 * **The filter's bar floats over the header and the page under it**: a layer drawn last, laid over
 * the header's own box, with a backdrop across the whole page beneath it — so a tap anywhere but
 * a sport folds it and changes nothing, and so does the back button on Android while it is open.
 * The shell's tab bar is outside the page and stays live; leaving by it folds the bar too.
 * It is never a `Modal` (ADR-0178). The header's box is measured for it, because the bar has to
 * stand exactly where the pill stands.
 *
 * **Every state has its drawing.** While the read is on its way the header has only its way back.
 * `group_not_found` is one sentence, because the server gives the same answer for *no such group*
 * and *not one of yours* and both have one remedy; any other failure says why and offers the retry.
 * The tabs wait for the sport as well as the group: the phone is read before anything is drawn for
 * a sport, so nothing is drawn for one and then redrawn for another (ADR-0188 §4).
 */

import { router, useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { useHardwareBack } from '@/shared/lib/platform';
import { ScreenHeader, Segment, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { GROUP_TABS, OPENING_TAB, type GroupTab } from '../domain/groupPage';
import { useGroupSport } from '../hooks/useGroupSport';
import { useGroup } from '../hooks/useGroups';

import { FillInTab, PostAGame } from './FillInTab';
import { FriendsTab } from './FriendsTab';
import { GamesTab } from './GamesTab';
import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { membersAtClub } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';
import { SportBar, SportPill } from './SportFilter';

const COPY = GROUPS_COPY.group;

/** The four tabs' words — read at load, so from the import-free copy module (`groupsCopy.ts`). */
const TABS = GROUP_TABS.map((key) => ({ key, label: GROUPS_COPY.group.tabs[key] }));

export function GroupScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;
  const { sports, sport, choose } = useGroupSport();

  const [tab, setTab] = useState<GroupTab>(OPENING_TAB);
  const [unfolded, setUnfolded] = useState(false);
  const [headerHeight, setHeaderHeight] = useState<number>();

  const fold = () => setUnfolded(false);

  function pick(picked: Sport) {
    if (picked !== sport) choose(picked);
    fold();
  }

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <View style={s.page}>
        <View onLayout={(event) => setHeaderHeight(event.nativeEvent.layout.height)}>
          <ScreenHeader
            compact
            onBack={() => router.back()}
            backLabel={COPY.back}
            lead={
              group === undefined ? undefined : (
                <GroupMonogram monogram={group.monogram} size="header" />
              )
            }
            title={group?.name}
            subline={
              group === undefined
                ? undefined
                : membersAtClub(group.memberCount, group.homeClub.name)
            }
            right={
              group === undefined || sports === undefined || sport === undefined ? undefined : (
                <SportPill sports={sports} sport={sport} onUnfold={() => setUnfolded(true)} />
              )
            }
          />
        </View>

        {group === undefined ? (
          read.error === null ? null : (
            <View style={s.body}>
              <ReadFailure
                error={read.error}
                message={codeMessage(COPY.refused, read.error)}
                onRetry={() => void read.refetch()}
              />
            </View>
          )
        ) : (
          <>
            <Segment options={TABS} selected={tab} onSelect={setTab} style={s.tabs} />
            <ScrollView contentContainerStyle={s.body}>
              {sport === undefined ? null : <TabBody tab={tab} group={group} sport={sport} />}
            </ScrollView>
            {tab === 'fillIn' ? (
              <View style={s.postAGame}>
                <PostAGame />
              </View>
            ) : null}
          </>
        )}

        {unfolded && sports !== undefined && sport !== undefined ? (
          <>
            <FoldAway onFold={fold} />
            <Pressable
              testID="sport-filter-backdrop"
              onPress={fold}
              accessible={false}
              importantForAccessibility="no"
              style={StyleSheet.absoluteFill}
            />
            <View
              pointerEvents="box-none"
              style={[s.barSlot, headerHeight === undefined ? undefined : { height: headerHeight }]}
            >
              <SportBar sports={sports} sport={sport} onChoose={pick} />
            </View>
          </>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

function TabBody({
  tab,
  group,
  sport,
}: {
  readonly tab: GroupTab;
  readonly group: Group;
  readonly sport: Sport;
}) {
  switch (tab) {
    case 'games':
      return <GamesTab group={group} sport={sport} />;
    case 'fillIn':
      return <FillInTab group={group} />;
    case 'friends':
      return <FriendsTab group={group} sport={sport} />;
    case 'info':
      return null;
  }
}

/**
 * **What folds an open bar besides a tap** — mounted only while it is open. Android's back folds it
 * rather than leaving the page (closed, back is the navigator's again). And the page losing focus
 * folds it: the shell's tab bar is outside the page and the backdrop cannot cover it, so a tap
 * there leaves the page with the bar open, and it must not be open when the player comes back.
 */
function FoldAway({ onFold }: { readonly onFold: () => void }) {
  useHardwareBack(onFold);

  // Through a ref, so the blur subscription is made once rather than on every render of a parent
  // whose `fold` is a new function each time — a cleanup per render would fold on every render.
  const latest = useRef(onFold);
  latest.current = onFold;
  useFocusEffect(useCallback(() => () => latest.current(), []));

  return null;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  // The layer the bar is laid over: no padding of its own, so its top is the header's.
  page: { flex: 1 },
  tabs: { marginHorizontal: theme.size.gutter },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  // Over the header's box, right-aligned so the current sport stands where the pill stood: the
  // bar's inset is taken back out of the gutter.
  barSlot: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingHorizontal: theme.size.gutter - theme.size.groupPage.filterPad,
  },
  // Over the page's bottom corner, at the gutter (play 46).
  postAGame: { position: 'absolute', right: theme.size.gutter, bottom: theme.size.gutter },
});
