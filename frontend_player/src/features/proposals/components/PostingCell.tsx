/**
 * **One cell of the posting grid** — a day's range, drawn in one of nine looks
 * ([#558](https://github.com/Raketa02/Raketa/issues/558); the screens A5.2; mocks 23–32).
 *
 * ```
 * dead            paper2, no number                         nobody who fits is free
 * few             mintSoft, the count in mintInk            some fit, no court
 * enough          gridLight, the count in its ink           a full game's worth, no court
 * thin            gridMid, the count and the court glyph    a court, fewer than a full game
 * hot             mintInk ringed in volt, white count+glyph a court and a full game
 * outside hours   any of the above at .5, a dashed edge     still pickable with the glyph
 * past            .15, not a button                         earlier today
 * your pick       an ink outline off the cell, a white ✓    the hour and court in the post
 * happening       a coralInk dot top-right, ringed white    a game already there
 * ```
 *
 * **The fill is the server's values drawn** (`cellFill`); the pick is the only look the client
 * decides. The number is the cap's (*5+*), each fill's figure in its own ink — never white on the
 * two middle greens, where the mocks' white is 1,51 and 2,15 (theme `gridLight`), and white only on
 * `mintInk`, Rule C's bed for it. Every look is also a word: the cell is a button named for its day
 * and range, its count and every flag over it (`cellSpoken`), and *selected* while it is the pick —
 * colour is never the only signal (Part 13).
 */

import Feather from '@expo/vector-icons/Feather';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { cellFill, opensSheet, type CellFill, type PostingCell as Cell } from '../domain/posting';

import { POSTING_COPY } from './postingCopy';
import { cellCount, cellSpoken } from './postingPresentation';

const GRID = theme.size.postingGrid;

export interface PostingCellProps {
  readonly cell: Cell;
  readonly picked: boolean;
  /** The read's clock — what *today* and *tomorrow* are named against. */
  readonly readAt: number;
  readonly onPress: () => void;
}

export function PostingCell({ cell, picked, readAt, onPress }: PostingCellProps) {
  const fill = cellFill(cell);
  const count = cellCount(cell);
  const glyph = cell.courtFree && fill !== 'dead';
  const inert = !opensSheet(cell);

  return (
    <View style={[s.slot, picked ? s.picked : undefined]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={cellSpoken(cell, picked, readAt)}
        accessibilityHint={inert ? undefined : POSTING_COPY.cellHint}
        accessibilityState={{ selected: picked, disabled: inert }}
        disabled={inert}
        onPress={onPress}
        testID={`posting-cell-${cell.day}-${cell.range}`}
        style={({ pressed }) => [
          s.edge,
          fill === 'hot' ? s.hotEdge : undefined,
          cell.outsideYourHours ? s.outside : undefined,
          cell.past ? s.past : undefined,
          pressed ? s.pressed : undefined,
        ]}
      >
        <View style={[s.cell, FILL[fill], fill === 'hot' ? s.ring : undefined]}>
          {count === undefined ? null : (
            <Text style={[s.count, { color: INK[fill] }]} testID="posting-cell-count">
              {count}
            </Text>
          )}
          {glyph ? (
            <View style={[s.glyph, { borderColor: INK[fill] }]} testID="posting-cell-court" />
          ) : null}
          {cell.happening ? <View style={s.dot} testID="posting-cell-happening" /> : null}
        </View>
      </Pressable>
      {picked ? (
        <View style={s.tick} pointerEvents="none" testID="posting-cell-picked">
          <Feather
            name="check"
            size={theme.size.rowLeadGlyph}
            color={theme.color.ink}
            accessibilityElementsHidden
            importantForAccessibility="no"
          />
        </View>
      ) : null}
    </View>
  );
}

/** Each fill's figure and glyph — its own ink, white only on `mintInk` (Rule C). */
const INK: Readonly<Record<CellFill, string>> = {
  dead: theme.color.muted,
  few: theme.color.mintInk,
  enough: theme.color.gridLightInk,
  thin: theme.color.gridMidInk,
  hot: theme.color.surface,
};

const FILL = StyleSheet.create({
  dead: { backgroundColor: theme.color.paper2 },
  few: { backgroundColor: theme.color.mintSoft },
  enough: { backgroundColor: theme.color.gridLight },
  thin: { backgroundColor: theme.color.gridMid },
  hot: { backgroundColor: theme.color.mintInk },
});

const s = StyleSheet.create({
  // The slot keeps the pick's room on every side, so a pick outlines the cell without moving it.
  slot: {
    flex: 1,
    height: GRID.cell,
    borderRadius: theme.radius.postingCell + GRID.pickGap + GRID.pickRing,
    padding: GRID.pickGap + GRID.pickRing,
  },
  picked: { padding: GRID.pickGap, borderWidth: GRID.pickRing, borderColor: theme.color.ink },
  // The edge's room carries the hot cell's dark line, and the dashed edge outside the poster's week.
  edge: { flex: 1, borderRadius: theme.radius.postingCell, padding: GRID.outline },
  hotEdge: { padding: 0, borderWidth: GRID.outline, borderColor: theme.color.mintInk },
  outside: {
    opacity: GRID.outside,
    padding: 0,
    borderStyle: 'dashed',
    borderWidth: GRID.dash,
    borderColor: theme.color.mintInk,
  },
  past: { opacity: GRID.past },
  pressed: { opacity: 0.7 },
  cell: {
    flex: 1,
    borderRadius: theme.radius.postingCell - GRID.outline,
    paddingHorizontal: theme.space.xs,
    paddingVertical: theme.space.xxs,
    overflow: 'hidden',
  },
  ring: { borderWidth: GRID.ring, borderColor: theme.color.volt },
  count: { ...theme.num.m, ...theme.tabular },
  glyph: {
    position: 'absolute',
    right: theme.space.xs,
    bottom: theme.space.xs,
    width: GRID.glyph.width,
    height: GRID.glyph.height,
    borderWidth: GRID.glyph.stroke,
    borderRadius: GRID.glyph.radius,
  },
  dot: {
    position: 'absolute',
    top: theme.space.xxs,
    right: theme.space.xxs,
    width: GRID.dot,
    height: GRID.dot,
    borderRadius: GRID.dot / 2,
    borderWidth: GRID.dotRing,
    borderColor: theme.color.surface,
    backgroundColor: theme.color.coralInk,
  },
  // The pick's badge: a white disc with an ink tick, over the cell's middle (mock 31).
  tick: {
    position: 'absolute',
    alignSelf: 'center',
    top: (GRID.cell - GRID.tick) / 2 - GRID.pickRing,
    width: GRID.tick,
    height: GRID.tick,
    borderRadius: GRID.tick / 2,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
