/**
 * **A Groups heating up card** ([#800](https://github.com/Rakieta02/Rakieta/issues/800); the Home rows
 * screens §3.2; home rows 3, 3.2, 4, 5, 21) — **slimmer since
 * [#821](https://github.com/Rakieta02/Rakieta/issues/821)** (ADR-0205 §5, Q22; home refactor 5.1): the
 * heat bar, *+N this month* and the sport line are gone. The group sheet keeps the sports and *new this
 * month*; the heat still orders the groups and picks the tags, and is drawn nowhere.
 *
 * ```
 * ╭──────────────────────────────────────╮
 * │╱╱╱╱╱╱ the group's colour ╱╱ ▲ HOTTEST │  ← band: the monogram's hue, paler stripes; the tag
 * │ ┌────┐                               │     on its ink pill, the mark in volt
 * │ │ O3 │  ← the shield over band and body
 * │ └────╯                               │
 * │ Ogrody 33 Club                       │  ← h2
 * │ 14                                11 │  ← num.m
 * │ games this week              players │  ← tiny: the games at the left, the players at the right
 * │ ▣▣▣▣                    ( Ask to join )│  ← four faces; the chip
 * ╰──────────────────────────────────────╯
 * ```
 *
 * **Two doors, and the card is not one element.** A tap on the chip acts (the mechanics §5.7); a tap
 * anywhere else opens the group sheet. So the card is 5.1's `Card` with its pressed border drawn by
 * the two presses that open the sheet — the body, and the faces beside the chip — and the chip is a
 * button of its own, as Home's game card draws its two (5.1's `pressed` note). The faces' press is
 * the body's door a second time, hidden from a listener, who reaches the sheet by the body.
 *
 * **Everything is the server's**: the tag, the figures, the faces.
 *
 * **Two places, two sets of gaps** (`layout`, 2026-11-26). On the Groups heating up page the card is
 * drawn at its own gaps. On Home's line it is `lineCardRatio` of the line's content, wider than the
 * page's 0,74, and **keeps its shape**: every vertical gap grows by the same factor onto the 3pt grid
 * (`GAPS`) — 9·6·3·9·12 to 15·9·6·15·18 — so its height grows as its width did, the words and shapes
 * their own size and the sides their own inset.
 *
 * **While Groups heating up's first page is read, the card stands as its skeleton**
 * (`HottestGroupCardSkeleton`, [#872](https://github.com/Rakieta02/Rakieta/issues/872)): 5.1's white
 * card is always there, so it is drawn as itself, at the card's own height, with the shapes every
 * card has inside it — the band, the shield over it in the card's white ring, the name, and the two
 * figures over their words. The tag is the hottest few's and the faces are as many as the server
 * sends, so neither is drawn; nor is the chip, whose words are the reader's relation — the foot keeps
 * its room.
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { Button, Card, Plus, SkeletonBlock, SkeletonLine, SkeletonWords, theme } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import type { GroupAction } from '../domain/groupRules';
import { groupAction } from '../domain/groupRules';
import { cardFaces, isJoinTap } from '../domain/hottest';
import type { HeatTag } from '../domain/vocabulary';

import { FaceStack } from './FaceStack';
import { GROUPS_COPY } from './groupsCopy';
import { GroupMonogram, monogramHue } from './GroupMonogram';
import { gamesThisWeekWords, hottestCardLabel, hottestChipLabel } from './groupsPresentation';

const HOT = GROUPS_COPY.hottest;
const SIZE = theme.size.hottest;

/** **Where the card stands** — Home's line, or the Groups heating up page. */
export type HottestCardLayout = 'row' | 'page';

export interface HottestGroupCardProps {
  readonly group: HottestGroup;
  readonly width: number;
  /** Home's line draws the line's gaps; the page, the card's own. */
  readonly layout: HottestCardLayout;
  /** Anywhere but the chip: the group sheet. */
  readonly onOpen: () => void;
  /** The chip, by what it offers: join, ask, the withdraw sheet, or the group's page. */
  readonly onChip: (action: GroupAction) => void;
}

