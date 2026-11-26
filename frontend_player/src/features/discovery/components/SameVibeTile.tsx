/**
 * **A Same vibe tile** ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows screens
 * §6.2, §6.4; the words §31.8; home rows 20, 22–22.3, 24; design-system 7.35) — `shared/ui`'s tinted
 * pale tile, washed in their court poster's hue, with:
 *
 * ```
 * ┌────────────────────────────────────┐
 * │ [face]  karol.t               (98%) │  the face, the nickname, the vibe % in a white circle
 * │         6 things in common          │
 * │ [Stays for a drink] [Plays to win]  │  the tags they share, green, as many whole as fit in
 * │ [Here to improve]  [+2 more]        │  three lines — the last place +N more (`SharedTags`)
 * │                                (✓)  │  the round friend button, bottom-right
 * └────────────────────────────────────┘
 * ```
 *
 * **Two doors**: the round button acts, asking from *same vibe*; a tap anywhere else opens the vibe
 * sheet (`onOpen`). The face is not a door of its own here — the sheet's is.
 *
 * Home's row hands the rail's width and draws the row's sizes; See all hands its column and draws the
 * grid's (`theme.size.sameVibe`).
 *
 * **The row's gaps are grown** (2026-11-26): on Home's line the tile is `lineCardRatio` of the line's
 * content, wider than the page's 0,74, and **keeps its shape** — every vertical gap grows by the same
 * factor onto the 3pt grid (`GAPS`), 12·9·6·6 to 21·15·9·9 down the tile, so its height grows as its
 * width did, the words, the face, the chips and the sides their own. The grid keeps its own.
 *
 * **While See all's first page is read, a grid tile stands as its skeleton** (`SAME_VIBE_TILE_SKELETON`,
 * [#872](https://github.com/Raketa02/Raketa/issues/872)): the pale tile is a white card that is always
 * there, so it is drawn as itself — without the wash, which is the person's — at the grid tile's own
 * height (its three lines of chips keep their room), and inside it the shapes every tile has: the face,
 * the nickname and the % circle, the count's words, a first chip, and the round button's circle in
 * its corner.
 */

import { StyleSheet, Text, View } from 'react-native';

import { RoundFriendButton } from '@/features/friends/types';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import {
  PlayerPhoto,
  SkeletonBlock,
  SkeletonCircle,
  SkeletonLine,
  SkeletonWords,
  TAG_HEIGHT,
  TintedTile,
  playerPhotoRadius,
  theme,
} from '@/shared/ui';
import { thingsInCommon } from '@/shared/vocabulary/socialTagPresentation';

import { FOUND_THROUGH_TAGS, type SameVibePlayer } from '../domain/sameVibe';

import { vibeTileLabel } from './discoveryCopy';
import type { SeeAllSkeletonTile } from './SeeAllScreen';
import { SHARED_TAGS_ROOM, SharedTags, sharedTagsRoom } from './SharedTags';

export interface SameVibeTileProps {
  readonly player: SameVibePlayer;
  /** Home's row or See all's grid — the width handed in, and the face's and the circle's sizes. */
  readonly layout: 'row' | 'grid';
  readonly width: number;
  /** Anywhere but the button: the vibe sheet. */
  readonly onOpen: () => void;
}

export function SameVibeTile({ player, layout, width, onOpen }: SameVibeTileProps) {
  const face = theme.size.sameVibe.face[layout];
  const circle = theme.size.sameVibe.percent[layout];
  const gaps = GAPS[layout];

  return (
    <TintedTile
      playerId={player.playerId}
      accessibilityLabel={vibeTileLabel(player)}
      onPress={onOpen}
      width={width}
      testID={`same-vibe-${player.playerId}`}
      corner={
        <RoundFriendButton
          playerId={player.playerId}
          nickname={player.nickname}
          relation={player.relation}
          where={FOUND_THROUGH_TAGS}
        />
      }
    >
      <View style={[s.head, ROOM[layout].head]}>
        <PlayerPhoto
          playerId={player.playerId}
          {...(player.photoUrl === undefined ? {} : { photoUrl: player.photoUrl })}
          box={{ kind: 'face', size: face }}
        />
        <View style={s.who}>
          <View style={s.nameLine}>
            <Text style={s.name} numberOfLines={1}>
              {player.nickname}
            </Text>
            <View style={[s.circle, { width: circle, height: circle }]}>
              <Text style={s.percent} numberOfLines={1}>
                {formatPercent(player.vibePercent)}
              </Text>
            </View>
          </View>
          <Text style={s.inCommon} numberOfLines={1}>
            {thingsInCommon(player.inCommon)}
          </Text>
        </View>
      </View>
      <SharedTags tags={player.sharedTags} lineGap={gaps.tagLines} />
    </TintedTile>
  );
}

/** **A grid tile while See all's first page is read** (#872): the white tile, and its shapes. */
export const SAME_VIBE_TILE_SKELETON: SeeAllSkeletonTile = {
  height: (_width, fontScale) => sameVibeTileHeight(fontScale, 'grid'),
  Tile: SameVibeTileSkeleton,
};

