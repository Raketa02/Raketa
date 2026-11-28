/**
 * **A Same competitive level card** ([#802](https://github.com/Rakieta02/Rakieta/issues/802); the Home
 * rows screens §4.2, §4.4; the words §31.5; home rows 7, 8, 10, 10.2, 10.3, 12–16; design-system
 * 7.34) — a dark card on its own ground (`levelCardGround`). **Its foot says no gap in words since
 * [#821](https://github.com/Rakieta02/Rakieta/issues/821)** (ADR-0205 §5, Q22; home refactor 7): *0,02
 * below you* is gone, from the drawing and from the pairing's spoken name; the comparison sheet's
 * blocks still say it. Top to bottom:
 *
 * ```
 * ┌──────────────────────────────────────────┐
 * │ [face]          91%           [face]     │  the reader · the % in the game cards' colour,
 * │  You            EVEN          zofia.b    │  EVEN, the sport with its dot · them
 * │  2,71         ● Padel          2,69      │
 * │              YOU                         │
 * │ ████████████▌▐░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▒▒   │  the comparison bar, onDark (7.33)
 * │ NEW  DEVELOPING ESTABLISHED  ADVANCED    │
 * │ 2 sports ›                          (✓)  │  N sports › · the round button
 * └──────────────────────────────────────────┘
 * ```
 *
 * **Three doors and nothing else** (the screens §4.2, *a call*): the other's face or nickname opens
 * their record (`onOpen`); *N sports ›* — drawn only with more than one shared sport — opens the
 * comparison sheet (`onCompare`); the round button acts, asking from *same level* in the card's
 * sport. The % is the server's, coloured by the game cards' breaks (`balanceTone`: green from 70,
 * amber 55–69, red under 55) in the game cards' inks (`BALANCE_FIGURE`).
 *
 * Home's row hands the rail's width; See all stretches the card across the content.
 *
 * **Two places, two sets of gaps** (`layout`, 2026-11-26). In See all the card is drawn at its own
 * gaps. On Home's line it is `lineCardRatio` of the line's content, wider than the page's 0,74, and
 * **keeps its shape**: every vertical gap grows by the same factor onto the 3pt grid (`GAPS`) —
 * 15·3·3·12·6·6 to 24·6·6·18·9·9 down the card, the middle's 3·6 to 6·9 — so its height grows as its
 * width did, the words, the faces and the bar their own size and the sides their own inset.
 *
 * **While See all's first page is read, the card is one skeleton block** (`SAME_LEVEL_CARD_SKELETON`,
 * [#872](https://github.com/Rakieta02/Rakieta/issues/872)): a dark card is drawn as a `skeleton` block,
 * never a dark one (design system 5.6), at its own corner and at the height its drawing gives it.
 */

import { Feather } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { BAND_NAMES, bandPresentation, sportLabel } from '@/features/onboarding/types';
import { RoundFriendButton } from '@/features/friends/types';
import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { BALANCE_FIGURE, ComparisonBar, PlayerPhoto, SkeletonBlock, theme } from '@/shared/ui';
import { balanceTone } from '@/shared/vocabulary/balancePresentation';

import { foundAtSameLevel, moreSportsOf, type SameLevelPlayer } from '../domain/sameLevel';
import type { ReaderFace } from '../hooks/useReaderFace';

import {
  DISCOVERY_COPY,
  compareLabel,
  levelsLine,
  pairingLabel,
  sportsCount,
} from './discoveryCopy';
import type { SeeAllSkeletonTile } from './SeeAllScreen';

/** **Where the card stands** — Home's line, or See all's list. */
export type SameLevelCardLayout = 'row' | 'list';

export interface SameLevelCardProps {
  readonly player: SameLevelPlayer;
  /** The reader's face, on the left — none drawn while the reader is not known. */
  readonly you: ReaderFace | undefined;
  /** Home's line draws the line's gaps; See all, the card's own. */
  readonly layout: SameLevelCardLayout;
  /** Home's row: the rail's width. See all leaves it out, and the card takes the content width. */
  readonly width?: number;
  /** Their face or nickname: their record. */
  readonly onOpen: () => void;
  /** *N sports ›*: the comparison sheet. */
  readonly onCompare: () => void;
}

