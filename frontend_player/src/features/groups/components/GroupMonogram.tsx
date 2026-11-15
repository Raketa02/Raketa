/**
 * **A group's tile** — two letters on a colour that never changes for that group (play 1, 9, 38,
 * 40; docs/design-system.md 7.20). The letters and the colour key are the backend's (ADR-0183 §5),
 * so every client draws the same tile; this draws it at one of its sizes — as a tile, or as the
 * shield a Hottest groups card lays over its band (#800) — and maps the key to `MONOGRAM_HUES`, the
 * only place a key becomes a hue.
 *
 * **Hidden from assistive technology.** The tile is a picture of the name, and the name is always
 * drawn and spoken beside it; reading *O 3* before *Ogrody 33 Club* would be the name twice, the
 * first time wrong.
 */

import { StyleSheet, Text, View } from 'react-native';

import { MONOGRAM_HUES, theme } from '@/shared/ui';

import type { Monogram } from '../domain/group';

export type MonogramSize = 'card' | 'row' | 'header' | 'shield' | 'sheet';

/**
 * **A tile**, every corner rounded — or **a shield** (#800, home rows 3): square on top, its two
 * lower corners rounded deeper, in a white ring — a Hottest groups card's badge over its band.
 */
export type MonogramShape = 'tile' | 'shield';

export interface GroupMonogramProps {
  readonly monogram: Monogram;
  readonly size: MonogramSize;
  readonly shape?: MonogramShape;
}

/**
 * The key's hue — exported for the band a Hottest groups card draws in the group's colour (#800). A
 * key past the palette — a server that grew it first — wraps rather than failing.
 */
export function monogramHue(key: number): string {
  const index =
    ((Math.trunc(key) % MONOGRAM_HUES.length) + MONOGRAM_HUES.length) % MONOGRAM_HUES.length;
  return MONOGRAM_HUES[index] ?? MONOGRAM_HUES[0];
}

export function GroupMonogram({ monogram, size, shape = 'tile' }: GroupMonogramProps) {
  const side = theme.size.monogram[size];
  const letters = Math.round(side * theme.size.monogram.letters);
  const corners =
    shape === 'tile'
      ? { borderRadius: Math.round(side * theme.size.monogram.radius) }
      : {
          borderBottomLeftRadius: Math.round(side * theme.size.hottest.shieldFoot),
          borderBottomRightRadius: Math.round(side * theme.size.hottest.shieldFoot),
        };

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[
        s.tile,
        {
          width: side,
          height: side,
          ...corners,
          backgroundColor: monogramHue(monogram.colourKey),
        },
        shape === 'shield' ? s.shield : undefined,
      ]}
    >
      {/* Drawn as it comes — never re-cased (ADR-0183 §5). At a large OS text size the letters
          grow and then shrink back to fit the tile — Part 13's mechanism for a fixed box, the
          yes tile's, and never `allowFontScaling={false}`, which is the level bar's alone. */}
      <Text style={[s.letters, { fontSize: letters }]} numberOfLines={1} adjustsFontSizeToFit>
        {monogram.letters}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  tile: { alignItems: 'center', justifyContent: 'center' },
  // The card's white, so the shield reads as lying over the band rather than cut out of it.
  shield: { borderWidth: theme.size.hottest.shieldRing, borderColor: theme.color.surface },
  letters: {
    fontFamily: theme.font.sans[700],
    color: theme.color.surface,
    includeFontPadding: false,
  },
});