/** The grid's face and % circle. */
const GRID_FACE = theme.size.sameVibe.face.grid;
const GRID_CIRCLE = theme.size.sameVibe.percent.grid;

/**
 * **The tile's vertical gaps, in its two places** (2026-11-26) — the grid's, the drawing's own; and
 * Home's line's, where the tile is `lineCardRatio` of the content rather than 0,74: each ×1,6 onto the
 * 3pt grid, so the tile's height grows as its width did (182 → 203 at the OS's own text size, the
 * exact 204). `overHead` is what stands over `TintedTile`'s own `md` above the head — 12 in the
 * grid, 21 on the line; `headToTags` the gap under the head; `tagLines` the gap between the chips'
 * lines.
 */
const GAPS: Readonly<
  Record<
    SameVibeTileProps['layout'],
    { readonly overHead: number; readonly headToTags: number; readonly tagLines: number }
  >
> = {
  grid: { overHead: 0, headToTags: theme.space.sm, tagLines: theme.space.xs },
  row: { overHead: theme.space.sm, headToTags: theme.space.lg, tagLines: theme.space.sm },
};

/** `TintedTile`'s border, a `line` point all round. */
const TILE_BORDER = 1;

function SameVibeTileSkeleton() {
  return (
    <View style={s.skeletonTile}>
      <View style={[s.head, ROOM.grid.head]}>
        <SkeletonBlock style={s.skeletonFace} />
        <View style={s.who}>
          <View style={s.nameLine}>
            <SkeletonLine role={theme.type.h2} width="60%" style={s.skeletonName} />
            <SkeletonCircle size={GRID_CIRCLE} />
          </View>
          {/* With a one-figure count, as nearly every tile says. Worked out at the call. */}
          <SkeletonWords role={theme.type.rlLabel} words={thingsInCommon(2)} />
        </View>
      </View>
      <View style={s.skeletonTags}>
        <SkeletonBlock style={s.skeletonChip} />
      </View>
      <SkeletonCircle size={theme.size.roundFriend.face} style={s.skeletonRound} />
    </View>
  );
}

/**
 * **A tile's height** in its place, read off its drawing: its border; `md` and the place's own above
 * the head, which is the taller of the face and the words beside it (the nickname's line, as tall as
 * the % circle where that is taller, over the count); a gap under it; the three lines' room, their
 * gaps the place's; and the corner's reach. The words' lines grow with the phone's text size, as the
 * OS grows them; the room is the one the tile keeps from its first frame.
 */
export function sameVibeTileHeight(fontScale: number, layout: SameVibeTileProps['layout']): number {
  const { space, type, size } = theme;
  const gaps = GAPS[layout];
  const face = size.sameVibe.face[layout];
  const circle = size.sameVibe.percent[layout];
  const words =
    Math.max(type.h2.lineHeight * fontScale, circle) + type.rlLabel.lineHeight * fontScale;
  return (
    2 * TILE_BORDER +
    space.md +
    gaps.overHead +
    Math.max(face, words) +
    gaps.headToTags +
    sharedTagsRoom(gaps.tagLines) +
    size.minTouch
  );
}

/** Where the round button's circle stands: centred in its reach, at the tile's corner. */
const ROUND_INSET = (theme.size.minTouch - theme.size.roundFriend.face) / 2;

const s = StyleSheet.create({
  // `TintedTile`'s white card, drawn as itself: surface, its `line` border, its corner, its padding.
  skeletonTile: {
    flex: 1,
    backgroundColor: theme.color.surface,
    borderWidth: TILE_BORDER,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
    paddingHorizontal: theme.space.md,
    paddingTop: theme.space.md,
  },
  skeletonFace: {
    width: GRID_FACE,
    height: GRID_FACE,
    borderRadius: playerPhotoRadius(GRID_FACE),
  },
  skeletonName: { flex: 1 },
  skeletonTags: { height: SHARED_TAGS_ROOM },
  skeletonChip: { width: '60%', height: TAG_HEIGHT, borderRadius: theme.radius.pill },
  skeletonRound: { position: 'absolute', right: ROUND_INSET, bottom: ROUND_INSET },
  // Over it and under it, the place's gaps (`ROOM`).
  head: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.space.sm },
  who: { flex: 1 },
  // The nickname takes the line, and the circle stands at its end; the count runs under both.
  nameLine: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  name: { ...theme.type.h2, color: theme.color.ink, flex: 1 },
  // The vibe % in a white circle, on the tint (home rows 22).
  circle: {
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  percent: {
    ...theme.num.tiny,
    ...theme.tabular,
    fontFamily: theme.font.mono[600],
    color: theme.color.ink,
  },
  inCommon: { ...theme.type.rlLabel, color: theme.color.muted },
});

/** **The gaps drawn, in a place** — `GAPS` as styles; the chips' lines take theirs as a prop. */
function roomOf(layout: SameVibeTileProps['layout']) {
  const gaps = GAPS[layout];
  return StyleSheet.create({
    head: { marginTop: gaps.overHead, marginBottom: gaps.headToTags },
  });
}

const ROOM = { grid: roomOf('grid'), row: roomOf('row') } as const;
