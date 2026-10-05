/**
 * **Play, as it opens with `classic_play` off** — a *Groups | Explore* segment pinned at the top,
 * and the page for the segment under it ([#512](https://github.com/Raketa02/Raketa/issues/512),
 * play mocks 1 and 3, PRD #500 stories 1–4).
 *
 * The shell's for the reason Now, Chats and You are: a tab owns its own words and composes other
 * features' pages under them. *Groups* is `features/groups`' list; *Explore* is
 * `features/find_a_game_next`'s empty screen — the place the rebuilt Find a game will grow, which
 * is what Explore is for — so the placeholder the Play tab used to show whole now sits under the
 * segment that will fill it.
 *
 * **The segment is remembered per account on the phone**
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)),
 * and nothing is drawn until the phone has been read: a screen that drew Groups and then jumped to
 * Explore would be the flash §4 forbids. The read is a local key, so the wait is a frame.
 *
 * **The segment is pinned rather than in the page**, and it is not `ShellScreen`'s header: that
 * header shares its width with a title column, and the mocks draw the switch across the whole
 * content width, with nothing beside it. What it keeps from 10.1 is the top safe-area edge, the
 * gutter and the header's own vertical padding.
 */

import { StyleSheet, View } from 'react-native';

import { FindAGameNextScreen } from '@/features/find_a_game_next/types';
import { GroupsSection } from '@/features/groups/types';
import { Segment, theme, TopSafeArea } from '@/shared/ui';

import type { PlaySegment } from '../domain/playSegment';
import { usePlaySegment } from '../hooks/usePlaySegment';

import { PLAY_COPY } from './shellCopy';

const OPTIONS: readonly { readonly key: PlaySegment; readonly label: string }[] = [
  { key: 'groups', label: PLAY_COPY.segment.groups },
  { key: 'explore', label: PLAY_COPY.segment.explore },
];

export function PlayScreen() {
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
