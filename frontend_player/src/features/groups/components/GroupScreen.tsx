/**
 * **A group's page** — its header with the sport filter, the four tabs, Games, Fill in and
 * Friends in the state of a group that is just starting (play 14–17, 39–55; #512, #513), and Info
 * (play 57–60; [#514](https://github.com/Raketa02/Raketa/issues/514)).
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
 * **The filter's bar floats over the header and the page under it** — `SportFilterPage`'s, which
 * Members shares. On an official group it lists only the sports the group declares (#519); a
 * member rated in none of them gets `AddSportCard` in place of Games, Fill in and Friends, and
 * Info as it is — the way out is not a sport's.
 *
 * **The Info tab counts the requests waiting on an Owner** (#529): the Chats badge at the segment's
 * size over the tab's corner, from every tab, and spoken with the tab's name — so an Owner on Games
 * knows somebody is asking without opening Info. Nobody else's page reads the requests, so nobody
 * else's tab carries a count.
 *
 * **The Games tab counts the cards where somebody is already In with you** (#553, the screens A1,
 * mock 1's *Games 4*): the same badge, off the deck's own read — the one the tab draws, for the
 * sport the page is on and the kind its switch stands on, so the two never disagree and the count
 * costs no second request. **The *Fill in* tab counts its *Seats to fill*** (#557, mock 11's *Fill
 * in 1*) — the rescue board's own badge, read for the page's sport.
 *
 * **Fill in is `proposals`' board** (#557): *Seats to fill* and *You're In*, and — with neither — the
 * starting card a group has always drawn there (`FillInTab`), handed in as the Games tab hands in
 * its own. *+ Post a game* floats over the page's corner and opens *Post a game* (#558).
 *
 * **Which tab it is on is the page's store** (`groupTab.store`, #558) rather than its state, because
 * *Post a game* turns it to Fill in from over the page, so every way back lands on *You're In*; the
 * entry, and the post's draft with it, go when the page does.
 *
 * **Games lays itself out** (#553): the deck fills the page between the switch and its three
 * buttons, so it is drawn outside the page's scroller, and scrolls itself in the states that are
 * not a deck — the question, the starting card.
 *
 * **Info re-reads on a pull** (#529) — the group, who is waiting and the members row with it.
 * Only Info: the other three tabs are drawn for a sport and read their own rows.
 *
 * **Every state has its drawing.** While the read is on its way the header has only its way back.
 * `group_not_found` is one sentence, because the server gives the same answer for *no such group*
 * and *not one of yours* and both have one remedy; any other failure says why and offers the retry.
 * The tabs wait for the sport as well as the group: the phone is read before anything is drawn for
 * a sport, so nothing is drawn for one and then redrawn for another (ADR-0188 §4).
 */

import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  FillInBoard,
  forgetPostDraft,
  useFillInBadge,
  useGamesBadge,
} from '@/features/proposals/types';
import { codeMessage } from '@/shared/errors';
import { ScreenHeader, Segment, theme, type SegmentOption } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { GROUP_TABS, OPENING_TAB, type GroupTab } from '../domain/groupPage';
import { useGroup, useGroupReread, useJoinRequests } from '../hooks/useGroups';
import { useGameIntent } from '../store/gameIntent.store';
import { useGroupTab } from '../store/groupTab.store';

import { AddSportCard } from './AddSportCard';
import { FillInTab, PostAGame } from './FillInTab';
import { FriendsTab } from './FriendsTab';
import { GamesTab } from './GamesTab';
import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { fillInTabLabel, gamesTabLabel, infoTabLabel, membersAtClub } from './groupsPresentation';
import { InfoTab } from './InfoTab';
import { ReadFailure } from './ReadFailure';
import { SportFilterPage } from './SportFilterPage';

const COPY = GROUPS_COPY.group;

/** The four tabs' words — read at load, so from the import-free copy module (`groupsCopy.ts`). */
const TABS = GROUP_TABS.map((key) => ({ key, label: GROUPS_COPY.group.tabs[key] }));

/** The four tabs, Info carrying how many are waiting on an Owner. */
function useGroupTabs(groupId: string, isOwner: boolean): readonly SegmentOption<GroupTab>[] {
  const requests = useJoinRequests(groupId, isOwner);
  // The Owner's alone: a page read after the reader stopped owning the group keeps no count, even
  // with an old answer still cached under the key.
  const waiting = isOwner ? (requests.data?.length ?? 0) : 0;

  return TABS.map((option) =>
    option.key !== 'info' || waiting === 0
      ? option
      : { ...option, badge: waiting, accessibilityLabel: infoTabLabel(waiting) },
  );
}

interface GroupTabsProps {
  readonly groupId: string;
  readonly isOwner: boolean;
  readonly selected: GroupTab;
  readonly onSelect: (tab: GroupTab) => void;
}

