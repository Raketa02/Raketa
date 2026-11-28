/**
 * **A people row's See all** — the frame every one draws ([#801](https://github.com/Rakieta02/Rakieta/issues/801),
 * [#802](https://github.com/Rakieta02/Rakieta/issues/802); the Home rows screens §4.4, §5.3), pushed
 * over Home whose tab stays lit:
 *
 * - **Header**: ‹, the row's title, and the sport pill — *● All ‹* — which slides open over the title
 *   onto the sports the read offers, the chosen one last (`shared/ui`'s `SportPillFrame`, offering
 *   *All*; `pillChoices`). **The pill stands from the first frame**: until a read has offered its
 *   sports it offers every sport, so it is drawn at its final shape and can be used while the page
 *   reads — the header never changes shape at the reveal, where a title wrapping beside a pill that
 *   grew its chevron would push the page down.
 * - **Body**: the row's cards or tiles in the server's order, **20 to a page, the next read as the
 *   list nears its end** — one column or the caller's.
 * - **Every state**: reading, failed (the recovery sentence and *Try again*), offline (resumes), a
 *   later page refused (said under the list, with its own *Try again*), the empty line, and the pull,
 *   which reads every page again. **The pill keeps the last sports a read offered**, so a sport whose
 *   read is out or failed keeps *All* a tap away.
 * - **Reading shimmers** ([#872](https://github.com/Rakieta02/Rakieta/issues/872); PRD #867; the
 *   loading shimmer log §10): while the first page is out with nothing to draw, **the row's own tile
 *   or card stands as a skeleton in the grid, as many lines of it as fill the screen** (`skeleton`,
 *   the caller's shape; `SeeAllSkeleton`), and the page comes in on one cross-fade once that read
 *   finishes (`Reveal`) — landed, refused, or held for a connection, so the failure and the offline
 *   note take the skeleton's place. A read refused once and asked again is still on its way: the
 *   skeleton stays through Query's retries, and *Try again* or the connection back stands it again.
 *   **Per sport**: a sport not read yet shimmers, one read in the last few minutes opens at once. A
 *   later page keeps the foot's behaviour, and a pull never shows the skeleton.
 *
 * What each row draws, and the record and sheets its cards open, are the caller's; they stand beside
 * the frame (`overlays`), and the frame hides itself from a screen reader while one is up.
 */

import { router } from 'expo-router';
import { useState, type ComponentType, type ReactElement, type ReactNode } from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';

import { ReadFailure } from '@/features/groups/types';
import { offlineMessage } from '@/shared/errors';
import {
  Note,
  Reveal,
  ScreenHeader,
  SkeletonGround,
  SportPillFrame,
  TopSafeArea,
  behindOverlay,
  theme,
  type SportPillWords,
  useTabBarReach,
} from '@/shared/ui';
import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import { pillChoices, type SeeAllSport } from '../domain/seeAll';
import type { SeeAllList } from '../hooks/useSeeAllPages';

/** How near the end the next page is asked for — half a screen of cards. */
const NEAR_THE_END = 0.5;

/** 9 between cards and tiles, both ways (Appendix B). */
const COLUMN_GAP = theme.space.sm;

/**
 * **A row's tile or card as a skeleton** (#872) — what stands in the grid while the first page is out.
 * The frame stands each in a box a column wide and `height` tall, and lays as many lines of them as
 * fill the screen.
 */
export interface SeeAllSkeletonTile {
  /**
   * How tall the tile or card stands at a column's width and the phone's text size (`fontScale`) —
   * read off its own drawing, its words' lines grown as the OS grows them.
   */
  readonly height: (width: number, fontScale: number) => number;
  /** Its skeleton, filling the box it is stood in. */
  readonly Tile: ComponentType;
}

export interface SeeAllScreenProps<Person extends { readonly playerId: string }> {
  readonly title: string;
  readonly backLabel: string;
  readonly pillWords: SportPillWords<SeeAllSport>;
  readonly choice: SeeAllSport;
  readonly onPick: (choice: SeeAllSport) => void;
  readonly list: SeeAllList<Person>;
  /** One person, as the row draws them here, at the width of one column. */
  readonly renderPerson: (person: Person, width: number) => ReactElement;
  /** One person's place while the first page reads — the same tile or card, as a skeleton. */
  readonly skeleton: SeeAllSkeletonTile;
  /** How many to a line — one, or the grid's columns. */
  readonly columns?: number;
  /** The empty list's line — for *All*, or the chosen sport. */
  readonly emptyLine: string;
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

