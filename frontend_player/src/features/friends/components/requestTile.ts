/**
 * **The request tile's frame** ([#816](https://github.com/Rakieta02/Rakieta/issues/816); home refactor
 * 2; Q3) — what FRIEND REQUESTS' and ASKED FOR A LEVEL's tiles share in Needs your answer, held once
 * so the two sections' buttons line up on one sheet.
 *
 * Bounded in `ink`, friends 5's request card: something waiting on the reader. **The title takes two
 * lines at most, and the buttons stand at the tile's foot** (`marginTop: 'auto'`): the `wide` rail
 * stands every tile as tall as the tallest, and the room a shorter title leaves goes above the
 * buttons, so they sit level across the rail. What stands above them is each section's own.
 */

import { StyleSheet } from 'react-native';

import { theme } from '@/shared/ui';

/** The most lines a tile's title takes, so its buttons sit level with the next tile's. */
export const TITLE_LINES = 2;

export const REQUEST_TILE = StyleSheet.create({
  tile: { borderColor: theme.color.ink, gap: theme.space.md },
  top: { flexDirection: 'row', gap: theme.space.sm, alignItems: 'flex-start' },
  pressed: { opacity: 0.7 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  buttons: { flexDirection: 'row', gap: theme.space.sm, marginTop: 'auto' },
  button: { flex: 1 },
});
