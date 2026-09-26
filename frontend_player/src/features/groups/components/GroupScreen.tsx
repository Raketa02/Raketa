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
 * **Every state has its drawing.** While the read is on its way the header has only its way back.
 * `group_not_found` is one sentence, because the server gives the same answer for *no such group*
 * and *not one of yours* and both have one remedy; any other failure says why and offers the retry.
 * The tabs wait for the sport as well as the group: the phone is read before anything is drawn for
 * a sport, so nothing is drawn for one and then redrawn for another (ADR-0188 §4).
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { ScreenHeader, Segment, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { GROUP_TABS, OPENING_TAB, type GroupTab } from '../domain/groupPage';
import { useGroup } from '../hooks/useGroups';

import { AddSportCard } from './AddSportCard';
import { FillInTab, PostAGame } from './FillInTab';
import { FriendsTab } from './FriendsTab';
import { GamesTab } from './GamesTab';
import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { membersAtClub } from './groupsPresentation';
import { InfoTab } from './InfoTab';
import { ReadFailure } from './ReadFailure';
import { SportFilterPage } from './SportFilterPage';

const COPY = GROUPS_COPY.group;

/** The four tabs' words — read at load, so from the import-free copy module (`groupsCopy.ts`). */
const TABS = GROUP_TABS.map((key) => ({ key, label: GROUPS_COPY.group.tabs[key] }));

export function GroupScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;

  const [tab, setTab] = useState<GroupTab>(OPENING_TAB);

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
        {(sport, toAdd) =>
          group === undefined ? (
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
                {/* Info is about the group rather than a sport, so it never waits for the filter. */}
                {tab === 'info' ? (
                  <InfoTab group={group} />
                ) : toAdd.length > 0 ? (
                  <AddSportCard sports={toAdd} />
                ) : sport === undefined ? null : (
                  <TabBody tab={tab} group={group} sport={sport} />
                )}
              </ScrollView>
              {tab === 'fillIn' && toAdd.length === 0 ? (
                <View style={s.postAGame}>
                  <PostAGame />
                </View>
              ) : null}
            </>
          )
        }
      </SportFilterPage>
    </SafeAreaView>
  );
}

/** The three tabs drawn for the filter's sport. */
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
      return <FillInTab group={group} />;
    case 'friends':
      return <FriendsTab group={group} sport={sport} />;
  }
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  tabs: { marginHorizontal: theme.size.gutter },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  // Over the page's bottom corner, at the gutter (play 46).
  postAGame: { position: 'absolute', right: theme.size.gutter, bottom: theme.size.gutter },
});
