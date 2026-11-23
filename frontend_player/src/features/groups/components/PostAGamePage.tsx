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
 * **It turns the page under it to You’re in as it opens** (`groupTab.store`; #847's interim, Fill in
 * until then): every way back — the chevron, the hardware back, the swipe — lands there, and so does
 * a post, whether the player came from You’re in's button or from *Nothing picked right now* on
 * Games. The ticket after it (#848) leaves the page alone on opening, lands only a post on You’re in,
 * and backs out to the tab Post a game came from.
 *
 * **Rated in none of the group's sports** (an official group's, #519), there is nothing to post:
 * *Get rated in padel to post here*, with the passport's *Add a sport* for each (Q80) — whose pass
 * returns to the group, on You’re in (#729, #847). **Rated in nothing, in a player group**, it is the
 * door where play begins instead (#730, ADR-0200 §2): every way of playing asks the same thing, and the
 * pass it begins returns to You’re in too. While the group or the phone is still being read, the
 * header alone; a refused read says why with the retry.
 */

import { router } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { LevelDoor, fromAGroup } from '@/features/onboarding/types';
import { POSTING_COPY, PostAGameScreen, type PostingSport } from '@/features/proposals/types';
import { codeMessage } from '@/shared/errors';
import { ScreenHeader, theme } from '@/shared/ui';

import { useGroup } from '../hooks/useGroups';
import { useGroupSport } from '../hooks/useGroupSport';
import { useGameIntent } from '../store/gameIntent.store';
import { useGroupTab } from '../store/groupTab.store';

import { AddSportCard } from './AddSportCard';
import { groupRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { rateToPostHeadline } from './groupsPresentation';
import { ReadFailure } from './ReadFailure';

export function PostAGamePage({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;
  const { sports, sport, toAdd, needsALevel } = useGroupSport(group?.declaredSports);
  const chosen = useGameIntent((state) => state.intent);

  // The page under this one goes to You’re in now, unseen, so every way back arrives there.
  useEffect(() => {
    useGroupTab.getState().show(groupId, 'youreIn');
  }, [groupId]);

  const leave = () => {
    if (router.canGoBack()) router.back();
    else router.replace(groupRoute(groupId));
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
        onLeave={leave}
      />
    );
  }

  const unrated = group === undefined ? [] : toAdd.length > 0 ? toAdd : group.sports;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={POSTING_COPY.title} onBack={leave} backLabel={POSTING_COPY.back} />
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
          // A pass begun here returns to the group on You’re in — where this screen put the page
          // under it, and where every way back from it lands (#729).
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
