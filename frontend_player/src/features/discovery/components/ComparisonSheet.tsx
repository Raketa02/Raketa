/**
 * **The comparison sheet** — *You vs zofia.b* ([#802](https://github.com/Rakieta02/Rakieta/issues/802);
 * the Home rows screens §4.3; the mechanics §6.5; the words §31.6; home rows 9, 11; design-system
 * 7.34). Opened by a card's *N sports ›*, on Home's row and in See all alike.
 *
 * - **The title row**: *You vs zofia.b*, and the sheet's friend button at its right end —
 *   `friends`' worded twin (*✓ Friends*, *+ Add friend*, *Request sent*, *Accept*), asking from *same
 *   level* in **the card's sport**, the one the card showed.
 * - **One block per shared sport, in the served order — most even first** — divided by hairlines:
 *   the sport with its dot and *You 2,71 · zofia.b 2,69*; the comparison bar in its light paint (a
 *   mint fill, an ink mark); the gap in words, and *91% even* as the tag of its tone, the light
 *   version of the card's colour (mint, amber or red, by the game cards' breaks).
 * - **Three or four blocks stack the same way**, and the sheet scrolls (`BottomSheet`'s own cap).
 *
 * **All of it rides on the card's item** (§6.5): the sheet reads nothing. The person comes in from
 * the caller's current read, so a friend write that re-reads the row moves the button here too.
 */

import { StyleSheet, Text, View } from 'react-native';

import { BAND_NAMES, bandPresentation, sportLabel } from '@/features/onboarding/types';
import { RoundFriendButton } from '@/features/friends/types';
import { BottomSheet, ComparisonBar, Hairline, Tag, theme } from '@/shared/ui';
import { balanceTone } from '@/shared/vocabulary/balancePresentation';

import {
  foundAtSameLevel,
  levelGapOf,
  type LevelComparison,
  type SameLevelPlayer,
} from '../domain/sameLevel';

import {
  DISCOVERY_COPY,
  closeComparisonLabel,
  comparisonTitle,
  evenTag,
  gapLine,
  levelsLine,
} from './discoveryCopy';

export interface ComparisonSheetProps {
  readonly visible: boolean;
  /** Whom the sheet compares — kept by the caller while the sheet closes, so it leaves drawn. */
  readonly player: SameLevelPlayer;
  readonly onClose: () => void;
}

export function ComparisonSheet({ visible, player, onClose }: ComparisonSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={comparisonTitle(player.nickname)}
      closeLabel={closeComparisonLabel(player.nickname)}
      action={
        <RoundFriendButton
          playerId={player.playerId}
          nickname={player.nickname}
          relation={player.relation}
          where={foundAtSameLevel(player.shown.sport)}
          variant="worded"
        />
      }
    >
      {player.sports.map((comparison, index) =>
        index === 0 ? (
          <Block key={comparison.sport} comparison={comparison} nickname={player.nickname} />
        ) : (
          <Hairline key={comparison.sport} style={s.fold}>
            <Block comparison={comparison} nickname={player.nickname} />
          </Hairline>
        ),
      )}
    </BottomSheet>
  );
}

function Block({
  comparison,
  nickname,
}: {
  readonly comparison: LevelComparison;
  readonly nickname: string;
}) {
  return (
    <View style={s.block} testID={`comparison-${comparison.sport}`}>
      <View style={s.head}>
        <View style={s.sport}>
          <View style={[s.dot, { backgroundColor: theme.sport[comparison.sport] }]} />
          <Text style={s.sportName} numberOfLines={1}>
            {sportLabel(comparison.sport)}
          </Text>
        </View>
        <Text style={s.levels} numberOfLines={1}>
          {levelsLine(comparison, nickname)}
        </Text>
      </View>
      <ComparisonBar
        yours={comparison.yourLevel}
        theirs={comparison.theirLevel}
        band={bandPresentation(comparison.yourBand)?.key}
        bandNames={BAND_NAMES}
        markLabel={DISCOVERY_COPY.sameLevel.youMark}
        variant="base"
        accessibilityLabel={levelsLine(comparison, nickname)}
      />
      <View style={s.foot}>
        <Text style={s.gap} numberOfLines={1}>
          {gapLine(levelGapOf(comparison.levelGap))}
        </Text>
        <Tag
          label={evenTag(comparison.percentEven)}
          variant={balanceTone(comparison.percentEven)}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  fold: { marginTop: theme.space.md },
  block: { gap: theme.space.sm, paddingBottom: theme.space.xs },
  head: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
  },
  sport: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs, flexShrink: 1 },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  sportName: { ...theme.type.h2, color: theme.color.ink },
  levels: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  foot: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  gap: { ...theme.type.rlLabel, color: theme.color.muted, flexShrink: 1 },
});
