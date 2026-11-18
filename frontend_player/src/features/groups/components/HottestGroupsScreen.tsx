/**
 * **Groups heating up** — every group with 3 or more players, hottest first, page by page
 * ([#823](https://github.com/Raketa02/Raketa/issues/823); ADR-0205 §7, Q18, Q35, Q36; the Home rows
 * screens §3.6; the mechanics §5.10), pushed over Home by its line's *All groups ›*, the Home tab
 * still lit. **Shaped like the people See all screens** (`discovery`'s `SeeAllScreen`), without their
 * sport pill — the page has no filter:
 *
 * ```
 * ‹  Groups heating up                          ← ScreenHeader: back to Home, the title a header
 * ╭──────────────────────────────────────────╮
 * │╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱ ▲ HOTTEST │  ← the line's card, at the content's whole width
 * │ ┌────┐ Ogrody 33 Club                    │
 * │ 14                                    11 │
 * │ ▣▣▣▣                       ( Ask to join )│
 * ╰──────────────────────────────────────────╯
 *   9
 * ╭──────────────────────────────────────────╮  ← the next, in the row's order: HOTTEST, then
 * │ …                            ( You’re in )│    GROWING by heat, then the rest by heat — the
 * ╰──────────────────────────────────────────╯    reader's own groups among them
 * ```
 *
 * - **Body**: the cards in the server's order, **20 to a page, the next read as the list nears its
 *   end**, one column at the content width (screen − 30). The first six are the line's.
 * - **Every state** is See all's: reading (a spinner where the list will be), failed (the recovery
 *   sentence and *Try again*), offline (resumes), a later page refused (said under the list, with its
 *   own *Try again*), the empty line, the end (nothing more is asked), and the pull, which reads every
 *   page again.
 * - **The taps are the line's** (`useHottestTaps`): a card opens the same group sheet, and the chips
 *   make the same writes, drawn at once here and on the line under the page. While the sheet is up
 *   the page steps back from a screen reader.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { Note, ScreenHeader, TopSafeArea, behindOverlay, theme } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import { useHottestGroupsPage, type HottestGroupsList } from '../hooks/useHottestGroups';

import { GROUPS_COPY } from './groupsCopy';
import { HottestGroupCard } from './HottestGroupCard';
import { useHottestTaps, type HottestTaps } from './HottestGroupTaps';
import { ReadFailure } from './ReadFailure';

const PAGE = GROUPS_COPY.hottest.page;

/** How near the end the next page is asked for — half a screen of cards, as See all asks. */
const NEAR_THE_END = 0.5;

export function HottestGroupsScreen() {
  const list = useHottestGroupsPage();
  const taps = useHottestTaps(list.groups ?? NO_GROUPS);

  return (
    <>
      <View style={s.root} {...behindOverlay(taps.sheetUp)}>
        <TopSafeArea style={s.screen}>
          <ScreenHeader onBack={() => router.back()} backLabel={PAGE.back} title={PAGE.title} />
          <Body list={list} taps={taps} />
        </TopSafeArea>
      </View>
      {taps.sheet}
    </>
  );
}

const NO_GROUPS: readonly HottestGroup[] = [];

function Body({ list, taps }: { readonly list: HottestGroupsList; readonly taps: HottestTaps }) {
  // A pull is the pull's own state, never the query's: a background read spins nothing.
  const [pulling, setPulling] = useState(false);
  // The content width: 15 at each gutter (Appendix B).
  const { width: screen } = useWindowDimensions();
  const width = screen - 2 * theme.size.gutter;

  if (list.groups === undefined) {
    return (
      <View style={s.standing}>
        {list.error !== null ? (
          <ReadFailure error={list.error} onRetry={list.retry} />
        ) : list.paused ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : (
          <ActivityIndicator accessibilityLabel={PAGE.reading} color={theme.color.muted} />
        )}
      </View>
    );
  }

  const pull = () => {
    if (pulling) return;
    setPulling(true);
    void list.reread().finally(() => setPulling(false));
  };

  return (
    <FlatList<HottestGroup>
      testID="hottest-groups-list"
      data={list.groups}
      keyExtractor={(group) => group.id}
      contentContainerStyle={s.content}
      renderItem={({ item }) => (
        <HottestGroupCard
          group={item}
          width={width}
          onOpen={() => taps.openSheet(item.id)}
          onChip={(action) => taps.chip(item, action)}
        />
      )}
      ListEmptyComponent={
        <Text testID="hottest-groups-list-empty" style={s.empty}>
          {PAGE.nobody}
        </Text>
      }
      ListFooterComponent={
        list.moreFailure === undefined ? null : (
          <ReadFailure error={list.moreFailure.error} onRetry={list.moreFailure.retry} />
        )
      }
      onEndReached={list.loadMore}
      onEndReachedThreshold={NEAR_THE_END}
      refreshControl={
        <RefreshControl
          refreshing={pulling}
          onRefresh={pull}
          tintColor={theme.color.muted}
          colors={[theme.color.muted]}
          progressBackgroundColor={theme.color.paper}
        />
      }
    />
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  screen: { flex: 1, backgroundColor: theme.color.paper },
  standing: { paddingHorizontal: theme.size.gutter, paddingTop: theme.space.lg },
  // 9 between cards; 15 at the gutter (Appendix B).
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.xxl,
    gap: theme.space.sm,
  },
  empty: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.xl,
  },
});
