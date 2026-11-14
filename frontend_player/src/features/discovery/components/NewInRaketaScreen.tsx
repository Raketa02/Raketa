/**
 * **New in Raketa's See all** — pushed over Home, whose tab stays lit
 * ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows screens §5.3; the mechanics
 * §7.4; home rows 19, 19.2).
 *
 * - **Header**: ‹, *New in Raketa*, and the sport pill — *● All ‹* — which slides open over the title
 *   onto the sports at least one Joiner holds a level in, the chosen one last (`shared/ui`'s
 *   `SportPillFrame`, offering *All*).
 * - **Body**: the tiles in two columns, newest first, friends where they fall, **20 to a page, the next
 *   read as the grid nears its end**. A sport keeps only who holds a level in it, and one that leaves
 *   nobody says *Nobody new plays squash yet* in place of the grid.
 * - **Every state**: reading (a spinner where the grid will be), failed (the recovery sentence and *Try
 *   again*), offline (resumes), a later page refused (said under the grid, with its own *Try again*),
 *   and the pull, which reads every page again.
 *
 * A tile opens the record and its round button acts, as on Home's row; **every friend write re-reads
 * every people list** (`LISTS_PEOPLE`), so this grid and the row under the screen both move.
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

import { ReadFailure } from '@/features/groups/types';
import { offlineMessage } from '@/shared/errors';
import { Note, ScreenHeader, SportPillFrame, TopSafeArea, behindOverlay, theme } from '@/shared/ui';

import type { Sport } from '@/shared/vocabulary/sport';

import { pillChoices, type Joiner, type SeeAllSport } from '../domain/joiner';
import { useNewInRaketaPage, type JoinerGrid } from '../hooks/useNewInRaketa';

import { DISCOVERY_COPY, SEE_ALL_PILL_WORDS, nobodyNewPlays } from './discoveryCopy';
import { JoinerRecord } from './JoinerRecord';
import { JoinerTile } from './JoinerTile';

/** See all's two columns (home rows 19). */
const COLUMNS = 2;

/** How near the end the next page is asked for — half a screen of tiles. */
const NEAR_THE_END = 0.5;

export function NewInRaketaScreen() {
  const [choice, setChoice] = useState<SeeAllSport>('all');
  const [reading, setReading] = useState<string>();
  const grid = useNewInRaketaPage(choice);
  // The last sports a read offered: a sport whose read is still out, or failed, keeps the pill —
  // and the way back to *All* with it.
  const [offered, setOffered] = useState<readonly Sport[]>();
  if (grid.sports !== undefined && grid.sports !== offered) setOffered(grid.sports);

  return (
    <>
      <View style={s.root} {...behindOverlay(reading !== undefined)}>
        <TopSafeArea style={s.screen}>
          <SportPillFrame<SeeAllSport>
            sports={offered === undefined ? undefined : pillChoices(offered, choice)}
            sport={choice}
            onPick={setChoice}
            words={SEE_ALL_PILL_WORDS}
            header={(pill) => (
              <ScreenHeader
                onBack={() => router.back()}
                backLabel={DISCOVERY_COPY.newInRaketa.back}
                title={DISCOVERY_COPY.newInRaketa.title}
                right={pill}
              />
            )}
          >
            <Grid choice={choice} grid={grid} onOpen={setReading} />
          </SportPillFrame>
        </TopSafeArea>
      </View>

      <JoinerRecord playerId={reading} onClose={() => setReading(undefined)} />
    </>
  );
}

interface GridProps {
  readonly choice: SeeAllSport;
  readonly grid: JoinerGrid;
  readonly onOpen: (playerId: string) => void;
}

function Grid({ choice, grid, onOpen }: GridProps) {
  const { width: screen } = useWindowDimensions();
  // A pull is the pull's own state, never the query's: a background read spins nothing.
  const [pulling, setPulling] = useState(false);
  const tile = (screen - 2 * theme.size.gutter - theme.space.sm * (COLUMNS - 1)) / COLUMNS;

  if (grid.joiners === undefined) {
    return (
      <View style={s.standing}>
        {grid.error !== null ? (
          <ReadFailure error={grid.error} onRetry={grid.retry} />
        ) : grid.paused ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : (
          <ActivityIndicator
            accessibilityLabel={DISCOVERY_COPY.newInRaketa.reading}
            color={theme.color.muted}
          />
        )}
      </View>
    );
  }

  const pull = () => {
    if (pulling) return;
    setPulling(true);
    void grid.reread().finally(() => setPulling(false));
  };

  return (
    <FlatList<Joiner>
      testID="new-in-raketa-grid"
      data={grid.joiners}
      keyExtractor={(joiner) => joiner.playerId}
      numColumns={COLUMNS}
      columnWrapperStyle={s.columns}
      contentContainerStyle={s.content}
      renderItem={({ item }) => (
        <JoinerTile joiner={item} width={tile} layout="grid" onOpen={() => onOpen(item.playerId)} />
      )}
      ListEmptyComponent={
        <Text testID="nobody-new" style={s.nobody}>
          {choice === 'all' ? DISCOVERY_COPY.newInRaketa.nobodyAtAll : nobodyNewPlays(choice)}
        </Text>
      }
      ListFooterComponent={
        grid.moreFailure === undefined ? null : (
          <ReadFailure error={grid.moreFailure.error} onRetry={grid.moreFailure.retry} />
        )
      }
      onEndReached={grid.loadMore}
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
  // 9 between tiles, both ways; 15 at the gutter (Appendix B).
  columns: { gap: theme.space.sm },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.xxl,
    gap: theme.space.sm,
  },
  nobody: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.xl,
  },
});
