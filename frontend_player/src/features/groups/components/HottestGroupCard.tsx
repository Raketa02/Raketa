/**
 * **A Hottest groups card** ([#800](https://github.com/Raketa02/Raketa/issues/800); the Home rows
 * screens §3.2; home rows 3, 3.2, 4, 5, 21).
 *
 * ```
 * ╭──────────────────────────────────────╮
 * │╱╱╱╱╱╱ the group's colour ╱╱ ▲ HOTTEST │  ← band: the monogram's hue, paler stripes; the tag
 * │ ┌────┐                               │     on its ink pill, the mark in volt
 * │ │ O3 │  ← the shield over band and body
 * │ └────╯                               │
 * │ Ogrody 33 Club                       │  ← h2
 * │ ● ● ● ● Padel · Tennis · Squash · Ba…│  ← the dots, the names cut with an ellipsis
 * │ 14               11                  │  ← num.m
 * │ games this week  players +3 this month│  ← tiny, the growth in mintInk
 * │ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ │  ← the heat bar, amber to coral, at the served share
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
 * **Everything is the server's**: the tag, the figures, the faces, the share the bar fills to.
 */

import { useId, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Defs, LinearGradient, Path, Rect, Stop } from 'react-native-svg';

import { Button, Card, Plus, theme } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import type { GroupAction } from '../domain/groupRules';
import { groupAction } from '../domain/groupRules';
import { cardFaces, heatFill, isJoinTap } from '../domain/hottest';
import type { HeatTag } from '../domain/vocabulary';

import { FaceStack } from './FaceStack';
import { GROUPS_COPY } from './groupsCopy';
import { GroupMonogram, monogramHue } from './GroupMonogram';
import {
  gamesThisWeekWords,
  grownBy,
  hottestCardLabel,
  hottestChipLabel,
  hottestSports,
} from './groupsPresentation';
import { SportDots } from './SportDots';

const HOT = GROUPS_COPY.hottest;
const SIZE = theme.size.hottest;

export interface HottestGroupCardProps {
  readonly group: HottestGroup;
  readonly width: number;
  /** Anywhere but the chip: the group sheet. */
  readonly onOpen: () => void;
  /** The chip, by what it offers: join, ask, the withdraw sheet, or the group's page. */
  readonly onChip: (action: GroupAction) => void;
}

export function HottestGroupCard({ group, width, onOpen, onChip }: HottestGroupCardProps) {
  const [pressed, setPressed] = useState(false);
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

        <View style={s.body}>
          <Text style={s.name} numberOfLines={1}>
            {group.name}
          </Text>
          <View style={s.sports}>
            <SportDots sports={group.sports} />
            <Text style={s.sportNames} numberOfLines={1}>
              {hottestSports(group.sports)}
            </Text>
          </View>
          <View style={s.figures}>
            <Figure value={group.gamesThisWeek} words={gamesThisWeekWords(group.gamesThisWeek)} />
            <Figure
              value={group.memberCount}
              words={HOT.players}
              grown={grownBy(group.newThisMonth)}
            />
          </View>
          <HeatBar share={group.heatShare} />
        </View>
      </Pressable>

      <View style={s.foot}>
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

/** One figure: the number in mono over its words, the green growth beside the players. */
function Figure({
  value,
  words,
  grown,
}: {
  readonly value: number;
  readonly words: string;
  readonly grown?: string | undefined;
}) {
  return (
    <View style={s.figure}>
      <Text style={s.value}>{value}</Text>
      <Text style={s.words} numberOfLines={1}>
        {words}
        {grown === undefined ? null : (
          <>
            {' '}
            <Growth>{grown}</Growth> {HOT.thisMonth}
          </>
        )}
      </Text>
    </View>
  );
}

/** **The green growth**, *+3* — a gain banked, mono, `mintInk` (1.3 as amended). The sheet's too. */
export function Growth({ children }: { readonly children: string }) {
  return <Text style={s.grown}>{children}</Text>;
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

/**
 * **The heat bar** — a pale track, filled from the left to the served share in a gradient from amber
 * to coral: the heat, the hot tag's colour at its end (Part 16, 2026-11-14). Every card's bar is
 * measured against the HOTTEST card's, which is full.
 */
function HeatBar({ share }: { readonly share: number }) {
  const fill = heatFill(share);
  const gradient = useId();
  return (
    <View
      style={s.track}
      testID="heat-bar"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <View style={[s.fill, { width: `${fill * 100}%` }]} testID="heat-fill">
        <Svg width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">
          <Defs>
            <LinearGradient id={gradient} x1="0" y1="0" x2="1" y2="0">
              <Stop offset={0} stopColor={theme.color.amber} />
              <Stop offset={1} stopColor={theme.color.coral} />
            </LinearGradient>
          </Defs>
          <Rect x={0} y={0} width={1} height={1} fill={`url(#${gradient})`} />
        </Svg>
      </View>
    </View>
  );
}

/** Below the band: the shield's overhang under it, then 9 to the name. */
const BODY_TOP = SIZE.shieldTop + theme.size.monogram.shield - SIZE.band + theme.space.sm;

const s = StyleSheet.create({
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
  body: {
    paddingTop: BODY_TOP,
    paddingHorizontal: theme.space.md,
    gap: theme.space.xs,
  },
  name: { ...theme.type.h2, color: theme.color.ink },
  sports: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  sportNames: { ...theme.type.tiny, color: theme.color.muted, flexShrink: 1 },
  figures: { flexDirection: 'row', gap: theme.space.md },
  figure: { flex: 1, gap: theme.space.xxs },
  value: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  words: { ...theme.type.tiny, color: theme.color.muted },
  grown: {
    ...theme.num.tiny,
    ...theme.tabular,
    fontFamily: theme.font.mono[600],
    color: theme.color.mintInk,
  },
  track: {
    height: SIZE.heatBar,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.line2,
    overflow: 'hidden',
    marginTop: theme.space.xxs,
  },
  fill: { height: '100%', borderRadius: theme.radius.pill, overflow: 'hidden' },
  foot: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingHorizontal: theme.space.md,
    paddingTop: theme.space.sm,
    paddingBottom: theme.space.md,
  },
  // 34 and `hit.btn` reach 44 (6.5), the same reach as a button beside it.
  faces: { flex: 1, minHeight: theme.size.btn, justifyContent: 'center' },
});