export function HottestGroupCard({ group, width, layout, onOpen, onChip }: HottestGroupCardProps) {
  const [pressed, setPressed] = useState(false);
  const room = ROOM[layout];
  const opens = {
    onPress: onOpen,
    onPressIn: () => setPressed(true),
    onPressOut: () => setPressed(false),
  };

  return (
    <Card pressed={pressed} style={[s.card, { width }]}>
      <Pressable
        {...opens}
        accessibilityRole="button"
        accessibilityLabel={hottestCardLabel(group)}
        accessibilityHint={HOT.opensSheet}
        testID={`hottest-${group.id}`}
      >
        <Band colourKey={group.monogram.colourKey} width={width} />
        {group.tag === null ? null : <TagPill tag={group.tag} />}
        <View style={s.shield}>
          <GroupMonogram monogram={group.monogram} size="shield" shape="shield" />
        </View>

        <View style={[s.body, room.body]}>
          <Text style={s.name} numberOfLines={1}>
            {group.name}
          </Text>
          <View style={s.figures}>
            <Figure
              value={group.gamesThisWeek}
              words={gamesThisWeekWords(group.gamesThisWeek)}
              layout={layout}
              testID="hottest-games"
            />
            <Figure
              value={group.memberCount}
              words={HOT.players}
              end
              layout={layout}
              testID="hottest-players"
            />
          </View>
        </View>
      </Pressable>

      <View style={[s.foot, room.foot]}>
        <Pressable
          {...opens}
          style={s.faces}
          hitSlop={theme.hit.btn}
          accessible={false}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          <FaceStack faces={cardFaces(group)} more={0} testIDPrefix={`hottest-face-${group.id}-`} />
        </Pressable>
        <ChipButton action={groupAction(group)} groupName={group.name} onPress={onChip} />
      </View>
    </Card>
  );
}

/** The chip at the card's foot (the screens §3.2's table). */
function ChipButton({
  action,
  groupName,
  onPress,
}: {
  readonly action: GroupAction;
  readonly groupName: string;
  readonly onPress: (action: GroupAction) => void;
}) {
  return (
    <Button
      label={HOT.chip[action]}
      accessibilityLabel={hottestChipLabel(action, groupName)}
      {...(action === 'requested'
        ? { accessibilityHint: HOT.opensWithdraw }
        : action === 'in'
          ? { accessibilityHint: HOT.opensGroup }
          : {})}
      variant={isJoinTap(action) ? 'dark' : 'secondary'}
      size="sm"
      shape="pill"
      onPress={() => onPress(action)}
    />
  );
}

/**
 * One figure: the number in mono over its words — at the card's left, or held against its right edge
 * (`end`), as home refactor 5.1 draws *11 players*.
 */
function Figure({
  value,
  words,
  end = false,
  layout,
  testID,
}: {
  readonly value: number;
  readonly words: string;
  readonly end?: boolean;
  readonly layout: HottestCardLayout;
  readonly testID: string;
}) {
  return (
    <View style={[s.figure, ROOM[layout].figure, end ? s.figureEnd : undefined]} testID={testID}>
      <Text style={s.value}>{value}</Text>
      <Text style={s.words} numberOfLines={1}>
        {words}
      </Text>
    </View>
  );
}

/**
 * **The band** — the group's own colour with paler stripes across it, drawn as diagonals one stripe
 * apart from before the left edge to the right one. Hidden: it is a picture of the group's tile.
 */