/** The tab bar — with Games' and Fill in's counts once there is a sport to read them for. */
function GroupTabs({ sport, ...props }: GroupTabsProps & { readonly sport: Sport | undefined }) {
  const tabs = useGroupTabs(props.groupId, props.isOwner);
  return sport === undefined ? (
    <Segment options={tabs} selected={props.selected} onSelect={props.onSelect} style={s.tabs} />
  ) : (
    <TabsWithCounts {...props} tabs={tabs} sport={sport} />
  );
}

function TabsWithCounts({
  groupId,
  selected,
  onSelect,
  tabs,
  sport,
}: GroupTabsProps & { readonly tabs: readonly SegmentOption<GroupTab>[]; readonly sport: Sport }) {
  const chosen = useGameIntent((state) => state.intent);
  const games = useGamesBadge(groupId, sport, chosen);
  const seats = useFillInBadge(groupId, sport);
  const counted = tabs.map((option) => {
    if (option.key === 'games' && games > 0) {
      return { ...option, badge: games, accessibilityLabel: gamesTabLabel(games) };
    }
    if (option.key === 'fillIn' && seats > 0) {
      return { ...option, badge: seats, accessibilityLabel: fillInTabLabel(seats) };
    }
    return option;
  });
  return <Segment options={counted} selected={selected} onSelect={onSelect} style={s.tabs} />;
}

/** A pull's spinner: on from the pull until the re-read has settled, and one pull at a time. */
function usePull(reread: () => Promise<void>) {
  const [refreshing, setRefreshing] = useState(false);
  const inFlight = useRef(false);

  async function pull() {
    if (inFlight.current) return;
    inFlight.current = true;
    setRefreshing(true);
    try {
      await reread();
    } catch {
      // A refused re-read is the read's own to say, on what it draws; the spinner only stops.
    } finally {
      inFlight.current = false;
      setRefreshing(false);
    }
  }

  return { refreshing, pull: () => void pull() };
}

export function GroupScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;

  const tab = useGroupTab((state) => state.tabs[groupId]) ?? OPENING_TAB;
  const show = useGroupTab((state) => state.show);
  const setTab = (next: GroupTab) => show(groupId, next);
  const { refreshing, pull } = usePull(useGroupReread(groupId));

  // The page's tab and *Post a game*'s draft are kept while the page is up, and go with it — so it
  // opens on Games the next time, and the next post starts from nothing.
  useEffect(
    () => () => {
      useGroupTab.getState().forget(groupId);
      forgetPostDraft(groupId);
    },
    [groupId],
  );

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <SportFilterPage
        {...(group?.declaredSports === undefined ? {} : { declaredSports: group.declaredSports })}
        header={(pill) => (
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
            right={group === undefined ? undefined : pill}
          />
        )}
      >
        {(sport, toAdd) => {
          // The sport the three sport tabs are drawn for — none while the reader must add one.
          const playing = toAdd.length === 0 ? sport : undefined;
          return group === undefined ? (
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
              <GroupTabs
                groupId={groupId}
                isOwner={group.isOwner}
                sport={playing}
                selected={tab}
                onSelect={setTab}
              />
              {tab === 'games' && playing !== undefined ? (
                // The deck lays itself out — see the module note.
                <View style={s.fill}>
                  <GamesTab group={group} sport={playing} />
                </View>
              ) : (
                <ScrollView
                  contentContainerStyle={s.body}
                  refreshControl={
                    tab === 'info' ? (
                      // The Shell's control, drawn as the Shell draws it.
                      <RefreshControl
                        refreshing={refreshing}
                        onRefresh={pull}
                        tintColor={theme.color.muted}
                        colors={[theme.color.muted]}
                        progressBackgroundColor={theme.color.paper}
                      />
                    ) : undefined
                  }
                >
                  {/* Info is about the group rather than a sport, so it never waits for the filter. */}
                  {tab === 'info' ? (
                    <InfoTab group={group} />
                  ) : toAdd.length > 0 ? (
                    <AddSportCard sports={toAdd} />
                  ) : sport === undefined ? null : (
                    <TabBody tab={tab} group={group} sport={sport} />
                  )}
                </ScrollView>
              )}
              {tab === 'fillIn' && toAdd.length === 0 ? (
                <View style={s.postAGame}>
                  <PostAGame groupId={groupId} />
                </View>
              ) : null}
            </>
          );
        }}
      </SportFilterPage>
    </SafeAreaView>
  );
}

/** The two scrolled tabs drawn for the filter's sport; Games lays itself out. */
function TabBody({
  tab,
  group,
  sport,
}: {
  readonly tab: Exclude<GroupTab, 'info'>;
  readonly group: Group;
  readonly sport: Sport;
}) {
  switch (tab) {
    case 'games':
      return <GamesTab group={group} sport={sport} />;
    case 'fillIn':
      return <FillInBoard groupId={group.id} sport={sport} empty={<FillInTab group={group} />} />;
    case 'friends':
      return <FriendsTab group={group} sport={sport} />;
  }
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  tabs: { marginHorizontal: theme.size.gutter },
  fill: { flex: 1 },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  // Over the page's bottom corner, at the gutter (play 46).
  postAGame: { position: 'absolute', right: theme.size.gutter, bottom: theme.size.gutter },
});