export function SameLevelCard({
  player,
  you,
  layout,
  width,
  onOpen,
  onCompare,
}: SameLevelCardProps) {
  const COPY = DISCOVERY_COPY.sameLevel;
  const shown = player.shown;
  const more = moreSportsOf(player);
  const room = ROOM[layout];

  return (
    <View
      style={[s.card, room.card, width === undefined ? undefined : { width }]}
      testID={`same-level-${player.playerId}`}
    >
      <View style={s.pairing}>
        <View style={[s.side, room.side]}>
          {you === undefined ? (
            <View style={s.noFace} />
          ) : (
            <PlayerPhoto
              playerId={you.playerId}
              {...(you.photoUrl === undefined ? {} : { photoUrl: you.photoUrl })}
              box={{ kind: 'face', size: theme.size.sameLevel.face }}
            />
          )}
          <Text style={s.name} numberOfLines={1}>
            {COPY.you}
          </Text>
          <Text style={s.level}>{formatLevel(shown.yourLevel)}</Text>
        </View>

        <View style={s.middle} accessible accessibilityLabel={pairingLabel(shown, player.nickname)}>
          <Text
            style={[s.figure, { color: BALANCE_FIGURE[balanceTone(shown.percentEven)] }]}
            numberOfLines={1}
          >
            {formatPercent(shown.percentEven)}
          </Text>
          <Text style={[s.even, room.even]}>{COPY.even}</Text>
          <View style={[s.sport, room.sport]}>
            <View style={[s.dot, { backgroundColor: theme.sport[shown.sport] }]} />
            <Text style={s.sportName} numberOfLines={1}>
              {sportLabel(shown.sport)}
            </Text>
          </View>
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel={player.nickname}
          onPress={onOpen}
          hitSlop={theme.hit.peopleRow}
          style={({ pressed }) => [s.side, room.side, pressed ? s.pressed : undefined]}
        >
          <PlayerPhoto
            playerId={player.playerId}
            {...(player.photoUrl === undefined ? {} : { photoUrl: player.photoUrl })}
            box={{ kind: 'face', size: theme.size.sameLevel.face }}
          />
          <Text style={s.name} numberOfLines={1}>
            {player.nickname}
          </Text>
          <Text style={s.level}>{formatLevel(shown.theirLevel)}</Text>
        </Pressable>
      </View>

      <View style={room.bar}>
        <ComparisonBar
          yours={shown.yourLevel}
          theirs={shown.theirLevel}
          band={bandPresentation(shown.yourBand)?.key}
          bandNames={BAND_NAMES}
          markLabel={COPY.youMark}
          variant="onDark"
          accessibilityLabel={levelsLine(shown, player.nickname)}
        />
      </View>

      <View style={[s.foot, room.foot]}>
        <View style={s.words}>
          {more === undefined ? null : (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={compareLabel(player.nickname, more)}
              onPress={onCompare}
              hitSlop={theme.hit.sportsLink}
              style={({ pressed }) => [s.sports, pressed ? s.pressed : undefined]}
            >
              <Text style={s.sportsWords}>{sportsCount(more)}</Text>
              <Feather
                name="chevron-right"
                size={theme.type.rlValue.fontSize}
                color={theme.color.volt}
                accessibilityElementsHidden
                importantForAccessibility="no"
              />
            </Pressable>
          )}
        </View>
        <RoundFriendButton
          playerId={player.playerId}
          nickname={player.nickname}
          relation={player.relation}
          where={foundAtSameLevel(shown.sport)}
        />
      </View>
    </View>
  );
}

/** **A card while See all's first page is read** (#872): one block, as tall as the card. */
export const SAME_LEVEL_CARD_SKELETON: SeeAllSkeletonTile = {
  height: (_width, fontScale) => sameLevelCardHeight(fontScale, 'list'),
  Tile: SameLevelCardSkeleton,
};

function SameLevelCardSkeleton() {
  return <SkeletonBlock style={s.skeleton} />;
}

/**
 * **The card's height** in its place, read off its drawing: a gap above and one below; the pairing —
 * the taller of a side (the face, the nickname and the level, a gap apart) and the middle (the %,
 * *EVEN* a gap under it, the sport a gap under that); the comparison bar a gap under it (its *YOU*
 * row, the mark's row and the band names, `ComparisonBar`'s three, set at a fixed size); and the foot
 * a gap under that, a reach tall. Every other line grows with the phone's text size, as the OS grows
 * it.
 */