function Band({ colourKey, width }: { readonly colourKey: number; readonly width: number }) {
  const height = SIZE.band;
  const step = SIZE.stripe * 2;
  const stripes: string[] = [];
  for (let x = -height; x < width + step; x += step) {
    stripes.push(`M ${x} ${height} L ${x + height} 0`);
  }
  return (
    <View
      style={[s.band, { backgroundColor: monogramHue(colourKey) }]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={width} height={height}>
        <Path
          d={stripes.join(' ')}
          stroke={theme.color.groupBandStripe}
          strokeWidth={SIZE.stripe}
        />
      </Svg>
    </View>
  );
}

/** *▲ HOTTEST* or *+ GROWING* — the mark drawn in volt on an ink pill; spoken with the card. */
function TagPill({ tag }: { readonly tag: HeatTag }) {
  return (
    <View
      style={s.tag}
      testID={`hottest-tag-${tag}`}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {tag === 'HOTTEST' ? (
        <Svg width={SIZE.tagMark} height={SIZE.tagMark} viewBox="0 0 10 10">
          <Path d="M 5 0.5 L 9.5 9.5 L 0.5 9.5 Z" fill={theme.color.volt} />
        </Svg>
      ) : (
        <Plus />
      )}
      <Text style={s.tagWord}>{HOT.tag[tag]}</Text>
    </View>
  );
}

/** **A card while the page's first read is out** (#872): the white card, and its shapes. */
export function HottestGroupCardSkeleton({
  width,
  height,
}: {
  readonly width: number;
  /** `hottestCardHeight`'s, at the phone's text size. */
  readonly height: number;
}) {
  return (
    <View testID="hottest-skeleton-card" style={[s.skeletonCard, { width, height }]}>
      <SkeletonBlock style={s.skeletonBand} />
      <View style={s.skeletonShield}>
        <SkeletonBlock style={s.skeletonShieldTile} />
      </View>
      <View style={[s.body, ROOM.page.body]}>
        <SkeletonLine role={theme.type.h2} width="50%" />
        <View style={s.figures}>
          {/* Two figures each, as most cards draw. Worked out at the call. */}
          <View style={[s.figure, ROOM.page.figure]}>
            <SkeletonWords role={FIGURE} words="14" />
            <SkeletonWords role={theme.type.tiny} words={gamesThisWeekWords(14)} />
          </View>
          <View style={[s.figure, ROOM.page.figure, s.figureEnd]}>
            <SkeletonWords role={FIGURE} words="11" style={s.skeletonEnd} />
            <SkeletonWords role={theme.type.tiny} words={HOT.players} style={s.skeletonEnd} />
          </View>
        </View>
      </View>
    </View>
  );
}

/**
 * **The card's height**, read off its drawing in its place (`layout`, the page's by default): its
 * border; the band; the body under it — the shield's overhang and a gap (`bodyTop`), the name, a gap,
 * and the figures, each number over its words a gap apart; and the foot — a gap above and one below,
 * and between them the faces' reach, a button tall, the chip beside them a step shorter. The words'
 * lines grow with the phone's text size (`fontScale`), as the OS grows them.
 */
export function hottestCardHeight(fontScale: number, layout: HottestCardLayout = 'page'): number {
  const { type, num, size } = theme;
  const gaps = GAPS[layout];
  return (
    2 * CARD_BORDER +
    SIZE.band +
    bodyTop(layout) +
    type.h2.lineHeight * fontScale +
    gaps.nameToFigures +
    num.m.lineHeight * fontScale +
    gaps.figureToWords +
    type.tiny.lineHeight * fontScale +
    gaps.figuresToFoot +
    size.btn +
    gaps.footToEdge
  );
}

/**
 * **The card's vertical gaps, in its two places** (2026-11-26) — the page's, the drawing's own; and
 * Home's line's, where the card is `lineCardRatio` of the content rather than 0,74: each ×1,6 onto
 * the 3pt grid, so the card's height grows as its width did (188 → 212 at the OS's own text size,
 * the exact 211). Top to bottom, as the card draws them.
 */
const GAPS: Readonly<
  Record<
    HottestCardLayout,
    {
      readonly shieldToName: number;
      readonly nameToFigures: number;
      readonly figureToWords: number;
      readonly figuresToFoot: number;
      readonly footToEdge: number;
    }
  >
> = {
  page: {
    shieldToName: theme.space.sm,
    nameToFigures: theme.space.xs,
    figureToWords: theme.space.xxs,
    figuresToFoot: theme.space.sm,
    footToEdge: theme.space.md,
  },
  row: {
    shieldToName: theme.space.lg,
    nameToFigures: theme.space.sm,
    figureToWords: theme.space.xs,
    figuresToFoot: theme.space.lg,
    footToEdge: theme.space.xl,
  },
};

/** Below the band: the shield's overhang under it, then the gap to the name. */
function bodyTop(layout: HottestCardLayout): number {
  return SIZE.shieldTop + theme.size.monogram.shield - SIZE.band + GAPS[layout].shieldToName;
}

/** 5.1's card border, a `line` point all round. */
const CARD_BORDER = 1;

/** A figure's number, as the card sets it. */
const FIGURE = { ...theme.num.m, ...theme.tabular };

/** The shield's two lower corners — `GroupMonogram`'s, on its outer edge. */
const SHIELD_FOOT = Math.round(theme.size.monogram.shield * SIZE.shieldFoot);

const s = StyleSheet.create({
  // 5.1's card drawn as itself, its padding moved inside as the card's is.
  skeletonCard: {
    backgroundColor: theme.color.surface,
    borderWidth: CARD_BORDER,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
  },
  // Edge to edge, the card's corner clipping it, as the band is.
  skeletonBand: { height: SIZE.band, borderRadius: 0 },
  // The shield's place, its ring the card's white — so it lies over the band, as the real one does.
  skeletonShield: {
    position: 'absolute',
    top: SIZE.shieldTop,
    left: theme.space.md,
    width: theme.size.monogram.shield,
    height: theme.size.monogram.shield,
    padding: SIZE.shieldRing,
    backgroundColor: theme.color.surface,
    borderBottomLeftRadius: SHIELD_FOOT,
    borderBottomRightRadius: SHIELD_FOOT,
  },
  skeletonShieldTile: {
    flex: 1,
    borderRadius: 0,
    borderBottomLeftRadius: SHIELD_FOOT - SIZE.shieldRing,
    borderBottomRightRadius: SHIELD_FOOT - SIZE.shieldRing,
  },
  skeletonEnd: { alignSelf: 'flex-end' },
  // 5.1's card, its padding moved inside so the band runs to the card's edges.
  card: { padding: 0, overflow: 'hidden' },
  band: { height: SIZE.band },
  shield: { position: 'absolute', top: SIZE.shieldTop, left: theme.space.md },
  tag: {
    position: 'absolute',
    top: theme.space.sm,
    right: theme.space.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    height: theme.size.tag,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.ink,
  },
  tagWord: { ...theme.type.tag, color: theme.color.surface },
  // The gaps are the place's (`ROOM`); the sides are the card's, in both.
  body: { paddingHorizontal: theme.space.md },
  name: { ...theme.type.h2, color: theme.color.ink },
  figures: { flexDirection: 'row', gap: theme.space.md },
  figure: { flex: 1 },
  // The players, held against the card's right edge (home refactor 5.1).
  figureEnd: { alignItems: 'flex-end' },
  value: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  words: { ...theme.type.tiny, color: theme.color.muted },
  foot: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingHorizontal: theme.space.md,
  },
  // 34 and `hit.btn` reach 44 (6.5), the same reach as a button beside it.
  faces: { flex: 1, minHeight: theme.size.btn, justifyContent: 'center' },
});

/** **The gaps drawn, in a place** — `GAPS` as styles. */
function roomOf(layout: HottestCardLayout) {
  const gaps = GAPS[layout];
  return StyleSheet.create({
    body: { paddingTop: bodyTop(layout), gap: gaps.nameToFigures },
    figure: { gap: gaps.figureToWords },
    foot: { paddingTop: gaps.figuresToFoot, paddingBottom: gaps.footToEdge },
  });
}

const ROOM = { page: roomOf('page'), row: roomOf('row') } as const;
