/**
 * **The list** (rankings 5, 7–11; the screens §5.2, §5.3; [#775](https://github.com/Raketa02/Raketa/issues/775),
 * [#776](https://github.com/Raketa02/Raketa/issues/776)): one row per listed player the reader can
 * see, best first, on one white card — and the page's scroller, the card and the podium its header.
 *
 * **A row:**
 *
 * - **The place** — `coralInk` for 1–3 and `muted` after (rankings 7). A true place, so a hidden or
 *   blocked row leaves a gap. Coral is §1.2's closed list's mark; drawn as a figure it is the text
 *   form, `coralInk`, which keeps 4,5:1 on white where `coral` would not (Part 16, 2026-11-08).
 * - **The face and the nickname**, the reader's own reading *You* on a `coralSoft` tint (rankings 11).
 * - **The form** — the record's own *Run of form*: the last five results with a winner, oldest
 *   first, a mint square for a win and a grey one for a loss, never padded.
 * - **The chip**, and **the level**, right-aligned and mono.
 *
 * **A tap on the row opens the record** — the face is in the row, so it opens it too. The reader's own
 * row opens their own record.
 *
 * **Virtualised, in pages of 50** (#776; architecture Part 12). Within half a screen of either end the
 * list asks for the next page that way; a page landing above the rows on screen is laid in without
 * moving them (`maintainVisibleContentPosition`). A page is drawn whole as it lands — fifty light rows
 * — so the reader's row is on hand to centre the moment a jump lands.
 *
 * **The floating *You · 212th*** (`JumpToMe`) shows while the reader is listed in General and their
 * row is off screen; a row counts as on screen once half of it is. What it last said outlives a jump's
 * new list, so the button stays up until the row it centres is on screen. **A tap centres the
 * reader's row**: scrolled to where it is already drawn, or — further down than the list has read —
 * the page around it read, and drawn as a new list centred on the row once it lands. A row not yet
 * laid out is scrolled to as nearly as the header and an average row put it, so it is drawn, and
 * centred once it has been: when the content grows, and on each of the next few frames. **While a
 * centring is owed the top of the list asks for nothing** — a new list starts at its top, and would
 * otherwise read the page above before it reached the reader. The reader's own drag takes the list
 * back.
 */

import { useEffect, useRef, useState, type ReactElement } from 'react';
import {
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
  type RefreshControlProps,
  type ViewToken,
} from 'react-native';

import { ROW_FACE } from '@/features/groups/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { PlayerPhoto, RunOfForm, theme } from '@/shared/ui';

import type { RankedRow } from '../domain/ranking';
import type { Jump, ListWindow } from '../hooks/rankingRead';

import { JUMP_ROOM, JumpToMe } from './JumpToMe';
import { RankChip } from './RankChip';
import { RANKINGS_COPY, rankedRowLabel, rowName } from './rankingsCopy';

/**
 * **The true places drawn in coral** (rankings 7; the screens §5.2: *coral for places 1–3*) — by the
 * place, not by the row's position: with second hidden the coral reads 1 and 3. The podium is the
 * first three rows the reader sees (`podiumOf`), a different count on purpose.
 */
const CORAL_PLACES = 3;

/**
 * **A page drawn whole as it lands** — the server's page of 50, so the reader's row is drawn, and can
 * be measured and centred, the moment a jump lands. The server owns the size; this is how much the
 * list draws at once, and a page with rows left out holds fewer.
 */
const A_PAGE = 50;

/** Within half a screen of an end, the next page that way is asked for — `pageEnd`'s rule. */
const HALF_A_SCREEN = 0.5;

/** A row is on screen once half of it is. */
const ON_SCREEN = { itemVisiblePercentThreshold: 50 } as const;

/** A row not yet laid out is tried again on each of this many frames, then when the content grows. */
const FRAMES_TO_CENTRE = 3;

export interface RankingListProps {
  readonly window: ListWindow;
  readonly rows: readonly RankedRow[];
  /** Above the rows: the card and the podium, or the failure of the page above. */
  readonly header: ReactElement | null;
  /** Below the rows: the failure of the page below. */
  readonly footer: ReactElement | null;
  readonly refreshControl: ReactElement<RefreshControlProps>;
  readonly onOpen: (row: RankedRow) => void;
  readonly onStartReached: () => void;
  readonly onEndReached: () => void;
  /** Absent: no button — the reader isn't listed, or is hidden. */
  readonly jump: Jump | undefined;
}

