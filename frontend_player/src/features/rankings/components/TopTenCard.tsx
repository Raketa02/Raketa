/**
 * **A Top 10 card** ([#805](https://github.com/Raketa02/Raketa/issues/805); the Home rows screens
 * §7.2; the words §31.11; home rows 25–26.1; design-system 7.36) — the numeral, and the portrait
 * card standing over its right part.
 *
 * - **The numeral** (`TopTenNumeral`) behind the card's left edge, the card overlapping its last
 *   `topTen.overlap`; its baseline near the card's foot. *10* is a figure wider.
 * - **The portrait** — `shared/ui`'s `PortraitTile`: the photo or the court poster with the wash, and
 *   over it the nickname — *You* on the reader's own — then the level in mono and the week's move.
 * - **The move** — a drawn triangle and the count, **▲ in volt, ▼ in coral's lifted `gameCoral`**,
 *   with no ground, leaning as an italic does (home rows 25: *a triangle and a bold italic digit*).
 *   The app loads no italic, so the pair is slanted together rather than set in a face it has not got.
 *   **None for no change or *New*** — the read sends none (the README's override 10).
 * - **The reader's own card** is ringed in volt, outside its edge (home rows 26.1): the ring touches
 *   the dark card it bounds, so it is volt's stroke on dark.
 *
 * **A tap opens the record** — the row's to open. The card's spoken name is its place, name, level and
 * move (`topTenCardLabel`); the numeral and the chip say nothing of their own.
 */

import { StyleSheet, Text, View } from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';
import { PortraitTile, theme } from '@/shared/ui';

import type { Moved, TopTenPlayer } from '../domain/topTen';

import { MoveMark } from './MoveMark';
import { rowName, topTenCardLabel } from './rankingsCopy';
import { TopTenNumeral } from './TopTenNumeral';

const MOVE_INK: Readonly<Record<Moved['kind'], string>> = {
  UP: theme.color.volt,
  DOWN: theme.color.gameCoral,
};

export interface TopTenCardProps {
  readonly player: TopTenPlayer;
  /** The portrait's width — the rail's. */
  readonly width: number;
  readonly onOpen: () => void;
}

export function TopTenCard({ player, width, onOpen }: TopTenCardProps) {
  return (
    <View testID={`top-ten-card-${player.playerId}`} style={s.item}>
      <TopTenNumeral place={player.place} mine={player.isYou} />
      <View style={[s.card, { width }]}>
        <PortraitTile
          playerId={player.playerId}
          {...(player.photoUrl === undefined ? {} : { photoUrl: player.photoUrl })}
          width={width}
          aspect={theme.size.topTen.aspect}
          accessibilityLabel={topTenCardLabel(player)}
          onPress={onOpen}
        >
          <Text style={s.name} numberOfLines={1}>
            {rowName(player)}
          </Text>
          <View style={s.levelLine}>
            <Text style={s.level}>{formatLevel(player.level)}</Text>
            {player.chip === undefined ? null : <Move chip={player.chip} />}
          </View>
        </PortraitTile>
        {player.isYou ? <View testID="top-ten-ring" pointerEvents="none" style={s.ring} /> : null}
      </View>
    </View>
  );
}

/** *▲ 2* or *▼ 1*, drawn — hidden: the card's name says it. */
function Move({ chip }: { readonly chip: Moved }) {
  const ink = MOVE_INK[chip.kind];
  return (
    <View
      testID={`top-ten-chip-${chip.kind}`}
      style={s.move}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <MoveMark up={chip.kind === 'UP'} size={theme.size.topTen.chipMark} ink={ink} />
      <Text style={[s.count, { color: ink }]}>{String(chip.places)}</Text>
    </View>
  );
}

const RING = theme.size.topTen.ring;

const s = StyleSheet.create({
  // The numeral, then the card over its right part, both on the card's foot. Padded by the ring, so
  // the reader's ring is never clipped by the rail.
  item: { flexDirection: 'row', alignItems: 'flex-end', paddingVertical: RING },
  card: { marginLeft: -theme.size.topTen.overlap },
  // Over the wash, as on New in Raketa's tile — every label with the on-media shadow (7.31).
  name: { ...theme.type.h2, color: theme.color.surface, ...theme.shadow.textOnMedia },
  levelLine: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  level: {
    ...theme.num.tiny,
    ...theme.tabular,
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
  move: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    // An italic's slant, drawn: the mark and its count lean together.
    transform: [{ skewX: `${theme.size.topTen.lean}deg` }],
  },
  // Bold: the mono family's heaviest loaded weight, at the level's size.
  count: {
    ...theme.num.tiny,
    ...theme.tabular,
    fontFamily: theme.font.mono[600],
    ...theme.shadow.textOnMedia,
  },
  // Outside the card's edge, its corner following the card's.
  ring: {
    position: 'absolute',
    top: -RING,
    left: -RING,
    right: -RING,
    bottom: -RING,
    borderWidth: RING,
    borderColor: theme.color.volt,
    borderRadius: theme.radius.cardDark + RING,
  },
});