  // One column of the content width, the gap between columns taken out first.
  const columns = body.columns ?? 1;
  const { width: screen } = useWindowDimensions();
  const column = (screen - 2 * theme.size.gutter - COLUMN_GAP * (columns - 1)) / columns;
  // The first page's read has finished — landed, refused after its retries, or held for a
  // connection — so what it drew, its failure or the offline note takes the skeleton's place.
  const finished = list.people !== undefined || list.error !== null || list.paused;

  return (
    <>
      <View style={s.root} {...behindOverlay(overlayUp)}>
        <TopSafeArea style={s.screen}>
          <SportPillFrame<SeeAllSport>
            sports={pillChoices(offered ?? SPORTS, choice)}
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
            <SkeletonGround style={s.below}>
              {/* Keyed by the sport: each is a read of its own, so one not read yet shimmers and
                  one read already is simply drawn. */}
              <Reveal
                key={choice}
                finished={finished}
                landed={list.people !== undefined}
                style={s.below}
                skeleton={<SeeAllSkeleton tile={body.skeleton} columns={columns} column={column} />}
              >
                <Body list={list} {...body} columns={columns} column={column} />
              </Reveal>
            </SkeletonGround>
          </SportPillFrame>
        </TopSafeArea>
      </View>
      {overlays}
    </>
  );
}

type BodyProps<Person extends { readonly playerId: string }> = Pick<
  SeeAllScreenProps<Person>,
  'list' | 'renderPerson' | 'emptyLine' | 'testID'
> & { readonly columns: number; readonly column: number };

function Body<Person extends { readonly playerId: string }>({
  list,
  renderPerson,
  columns,
  column,
  emptyLine,
  testID,
}: BodyProps<Person>) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  // A pull is the pull's own state, never the query's: a background read spins nothing.
  const [pulling, setPulling] = useState(false);

  if (list.people === undefined) {
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
    <FlatList<Person>
      testID={testID}
      data={list.people}
      keyExtractor={(person) => person.playerId}
      numColumns={columns}
      {...(columns > 1 ? { columnWrapperStyle: s.columns } : {})}
      contentContainerStyle={[s.content, { paddingBottom: reach + theme.space.xxl }]}
      renderItem={({ item }) => renderPerson(item, column)}
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

/**
 * **The first page's place** (#872): the row's tile or card as a skeleton, a column wide, in the
 * grid's lines and gaps — as many lines as fill the room under the header (the window's height until
 * it is laid out, the room clipping what falls past its foot), so no line stands wholly off screen
 * moving with the band.
 */
function SeeAllSkeleton({
  tile: { height, Tile },
  columns,
  column,
}: {
  readonly tile: SeeAllSkeletonTile;
  readonly columns: number;
  readonly column: number;
}) {
  const window = useWindowDimensions();
  const [room, setRoom] = useState<number>();
  const tall = height(column, window.fontScale);
  // What shows above the floating bar: the strip under it holds no line (#881, the code review).
  const reach = useTabBarReach();
  const lines = Math.ceil(Math.max(0, (room ?? window.height) - reach) / (tall + COLUMN_GAP));

  return (
    <View
      testID="see-all-skeleton"
      style={s.skeleton}
      onLayout={(event) => setRoom(event.nativeEvent.layout.height)}
    >
      {Array.from({ length: lines }, (_line, line) => (
        <View key={`line-${line}`} style={s.line}>
          {Array.from({ length: columns }, (_tile, at) => (
            <View
              key={`tile-${at}`}
              testID="see-all-skeleton-tile"
              style={{ width: column, height: tall }}
            >
              <Tile />
            </View>
          ))}
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  screen: { flex: 1, backgroundColor: theme.color.paper },
  below: { flex: 1 },
  standing: { paddingHorizontal: theme.size.gutter, paddingTop: theme.space.lg },
  // The list's own gutter and gaps, clipped at the room's foot.
  skeleton: {
    flex: 1,
    paddingHorizontal: theme.size.gutter,
    gap: COLUMN_GAP,
    overflow: 'hidden',
  },
  line: { flexDirection: 'row', gap: COLUMN_GAP },
  // 9 between cards and tiles, both ways; 15 at the gutter (Appendix B).
  columns: { gap: COLUMN_GAP },
  content: {
    paddingHorizontal: theme.size.gutter,
    gap: COLUMN_GAP,
  },
  empty: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.xl,
  },
});
