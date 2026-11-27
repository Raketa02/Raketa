/**
 * **Play** — the player's groups, and, behind the `explore` feature flag, a *Groups | Explore*
 * segment pinned at the top with the page for the segment under it
 * ([#512](https://github.com/Raketa02/Raketa/issues/512), play mocks 1 and 3, PRD #500 stories 1–4;
 * [#826](https://github.com/Raketa02/Raketa/issues/826),
 * [ADR-0206](../../../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)
 * §11).
 *
 * The shell's for the reason Home and You are: a tab owns its own words and composes other
 * features' pages under them. *Groups* is `features/groups`' list; *Explore* is
 * `features/find_a_game_next`'s empty screen — the place the rebuilt Find a game will grow, which
 * is what Explore is for.
 *
 * **The feature flag is read once, when Play mounts** (`useFeatureOnMount`), and only an explicit
 * **on** draws the switcher: no datafile, a refused one or no signed-in player is off. A datafile
 * that lands while Play is up changes nothing until Play next mounts, so Explore never appears or
 * vanishes under the player's thumb. The two pages are two components because they read different
 * things, and the answer cannot change under either.
 *
 * **Off — Play as it ships** — is the Administrator's Groups tab exactly: a pinned `ScreenHeader`
 * titled *Groups* over the groups list, which scrolls and refreshes under it with + New and Join
 * where they always are. There is no segment and Explore cannot be reached, so the remembered
 * segment is **never read and never written**: a saved `explore` stays the player's own choice
 * (ADR-0188) for the day the feature flag comes on. Not `ShellScreen`, whose scroller would nest the
 * list's own.
 *
 * **On — today's Play, unchanged.** The segment is remembered per account on the phone
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)),
 * and nothing is drawn until the phone has been read: a screen that drew Groups and then jumped to
 * Explore would be the flash §4 forbids. The read is a local key, so the wait is a frame. The
 * segment is pinned rather than in the page, and it is not `ShellScreen`'s header: that header
 * shares its width with a title column, and the mocks draw the switch across the whole content
 * width, with nothing beside it. What it keeps from 10.1 is the top safe-area edge, the gutter and
 * the header's own vertical padding.
 */

import { StyleSheet, View } from 'react-native';

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { FindAGameNextScreen } from '@/features/find_a_game_next/types';
import { GroupsSection } from '@/features/groups/types';
import { ScreenHeader, Segment, theme, TopSafeArea } from '@/shared/ui';

import type { PlaySegment } from '../domain/playSegment';
import { usePlaySegment } from '../hooks/usePlaySegment';

import { PLAY_COPY } from './shellCopy';

const OPTIONS: readonly { readonly key: PlaySegment; readonly label: string }[] = [
  { key: 'groups', label: PLAY_COPY.segment.groups },
  { key: 'explore', label: PLAY_COPY.segment.explore },
];

export function PlayScreen() {
  const explore = useFeatureOnMount('explore');

  return explore ? <PlaySegments /> : <PlayGroups />;
}

/** `explore` off: the groups, under one *Groups* title. */
function PlayGroups() {
  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader title={PLAY_COPY.title} />
      <GroupsSection />
    </TopSafeArea>
  );
}

/** `explore` on: the *Groups | Explore* switcher and the remembered segment's page. */
function PlaySegments() {
  const { segment, choose } = usePlaySegment();

  return (
    <TopSafeArea style={s.screen}>
      {segment === undefined ? null : (
        <>
          <View style={s.head}>
            <Segment options={OPTIONS} selected={segment} onSelect={choose} prominent />
          </View>
          {segment === 'groups' ? <GroupsSection /> : <FindAGameNextScreen />}
        </>
      )}
    </TopSafeArea>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  head: { paddingHorizontal: theme.size.gutter, paddingVertical: theme.space.md },
});
