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
 * - **Every state** is See all's: reading, failed (the recovery sentence and *Try again*), offline
 *   (resumes), a later page refused (said under the list, with its own *Try again*), the empty line,
 *   the end (nothing more is asked), and the pull, which reads every page again.
 * - **Reading shimmers, as See all does** ([#872](https://github.com/Raketa02/Raketa/issues/872); PRD
 *   #867; the loading shimmer log §10): while the first page is out with nothing to draw, **the card
 *   stands as its skeleton at the content's whole width, as many as fill the screen**
 *   (`HottestGroupCardSkeleton`), under the real header, and the page comes in on one cross-fade once
 *   that read finishes (`Reveal`) — landed, refused, or held for a connection, so the failure and the
 *   offline note take the skeleton's place. A read refused once and asked again is still on its way:
 *   the skeleton stays through Query's retries, and *Try again* or the connection back stands it again.
 *   A later page keeps the foot's behaviour, and a pull never shows the skeleton.
 * - **The taps are the line's** (`useHottestTaps`): a card opens the same group sheet, and the chips
 *   make the same writes, drawn at once here and on the line under the page. While the sheet is up
 *   the page steps back from a screen reader.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';

import { offlineMessage } from '@/shared/errors';
import {
  Note,
  Reveal,
  ScreenHeader,
  SkeletonGround,
  TopSafeArea,
  behindOverlay,
  theme,
} from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import { useHottestGroupsPage, type HottestGroupsList } from '../hooks/useHottestGroups';

import { GROUPS_COPY } from './groupsCopy';
import { HottestGroupCard, HottestGroupCardSkeleton, hottestCardHeight } from './HottestGroupCard';
import { useHottestTaps, type HottestTaps } from './HottestGroupTaps';
import { ReadFailure } from './ReadFailure';

const PAGE = GROUPS_COPY.hottest.page;

/** How near the end the next page is asked for — half a screen of cards, as See all asks. */
const NEAR_THE_END = 0.5;

/** 9 between cards (Appendix B). */
const CARD_GAP = theme.space.sm;

export function HottestGroupsScreen() {
  const list = useHottestGroupsPage();
  const taps = useHottestTaps(list.groups ?? NO_GROUPS);
  // The content width: 15 at each gutter (Appendix B).
  const { width: screen } = useWindowDimensions();
  const width = screen - 2 * theme.size.gutter;
  // The first page's read has finished — landed, refused after its retries, or held for a
  // connection — so what it drew, its failure or the offline note takes the skeleton's place.
  const finished = list.groups !== undefined || list.error !== null || list.paused;

  return (
    <>
      <View style={s.root} {...behindOverlay(taps.sheetUp)}>
        <TopSafeArea style={s.screen}>
          <ScreenHeader onBack={() => router.back()} backLabel={PAGE.back} title={PAGE.title} />
          <SkeletonGround style={s.below}>
            <Reveal
              finished={finished}
              landed={list.groups !== undefined}
              style={s.below}
              skeleton={<HottestGroupsSkeleton width={width} />}
            >
              <Body list={list} taps={taps} width={width} />
            </Reveal>
          </SkeletonGround>
        </TopSafeArea>
      </View>
      {taps.sheet}
    </>
  );
}

const NO_GROUPS: readonly HottestGroup[] = [];

/**
 * **The first page's place** (#872): cards as skeletons at the content's width, `sm` apart — as many
 * as fill the room under the header (the window's height until it is laid out, the room clipping what
 * falls past its foot), so no card stands wholly off screen moving with the band.
 */
function HottestGroupsSkeleton({ width }: { readonly width: number }) {
  const window = useWindowDimensions();
  const [room, setRoom] = useState<number>();
  const tall = hottestCardHeight(window.fontScale);
  const cards = Math.ceil((room ?? window.height) / (tall + CARD_GAP));

  return (
    <View
      testID="hottest-groups-skeleton"
      style={s.skeleton}
      onLayout={(event) => setRoom(event.nativeEvent.layout.height)}
    >
      {Array.from({ length: cards }, (_card, at) => (
        <HottestGroupCardSkeleton key={`card-${at}`} width={width} height={tall} />
      ))}
    </View>
  );
}

function Body({
  list,
  taps,
  width,
}: {
  readonly list: HottestGroupsList;
  readonly taps: HottestTaps;
  readonly width: number;
}) {
  // A pull is the pull's own state, never the query's: a background read spins nothing.
  const [pulling, setPulling] = useState(false);

  if (list.groups === undefined) {
    // While the read is out, nothing: the skeleton stands over this place.
    return list.error !== null ? (
      <View style={s.standing}>
        <ReadFailure error={list.error} onRetry={list.retry} />
      </View>
    ) : list.paused ? (
      <View style={s.standing}>
        <Note variant="amber">{offlineMessage('resumes')}</Note>
      </View>
    ) : null;
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
  below: { flex: 1 },
  standing: { paddingHorizontal: theme.size.gutter, paddingTop: theme.space.lg },
  // 9 between cards; 15 at the gutter (Appendix B).
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.xxl,
    gap: CARD_GAP,
  },
  // The list's own gutter and gaps, clipped at the room's foot.
  skeleton: {
    flex: 1,
    paddingHorizontal: theme.size.gutter,
    gap: CARD_GAP,
    overflow: 'hidden',
  },
  empty: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.xl,
  },
});
