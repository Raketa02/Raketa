/**
 * ***Post a game*, over a group's page** — what only the group knows, handed to `proposals`' screen
 * ([#558](https://github.com/Raketa02/Raketa/issues/558); the screens A5, A5.1; Q80).
 *
 * The screen is `proposals`', and the edge points one way — `groups` reads `proposals`, never the
 * reverse — so this page hands in what the group says: **the sports the reader may post in here**,
 * which are the page's own filter (`useGroupSport`: what they are rated in, among an official
 * group's declared sports), **each with how many members are rated in it** (the group's roster,
 * *Padel 10*); the sport the page is on; and the kind its switch stands on (`gameIntent.store`).
 *
 * **It leaves the page under it alone** (#848, PRD #844; #847 turned it to You’re in as it opened).
 * The tab the page stands on as this opens is the **origin** (`groupTab.store`, Games when the page
 * has not moved off its opening tab): every way back — the chevron, the hardware back, the swipe —
 * returns to the page as it was, on that tab, and the chevron names it (*Back to Games*, *Back to
 * You’re in*). **A post lands on You’re in**, from You’re in's button or *Nothing picked right now*
 * on Games, and so does a join from a cell's sheet: only then is the page turned, a moment before
 * it is uncovered, so the player sees the game they made. With no page under it — opened by a link —
 * the page is opened instead, on Games for a back-out and on You’re in for a landing.
 *
 * **Rated in none of the group's sports** (an official group's, #519), there is nothing to post:
 * *Get rated in padel to post here*, with the passport's *Add a sport* for each (Q80) — whose pass
 * returns to the group, on **You’re in**, where the button lives and a post lands, whichever tab this
 * was opened from (#729, #848). **Rated in nothing, in a player group**, it is the door where play
 * begins instead (#730, ADR-0200 §2): every way of playing asks the same thing, and the pass it begins
 * returns to You’re in too. While the group or the phone is still being read, the header alone; a
 * refused read says why with the retry.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LevelDoor, fromAGroup } from '@/features/onboarding/types';
import { POSTING_COPY, PostAGameScreen, type PostingSport } from '@/features/proposals/types';
import { codeMessage } from '@/shared/errors';
import { ScreenHeader, theme } from '@/shared/ui';

import { OPENING_TAB } from '../domain/groupPage';
import { useGroup } from '../hooks/useGroups';
import { useGroupSport } from '../hooks/useGroupSport';
import { useGameIntent } from '../store/gameIntent.store';
import { useGroupTab } from '../store/groupTab.store';

import { AddSportCard } from './AddSportCard';
import { groupRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { postAGameBackLabel, rateToPostHeadline } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';

export function PostAGamePage({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;
  const { sports, sport, toAdd, needsALevel } = useGroupSport(group?.declaredSports);
  const chosen = useGameIntent((state) => state.intent);

  // The tab the page stood on as this opened — read once: a landing turns the page under it.
  const [origin] = useState(() => useGroupTab.getState().tabs[groupId] ?? OPENING_TAB);
  const backLabel = postAGameBackLabel(origin);

  // Back to the page as it was — on the origin, which nothing here has touched.
  const leave = () => {
    if (router.canGoBack()) router.back();
    else router.replace(groupRoute(groupId));
  };

  // A post, or a join from a sheet: the page turns to You’re in, unseen under this, and is uncovered.
  const land = () => {
    useGroupTab.getState().show(groupId, 'youreIn');
    leave();
  };

  if (group !== undefined && sports !== undefined && sport !== undefined && toAdd.length === 0) {
    const rated: readonly PostingSport[] = sports.map((one) => ({
      sport: one,
      rated: group.ratedBySport.find((roster) => roster.sport === one)?.ratedCount ?? 0,
    }));
    return (
      <PostAGameScreen
        groupId={groupId}
        sports={rated}
        openingSport={sport}
        chosen={chosen}
        backLabel={backLabel}
        onLeave={leave}
        onLanded={land}
      />
    );
  }

  const unrated = group === undefined ? [] : toAdd.length > 0 ? toAdd : group.sports;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={POSTING_COPY.title} onBack={leave} backLabel={backLabel} />
      <View style={s.body}>
        {group === undefined ? (
          read.error === null ? (
            <ActivityIndicator
              accessibilityLabel={POSTING_COPY.opening}
              color={theme.color.muted}
            />
          ) : (
            <ReadFailure
              error={read.error}
              message={codeMessage(GROUPS_COPY.group.refused, read.error)}
              onRetry={() => void read.refetch()}
            />
          )
        ) : sports === undefined ? (
          <ActivityIndicator accessibilityLabel={POSTING_COPY.opening} color={theme.color.muted} />
        ) : needsALevel ? (
          // A player group, rated in nothing: the door, returning to You’re in for the card's reason.
          <LevelDoor from={fromAGroup(groupId, 'youreIn')} />
        ) : (
          // A pass begun here returns to the group on You’re in — where the button lives and a post
          // lands — never to the origin a back-out returns to (#729, #848).
          <AddSportCard
            sports={unrated}
            groupId={groupId}
            tab="youreIn"
            headline={rateToPostHeadline(unrated)}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
});
