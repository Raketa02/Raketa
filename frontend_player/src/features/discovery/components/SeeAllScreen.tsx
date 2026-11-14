/**
 * **A people row's See all** — the frame every one draws ([#801](https://github.com/Raketa02/Raketa/issues/801),
 * [#802](https://github.com/Raketa02/Raketa/issues/802); the Home rows screens §4.4, §5.3), pushed
 * over Home whose tab stays lit:
 *
 * - **Header**: ‹, the row's title, and the sport pill — *● All ‹* — which slides open over the title
 *   onto the sports the read offers, the chosen one last (`shared/ui`'s `SportPillFrame`, offering
 *   *All*; `pillChoices`).
 * - **Body**: the row's cards or tiles in the server's order, **20 to a page, the next read as the
 *   list nears its end** — one column or the caller's.
 * - **Every state**: reading (a spinner where the list will be), failed (the recovery sentence and
 *   *Try again*), offline (resumes), a later page refused (said under the list, with its own *Try
 *   again*), the empty line, and the pull, which reads every page again. **The pill keeps the last
 *   sports a read offered**, so a sport whose read is out or failed keeps *All* a tap away.
 *
 * What each row draws, and the record and sheets its cards open, are the caller's; they stand beside
 * the frame (`overlays`), and the frame hides itself from a screen reader while one is up.
 */

import { router } from 'expo-router';
import { useState, type ReactElement, type ReactNode } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { ReadFailure } from '@/features/groups/types';
import { offlineMessage } from '@/shared/errors';
import {
  Note,
  ScreenHeader,
  SportPillFrame,
  TopSafeArea,
  behindOverlay,
  theme,
  type SportPillWords,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { pillChoices, type SeeAllSport } from '../domain/seeAll';
import type { SeeAllList } from '../hooks/useSeeAllPages';

/** How near the end the next page is asked for — half a screen of cards. */
const NEAR_THE_END = 0.5;

export interface SeeAllScreenProps<Person extends { readonly playerId: string }> {
  readonly title: string;
  readonly backLabel: string;
  readonly pillWords: SportPillWords<SeeAllSport>;
  readonly choice: SeeAllSport;
  readonly onPick: (choice: SeeAllSport) => void;
  readonly list: SeeAllList<Person>;
  /** One person, as the row draws them here. */
  readonly renderPerson: (person: Person) => ReactElement;
  /** How many to a line — one, or the grid's columns. */
  readonly columns?: number;
  /** The empty list's line — for *All*, or the chosen sport. */
  readonly emptyLine: string;
  /** The spinner's spoken name while the first page reads. */
  readonly readingLabel: string;
  readonly testID: string;
  /** The record or sheet a card opened, drawn beside the frame. */
  readonly overlays: ReactNode;
  /** Whether one of them is up — the frame steps back from a screen reader while it is. */
  readonly overlayUp: boolean;
}

export function SeeAllScreen<Person extends { readonly playerId: string }>({
  title,
  backLabel,
  pillWords,
  choice,
  onPick,
  list,
  overlays,
  overlayUp,
  ...body
}: SeeAllScreenProps<Person>) {
  // The last sports a read offered: a sport whose read is still out, or failed, keeps the pill —
  // and the way back to *All* with it.
  const [offered, setOffered] = useState<readonly Sport[]>();
  if (list.sports !== undefined && list.sports !== offered) setOffered(list.sports);

  return (
    <>
      <View style={s.root} {...behindOverlay(overlayUp)}>
        <TopSafeArea style={s.screen}>
          <SportPillFrame<SeeAllSport>
            sports={offered === undefined ? undefined : pillChoices(offered, choice)}
            sport={choice}
            onPick={onPick}
            words={pillWords}
            header={(pill) => (
              <ScreenHeader
                onBack={() => router.back()}
                backLabel={backLabel}
                title={title}
                right={pill}
              />
            )}
          >
            <Body list={list} {...body} />
          </SportPillFrame>
        </TopSafeArea>
      </View>
      {overlays}
    </>
  );
}

type BodyProps<Person extends { readonly playerId: string }> = Pick<
  SeeAllScreenProps<Person>,
  'list' | 'renderPerson' | 'columns' | 'emptyLine' | 'readingLabel' | 'testID'
>;

function Body<Person extends { readonly playerId: string }>({
  list,
  renderPerson,
  columns = 1,
  emptyLine,
  readingLabel,
  testID,
}: BodyProps<Person>) {
  // A pull is the pull's own state, never the query's: a background read spins nothing.
  const [pulling, setPulling] = useState(false);

  if (list.people === undefined) {
    return (
      <View style={s.standing}>
        {list.error !== null ? (
          <ReadFailure error={list.error} onRetry={list.retry} />
        ) : list.paused ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : (
          <ActivityIndicator accessibilityLabel={readingLabel} color={theme.color.muted} />
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
    <FlatList<Person>
      testID={testID}
      data={list.people}
      keyExtractor={(person) => person.playerId}
      numColumns={columns}
      {...(columns > 1 ? { columnWrapperStyle: s.columns } : {})}
      contentContainerStyle={s.content}
      renderItem={({ item }) => renderPerson(item)}
      ListEmptyComponent={
        <Text testID={`${testID}-empty`} style={s.empty}>
          {emptyLine}
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
  // 9 between cards and tiles, both ways; 15 at the gutter (Appendix B).
  columns: { gap: theme.space.sm },
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