export function RankingList({
  window,
  rows,
  header,
  footer,
  refreshControl,
  onOpen,
  onStartReached,
  onEndReached,
  jump,
}: RankingListProps) {
  const list = useRef<FlatList<RankedRow>>(null);
  // Whether the reader's row is on screen — `undefined` until the list first says.
  const [seen, setSeen] = useState<boolean>();
  // FlatList refuses a viewability callback that changes while it is mounted: one, for good.
  const onViewable = useRef(({ viewableItems }: { viewableItems: ViewToken<RankedRow>[] }) =>
    setSeen(viewableItems.some((token) => token.item.isYou)),
  ).current;

  // A centring owed — kept until it lands, or until the reader's own drag takes the list back.
  const owed = useRef<{ readonly animated: boolean; frames: number }>();
  const missed = useRef(false);
  const headerLength = useRef(0);
  const meAt = rows.findIndex((row) => row.isYou);
  const centre = () => {
    const want = owed.current;
    if (want === undefined || meAt < 0 || list.current === null) return;
    missed.current = false;
    list.current.scrollToIndex({ index: meAt, viewPosition: 0.5, animated: want.animated });
    if (!missed.current) owed.current = undefined;
  };
  // A frame's retry runs the centring of the drawing it lands on, never the one it was asked from.
  const latestCentre = useRef(centre);
  // After every drawing — a new window is a new list, a page lands — a centring owed is tried again.
  useEffect(() => {
    latestCentre.current = centre;
    centre();
  });

  const press = () => {
    if (jump === undefined) return;
    owed.current = { animated: meAt >= 0, frames: 0 };
    if (meAt >= 0) centre();
    else jump.toMe?.();
  };

  return (
    <View style={s.frame}>
      <FlatList
        key={window}
        ref={list}
        testID="rankings-page"
        data={rows}
        keyExtractor={(row) => row.playerId}
        renderItem={({ item, index }) => (
          <View
            style={[
              s.cell,
              index === 0 ? s.cardTop : undefined,
              index === rows.length - 1 ? s.cardFoot : undefined,
            ]}
          >
            <RankingRow row={item} divided={index > 0} onOpen={onOpen} />
          </View>
        )}
        ListHeaderComponent={
          <View
            onLayout={(event) => {
              headerLength.current = event.nativeEvent.layout.height;
            }}
          >
            {header}
          </View>
        }
        ListFooterComponent={footer}
        contentContainerStyle={[s.body, jump === undefined ? undefined : s.roomForTheButton]}
        refreshControl={refreshControl}
        initialNumToRender={A_PAGE}
        maxToRenderPerBatch={A_PAGE}
        onStartReached={() => {
          if (owed.current === undefined) onStartReached();
        }}
        onStartReachedThreshold={HALF_A_SCREEN}
        onEndReached={onEndReached}
        onEndReachedThreshold={HALF_A_SCREEN}
        maintainVisibleContentPosition={{ minIndexForVisible: 0 }}
        viewabilityConfig={ON_SCREEN}
        onViewableItemsChanged={onViewable}
        onScrollToIndexFailed={({ index, averageItemLength }) => {
          missed.current = true;
          list.current?.scrollToOffset({
            offset: headerLength.current + averageItemLength * index,
            animated: false,
          });
          const want = owed.current;
          if (want !== undefined && want.frames < FRAMES_TO_CENTRE) {
            want.frames += 1;
            requestAnimationFrame(() => latestCentre.current());
          }
        }}
        onContentSizeChange={centre}
        onScrollBeginDrag={() => {
          owed.current = undefined;
        }}
      />

      {jump === undefined ? null : <JumpToMe jump={jump} seen={seen} onPress={press} />}
    </View>
  );
}

function RankingRow({
  row,
  divided,
  onOpen,
}: {
  readonly row: RankedRow;
  readonly divided: boolean;
  readonly onOpen: (row: RankedRow) => void;
}) {
  return (
    <Pressable
      testID={`ranked-row-${row.playerId}`}
      accessibilityRole="button"
      accessibilityLabel={rankedRowLabel(row)}
      accessibilityHint={row.isYou ? RANKINGS_COPY.openOwnRecord : RANKINGS_COPY.openRecord}
      onPress={() => onOpen(row)}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        row.isYou ? s.you : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <Text
        testID={`ranked-place-${row.place}`}
        style={[s.place, row.place <= CORAL_PLACES ? s.podiumPlace : undefined]}
      >
        {row.place}
      </Text>
      <PlayerPhoto
        playerId={row.playerId}
        {...(row.photoUrl === undefined ? {} : { photoUrl: row.photoUrl })}
        box={{ kind: 'face', size: ROW_FACE }}
      />
      <View style={s.words}>
        <Text style={s.name} numberOfLines={1}>
          {rowName(row)}
        </Text>
        <RunOfForm results={row.form} />
      </View>
      {row.chip === undefined ? null : <RankChip chip={row.chip} />}
      <Text style={s.level}>{formatLevel(row.level)}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  frame: { flex: 1 },
  body: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.lg },
  // The last row clears the floating button.
  roomForTheButton: { paddingBottom: JUMP_ROOM },
  // One white card drawn a row at a time — `Card`'s surface, border and radius — its rows edge to
  // edge so the reader's tint reaches both sides (rankings 11).
  cell: {
    backgroundColor: theme.color.surface,
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: theme.color.line,
    overflow: 'hidden',
  },
  cardTop: {
    borderTopWidth: 1,
    borderTopLeftRadius: theme.radius.card,
    borderTopRightRadius: theme.radius.card,
  },
  cardFoot: {
    borderBottomWidth: 1,
    borderBottomLeftRadius: theme.radius.card,
    borderBottomRightRadius: theme.radius.card,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
    paddingHorizontal: theme.space.lg,
  },
  // 5.3: `line2` folds one card into rows.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  you: { backgroundColor: theme.color.coralSoft },
  pressed: { opacity: 0.7 },
  place: {
    ...theme.num.s,
    ...theme.tabular,
    width: theme.size.rankings.place,
    color: theme.color.muted,
  },
  podiumPlace: { color: theme.color.coralInk },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  level: { ...theme.num.m, ...theme.tabular, color: theme.color.ink, textAlign: 'right' },
});
