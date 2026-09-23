/**
 * One of the deck card's three tiles — a name, and the figure under it, on the wash.
 *
 * It is `StatBox`'s shape read on the app's second dark surface
 * ([ADR-0169](../../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7): the same padding, the same corner, a label over a tabular figure — on the **existing
 * dark-tile tokens** rather than the recessed paper. `onDarkTag` is the bed, which is 5.2's
 * repaint of a tag's ground; the label is `eyebrow` in `onDarkEyebrow` (4,74 on `night`),
 * because the mocks set the names small, capitalised and tracked, which is what an eyebrow is;
 * the figure is `surface`.
 *
 * A component of the deck's own rather than a third `StatBox` variant, because it differs from
 * the box in the label's role and not only in its colours — and a variant that changed the type
 * role would be the *one shape* argument `StatBox` exists on, broken from inside. It is fenced
 * to this card with the rest of §7's values: the day a second surface wants a dark tile, the
 * shape moves down and gains a variant properly.
 *
 * **Always three, and a dash is a figure's absence.** The row is the deck's promise of the same
 * three facts on every card (`deckTiles`); the tile prints whatever it is handed and decides
 * nothing. It announces nothing of its own — the card body speaks the tiles that have a figure.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { DeckTile as Tile } from '../deckCardPresentation';

export interface DeckTileProps {
  readonly tile: Tile;
}

export function DeckTile({ tile }: DeckTileProps) {
  return (
    <View style={s.tile}>
      <Text style={s.label} numberOfLines={1}>
        {tile.label}
      </Text>
      <Text style={s.figure} numberOfLines={1}>
        {tile.value}
      </Text>
    </View>
  );
}

/** The row the three sit in — equal thirds, as `StatRow` gives its boxes. */
export function DeckTileRow({ tiles }: { readonly tiles: readonly Tile[] }) {
  return (
    <View style={s.row}>
      {tiles.map((tile) => (
        <DeckTile key={tile.key} tile={tile} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', gap: theme.space.xs },
  tile: {
    flex: 1,
    gap: theme.space.xxs,
    borderRadius: theme.radius.note,
    paddingVertical: theme.space.xs,
    paddingHorizontal: theme.space.sm,
    backgroundColor: theme.color.onDarkTag,
  },
  label: { ...theme.type.eyebrow, textTransform: 'uppercase', color: theme.color.onDarkEyebrow },
  // `num.s`, as the stat box's figure is: the Level is printed hugely two rows up, and a tile
  // that competed with it would read as a second rating.
  figure: { ...theme.num.s, ...theme.tabular, color: theme.color.surface },
});
