/**
 * **A Same competitive level card** ([#802](https://github.com/Raketa02/Raketa/issues/802); the Home
 * rows screens §4.2, §4.4; the words §31.5; home rows 7, 8, 10, 10.2, 10.3, 12–16; design-system
 * 7.34) — a dark card on its own ground (`levelCardGround`). **Its foot says no gap in words since
 * [#821](https://github.com/Raketa02/Raketa/issues/821)** (ADR-0205 §5, Q22; home refactor 7): *0,02
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
 * **While See all's first page is read, the card is one skeleton block** (`SAME_LEVEL_CARD_SKELETON`,
 * [#872](https://github.com/Raketa02/Raketa/issues/872)): a dark card is drawn as a `skeleton` block,
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

export interface SameLevelCardProps {
  readonly player: SameLevelPlayer;
  /** The reader's face, on the left — none drawn while the reader is not known. */
  readonly you: ReaderFace | undefined;
  /** Home's row: the rail's width. See all leaves it out, and the card takes the content width. */
  readonly width?: number;
  /** Their face or nickname: their record. */
  readonly onOpen: () => void;
  /** *N sports ›*: the comparison sheet. */
  readonly onCompare: () => void;
}

export function SameLevelCard({ player, you, width, onOpen, onCompare }: SameLevelCardProps) {
  const COPY = DISCOVERY_COPY.sameLevel;
  const shown = player.shown;
  const more = moreSportsOf(player);

  return (
    <View
      style={[s.card, width === undefined ? undefined : { width }]}
      testID={`same-level-${player.playerId}`}
    >
      <View style={s.pairing}>
        <View style={s.side}>
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
          <Text style={s.even}>{COPY.even}</Text>
          <View style={s.sport}>
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
          style={({ pressed }) => [s.side, pressed ? s.pressed : undefined]}
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

      <View style={s.bar}>
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

      <View style={s.foot}>
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
  height: (_width, fontScale) => cardHeight(fontScale),
  Tile: SameLevelCardSkeleton,
};

function SameLevelCardSkeleton() {
  return <SkeletonBlock style={s.skeleton} />;
}

/**
 * **The card's height**, read off its drawing: `lg` above and `xs` below; the pairing — the taller
 * of a side (the face, the nickname and the level, `xxs` apart) and the middle (the %, *EVEN* `xxs`
 * under it, the sport `xs` under that); the comparison bar `md` under it (its *YOU* row, the mark's
 * row and the band names, `ComparisonBar`'s three, set at a fixed size); and the foot `xs` under
 * that, a reach tall. Every other line grows with the phone's text size, as the OS grows it.
 */
function cardHeight(fontScale: number): number {
  const { space, type, num, size } = theme;
  const bar = size.comparisonBar;
  const line = (role: { readonly lineHeight: number }) => role.lineHeight * fontScale;
  const side = FACE + space.xxs + line(type.h2) + space.xxs + line(num.s);
  const middle =
    line(num.xl) +
    space.xxs +
    line(type.eyebrow) +
    space.xs +
    Math.max(size.sportDot, line(type.rlLabel));
  const comparison =
    type.tag.lineHeight + bar.labelGap + bar.markHeight + bar.namesTop + type.tag.lineHeight;
  const foot = Math.max(size.minTouch, line(type.rlValue));
  return space.lg + Math.max(side, middle) + space.md + comparison + space.xs + foot + space.xs;
}

const FACE = theme.size.sameLevel.face;

const s = StyleSheet.create({
  // The whole card, at the dark card's corner.
  skeleton: { flex: 1, borderRadius: theme.radius.cardDark },
  // 5.2's dark card — its radius and padding — on the card's own ground (7.34). No shadow.
  card: {
    backgroundColor: theme.color.levelCardGround,
    borderRadius: theme.radius.cardDark,
    paddingHorizontal: theme.space.lg,
    paddingTop: theme.space.lg,
    paddingBottom: theme.space.xs,
  },
  pairing: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' },
  side: { alignItems: 'center', gap: theme.space.xxs, minWidth: FACE },
  noFace: { width: FACE, height: FACE },
  name: { ...theme.type.h2, color: theme.color.surface, maxWidth: 2 * FACE },
  level: { ...theme.num.s, ...theme.tabular, color: theme.color.onDarkTiny },
  middle: { flex: 1, alignItems: 'center', paddingHorizontal: theme.space.xs },
  // The game card's figure (num.xl) — large text, which is what lets the three inks stand here.
  figure: { ...theme.num.xl, ...theme.tabular },
  even: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkTiny,
    marginTop: theme.space.xxs,
  },
  sport: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xs,
    marginTop: theme.space.xs,
  },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  sportName: { ...theme.type.rlLabel, color: theme.color.onDarkTiny },
  bar: { marginTop: theme.space.md },
  foot: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: theme.space.xs,
    minHeight: theme.size.minTouch,
  },
  words: { flexDirection: 'row', alignItems: 'center', flexShrink: 1 },
  sports: { flexDirection: 'row', alignItems: 'center' },
  sportsWords: { ...theme.type.rlValue, fontFamily: theme.font.sans[700], color: theme.color.volt },
  // 6.6: a press on a dark card dims what was pressed.
  pressed: { opacity: 0.7 },
});
