/**
 * **A Groups heating up card** ([#800](https://github.com/Raketa02/Raketa/issues/800); the Home rows
 * screens §3.2; home rows 3, 3.2, 4, 5, 21) — **slimmer since
 * [#821](https://github.com/Raketa02/Raketa/issues/821)** (ADR-0205 §5, Q22; home refactor 5.1): the
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
 */

import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { Button, Card, Plus, theme } from '@/shared/ui';

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
          <View style={s.figures}>
            <Figure
              value={group.gamesThisWeek}
              words={gamesThisWeekWords(group.gamesThisWeek)}
              testID="hottest-games"
            />
            <Figure value={group.memberCount} words={HOT.players} end testID="hottest-players" />
          </View>
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

/**
 * One figure: the number in mono over its words — at the card's left, or held against its right edge
 * (`end`), as home refactor 5.1 draws *11 players*.
 */
function Figure({
  value,
  words,
  end = false,
  testID,
}: {
  readonly value: number;
  readonly words: string;
  readonly end?: boolean;
  readonly testID: string;
}) {
  return (
    <View style={[s.figure, end ? s.figureEnd : undefined]} testID={testID}>
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
  figures: { flexDirection: 'row', gap: theme.space.md },
  figure: { flex: 1, gap: theme.space.xxs },
  // The players, held against the card's right edge (home refactor 5.1).
  figureEnd: { alignItems: 'flex-end' },
  value: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  words: { ...theme.type.tiny, color: theme.color.muted },
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