export function sameLevelCardHeight(fontScale: number, layout: SameLevelCardLayout): number {
  const { type, num, size } = theme;
  const gaps = GAPS[layout];
  const bar = size.comparisonBar;
  const line = (role: { readonly lineHeight: number }) => role.lineHeight * fontScale;
  const side = FACE + gaps.inSide + line(type.h2) + gaps.inSide + line(num.s);
  const middle =
    line(num.xl) +
    gaps.toEven +
    line(type.eyebrow) +
    gaps.toSport +
    Math.max(size.sportDot, line(type.rlLabel));
  const comparison =
    type.tag.lineHeight + bar.labelGap + bar.markHeight + bar.namesTop + type.tag.lineHeight;
  const foot = Math.max(size.minTouch, line(type.rlValue));
  return (
    gaps.top + Math.max(side, middle) + gaps.toBar + comparison + gaps.toFoot + foot + gaps.bottom
  );
}

const FACE = theme.size.sameLevel.face;

/**
 * **The card's vertical gaps, in its two places** (2026-11-26) — See all's, the drawing's own; and
 * Home's line's, where the card is `lineCardRatio` of the content rather than 0,74: each ×1,6 onto
 * the 3pt grid, so the card's height grows as its width did (226 → 253 at the OS's own text size,
 * the exact 253). Top to bottom, as the card draws them; `toEven` and `toSport` are the middle's.
 */
const GAPS: Readonly<
  Record<
    SameLevelCardLayout,
    {
      readonly top: number;
      readonly inSide: number;
      readonly toEven: number;
      readonly toSport: number;
      readonly toBar: number;
      readonly toFoot: number;
      readonly bottom: number;
    }
  >
> = {
  list: {
    top: theme.space.lg,
    inSide: theme.space.xxs,
    toEven: theme.space.xxs,
    toSport: theme.space.xs,
    toBar: theme.space.md,
    toFoot: theme.space.xs,
    bottom: theme.space.xs,
  },
  row: {
    top: theme.space.xxl,
    inSide: theme.space.xs,
    toEven: theme.space.xs,
    toSport: theme.space.sm,
    toBar: theme.space.xl,
    toFoot: theme.space.sm,
    bottom: theme.space.sm,
  },
};

const s = StyleSheet.create({
  // The whole card, at the dark card's corner.
  skeleton: { flex: 1, borderRadius: theme.radius.cardDark },
  // 5.2's dark card — its radius and padding — on the card's own ground (7.34). No shadow.
  card: {
    backgroundColor: theme.color.levelCardGround,
    borderRadius: theme.radius.cardDark,
    // The sides are the card's; the top and the foot are the place's (`ROOM`).
    paddingHorizontal: theme.space.lg,
  },
  pairing: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' },
  side: { alignItems: 'center', minWidth: FACE },
  noFace: { width: FACE, height: FACE },
  name: { ...theme.type.h2, color: theme.color.surface, maxWidth: 2 * FACE },
  level: { ...theme.num.s, ...theme.tabular, color: theme.color.onDarkTiny },
  middle: { flex: 1, alignItems: 'center', paddingHorizontal: theme.space.xs },
  // The game card's figure (num.xl) — large text, which is what lets the three inks stand here.
  figure: { ...theme.num.xl, ...theme.tabular },
  even: { ...theme.type.eyebrow, color: theme.color.onDarkTiny },
  sport: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  sportName: { ...theme.type.rlLabel, color: theme.color.onDarkTiny },
  foot: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: theme.size.minTouch,
  },
  words: { flexDirection: 'row', alignItems: 'center', flexShrink: 1 },
  sports: { flexDirection: 'row', alignItems: 'center' },
  sportsWords: { ...theme.type.rlValue, fontFamily: theme.font.sans[700], color: theme.color.volt },
  // 6.6: a press on a dark card dims what was pressed.
  pressed: { opacity: 0.7 },
});

/** **The gaps drawn, in a place** — `GAPS` as styles. */
function roomOf(layout: SameLevelCardLayout) {
  const gaps = GAPS[layout];
  return StyleSheet.create({
    card: { paddingTop: gaps.top, paddingBottom: gaps.bottom },
    side: { gap: gaps.inSide },
    even: { marginTop: gaps.toEven },
    sport: { marginTop: gaps.toSport },
    bar: { marginTop: gaps.toBar },
    foot: { marginTop: gaps.toFoot },
  });
}

const ROOM = { list: roomOf('list'), row: roomOf('row') } as const;
